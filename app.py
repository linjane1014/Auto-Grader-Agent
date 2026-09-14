import streamlit as st
import pandas as pd
import io
import os
import base64
import datetime
import smtplib
import re
import time
import urllib.parse
import email.utils
import zipfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict
import config
from src.agents.extractor import ExtractorAgent
from src.agents.grader import GraderAgent
from src.agents.analyst import AnalystAgent
from src.agents.problem_analyzer import ProblemAnalyzerAgent

st.set_page_config(page_title="常微分方程 Multi-Agent", layout="wide")
st.title("🚀  Multi-Agent 批改系统 ")

# --- 初始化状态机 ---
for key in ['stage', 'extracted_problems', 'grading_results', 'analysis_data', 'final_problems_data', 'uploaded_files', 'final_rubric', 'final_answer']:
    if key not in st.session_state:
        st.session_state[key] = 0 if key == 'stage' else ([] if key in ['extracted_problems', 'grading_results', 'final_problems_data', 'uploaded_files'] else ({} if key == 'analysis_data' else ""))
if 'processing_done' not in st.session_state:
    st.session_state.processing_done = False

# --- 侧边栏：模型配置 ---
st.sidebar.header("⚙️ 模型配置")
provider = st.sidebar.selectbox("选择大模型平台", list(config.MODEL_OPTIONS.keys()))
model_name = st.sidebar.selectbox("选择模型", config.MODEL_OPTIONS[provider])
api_key = st.sidebar.text_input("🔑 API Key", type="password", value=config.DEFAULT_API_KEYS.get(provider, ""))

# --- 侧边栏：动态标准调整 ---
if st.session_state.stage == 2:
    st.sidebar.markdown("---")
    st.sidebar.header("📖 当前应用的批改标准")
    sidebar_preview = st.sidebar.toggle("👁️ 预览模式 (关闭以编辑)", value=True)
    
    if sidebar_preview:
        st.sidebar.markdown("**📌 正在使用的标准答案**")
        st.sidebar.info(st.session_state.final_answer.replace('\\n', '\n').replace('\n', '\n\n'))
        st.sidebar.markdown("**⚖️ 正在使用的评分细则**")
        st.sidebar.warning(st.session_state.final_rubric.replace('\\n', '\n').replace('\n', '\n\n'))
        new_ans, new_rubric = st.session_state.final_answer, st.session_state.final_rubric
    else:
        new_ans = st.sidebar.text_area("📌 编辑标准答案", value=st.session_state.final_answer, height=300)
        new_rubric = st.sidebar.text_area("⚖️ 编辑评分细则", value=st.session_state.final_rubric, height=300)
    
    if st.sidebar.button("🔄 应用新标准，重新批改全部作业", use_container_width=True):
        st.session_state.final_answer = new_ans
        st.session_state.final_rubric = new_rubric
        st.session_state.processing_done = False
        st.session_state.grading_results = []
        st.rerun()

# ==========================================
# 阶段 0：文件上传与题目提取
# ==========================================
if st.session_state.stage == 0:
    st.header("1️⃣ 上传作业并提取题目")
    uploaded_files = st.file_uploader("📂 批量上传作业 (.tex 和同名 .pdf)", type=['tex', 'pdf'], accept_multiple_files=True)
    
    if st.button("🔍 智能提取题目与生成标准") and api_key and uploaded_files:
        analyzer = ProblemAnalyzerAgent(api_key, provider, model_name)
        sample_tex = next((f.getvalue().decode('utf-8') for f in uploaded_files if f.name.endswith('.tex')), None)
                
        if sample_tex:
            with st.spinner("🧠 正在阅读首份作业并自动解题 (提取多题)..."):
                st.session_state.extracted_problems = analyzer.analyze_and_generate(sample_tex)
                if st.session_state.extracted_problems:
                    st.session_state.uploaded_files = uploaded_files
                    st.session_state.stage = 1
                    st.rerun()
                else:
                    st.error("未能提取到题目，请检查文件或重试。")
        else:
            st.warning("请确保上传了至少一份 .tex 文件。")

# ==========================================
# 阶段 1：教师人工核对评分标准
# ==========================================
elif st.session_state.stage == 1:
    st.header("2️⃣ 教师核对与微调评分标准")
    
    preview_mode = st.toggle("👁️ 开启公式渲染预览模式 (关闭以修改源码)", value=True)
    updated_problems = []
    
    for i, prob in enumerate(st.session_state.extracted_problems):
        st.markdown(f"### 题目 {i+1}：")
        st.markdown(f"> {prob.get('question', '未知题目')}")
        
        col1, col2 = st.columns(2)
        with col1:
            if preview_mode:
                st.markdown("**📖 标准答案 (渲染效果)**")
                current_ans = st.session_state.get(f"ans_{i}", prob.get('standard_answer', ''))
                st.info(current_ans.replace('\\n', '\n').replace('\n', '\n\n'))
                new_ans = current_ans
            else:
                new_ans = st.text_area(f"📖 标准答案 (第 {i+1} 题)", value=st.session_state.get(f"ans_{i}", prob.get('standard_answer', '')), height=200, key=f"ans_{i}")
                
        with col2:
            if preview_mode:
                st.markdown("**📝 评分标准 (渲染效果)**")
                current_rubric = st.session_state.get(f"rub_{i}", prob.get('rubric', ''))
                st.warning(current_rubric.replace('\\n', '\n').replace('\n', '\n\n'))
                new_rubric = current_rubric
            else:
                new_rubric = st.text_area(f"📝 评分标准 (第 {i+1} 题)", value=st.session_state.get(f"rub_{i}", prob.get('rubric', '')), height=200, key=f"rub_{i}")
            
        updated_problems.append({"question": prob.get('question'), "standard_answer": new_ans, "rubric": new_rubric})
        st.markdown("---")
        
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("⬅️ 返回重选文件"):
            st.session_state.stage = 0
            st.rerun()
    with col_btn2:
        if st.button("✅ 确认无误，开始批量批改"):
            st.session_state.final_problems_data = updated_problems
            combined_answer, combined_rubric = "", ""
            for i, p in enumerate(updated_problems):
                combined_answer += f"【第{i+1}题】\n题目：{p['question']}\n标准答案：{p['standard_answer']}\n\n"
                combined_rubric += f"【第{i+1}题评分细则】\n{p['rubric']}\n\n"
            st.session_state.final_answer = combined_answer
            st.session_state.final_rubric = combined_rubric
            st.session_state.stage = 2
            st.rerun()

# ==========================================
# 阶段 2：启动批改与结果展示
# ==========================================
elif st.session_state.stage == 2:
    st.header("3️⃣ 批量批改与多维学情分析")
    
    if not st.session_state.processing_done:
        extractor = ExtractorAgent(api_key, provider, model_name)
        grader = GraderAgent(api_key, provider, model_name)
        analyst = AnalystAgent(api_key, provider, model_name)
        
        progress_bar = st.progress(0)
        file_groups = defaultdict(dict)
        for f in st.session_state.uploaded_files:
            name, ext = os.path.splitext(f.name)
            file_groups[name][ext.lower()] = f
            
        processed_count = 0
        total_groups = len(file_groups)

        for name, files in file_groups.items():
            if '.tex' not in files: continue
            
            content = files['.tex'].getvalue().decode('utf-8')
            pdf_bytes = files.get('.pdf').getvalue() if files.get('.pdf') else None
            
            try:
                with st.spinner(f"🕵️ 提取信息: {name}"):
                    info = extractor.extract(content)
                with st.spinner(f"🧠 AI 多题独立批改中: {name}"):
                    grade_res = grader.grade(content, st.session_state.final_rubric, st.session_state.final_answer)
                
                details = grade_res.get('details', [])
                for d in details:
                    d['Teacher_得分'] = str(d.get('score', '0'))
                    d['Teacher_反馈'] = d.get('feedback', '')
                    d['AI_得分'] = str(d.get('score', '0'))
                    d['AI_诊断'] = d.get('diagnostic', '')
                    d['AI_反馈'] = d.get('feedback', '')

                st.session_state.grading_results.append({
                    "批改时间": datetime.datetime.now().strftime("%Y/%m/%d %H:%M"),
                    "作业名称": name,
                    "学生学号": info.get('student_id', '未知'),
                    "识别姓名": info.get('student_name', '未知'),
                    "原始作业_tex": content,
                    "原始作业_pdf": pdf_bytes, 
                    "AI_总分": str(grade_res.get('total_score', '0')),
                    "details": details 
                })
            except Exception as e:
                st.error(f"处理 {name} 异常: {str(e)}")
                
            processed_count += 1
            progress_bar.progress(processed_count / total_groups)
        
        if st.session_state.grading_results:
            with st.spinner("📊 正在生成多维度学情诊断..."):
                st.session_state.analysis_data = analyst.analyze(st.session_state.grading_results)
                
        st.session_state.processing_done = True
        st.rerun()

    # --- 数据大屏与导出 ---
    if st.session_state.processing_done and st.session_state.grading_results:
        st.markdown("---")
        st.header("📈 学情大屏分析 (Data Dashboard)")
        report = st.session_state.analysis_data
        
        current_scores = [sum(float(d.get('Teacher_得分', 0)) for d in r['details']) for r in st.session_state.grading_results]
            
        col1, col2, col3 = st.columns(3)
        col1.metric("📌 批改总份数", len(st.session_state.grading_results))
        if current_scores: col2.metric("🎯 班级平均总分", f"{sum(current_scores)/len(current_scores):.1f}")
        col3.info(f"**💡 整体学情总结:** {report.get('brief_summary', '无') if report else '无'}")
        
        col4, col5 = st.columns(2)
        with col4:
            st.write("**📊 班级总分频数分布直方图**")
            if current_scores:
                st.bar_chart(pd.Series(current_scores).value_counts().sort_index())
                
        with col5:
            st.write("**📝 单题高频错点预警**")
            pq_data = report.get("per_question_analysis", []) if report else []
            total_stu = len(st.session_state.grading_results)
            if pq_data:
                for item in pq_data:
                    st.markdown(f"**🔹 第 {item.get('q_idx')} 题**")
                    errors = item.get('common_errors', [])
                    if errors:
                        for err in errors:
                            count = err.get('count', 0)
                            st.caption(f"- {err.get('error_desc')}：**{count}** 人 (**{(count / total_stu) * 100 if total_stu > 0 else 0:.1f}%**)")
                    else:
                        st.caption("- 无明显错点")
        
        st.markdown("---")
        st.header("🧑‍🏫 教师复核与修正 (支持多题打分)")
        
        for stu_idx, res in enumerate(st.session_state.grading_results):
            teacher_total = sum(float(d.get('Teacher_得分', 0)) for d in res['details'])
            with st.expander(f"📝 {res['识别姓名']} ({res['学生学号']}) - 最终总分: {teacher_total} (AI 原始总分: {res['AI_总分']})"):
                col_left, col_right = st.columns([1, 1])
                with col_left:
                    if res['原始作业_pdf']:
                        base64_pdf = base64.b64encode(res['原始作业_pdf']).decode('utf-8')
                        st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)
                    else:
                        st.code(res['原始作业_tex'], language='latex')
                        
                with col_right:
                    st.markdown("### ✍️ 单题诊断与修正")
                    for q_i, detail in enumerate(res['details']):
                        st.markdown(f"#### 🔹 第 {detail.get('q_idx', q_i+1)} 题")
                        detail['Teacher_得分'] = st.text_input(f"第 {detail.get('q_idx', q_i+1)} 题得分 (修正)", value=detail['Teacher_得分'], key=f"score_{stu_idx}_{q_i}")
                        
                        tab_edit, tab_view = st.tabs(["✏️ 编辑反馈", "👁️ 预览诊断与反馈"])
                        with tab_edit:
                            detail['Teacher_反馈'] = st.text_area("给学生的单题反馈", value=detail['Teacher_反馈'], height=100, key=f"fb_{stu_idx}_{q_i}")
                        with tab_view:
                            # 提前在 f-string 外部处理换行符，避免语法错误
                            ai_diag_text = str(detail['AI_诊断']).replace('\n', ' ')
                            teacher_fb_text = str(detail['Teacher_反馈']).replace('\n', ' ')
                            
                            st.error(f"**🤖 AI 诊断**: {ai_diag_text}")
                            st.success(f"**👨‍🏫 教师反馈**: {teacher_fb_text}")
                        st.divider()

        st.markdown("---")
        
        # 文本转换引擎
        def format_html_content(raw_text):
            text = str(raw_text)
            text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
            def repl_math(m):
                encoded = urllib.parse.quote(m.group(1).strip())
                return f'<img src="https://latex.codecogs.com/png.image?\dpi{{120}}\bg_white\space {encoded}" style="vertical-align: middle; margin: 0 2px;" alt="" />'
            text = re.sub(r'\$\$(.*?)\$\$', repl_math, text, flags=re.DOTALL)
            text = re.sub(r'\$(.*?)\$', repl_math, text)
            return text.replace('\\n', '<br>').replace('\n', '<br>')

        student_reports = {}
        export_data = []
        for res in st.session_state.grading_results:
            teacher_total = sum(float(d.get('Teacher_得分', 0)) for d in res['details'])
            # 构建 Excel 行
            row = {"批改时间": res["批改时间"], "作业名称": res["作业名称"], "学生学号": res["学生学号"], "识别姓名": res["识别姓名"], "最终总分 (Teacher)": teacher_total}
            # 构建 HTML 报告
            html_content = f"<html><head><meta charset='utf-8'></head><body style='font-family: Arial, sans-serif; padding: 20px;'><h3 style='text-align: center;'>《常微分方程》作业批改报告</h3><p><strong>学生：</strong>{res['识别姓名']} （学号：{res['学生学号']}）</p><p><strong>得分：</strong><span style='color:#e74c3c; font-size:24px;'>{teacher_total}</span> 分</p><hr><h4>📝 详细各题诊断与反馈：</h4><div style='background-color: #f9f9f9; padding: 15px; border-radius: 8px;'>"
            for d in res['details']:
                idx = d.get('q_idx', '未知')
                row.update({f"第{idx}题_修正得分": d['Teacher_得分'], f"第{idx}题_AI诊断": d['AI_诊断'], f"第{idx}题_教师反馈": d['Teacher_反馈']})
                html_content += f"<div style='margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px dashed #ddd;'><strong>第 {idx} 题 (得分: {d['Teacher_得分']}):</strong><br><span style='color:#666;'><strong>诊断:</strong> {format_html_content(d['AI_诊断'])}</span><br><span style='color:#0056b3;'><strong>教师反馈:</strong> {format_html_content(d['Teacher_反馈'])}</span></div>"
            html_content += "</div></body></html>"
            student_reports[f"{res['学生学号']}_{res['识别姓名']}_成绩单"] = html_content
            export_data.append(row)
            
        df = pd.DataFrame(export_data)
        excel_output = io.BytesIO()
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='详细成绩单')
            
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for filename, html_data in student_reports.items():
                zip_file.writestr(f"{filename}.html", html_data)
                
        st.header("📥 数据与报告导出")
        col_dl1, col_dl2, col_dl3 = st.columns([2, 2, 1])
        with col_dl1: st.download_button("📊 下载 Excel 成绩总表", data=excel_output.getvalue(), file_name="多题批改_记录.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with col_dl2: st.download_button("🗂️ 下载独立成绩单 (ZIP)", data=zip_buffer.getvalue(), file_name="全班成绩单.zip", mime="application/zip", use_container_width=True)
        with col_dl3: 
            if st.button("🔄 重置系统", use_container_width=True):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()

        st.markdown("---")
        # ==========================================
        # 自动化成绩分发 (读取 config 配置)
        # ==========================================
        st.header("📧 自动化成绩分发 (邮件服务器)")
        roster_file = st.file_uploader("📋 上传学生通讯录 (.xlsx 或 .csv)", type=['xlsx', 'csv'])
        
        col_mail1, col_mail2 = st.columns(2)
        with col_mail1: sender_email = st.text_input("发件人邮箱账户:", value=config.SMTP_DEFAULT_SENDER)
        with col_mail2: sender_password = st.text_input("发件人邮箱授权码:", value=config.SMTP_DEFAULT_AUTH, type="password")
            
        if st.button("🚀 匹配名单并发送成绩单", use_container_width=True):
            if not sender_email or not sender_password or not roster_file:
                st.warning("⚠️ 请确认邮箱凭证和通讯录均已就绪。")
            else:
                try:
                    roster_df = pd.read_csv(roster_file) if roster_file.name.endswith('.csv') else pd.read_excel(roster_file)
                    id_col = next((c for c in roster_df.columns if '学号' in str(c)), None)
                    name_col = next((c for c in roster_df.columns if '姓名' in str(c)), None)
                    email_col = next((c for c in roster_df.columns if '邮箱' in str(c) or 'email' in str(c).lower()), None)
                    
                    if not email_col:
                        st.error("❌ 通讯录缺失邮箱列。")
                    else:
                        mapping = {}
                        for _, row in roster_df.iterrows():
                            mail_addr = str(row[email_col]).strip()
                            if mail_addr and mail_addr != 'nan':
                                if id_col and pd.notna(row[id_col]): mapping[str(row[id_col]).replace('.0', '').strip()] = mail_addr
                                elif name_col and pd.notna(row[name_col]): mapping[str(row[name_col]).strip()] = mail_addr
                        
                        success_count, progress_text = 0, st.empty()
                        
                        for idx, res in enumerate(st.session_state.grading_results):
                            student_id = str(res.get('学生学号', '')).replace('.0', '').strip()
                            target_email = mapping.get(student_id) or mapping.get(str(res.get('识别姓名', '')).strip())
                            if not target_email: continue
                            
                            msg = MIMEMultipart()
                            msg['From'], msg['To'], msg['Subject'] = sender_email, target_email, f"【成绩通知】作业批改结果 - {res['识别姓名']}"
                            msg['Date'], msg['Message-ID'] = email.utils.formatdate(localtime=True), email.utils.make_msgid()
                            msg.attach(MIMEText(student_reports[f"{student_id}_{res['识别姓名']}_成绩单"], 'html', 'utf-8'))
                            
                            try:
                                server = smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT)
                                server.login(sender_email, sender_password)
                                server.sendmail(sender_email, target_email, msg.as_string())
                                server.quit()
                                success_count += 1
                                progress_text.text(f"⏳ 正在发送: {res['识别姓名']} ({success_count}/{len(st.session_state.grading_results)})...")
                                time.sleep(2)
                            except Exception as e:
                                st.error(f"❌ 发送给 {res['识别姓名']} 失败: {str(e)}")
                                
                        st.success(f"✅ 发送任务结束！成功发送 {success_count} 封邮件。")
                except Exception as ex:
                    st.error(f"❌ 运行出错：{str(ex)}")

# 🚀 Auto-Grader-Agent: 基于 Multi-Agent 的常微分方程智能批改系统

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Framework-FF4B4B.svg)
![DeepSeek](https://img.shields.io/badge/Model-DeepSeek_V4-brightgreen.svg)
![SymPy](https://img.shields.io/badge/Engine-SymPy-orange.svg)

本系统是一款基于 **Multi-Agent（多智能体协作）** 与 **符号计算引擎** 的人机协同教务批改工具。专门针对包含复杂数学公式的大学理工科作业（如常微分方程）设计，旨在将助教从重复性的批改中解放出来，同时确保数学批改的绝对严谨性。

---

## ✨ 核心功能特性

- **🧠 全自动多题解析 (Zero-Shot Extraction)**
  上传学生作业（`.tex` / `.pdf`），系统自动提取所有题目，并在后台独立运算生成参考答案与细粒度评分量规（Rubric）。
- **👨‍🏫 人机协同闭环 (Human-in-the-loop)**
  拒绝 AI 盲目打分。提供可视化的教师复核看板，支持实时 Markdown/LaTeX 双重换行渲染，教师可二次微调 AI 的评分标准并下发执行。
- **🛡️ 防幻觉双重校验 (Anti-Hallucination Mechanism)**
  底层接入大语言模型进行语义理解，同时外挂 `SymPy` 符号计算引擎。当 AI 对公式化简或微积分步骤存疑时，强制交由计算机规则引擎校验，彻底杜绝大模型的数学“幻觉”。
- **📊 多维学情大屏 (Data Dashboard)**
  批改完成后，动态生成班级分数正态分布图，精准提取单题的高频错点预警与人数占比。
- **📧 自动化报告分发 (Automated Distribution)**
  支持一键导出全局 Excel 成绩单；内置高并发邮件发送引擎（支持连接池复用、避让退避与公式动态图片化渲染）；支持一键打包全班独立的 HTML 精美网页成绩单 (ZIP)。

---

## 🛠️ 技术栈

* **核心框架**: `Python`, `Streamlit`
* **智能体驱动**: `OpenAI API 格式` (兼容 DeepSeek-V4-Pro/Flash, 智谱 GLM-4, 阿里通义千问)
* **数学防幻觉引擎**: `SymPy` (Python 符号数学库)
* **数据处理与分发**: `Pandas`, `smtplib`, `email.utils`, `CodeCogs API`

---

## 🚀 工作流 (Workflow)

1. **阶段一（提取与解析）**：批量上传学生的作业文件，智能体自动阅读并解析考题。
2. **阶段二（核对与微调）**：教师通过双屏对照看板，核对并微调每道题的标准答案与采分点。
3. **阶段三（批改与分发）**：系统高并发完成全班批改，生成可视化大屏。教师完成个别人工修正后，一键发送批改邮件或导出本地成绩报告。




---
*Developed by [L]*

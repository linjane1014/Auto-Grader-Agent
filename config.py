import os
# from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
# load_dotenv()

# ==========================================
# 1. 核心模型与路由配置
# ==========================================
API_BASE_URLS = {
    "DeepSeek": "https://api.deepseek.com",
    "Zhipu": "https://open.bigmodel.cn/api/paas/v4/",
    "Qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1"
}

MODEL_OPTIONS = {
    "DeepSeek": ["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-reasoner", "deepseek-chat"],
    "Zhipu": ["glm-4-plus", "glm-4-0520", "glm-4-flash"],
    "Qwen": ["qwen-max", "qwen-plus", "qwen-turbo"]
}

DEFAULT_API_KEYS = {
    "DeepSeek": os.getenv("DEEPSEEK_API_KEY", ""),
    "Zhipu": os.getenv("ZHIPU_API_KEY", ""),
    "Qwen": ""
}

# ==========================================
# 2. 邮件分发配置
# ==========================================
SMTP_SERVER = "smtp.163.com"
SMTP_PORT = 465
SMTP_DEFAULT_SENDER = os.getenv("SMTP_SENDER_EMAIL", "")
SMTP_DEFAULT_AUTH = os.getenv("SMTP_AUTH_CODE", "")

# ==========================================
# 3. 预设标准与文本
# ==========================================
DEFAULT_RUBRIC = """满分10分，请严格按照以下标准给分，不得给同情分：
1. 正确写出积分因子公式，给 4 分。
2. 积分过程计算完全正确，给 4 分。
3. 最终通解整理正确，且必须包含积分常数 C，给 2 分。
4. 若遗漏常数 C，强制扣 2 分。
5. 若完全写错或空白，给 0 分。"""

DEFAULT_ANSWER = """题目：y' - (2/x)y = x^2 * e^x
1. 识别为一阶线性非齐次方程，P(x) = -2/x, Q(x) = x^2 * e^x。
2. 积分因子：\mu(x) = e^{\int (-2/x) dx} = e^{-2 \ln x} = x^{-2}。
3. 乘积分因子整理：(y * x^{-2})' = e^x。
4. 两边积分：y * x^{-2} = \int e^x dx = e^x + C。
5. 最终通解：y = x^2(e^x + C)。"""

# ==========================================
# 4. 智能体提示词模板 (Prompt Templates)
# ==========================================
ANALYZER_PROMPT = """你是一个资深的大学数学教授。请从学生提交的作业 LaTeX 源码中，提取出所有的数学题目。
对于每一道提取出的题目，你需要独立思考并生成：
1. 完整的题目内容。
2. 详细的标准推导答案。
3. 对应的细粒度评分标准（Rubric）。

【绝对指令】
必须以纯 JSON 格式输出，绝不允许使用 ```json 标记。由于输出为 JSON，所有的反斜杠必须双重转义（例如 \\\\int）。
必须严格遵守以下数据结构：
{
    "problems": [
        {
            "id": 1,
            "question": "求微分方程...",
            "standard_answer": "1. 识别方程类型...",
            "rubric": "本题满分10分..."
        }
    ]
}"""

GRADER_PROMPT_TEMPLATE = """你是一个极其严格的大学数学助教。请阅读学生的 LaTeX 作答，并针对以下给出的【各题标准答案】与【评分细则】，逐一进行独立批改。如果你对化简步骤不确定，立刻调用 verify_equation_equivalence 工具。

【标准答案参考】
{answer}

【评分细则】
{rubric}

【绝对指令】
1. 必须使用全中文回复。
2. 必须以纯 JSON 格式输出，绝不允许带有 ```json 标记。
3. 所有的数学公式和变量必须使用 $ 符号包裹。
4. 所有的反斜杠必须双重转义（例如写成 \\\\frac{{1}}{{x}}）。

必须严格按照以下 JSON 结构输出批改结果：
{{
    "total_score": "计算总和（数字）",
    "details": [
        {{
            "q_idx": 1,
            "score": "该题得分",
            "diagnostic": "该题的具体诊断指出对错...",
            "feedback": "该题给学生的反馈..."
        }}
    ]
}}"""

ANALYST_PROMPT = """你是一个资深数学数据分析师。请根据传入的学生单题成绩与总分列表，输出全局和单题的分析。
【绝对格式要求】
1. 以纯 JSON 格式输出，不使用 ```json 标记。反斜杠需双重转义。

必须包含以下字段：
{
    "average_total_score": 25.5,
    "per_question_analysis": [
        {
            "q_idx": 1,
            "average_score": 8.5,
            "common_errors": [
                {"error_desc": "遗漏常数C", "count": 3}
            ]
        }
    ],
    "brief_summary": "总体来看..."
}"""

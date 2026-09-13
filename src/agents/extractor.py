from openai import OpenAI
import json
import re

class ExtractorAgent:
    def __init__(self, api_key: str, provider: str, model: str):
        self.model = model
        # 动态路由分配 Base URL
        if provider == "Zhipu":
            base_url = "https://open.bigmodel.cn/api/paas/v4/"
        elif provider == "DeepSeek":
            base_url = "https://api.deepseek.com"
        else:
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    def extract(self, text: str) -> dict:
        system_prompt = """你是一个专门的信息提取智能体。只负责从文本中提取学生的姓名和10位数字学号。
必须返回纯 JSON，格式：{"student_name": "姓名", "student_id": "学号"}。如果没有，填"未知"。不要输出任何多余解释。"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ]
            )
            content = response.choices[0].message.content
            match = re.search(r'\{.*\}', content, re.DOTALL)
            return json.loads(match.group(0)) if match else {"student_name": "未知", "student_id": "未知"}
        except:
            return {"student_name": "未知", "student_id": "未知"}
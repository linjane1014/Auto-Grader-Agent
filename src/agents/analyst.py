from openai import OpenAI
import json
import config

class AnalystAgent:
    def __init__(self, api_key: str, provider: str, model: str):
        self.model = model
        base_url = config.API_BASE_URLS.get(provider, config.API_BASE_URLS["Qwen"])
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def analyze(self, results: list) -> dict:
        clean_results = [{"总分": r.get("AI_总分", "0"), "各题详情": [{"题号": d["q_idx"], "得分": d["AI_得分"], "诊断": d["AI_诊断"]} for d in r.get("details", [])]} for r in results]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": config.ANALYST_PROMPT},
                    {"role": "user", "content": json.dumps(clean_results, ensure_ascii=False)}
                ],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                return json.loads(content[start_idx:end_idx+1], strict=False)
            return {}
        except Exception as e:
            print(f"学情分析解析失败: {e}")
            return {}
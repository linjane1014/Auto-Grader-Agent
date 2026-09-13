from openai import OpenAI
import json
import config

class ProblemAnalyzerAgent:
    def __init__(self, api_key: str, provider: str, model: str):
        self.model = model
        base_url = config.API_BASE_URLS.get(provider, config.API_BASE_URLS["Qwen"])
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def analyze_and_generate(self, latex_content: str) -> list:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": config.ANALYZER_PROMPT},
                    {"role": "user", "content": latex_content}
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
                json_str = content[start_idx:end_idx+1]
                return json.loads(json_str, strict=False).get("problems", [])
            return []
        except Exception as e:
            print(f"题目解析失败: {e}")
            return []
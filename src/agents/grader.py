from openai import OpenAI
import json
import config
from src.tools.math_tool import verify_equation_equivalence, MATH_TOOL_DEF

class GraderAgent:
    def __init__(self, api_key: str, provider: str, model: str):
        self.model = model
        base_url = config.API_BASE_URLS.get(provider, config.API_BASE_URLS["Qwen"])
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def grade(self, latex_content: str, rubric: str, standard_answer: str) -> dict:
        system_prompt = config.GRADER_PROMPT_TEMPLATE.format(answer=standard_answer, rubric=rubric)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请批改以下作业：\n{latex_content}"}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            tools=[MATH_TOOL_DEF]
        )
        choice = response.choices[0]
        
        if choice.message.tool_calls:
            messages.append({
                "role": "assistant",
                "content": choice.message.content or "",
                "tool_calls": [{"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in choice.message.tool_calls]
            })
            for tc in choice.message.tool_calls:
                args = json.loads(tc.function.arguments)
                tool_res = verify_equation_equivalence(args.get('expr1_str'), args.get('expr2_str'))
                messages.append({"role": "tool", "content": tool_res, "tool_call_id": tc.id})
                
            final_res = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.1)
            content = final_res.choices[0].message.content
        else:
            content = choice.message.content
            
        content = content.strip()
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        
        try:
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            if start_idx != -1 and end_idx != -1:
                return json.loads(content[start_idx:end_idx+1], strict=False)
            raise ValueError("未找到 JSON 括号")
        except Exception as e:
            print(f"判卷解析失败: {e}")
            return {"total_score": "0", "details": [{"q_idx": 1, "score": "0", "diagnostic": "AI解析失败", "feedback": "AI解析失败"}]}
import sympy as sp
import json

def verify_equation_equivalence(expr1_str: str, expr2_str: str) -> str:
    """使用 sympy 验证两个数学表达式是否等价"""
    try:
        expr1_str = expr1_str.replace('^', '**').replace('e', 'E')
        expr2_str = expr2_str.replace('^', '**').replace('e', 'E')
        
        expr1 = sp.sympify(expr1_str)
        expr2 = sp.sympify(expr2_str)
        if sp.simplify(expr1 - expr2) == 0:
            return "验证结果：True。两个表达式在数学上完全等价。"
        else:
            return "验证结果：False。两个表达式不等价。"
    except Exception as e:
        return f"验证出错，无法解析该表达式: {e}"

MATH_TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "verify_equation_equivalence",
        "description": "调用底层 sympy 数学引擎，验证学生的推导步骤是否与标准结果逻辑等价。遇到复杂的公式化简、积分结果核对时，必须调用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "expr1_str": {"type": "string", "description": "要比对的第一个表达式，转化为 Python 兼容的数学字符串，如 x**2 + 2*x"},
                "expr2_str": {"type": "string", "description": "要比对的第二个表达式"}
            },
            "required": ["expr1_str", "expr2_str"]
        }
    }
}

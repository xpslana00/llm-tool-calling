"""
LLM Tool Calling demo
---------------------
Skript zavola LLM API (OpenAI), model si podle potreby vyzada nastroj
(vypocetni funkci), skript nastroj lokalne spusti a vysledek vrati zpet LLM,
ktere z nej sestavi finalni odpoved.
"""
import ast
import json
import math
import operator
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()  # cte OPENAI_API_KEY z prostredi

# ---------------------------------------------------------------------------
# Nastroje (tools)
# ---------------------------------------------------------------------------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv, ast.USub: operator.neg, ast.UAdd: operator.pos,
}
_FUNCS = {"sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
          "log": math.log, "abs": abs, "round": round}
_CONSTS = {"pi": math.pi, "e": math.e}


def _eval(node):
    """Bezpecne vyhodnoceni matematickeho vyrazu (bez eval())."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
        return _FUNCS[node.func.id](*[_eval(a) for a in node.args])
    if isinstance(node, ast.Name) and node.id in _CONSTS:
        return _CONSTS[node.id]
    raise ValueError("Nepodporovany vyraz")


def calculate(expression: str) -> dict:
    try:
        return {"expression": expression, "result": _eval(ast.parse(expression, mode="eval").body)}
    except Exception as exc:  # vratime chybu modelu, at na ni muze reagovat
        return {"expression": expression, "error": str(exc)}


def get_current_datetime() -> dict:
    return {"now": datetime.now().isoformat(timespec="seconds")}


AVAILABLE_TOOLS = {"calculate": calculate, "get_current_datetime": get_current_datetime}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Presne spocita matematicky vyraz. Podporuje + - * / ** % //, "
                           "funkce sqrt, sin, cos, tan, log, abs, round a konstanty pi, e.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "Napr. '(12.5*4)+sqrt(16)'"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Vrati aktualni datum a cas.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

# ---------------------------------------------------------------------------
# Hlavni smycka: LLM -> tool -> LLM
# ---------------------------------------------------------------------------
def run(question: str, max_rounds: int = 5) -> str:
    messages = [
        {"role": "system", "content": "Jsi uzitecny asistent. Na vypocty vzdy pouzij nastroj calculate."},
        {"role": "user", "content": question},
    ]

    for _ in range(max_rounds):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS_SCHEMA, tool_choice="auto"
        )
        msg = response.choices[0].message

        if not msg.tool_calls:          # model uz ma finalni odpoved
            return msg.content

        messages.append(msg)            # zprava s pozadavkem na volani nastroje
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            func = AVAILABLE_TOOLS.get(name)
            result = func(**args) if func else {"error": f"Neznamy nastroj {name}"}
            print(f"[tool] {name}({args}) -> {result}")
            messages.append({                # vysledek nastroje zpet do LLM
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    return "Prekrocen maximalni pocet kol volani nastroju."


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Kolik je (1234 * 5678) / 3 + sqrt(144)? A jake je dnes datum?"
    print(f"Otazka: {q}\n")
    print(f"\nOdpoved: {run(q)}")

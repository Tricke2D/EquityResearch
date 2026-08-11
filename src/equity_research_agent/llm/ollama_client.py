"""
Wrapper client untuk Ollama dengan dukungan tool-calling dan citation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import ollama
from equity_research_agent.llm.tools.calculate_ratio_tool import (
    CALCULATE_RATIO_TOOL_SCHEMA, execute_calculate_ratio_tool
)

MODEL_NAME = "llama3.2:3b"

TOOL_REGISTRY = {
    "calculate_ratio": execute_calculate_ratio_tool,
}


def ask_with_tools(user_prompt: str, system_prompt: str = None, sources: list = None) -> str:
    """
    Kirim prompt ke LLM dengan akses tool calculate_ratio.
    sources: list dict dengan statement_id, page, line untuk citation.
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=messages,
            tools=[CALCULATE_RATIO_TOOL_SCHEMA],
        )
    except Exception as e:
        return f"Error: {e}. Pastikan Ollama running."

    tool_calls = response.get("message", {}).get("tool_calls", [])
    if not tool_calls:
        return response["message"]["content"]

    messages.append(response["message"])

    for call in tool_calls:
        fn_name = call["function"]["name"]
        fn_args = call["function"]["arguments"]
        tool_fn = TOOL_REGISTRY.get(fn_name)
        
        if tool_fn:
            # Kirim sources ke tool
            result = tool_fn(fn_args, sources=sources)
            messages.append({
                "role": "tool",
                "content": str(result),
            })

    try:
        final_response = ollama.chat(model=MODEL_NAME, messages=messages)
        return final_response["message"]["content"]
    except Exception as e:
        return f"Error final response: {e}"
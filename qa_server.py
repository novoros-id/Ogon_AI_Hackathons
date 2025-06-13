# qa_server.py

import requests
from fastmcp import FastMCP
mcp = FastMCP("QA Server", port=3335)
@mcp.tool(
    name="ask_llama3",
    description="Отвечает на любые вопросы"
    )
def ask_llama3(question: str) -> str:
    """
    name: ask_llama3
    description: Отвечает на любые вопросы
    parameters:
      question: string
    returns: string
    """
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": question,
                "stream": False
            }
        )
        if response.status_code == 200:
            return response.json().get("response", "Нет ответа от модели.")
        else:
            return f"Ошибка Ollama: {response.status_code}"
    except Exception as e:
        return f"Ошибка при вызове модели: {str(e)}"


if __name__ == "__main__":
    print("Запуск QA Server на порту 3335")
    mcp.run(transport="streamable-http")
    
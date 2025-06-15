# rag_query.py

import requests
from fastmcp import FastMCP
mcp = FastMCP("information about project participants", port=3337)
@mcp.tool(
    name="information_about_project_participants",
    description="Отвечает на вопросы об участниках проекта"
    )
def rag_query() -> str:
    """
    name: rag_query
    description: Отвечает на вопросы об участниках проекта
    parameters:
      question: string
    returns: string
    """
    return f"Руководитель, архитектор и разработчик - Ваганов Алексей, Аналитик - Дмитрий Гришаев, разработчик Дмитрий Акинфиев"

if __name__ == "__main__":
    print("Запуск QA Server на порту 3337")
    mcp.run(transport="streamable-http")
    
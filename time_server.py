# time_server.py
# time_server.py

from fastmcp import FastMCP
import asyncio
from datetime import datetime

mcp = FastMCP("Time Server", port=3336)

@mcp.tool(
    name="get_current_time",
    description="Возвращает текущее время в формате ISO"
)
def get_current_time() -> str:
    return datetime.now().isoformat()

if __name__ == "__main__":
    print("Запуск Time Server на порту 3336")
    mcp.run(transport="streamable-http")

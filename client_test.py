from fastmcp import Client
import asyncio
import json

config = {
        "mcpServers": {
        "local": {
            "url": "http://localhost:8888/mcp",
            "transport": "streamable-http"
                }
            }
        }

client = Client(config)

async def main():
    # Connection is established here
    async with client:
        print(f"Client connected: {client.is_connected()}")

        # Make MCP calls within the context
        tools = await client.list_tools()
        print(f"Available tools: {tools}")

        # if any(tool.name == "greet" for tool in tools):
        #     result = await client.call_tool("greet", {"name": "World"})
        #     print(f"Greet result: {result}")

    # Connection is closed automatically here
    print(f"Client connected: {client.is_connected()}")

if __name__ == "__main__":
    asyncio.run(main())


# async def main():
#     # Конфигурация клиента для streamable-http транспорта
#     config = {
#         "mcpServers": {
#             "math": {
#                 "url": "http://localhost:3334/mcp/http-stream",
#                 "transport": "streamable-http"
#             }
#         }
#     }

#     # Создание клиента
#     client = Client(config)

#     async with client:
#         # Запрос списка инструментов
#         tools_response = await client.list_tools(server="math")
#         print("Available tools:")
#         print(json.dumps(tools_response, indent=2, ensure_ascii=False))

# if __name__ == "__main__":
#     asyncio.run(main())
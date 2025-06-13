

# mcp_agent_core.py

import logging
import asyncio
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager

from fastmcp import Client
from fastmcp import tools as Tool

from config import LOG_LEVEL, MCP_SERVERS_CONFIG, OLLAMA_API_URL
from tools import extract_text_content

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("MCPAgent")


class UserQueryRequest(BaseModel):
    user_input: str


class AgentResponse(BaseModel):
    tool_name: Optional[str] = None
    args: Dict[str, Any] = {}
    reply: Optional[str] = None


class MCPAgent:
    def __init__(self):
        self.tools_map: Dict[str, Tool] = {}
        self.mcp_clients: Dict[str, Client] = {}

    async def discover_tools(self):
        """Обнаружение инструментов через MCP"""
        logger.info("Discovering tools from MCP servers...")

        for server_name, server_config in MCP_SERVERS_CONFIG.items():
            url = server_config["url"]
            transport = server_config.get("transport", "default")
            try:
                # Формируем config точно так, как в рабочем скрипте
                full_config = {
                    "mcpServers": {
                        server_name: {
                            "url": url,
                            "transport": transport
                        }
                    }
                }

                # Создаём клиент
                client = Client(full_config)
                self.mcp_clients[server_name] = client

                async with client:
                    tools = await client.list_tools()
                    for tool in tools:
                        tool.server_url = url  # сохраняем URL для дальнейшего вызова
                        self.tools_map[tool.name] = tool
                        logger.info(f"Found tool '{tool.name}' on {server_name}")
            except Exception as e:
                logger.error(f"Can't connect to server {url}: {e}")
    # async def discover_tools(self):
    #     print("""Обнаружение инструментов через MCP""")
    #     logger.info("Discovering tools from MCP servers...")

    #     for server_name, server_config in MCP_SERVERS_CONFIG.items():

    #         try:
    #             config = {
    #                 "mcpServers": {
    #                     server_name: server_config
    #                 }
    #             }

    #             client = Client(config)
                
    #             async with client:
    #                 tools = await client.list_tools()
    #                 for tool in tools:
    #                     tool.server_url = server_config["url"]
    #                     self.tools_map[tool.name] = tool
    #                     logger.info(f"Found tool '{tool.name}' on {server_name}")
    #                 self.mcp_clients[server_name] = client
    #         except Exception as e:
    #             logger.error(f"Can't connect to server {server_config['url']}: {e}")

    def build_prompt_for_llm(self, user_input: str) -> str:
        """Формирует промпт для LLM с описанием инструментов"""
        prompt = "Ты помощник, который должен выбрать подходящий инструмент.\n"
        prompt += "Доступные инструменты:\n\n"

        for i, (name, tool) in enumerate(self.tools_map.items(), start=1):
            description = getattr(tool, "description", "Нет описания")
            input_schema = getattr(tool, "inputSchema", {})

            prompt += f"{i}. Инструмент: {name}\n"
            prompt += f"   Описание: {description}\n"
            prompt += f"   Параметры: {input_schema}\n\n"

        prompt += f"Запрос пользователя: {user_input}\n\n"
        prompt += "ОТВЕЧАЙ ТОЛЬКО JSON, БЕЗ ЛИШНИХ СЛОВ:\n"
        prompt += "{\n"
        prompt += '  "function": "...",\n'
        prompt += '  "args": {...}\n'
        prompt += "}\n"

        logger.debug(f"Сформированный промпт:\n{prompt}")
        return prompt

    async def query_ollama(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Вызывает Ollama API для выбора инструмента"""
        import aiohttp

        payload = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(OLLAMA_API_URL, json=payload) as res:
                if res.status == 200:
                    data = await res.text()
                    lines = data.strip().split('\n')
                    last_line = json.loads(lines[-1])
                    try:
                        return json.loads(last_line["response"])
                    except KeyError:
                        return None
                else:
                    logger.error(f"Ollama API error: {res.status} — {await res.text()}")
                    return None

    async def process_query(self, user_input: str) -> AgentResponse:
        """Основной метод обработки запроса от пользователя"""
        logger.info(f"Processing user input: {user_input}")

        if not self.tools_map:
            return AgentResponse(reply="Нет доступных инструментов")

        prompt = self.build_prompt_for_llm(user_input)
        decision = await self.query_ollama(prompt)

        if not decision or "function" not in decision:
            return AgentResponse(reply="Не удалось определить действие")

        tool_name = decision["function"]
        args = decision.get("args", {})

        if tool_name not in self.tools_map:
            return AgentResponse(reply=f"Неизвестный инструмент: {tool_name}")

        tool = self.tools_map[tool_name]
        server_name = next(name for name, conf in MCP_SERVERS_CONFIG.items()
                           if conf["url"] == tool.server_url)

        client = self.mcp_clients[server_name]

        try:
            result = await client.call_tool(tool_name, args)
            reply = extract_text_content(result)
        except Exception as e:
            logger.error(f"Ошибка при вызове инструмента: {e}", exc_info=True)
            reply = f"Ошибка при вызове инструмента: {str(e)}"

        return AgentResponse(tool_name=tool_name, args=args, reply=reply)


# === FastAPI Сервис ===

agent = MCPAgent()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await agent.discover_tools()
    yield

app = FastAPI(lifespan=lifespan)


@app.post("/query", response_model=AgentResponse)
async def handle_query(request: UserQueryRequest):
    return await agent.process_query(request.user_input)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


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
        prompt = "Ты помощник, который должен выбрать подходящий инструмент. При выборе инструмента обращай внимание на описание\n"
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

        #logger.debug(f"Сформированный промпт:\n{prompt}")
        print(prompt)
        return prompt
    async def query_ollama(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Вызывает Ollama API для получения JSON-ответа"""
        import aiohttp

        payload = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(OLLAMA_API_URL, json=payload) as res:
                    if res.status == 200:
                        data = await res.text()
                        lines = data.strip().split('\n')
                        last_line = json.loads(lines[-1])
                        
                        # Проверяем, является ли "response" валидным JSON
                        try:
                            return json.loads(last_line["response"])
                        except json.JSONDecodeError:
                            #logger.warning("LLM вернул текст вместо JSON")
                            return {"response": last_line["response"]}
                    else:
                        logger.error(f"Ollama API error: {res.status} — {await res.text()}")
                        return None
            except Exception as e:
                logger.error(f"Ошибка при обращении к Ollama: {e}", exc_info=True)
                return None
    # async def query_ollama(self, prompt: str) -> Optional[Dict[str, Any]]:
    #     """Вызывает Ollama API для выбора инструмента"""
    #     import aiohttp

    #     payload = {
    #         "model": "llama3",
    #         "prompt": prompt,
    #         "stream": False
    #     }

    #     async with aiohttp.ClientSession() as session:
    #         async with session.post(OLLAMA_API_URL, json=payload) as res:
    #             if res.status == 200:
    #                 data = await res.text()
    #                 lines = data.strip().split('\n')
    #                 last_line = json.loads(lines[-1])
    #                 try:
    #                     return json.loads(last_line["response"])
    #                 except KeyError:
    #                     return None
    #             else:
    #                 logger.error(f"Ollama API error: {res.status} — {await res.text()}")
    #                 return None

    async def process_query(self, user_input: str) -> AgentResponse:
        """Основной метод обработки запроса от пользователя"""
        logger.info(f"Processing user input: {user_input}")

        if not self.tools_map:
            return AgentResponse(reply="Нет доступных инструментов")

        prompt = self.build_prompt_for_llm(user_input)
        decision = await self.query_ollama(prompt)

        print(f"[DEBUG] LLM выбор mcp сервера: {decision}")

        if not decision or "function" not in decision:
            return AgentResponse(reply="Не удалось определить действие")

        tool_name = decision["function"]
        args = decision.get("args", {})

        if tool_name not in self.tools_map:
            return AgentResponse(reply=f"Неизвестный инструмент: {tool_name}")

        tool = self.tools_map[tool_name]
        server_url = getattr(tool, "server_url", None)

        if not server_url:
            logger.warning(f"No server URL found for tool {tool_name}")
            return AgentResponse(reply="Ошибка: сервер не найден")

        # Ищем имя сервера по URL
        server_name = None
        for name, conf in MCP_SERVERS_CONFIG.items():
            if conf["url"] == server_url:
                server_name = name
                break

        if not server_name:
            return AgentResponse(reply="Ошибка: конфигурация сервера не найдена")

        # Создаём новый клиент для этого вызова
        server_config = MCP_SERVERS_CONFIG[server_name]

        config = {
            "mcpServers": {
                server_name: {
                    "url": server_config["url"],
                    "transport": server_config["transport"]
                }
            }
        }

        client = Client(config)

        try:
            async with client:
                result = await client.call_tool(tool_name, args)
                # Логируем полный ответ от сервера
                #print(f"[DEBUG] Raw MCP response: {result}")
                #logger.debug(f"Raw MCP response for {tool_name}: {result}")

                reply = extract_text_content(result)
                print(f"[DEBUG] extract_text_content: {reply}")

                rag_prompt = f"""
                Пользователь спросил: "{user_input}"

                Вот данные, полученные от MCP-инструмента:
                {reply}

                В полученных данных MCP-инструмента найди ответ на вопрос и сделай человекочитаемый вывод только на русском языке.
                """
                #logger.debug(f"RAG-промпт для LLM:\n{rag_prompt}")
                print(f"[DEBUG] RAG-промпт для LLM: {rag_prompt}")
                rag_response = await self.query_ollama(rag_prompt)
                print(f"[DEBUG] RAG-ответ от LLM: {rag_response}")

                reply = rag_response.get("response", "Не могу интерпретировать данные") \
                    if isinstance(rag_response, dict) else "LLM не вернул текстовый ответ"


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
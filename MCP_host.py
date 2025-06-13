from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from fastmcp import Client
import json
import requests
import re
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Host", description="Host for coordinating MCP servers with Ollama")

# Конфигурация MCP-серверов
MCP_CONFIG = {
    "mcpServers": {
        "math": {
            "url": "http://localhost:3334/mcp",
            "transport": "streamable-http"
        },
        "question": {
            "url": "http://localhost:3335/mcp",
            "transport": "streamable-http"
        }
    }
}

# Модель для входящих запросов от Telegram-бота
class BotRequest(BaseModel):
    query: str

# Глобальные переменные для хранения схем инструментов
TOOLS_SCHEMA = {}

# Функция для вызова Ollama
def call_ollama(prompt: str) -> str:
    """Вызывает локальную модель Ollama для анализа запроса"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",  # Укажите вашу модель, например, llama3
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()["response"]
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")

# Инициализация MCP-клиента и получение схем инструментов
async def initialize_mcp_client():
    global TOOLS_SCHEMA
    client = Client(MCP_CONFIG)
    async with client:
        for server_name in MCP_CONFIG["mcpServers"]:
            tools_response = await client.list_tools(server=server_name)
            TOOLS_SCHEMA[server_name] = tools_response["tools"]
            logger.info(f"Tools for {server_name}: {json.dumps(tools_response, indent=2)}")
    return client

# Обработчик жизненного цикла приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_mcp_client()
    yield

app.lifespan = lifespan

# Эндпоинт для обработки запросов от Telegram-бота
@app.post("/process")
async def process_request(bot_request: BotRequest):
    query = bot_request.query
    logger.info(f"Received query: {query}")

    # Формирование промпта для Ollama
    prompt = f"""
    You are an assistant that routes user queries to one of two MCP servers based on the query content.
    Available servers:
    1. Math Server (name: "math"): Has a tool `add_numbers` that takes two numbers (a, b) and returns their sum.
       Schema: {json.dumps(TOOLS_SCHEMA.get('math', []), indent=2, ensure_ascii=False)}
    2. Question Server (name: "question"): Has a tool `answer_question` that takes a question string and returns an answer.
       Schema: {json.dumps(TOOLS_SCHEMA.get('question', []), indent=2, ensure_ascii=False)}

    User query: "{query}"

    Tasks:
    1. Determine which server and tool to use based on the query.
    2. Generate a JSON request for the selected tool according to its input_schema.
    3. Return **only one** JSON object in the following format, enclosed in ```json ... ```:
    ```json
    {{
        "server": "math" or "question",
        "tool": "add_numbers" or "answer_question",
        "parameters": {{...}}
    }}
    ```
    If the query doesn't match any tool, return an empty JSON:
    ```json
    {{}}
    ```

    Important:
    - Return exactly one JSON block.
    - Use lowercase server names ("math" or "question").
    - Do not include intermediate JSON objects (e.g., just parameters).
    - Ensure the JSON is valid and includes all required fields.

    Examples:
    Query: "Add 5 and 3"
    Response:
    ```json
    {{
        "server": "math",
        "tool": "add_numbers",
        "parameters": {{"a": 5, "b": 3}}
    }}
    ```
    Query: "What is the capital of France?"
    Response:
    ```json
    {{
        "server": "question",
        "tool": "answer_question",
        "parameters": {{"question": "What is the capital of France?"}}
    }}
    ```
    """

    # Вызов Ollama для анализа запроса
    ollama_response = call_ollama(prompt)
    logger.info(f"Ollama response: {ollama_response}")

    try:
        # Парсинг последнего JSON-блока
        matches = list(re.finditer(r'```json\s*(.*?)\s*```', ollama_response, re.DOTALL))
        if not matches:
            raise ValueError("Ollama did not return valid JSON")
        # Берем последний JSON-блок
        decision = json.loads(matches[-1].group(1))
        logger.info(f"Parsed decision: {decision}")
    except (ValueError, json.JSONDecodeError) as e:
        logger.error(f"Error parsing Ollama response: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid Ollama response: {str(e)}")

    # Проверка наличия необходимых ключей
    if not decision:
        raise HTTPException(status_code=400, detail="No suitable tool found for query")
    if not all(key in decision for key in ["server", "tool", "parameters"]):
        logger.error(f"Invalid decision format: {decision}")
        raise HTTPException(status_code=400, detail="Ollama response missing required fields")

    # Приведение server к нижнему регистру
    decision["server"] = decision["server"].lower()

    # Проверка допустимого сервера
    if decision["server"] not in MCP_CONFIG["mcpServers"]:
        logger.error(f"Invalid server: {decision['server']}")
        raise HTTPException(status_code=400, detail=f"Invalid server: {decision['server']}")

    # Вызов MCP-сервера
    client = Client(MCP_CONFIG)
    async with client:
        # Выводим доступные методы клиента для отладки
        logger.info(f"Client methods: {dir(client)}")
        try:
            # Пробуем вызвать call_tool с name и args
            result = await client.call_tool(
                name=decision["tool"],
                args=decision["parameters"],
                server=decision["server"]
            )
            logger.info(f"MCP tool result: {result}")
            return {"status": "success", "result": result}
        except Exception as e:
            logger.error(f"Error calling MCP tool: {str(e)}")
            # Альтернативный вызов через send_request
            try:
                mcp_request = {
                    "type": "tool_call",
                    "tool": decision["tool"],
                    "parameters": decision["parameters"],
                    "request_id": "test_" + str(hash(query))
                }
                result = await client.send_request(mcp_request, server=decision["server"])
                logger.info(f"MCP send_request result: {result}")
                return {"status": "success", "result": result.get("result", result)}
            except Exception as e2:
                logger.error(f"Error calling MCP send_request: {str(e2)}")
                raise HTTPException(status_code=500, detail=f"Error calling MCP tool: {str(e)} or send_request: {str(e2)}")

# Тестовый эндпоинт для проверки схем
@app.get("/tools")
async def get_tools():
    return TOOLS_SCHEMA

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# config.py

LOG_LEVEL = "INFO"

# Список MCP-серверов
MCP_SERVERS_CONFIG = {
    "math": {
        "url": "http://localhost:3334/mcp",
        "transport": "streamable-http"
    },
    "qa": {
        "url": "http://localhost:3335/mcp",
        "transport": "streamable-http"
    }
}

# URL Ollama
OLLAMA_API_URL = "http://localhost:11434/api/generate"
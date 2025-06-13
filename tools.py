# tools.py

from typing import Any
from mcp.types import TextContent


def extract_text_content(result: Any) -> str:
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], TextContent):
        return result[0].text
    return str(result)
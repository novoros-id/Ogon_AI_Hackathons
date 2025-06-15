# tools.py

from typing import Any
from mcp.types import TextContent
import json


# def extract_text_content(result: Any) -> str:
#     if isinstance(result, list) and len(result) > 0 and isinstance(result[0], TextContent):
#         return result[0].text
#     return str(result)

def extract_text_content(result: Any) -> str:
    """
    Возвращает все части текста из списка TextContent
    Если есть JSON — форматируем его
    """
    if isinstance(result, list):
        full_text = []
        for content in result:
            if not isinstance(content, TextContent):
                continue
            try:
                # Если это JSON — форматируем
                parsed = json.loads(content.text)
                full_text.append(json.dumps(parsed, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                full_text.append(content.text)

        return "\n\n".join(full_text)

    elif isinstance(result, TextContent):
        return result.text

    return str(result)
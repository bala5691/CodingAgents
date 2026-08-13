import base64
import json
import mimetypes
import re
from pathlib import Path


def message_text(message) -> str:
    content = message.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(item["text"])

        return "\n".join(parts)

    return str(content)


def extract_json(text: str) -> dict:
    """
    Tolerate models wrapping JSON in ```json fences.
    """
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)

    if fenced:
        text = fenced.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


def image_to_data_uri(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "image/png"
    raw = Path(path).read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"
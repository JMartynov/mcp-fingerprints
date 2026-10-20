import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

def sanitize_unicode_text(text: str) -> str:
    """Cleanly preserve Unicode, CJK, and international characters while stripping control characters."""
    if not isinstance(text, str):
        return ""
    # Strip control characters: [\x00-\x08\x0B\x0C\x0E-\x1F\x7F]
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    # Normalize whitespace (replace multiple spaces/newlines with a single space)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def sanitize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Sanitize metadata fields like description, author, and keywords preserving CJK."""
    if not isinstance(metadata, dict):
        return {}
    
    sanitized = dict(metadata)
    for field in ["description", "author"]:
        if field in sanitized and isinstance(sanitized[field], str):
            sanitized[field] = sanitize_unicode_text(sanitized[field])
            
    if "keywords" in sanitized and isinstance(sanitized["keywords"], list):
        sanitized["keywords"] = [
            sanitize_unicode_text(k) for k in sanitized["keywords"] if isinstance(k, str)
        ]
        
    return sanitized

def sanitize_tool_definition(tool: dict[str, Any]) -> dict[str, Any] | None:
    """Sanitize and normalize a tool definition, returning None if unrecoverable."""
    if not isinstance(tool, dict):
        logger.warning("Tool definition is not a dict: %s", type(tool))
        return None

    name = tool.get("name")
    if not isinstance(name, str):
        logger.warning("Tool definition has invalid name type: %s", type(name))
        return None

    # Use the new unicode-aware sanitizer
    name = sanitize_unicode_text(name)
    if not name:
        logger.warning("Tool definition has empty name after sanitization")
        return None

    description = tool.get("description", "")
    if isinstance(description, str):
        description = sanitize_unicode_text(description)
    else:
        description = ""

    raw_schema = tool.get("inputSchema") or tool.get("input_schema")
    if not isinstance(raw_schema, dict):
        input_schema = {"type": "object", "properties": {}}
    else:
        input_schema = dict(raw_schema)
        if "type" not in input_schema or input_schema["type"] != "object":
            input_schema["type"] = "object"
        props = input_schema.get("properties")
        if not isinstance(props, dict):
            input_schema["properties"] = {}
        else:
            cleaned_props = {}
            for k, v in props.items():
                if isinstance(v, dict):
                    cleaned_props[str(k)] = v
                else:
                    cleaned_props[str(k)] = {}
            input_schema["properties"] = cleaned_props

        req = input_schema.get("required")
        if isinstance(req, (list, tuple)):
            input_schema["required"] = [str(r) for r in req if isinstance(r, (str, int))]
        elif req is not None:
            input_schema["required"] = []

    sanitized = dict(tool)
    sanitized["name"] = name
    sanitized["description"] = description
    sanitized["inputSchema"] = input_schema
    return sanitized

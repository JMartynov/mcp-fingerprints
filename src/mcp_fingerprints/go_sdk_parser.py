"""Conservative extraction of inline official Go SDK tool declarations.

Only literal names, descriptions and JSON-shaped map/slice schemas are resolved.
This is source discovery, not a determination of the tools enabled at runtime.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any

logger = logging.getLogger(__name__)

_TOKEN = re.compile(
    r'//[^\n]*|/\*[\s\S]*?\*/|"(?:[^"\\\n]|\\.)*"|`[^`]*`|'
    r"'(?:[^'\\\n]|\\.)*'|[A-Za-z_]\w*|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|[^\s]"
)


def _string(token: str) -> str:
    if token.startswith("`") and token.endswith("`"):
        return token[1:-1].replace("\r", "")
    if not (token.startswith('"') and token.endswith('"')):
        raise ValueError("not a string literal")
    data = bytearray()
    i = 1
    escapes = {
        "a": 7,
        "b": 8,
        "f": 12,
        "n": 10,
        "r": 13,
        "t": 9,
        "v": 11,
        '"': 34,
        "\\": 92,
    }
    while i < len(token) - 1:
        char = token[i]
        i += 1
        if char != "\\":
            data.extend(char.encode("utf-8"))
            continue
        char = token[i]
        i += 1
        if char in escapes:
            data.append(escapes[char])
        elif char in "xuU":
            count = {"x": 2, "u": 4, "U": 8}[char]
            digits = token[i : i + count]
            if len(digits) != count or not re.fullmatch(r"[0-9a-fA-F]+", digits):
                raise ValueError("invalid escape")
            value = int(digits, 16)
            if char == "x":
                data.append(value)
            else:
                data.extend(chr(value).encode("utf-8"))
            i += count
        elif char in "01234567":
            digits = token[i - 1 : i + 2]
            if not re.fullmatch(r"[0-7]{3}", digits):
                raise ValueError("invalid octal escape")
            data.append(int(digits, 8))
            i += 2
        else:
            raise ValueError("unsupported escape")
    return data.decode("utf-8")


class _Literal:
    def __init__(self, tokens: list[str], pos: int = 0, constants: dict[str, str] | None = None) -> None:
        self.constants = constants or {}
        self.tokens = tokens
        self.pos = pos

    def take(self, expected: str | None = None) -> str:
        if self.pos >= len(self.tokens):
            raise ValueError("truncated literal")
        token = self.tokens[self.pos]
        if expected is not None and token != expected:
            raise ValueError("unsupported expression")
        self.pos += 1
        return token

    def element_type(self) -> None:
        token = self.take()
        if token == "interface":
            self.take("{")
            self.take("}")
        elif token not in ("any", "string", "bool", "int", "float64"):
            raise ValueError("unsupported literal type")

    def skip_value(self) -> None:
        """Skip non-contract fields without evaluating their expressions."""
        stack = []
        start = self.pos
        pairs = {"(": ")", "[": "]", "{": "}"}
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if not stack and token in (",", "}"):
                if self.pos == start:
                    raise ValueError("missing field value")
                return
            self.pos += 1
            if token in pairs:
                stack.append(pairs[token])
            elif token in (")", "]", "}") and (not stack or stack.pop() != token):
                raise ValueError("unbalanced expression")
        raise ValueError("truncated expression")

    def value(self, depth: int = 0) -> Any:
        if depth > 32:
            raise ValueError("literal nesting limit")
        token = self.take()
        if token.startswith(('"', "`")):
            return _string(token)
        if token in self.constants:
            val = self.constants[token]
            if val.startswith(('"', "`")):
                return _string(val)
        if token in ("true", "false", "nil"):
            return {"true": True, "false": False, "nil": None}[token]
        if re.fullmatch(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", token):
            if re.fullmatch(r"-?0\d+", token):
                raise ValueError("unsupported non-decimal number")
            number = float(token) if any(c in token for c in ".eE") else int(token)
            if isinstance(number, float) and not math.isfinite(number):
                raise ValueError("non-finite number")
            return number
        if token == "map":
            for part in ("[", "string", "]"):
                self.take(part)
            self.element_type()
            self.take("{")
            result: dict[str, Any] = {}
            while self.tokens[self.pos : self.pos + 1] != ["}"]:
                key = _string(self.take())
                self.take(":")
                result[key] = self.value(depth + 1)
                if self.tokens[self.pos : self.pos + 1] != ["}"]:
                    self.take(",")
            self.take("}")
            return result
        if token == "[":
            self.take("]")
            self.element_type()
            self.take("{")
            items = []
            while self.tokens[self.pos : self.pos + 1] != ["}"]:
                items.append(self.value(depth + 1))
                if self.tokens[self.pos : self.pos + 1] != ["}"]:
                    self.take(",")
            self.take("}")
            return items
        raise ValueError("unresolved expression")


def parse_official_go_tools(code: str) -> list[dict[str, Any]]:
    """Extract complete inline Server.AddTool literals; skip unresolved contracts.

    Import aliases are respected. Helpers, constants, inferred schemas and
    variable-based registrations need Go type/data-flow analysis and are omitted.
    """
    if "github.com/modelcontextprotocol/go-sdk/mcp" not in code:
        return []
        
    constants: dict[str, str] = {}
    for match in re.finditer(r'const\s+([a-zA-Z0-9_]+)\s*(?:[a-zA-Z0-9_.*]*\s*)?=\s*(["\'][^"\']+["\']|`[^`]+`)', code):
        constants[match.group(1)] = match.group(2)
        
    for match in re.finditer(r'const\s*\(\s*(.*?)\s*\)', code, re.DOTALL):
        block = match.group(1)
        for line_match in re.finditer(r'([a-zA-Z0-9_]+)\s*(?:[a-zA-Z0-9_.*]*\s*)?=\s*(["\'][^"\']+["\']|`[^`]+`)', block):
            constants[line_match.group(1)] = line_match.group(2)
            
    tokens = [t for t in _TOKEN.findall(code) if not t.startswith(("//", "/*"))]
    aliases = set() # fallback
    for i, token in enumerate(tokens):
        if token != "import":
            continue
        start = i + 1
        if tokens[start : start + 1] == ["("]:
            end = next(
                (j for j in range(start, len(tokens)) if tokens[j] == ")"), len(tokens)
            )
            start += 1
        else:
            end = min(start + 2, len(tokens))
        for j in range(start, end):
            if tokens[j] != '"github.com/modelcontextprotocol/go-sdk/mcp"':
                continue
            previous = tokens[j - 1] if j > start else ""
            if previous in (".", "_"):
                continue
            aliases.add(previous if re.fullmatch(r"[A-Za-z_]\w*", previous) else "mcp")
    tools = []
    for i in range(len(tokens) - 8):
        if tokens[i : i + 4] != [".", "AddTool", "(", "&"]:
            continue
        alias = tokens[i + 4]
        if alias not in aliases or tokens[i + 5 : i + 8] != [".", "Tool", "{"]:
            continue
        literal = _Literal(tokens, i + 8, constants=constants)
        fields = {}
        try:
            while literal.tokens[literal.pos : literal.pos + 1] != ["}"]:
                field = literal.take()
                literal.take(":")
                if field in ("Name", "Description", "InputSchema"):
                    fields[field] = literal.value()
                else:
                    literal.skip_value()
                if literal.tokens[literal.pos : literal.pos + 1] != ["}"]:
                    literal.take(",")
            literal.take("}")
            literal.take(",")
            name = fields.get("Name")
            schema = fields.get("InputSchema", {"type": "object", "properties": {}, "required": []})
            description = fields.get("Description", "")
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(description, str)
                or not isinstance(schema, dict)
            ):
                raise ValueError("unresolved name, description or input schema")
        except (ValueError, UnicodeError, OverflowError):
            logger.warning(
                "Unresolved official Go SDK tool literal; extraction does not establish an empty toolset"
            )
            continue
        tools.append({"name": name, "description": description, "inputSchema": schema})
    return tools

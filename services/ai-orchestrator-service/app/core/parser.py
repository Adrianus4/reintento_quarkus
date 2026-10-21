import json
import re
from typing import Any, Dict


def extract_and_parse_json(text: str) -> Dict[str, Any]:
    """
    Extract, repair, and deserialize JSON from model output.
    Handles markdown fences, trailing commas, and unclosed quotes/brackets/braces.
    """
    cleaned = text.strip()

    # 1. Extract from markdown code fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    else:
        # Find the first '{' and last '}'
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
        elif start != -1:
            cleaned = cleaned[start:]

    # 2. Try direct parsing first
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 3. Clean trailing commas (e.g. ", }" or ", ]")
    repaired = re.sub(r",\s*([\}\]])", r"\1", cleaned)

    try:
        return json.loads(repaired)
    except Exception:
        pass

    # 4. Repair incomplete/truncated JSON structures
    repaired = _repair_truncated_json(repaired)

    try:
        return json.loads(repaired)
    except Exception as exc:
        raise ValueError(f"Failed to parse resilient JSON from model output: {str(exc)}\nRaw: {cleaned[:300]}...")


def _repair_truncated_json(text: str) -> str:
    """Repair dangling quotes, open braces, and open brackets."""
    s = text.strip()

    # Check unescaped quotes
    in_string = False
    escape = False
    stack = []

    for char in s:
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char in "{[":
                stack.append(char)
            elif char == "}":
                if stack and stack[-1] == "{":
                    stack.pop()
            elif char == "]":
                if stack and stack[-1] == "[":
                    stack.pop()

    # If truncated inside a string, close quote
    if in_string:
        s += '"'

    # Remove any trailing comma before closing
    s = re.sub(r",\s*$", "", s)

    # Close remaining brackets and braces in reverse order
    while stack:
        opening = stack.pop()
        if opening == "{":
            s += "}"
        elif opening == "[":
            s += "]"

    return s


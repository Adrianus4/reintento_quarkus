import json
from typing import Any, Dict, Optional, Tuple
import yaml

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head", "trace"}


def parse_and_validate_openapi(content: str) -> Tuple[bool, str, str, int, Optional[str]]:
    """
    Parse JSON or YAML OpenAPI contract and validate structure.
    Returns: (is_valid, title, version, endpoints_count, error_message)
    """
    content_stripped = content.strip()
    if not content_stripped:
        return False, "", "", 0, "OpenAPI content is empty"

    parsed_doc: Dict[str, Any] = {}
    try:
        # Try JSON first
        if content_stripped.startswith("{"):
            parsed_doc = json.loads(content_stripped)
        else:
            parsed_doc = yaml.safe_load(content_stripped)
    except Exception as exc:
        return False, "", "", 0, f"Failed to parse contract as JSON or YAML: {str(exc)}"

    if not isinstance(parsed_doc, dict):
        return False, "", "", 0, "Root OpenAPI contract must be a JSON/YAML object"

    # Check for legacy Swagger 2.0
    if "swagger" in parsed_doc:
        return False, "", "", 0, "Legacy Swagger 2.0 detected. TCS Factory requires OpenAPI 3.0.x or 3.1.x"

    openapi_version = parsed_doc.get("openapi")
    if not openapi_version or not str(openapi_version).startswith("3."):
        return False, "", "", 0, f"Unsupported or missing OpenAPI version '{openapi_version}'. Must be 3.x"

    info = parsed_doc.get("info")
    if not isinstance(info, dict):
        return False, "", "", 0, "OpenAPI 'info' object is missing"

    title = str(info.get("title", "")).strip()
    if not title:
        return False, "", "", 0, "OpenAPI 'info.title' is required"

    version = str(info.get("version", "1.0.0")).strip()

    paths = parsed_doc.get("paths")
    if paths is None or not isinstance(paths, dict):
        return False, title, version, 0, "OpenAPI 'paths' dictionary is missing or invalid"

    # Count operations
    endpoints_count = 0
    for path, path_item in paths.items():
        if isinstance(path_item, dict):
            for method in path_item.keys():
                if method.lower() in HTTP_METHODS:
                    endpoints_count += 1

    return True, title, version, endpoints_count, None


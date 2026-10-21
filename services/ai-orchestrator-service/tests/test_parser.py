from app.core.parser import extract_and_parse_json


def test_parse_clean_json():
    raw = '{"name": "QuarkusMicroservice", "version": "1.0.0"}'
    result = extract_and_parse_json(raw)
    assert result["name"] == "QuarkusMicroservice"
    assert result["version"] == "1.0.0"


def test_parse_markdown_fenced_json():
    raw = """
    Here is the requested architectural specification:
    ```json
    {
      "architecture": "Hexagonal",
      "framework": "Quarkus"
    }
    ```
    Hope this helps!
    """
    result = extract_and_parse_json(raw)
    assert result["architecture"] == "Hexagonal"
    assert result["framework"] == "Quarkus"


def test_parse_json_with_trailing_commas():
    raw = '{"modules": ["auth", "payments", ], "enabled": true, }'
    result = extract_and_parse_json(raw)
    assert result["modules"] == ["auth", "payments"]
    assert result["enabled"] is True


def test_repair_truncated_json_missing_braces():
    # Simulates model output cut off before final closing brackets
    raw = '{"blueprint": {"entities": [{"name": "Payment", "amount": 100}'
    result = extract_and_parse_json(raw)
    assert "blueprint" in result
    assert result["blueprint"]["entities"][0]["name"] == "Payment"


def test_repair_truncated_json_inside_string():
    # Simulates truncation right in the middle of a string
    raw = '{"files": {"pom.xml": "<?xml version'
    result = extract_and_parse_json(raw)
    assert "files" in result
    assert "pom.xml" in result["files"]


from typing import Tuple
import httpx
from app.llm.base import BaseLLMClient


class AnthropicClient(BaseLLMClient):
    def __init__(self, api_key: str, mode: str = "balanced", model_name: str = None):
        self.api_key = api_key.strip() if api_key else ""
        self.mode = mode
        self.model_name = model_name if model_name and model_name != "default" else "claude-3-5-sonnet-20241022"
        self.endpoint = "https://api.anthropic.com/v1/messages"
        self.provider = "anthropic"

    def test_connection(self) -> bool:
        if not self.api_key or len(self.api_key) < 10:
            return False
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}]
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(self.endpoint, json=payload, headers=headers)
                return resp.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.2,
    ) -> Tuple[str, int, int]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "system": system_prompt + "\nIMPORTANT: Output MUST be valid JSON only, without markdown fences (no ```json) and no conversational text.",
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": temperature,
        }
        with httpx.Client(timeout=90.0) as client:
            resp = client.post(self.endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", [])
            text = content[0]["text"] if content else "{}"
            usage = data.get("usage", {})
            prompt_tokens = usage.get("input_tokens", len(user_prompt.split()))
            completion_tokens = usage.get("output_tokens", len(text.split()))
            return text, prompt_tokens, completion_tokens


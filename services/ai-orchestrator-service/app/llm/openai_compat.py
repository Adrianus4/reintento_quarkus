from typing import Tuple
import httpx
from app.llm.base import BaseLLMClient

PROVIDER_URLS = {
    "deepseek": "https://api.deepseek.com/chat/completions",
    "grok": "https://api.x.ai/v1/chat/completions",
}

DEEPSEEK_MODELS = {
    "economic": "deepseek-chat",
    "balanced": "deepseek-chat",
    "advanced": "deepseek-reasoner",
}

GROK_MODELS = {
    "economic": "grok-2-mini",
    "balanced": "grok-2",
    "advanced": "grok-2",
}


class OpenAICompatClient(BaseLLMClient):
    def __init__(self, provider: str, api_key: str, mode: str = "balanced"):
        self.provider = provider.lower()
        self.api_key = api_key
        self.mode = mode
        self.endpoint = PROVIDER_URLS.get(self.provider, PROVIDER_URLS["deepseek"])

        if self.provider == "deepseek":
            self.model_name = DEEPSEEK_MODELS.get(mode, "deepseek-chat")
        else:
            self.model_name = GROK_MODELS.get(mode, "grok-2")

    def test_connection(self) -> bool:
        if not self.api_key or len(self.api_key) < 10:
            return False
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1
        }
        try:
            with httpx.Client(timeout=5.0) as client:
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
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(self.endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", len(user_prompt.split()))
            completion_tokens = usage.get("completion_tokens", len(text.split()))
            return text, prompt_tokens, completion_tokens


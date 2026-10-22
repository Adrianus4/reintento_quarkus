from typing import Tuple
import httpx
from app.llm.base import BaseLLMClient

PROVIDER_URLS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
    "grok": "https://api.x.ai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "ollama": "http://localhost:11434/v1/chat/completions",
}

DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "deepseek": "deepseek-chat",
    "grok": "grok-2",
    "openrouter": "anthropic/claude-3.5-sonnet",
    "groq": "llama-3.3-70b-versatile",
    "ollama": "qwen2.5-coder:latest",
}


class OpenAICompatClient(BaseLLMClient):
    def __init__(self, provider: str, api_key: str, mode: str = "balanced", model_name: str = None, base_url: str = None):
        self.provider = provider.lower().strip() if provider else "openai"
        self.api_key = api_key.strip() if api_key else ""
        self.mode = mode

        if base_url:
            self.endpoint = base_url.rstrip("/") + "/chat/completions" if not base_url.endswith("/chat/completions") else base_url
        else:
            self.endpoint = PROVIDER_URLS.get(self.provider, PROVIDER_URLS["openai"])

        if model_name and model_name.strip() and model_name not in ("default", "mock-fast"):
            self.model_name = model_name.strip()
        else:
            self.model_name = DEFAULT_MODELS.get(self.provider, "gpt-4o")

    def test_connection(self) -> Tuple[bool, str]:
        if not self.api_key and self.provider != "ollama":
            return False, f"La API Key de {self.provider.upper()} está vacía."
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
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(self.endpoint, json=payload, headers=headers)
                if resp.status_code in (200, 201):
                    return True, f"Conexión exitosa con {self.provider.upper()} ({self.model_name})."
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", resp.text)
                    return False, f"{self.provider.upper()} API error ({resp.status_code}): {err_msg}"
                except Exception:
                    return False, f"{self.provider.upper()} error ({resp.status_code}): {resp.text[:150]}"
        except Exception as exc:
            return False, f"Error conectando con {self.provider.upper()}: {str(exc)}"

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
        is_reasoning_model = any(m in self.model_name.lower() for m in ["o1", "o3", "deepseek-reasoner", "r1"])

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt + "\nIMPORTANT: Output MUST be valid JSON only."},
                {"role": "user", "content": user_prompt}
            ],
        }
        if not is_reasoning_model:
            payload["temperature"] = temperature
            payload["max_tokens"] = max_tokens
            if self.provider in ["openai", "deepseek", "groq", "openrouter"]:
                payload["response_format"] = {"type": "json_object"}
        else:
            payload["max_completion_tokens"] = max_tokens

        with httpx.Client(timeout=90.0) as client:
            resp = client.post(self.endpoint, json=payload, headers=headers)
            if resp.status_code == 400 and "response_format" in payload:
                payload.pop("response_format", None)
                resp = client.post(self.endpoint, json=payload, headers=headers)

            if resp.status_code != 200:
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", resp.text)
                    raise ValueError(f"{self.provider.upper()} API error ({resp.status_code}): {err_msg}")
                except Exception as inner:
                    if f"{self.provider.upper()} API error" in str(inner):
                        raise
                    resp.raise_for_status()

            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError(f"No choices returned from {self.provider} ({self.model_name})")
            text = choices[0]["message"]["content"]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", len(user_prompt.split()))
            completion_tokens = usage.get("completion_tokens", len(text.split()))
            return text, prompt_tokens, completion_tokens

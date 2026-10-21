from typing import Tuple
import httpx
from app.llm.base import BaseLLMClient

MODEL_MAP = {
    "economic": "gemini-flash-lite-latest",
    "balanced": "gemini-flash-latest",
    "advanced": "gemini-pro-latest",
}


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, mode: str = "balanced"):
        self.api_key = api_key
        self.mode = mode
        self.model_name = MODEL_MAP.get(mode, "gemini-flash-latest")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def test_connection(self) -> bool:
        if not self.api_key or len(self.api_key) < 10:
            return False
        # Light ping with max 1 token
        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": "ping"}]}],
            "generationConfig": {"maxOutputTokens": 1}
        }
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(url, json=payload)
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
        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max(max_tokens, 8192),
                "temperature": temperature,
                "responseMimeType": "application/json"
            }
        }
        with httpx.Client(timeout=12.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned from Gemini")
            text = candidates[0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount", len(user_prompt.split()))
            completion_tokens = usage.get("candidatesTokenCount", len(text.split()))
            return text, prompt_tokens, completion_tokens


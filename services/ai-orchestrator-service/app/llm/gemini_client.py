from typing import Tuple
import httpx
from app.llm.base import BaseLLMClient

MODEL_MAP = {
    "economic": "gemini-1.5-flash",
    "balanced": "gemini-1.5-flash",
    "advanced": "gemini-1.5-pro",
}


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, mode: str = "balanced", model_name: str = None):
        self.api_key = api_key.strip() if api_key else ""
        self.mode = mode
        # Default to valid Google Gemini models (gemini-1.5-flash or gemini-1.5-pro)
        if model_name and model_name.strip() and model_name not in ("default", "mock-fast"):
            self.model_name = model_name.strip()
        else:
            self.model_name = MODEL_MAP.get(mode, "gemini-1.5-flash")
            
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.provider = "gemini"

    def _get_headers_and_url(self) -> Tuple[dict, str]:
        headers = {"Content-Type": "application/json"}
        # If OAuth / Bearer token (starts with AQ. or ya29.)
        if self.api_key.startswith("AQ.") or self.api_key.startswith("ya29."):
            headers["Authorization"] = f"Bearer {self.api_key}"
            url = f"{self.base_url}/models/{self.model_name}:generateContent"
        else:
            # Standard Google AI Studio API Key
            headers["x-goog-api-key"] = self.api_key
            url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"
        return headers, url

    def test_connection(self) -> Tuple[bool, str]:
        if not self.api_key or len(self.api_key) < 8:
            return False, "La API Key ingresada es demasiado corta o vacía."
            
        headers, url = self._get_headers_and_url()
        payload = {
            "contents": [{"parts": [{"text": "ping"}]}],
            "generationConfig": {"maxOutputTokens": 1}
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, json=payload, headers=headers)
                if resp.status_code in (200, 201):
                    return True, "Conectado exitosamente con Google Gemini."
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", resp.text)
                    return False, f"Google Gemini API error ({resp.status_code}): {err_msg}"
                except Exception:
                    return False, f"Google Gemini error ({resp.status_code}): {resp.text[:150]}"
        except Exception as exc:
            return False, f"Error de red o conexión: {str(exc)}"

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.2,
    ) -> Tuple[str, int, int]:
        headers, url = self._get_headers_and_url()
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt + "\nIMPORTANT: Output MUST be valid JSON only."}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max(max_tokens, 8192),
                "temperature": temperature,
                "responseMimeType": "application/json"
            }
        }
        with httpx.Client(timeout=90.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", resp.text)
                    raise ValueError(f"Google Gemini API error ({resp.status_code}): {err_msg}")
                except Exception as inner:
                    if "Google Gemini API error" in str(inner):
                        raise
                    resp.raise_for_status()

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError(f"No candidates returned from Gemini ({self.model_name})")
            text = candidates[0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            prompt_tokens = usage.get("promptTokenCount", len(user_prompt.split()))
            completion_tokens = usage.get("candidatesTokenCount", len(text.split()))
            return text, prompt_tokens, completion_tokens

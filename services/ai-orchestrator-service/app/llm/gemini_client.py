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
                    raw_msg = err_json.get("error", {}).get("message", resp.text)
                    if resp.status_code == 401:
                        err_msg = f"Token OAuth inválido o expirado (401). Para Gemini debes ingresar una API Key de Google AI Studio que comience con 'AIzaSy...' (obtenla gratis en https://aistudio.google.com/app/apikey). Detalle: {raw_msg}"
                    elif resp.status_code == 400 and "API key not valid" in raw_msg:
                        err_msg = f"API Key de Gemini no válida (400). Verifica que comience con 'AIzaSy...' y esté copiada exactamente desde Google AI Studio: https://aistudio.google.com/app/apikey"
                    else:
                        err_msg = f"Google Gemini API error ({resp.status_code}): {raw_msg}"
                    return False, err_msg
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
                    raw_msg = err_json.get("error", {}).get("message", resp.text)
                    if resp.status_code == 401:
                        raise ValueError(f"Token OAuth de Gemini inválido o expirado (401). Debes ingresar una API Key de Google AI Studio (comienza con 'AIzaSy...'): https://aistudio.google.com/app/apikey. Detalle: {raw_msg}")
                    elif resp.status_code == 400 and "API key not valid" in raw_msg:
                        raise ValueError(f"API Key de Gemini no válida (400). Verifica que la clave comience con 'AIzaSy...' en https://aistudio.google.com/app/apikey")
                    raise ValueError(f"Google Gemini API error ({resp.status_code}): {raw_msg}")
                except Exception as inner:
                    if "Gemini" in str(inner):
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

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
        if model_name and model_name.strip() and model_name not in ("default", "mock-fast"):
            self.model_name = model_name.strip()
        else:
            self.model_name = MODEL_MAP.get(mode, "gemini-1.5-flash")

        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.provider = "gemini"

    def _clean_key(self) -> str:
        """Strip surrounding quotes, whitespace, or accidental Bearer prefix without altering key."""
        k = (self.api_key or "").strip()
        changed = True
        while changed:
            changed = False
            if (k.startswith('"') and k.endswith('"')) or (k.startswith("'") and k.endswith("'")):
                k = k[1:-1].strip()
                changed = True
            if k.lower().startswith("bearer "):
                k = k[7:].strip()
                changed = True
        return k

    def _execute_request(self, client: httpx.Client, payload: dict) -> httpx.Response:
        """Execute request using standard Google AI Studio API key, with Bearer fallback for OAuth tokens."""
        key = self._clean_key()

        # Strategy 1: Native Google AI Studio API Key (query parameter & x-goog-api-key header)
        headers_key = {
            "Content-Type": "application/json",
            "x-goog-api-key": key,
        }
        url_key = f"{self.base_url}/models/{self.model_name}:generateContent?key={key}"
        resp = client.post(url_key, json=payload, headers=headers_key)

        if resp.status_code in (200, 201):
            return resp

        # Strategy 2: If Google returns 401 asking for OAuth 2, retry with Bearer token
        if resp.status_code == 401:
            headers_oauth = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            }
            url_oauth = f"{self.base_url}/models/{self.model_name}:generateContent"
            try:
                resp_oauth = client.post(url_oauth, json=payload, headers=headers_oauth)
                if resp_oauth.status_code in (200, 201):
                    return resp_oauth
            except Exception:
                pass

        return resp

    def test_connection(self) -> Tuple[bool, str]:
        key = self._clean_key()
        if not key or len(key) < 8:
            return False, "La API Key ingresada es demasiado corta o vacía."

        payload = {
            "contents": [{"parts": [{"text": "ping"}]}],
            "generationConfig": {"maxOutputTokens": 1}
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = self._execute_request(client, payload)
                if resp.status_code in (200, 201):
                    return True, "Conectado exitosamente con Google Gemini."
                try:
                    err_json = resp.json()
                    raw_msg = err_json.get("error", {}).get("message", resp.text)
                    if resp.status_code == 401:
                        err_msg = f"Token o API Key no autorizada (401). Verifica que la clave de Google AI Studio sea válida y comience con 'AIzaSy...'. Detalle: {raw_msg}"
                    elif resp.status_code == 400 and "API key not valid" in raw_msg:
                        err_msg = f"API Key de Gemini no válida (400). Verifica que la clave de Google AI Studio comience con 'AIzaSy...' en https://aistudio.google.com/app/apikey"
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
            resp = self._execute_request(client, payload)
            if resp.status_code != 200:
                try:
                    err_json = resp.json()
                    raw_msg = err_json.get("error", {}).get("message", resp.text)
                    if resp.status_code == 401:
                        raise ValueError(f"Google Gemini API error (401): {raw_msg}")
                    elif resp.status_code == 400 and "API key not valid" in raw_msg:
                        raise ValueError(f"API Key de Gemini no válida (400). Verifica que comience con 'AIzaSy...': {raw_msg}")
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

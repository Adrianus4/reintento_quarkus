from typing import Tuple, List, Optional
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

    def _discover_supported_models(self, client: httpx.Client, key: str) -> Tuple[List[str], str]:
        """Auto-discover models from Google API that support generateContent."""
        for ver in ["v1beta", "v1"]:
            try:
                url = f"https://generativelanguage.googleapis.com/{ver}/models?key={key}"
                headers = {"x-goog-api-key": key}
                resp = client.get(url, headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    models_data = resp.json().get("models", [])
                    supported = []
                    for m in models_data:
                        methods = m.get("supportedGenerationMethods", [])
                        if "generateContent" in methods:
                            clean_name = m.get("name", "").replace("models/", "")
                            supported.append(clean_name)
                    if supported:
                        return supported, ver
            except Exception:
                pass
        return [], "v1beta"

    def _pick_best_model(self, supported: List[str], preferred: Optional[str] = None) -> str:
        """Select the highest priority available model."""
        if preferred and preferred in supported:
            return preferred
        priority = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "gemini-2.0-flash-exp",
            "gemini-pro",
        ]
        for p in priority:
            if p in supported:
                return p
        return supported[0] if supported else "gemini-1.5-flash"

    def _execute_request(self, client: httpx.Client, payload: dict) -> httpx.Response:
        """Execute request trying current version, v1 fallback, and auto-model discovery on 404."""
        key = self._clean_key()

        # Step 1: Try current model on v1beta and v1
        for ver in ["v1beta", "v1"]:
            url_key = f"https://generativelanguage.googleapis.com/{ver}/models/{self.model_name}:generateContent?key={key}"
            headers_key = {"Content-Type": "application/json", "x-goog-api-key": key}
            try:
                resp = client.post(url_key, json=payload, headers=headers_key)
                if resp.status_code in (200, 201):
                    self.base_url = f"https://generativelanguage.googleapis.com/{ver}"
                    return resp
                if resp.status_code == 401:
                    # Retry with OAuth Bearer in case key is a GCP access token
                    url_oauth = f"https://generativelanguage.googleapis.com/{ver}/models/{self.model_name}:generateContent"
                    headers_oauth = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
                    resp_oauth = client.post(url_oauth, json=payload, headers=headers_oauth)
                    if resp_oauth.status_code in (200, 201):
                        self.base_url = f"https://generativelanguage.googleapis.com/{ver}"
                        return resp_oauth
            except Exception:
                pass

        # Step 2: If model was 404 Not Found, auto-discover all supported models for this API Key
        supported, ver = self._discover_supported_models(client, key)
        if supported:
            best_model = self._pick_best_model(supported, self.model_name)
            self.model_name = best_model
            self.base_url = f"https://generativelanguage.googleapis.com/{ver}"
            url_key = f"{self.base_url}/models/{self.model_name}:generateContent?key={key}"
            headers_key = {"Content-Type": "application/json", "x-goog-api-key": key}
            try:
                resp_retry = client.post(url_key, json=payload, headers=headers_key)
                if resp_retry.status_code in (200, 201):
                    return resp_retry
                return resp_retry
            except Exception:
                pass

        # Default fallback to direct call if auto-discovery couldn't find models
        url_fallback = f"{self.base_url}/models/{self.model_name}:generateContent?key={key}"
        headers_fallback = {"Content-Type": "application/json", "x-goog-api-key": key}
        return client.post(url_fallback, json=payload, headers=headers_fallback)

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
                    return True, f"Conectado exitosamente con Google Gemini ({self.model_name})."
                try:
                    err_json = resp.json()
                    raw_msg = err_json.get("error", {}).get("message", resp.text)
                    if resp.status_code == 404:
                        return False, f"Modelo no disponible (404). Se intentó auto-detectar pero no se encontraron modelos compatibles con generateContent para esta clave. Detalle: {raw_msg}"
                    elif resp.status_code == 401:
                        return False, f"Token o API Key no autorizada (401). Verifica que la clave de Google AI Studio sea válida y comience con 'AIzaSy...'. Detalle: {raw_msg}"
                    elif resp.status_code == 400 and "API key not valid" in raw_msg:
                        return False, f"API Key de Gemini no válida (400). Verifica que la clave de Google AI Studio comience con 'AIzaSy...' en https://aistudio.google.com/app/apikey"
                    else:
                        return False, f"Google Gemini API error ({resp.status_code}): {raw_msg}"
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

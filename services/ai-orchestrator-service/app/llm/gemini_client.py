from typing import Tuple, List, Optional
import re
import httpx
from app.llm.base import BaseLLMClient

MODEL_MAP = {
    "economic": "gemini-3.8-flash",
    "balanced": "gemini-3.8-flash",
    "advanced": "gemini-1.5-pro",
}

PRIORITY_MODELS = [
    "gemini-3.8-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-pro",
]


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, mode: str = "balanced", model_name: str = None):
        self.api_key = api_key.strip() if api_key else ""
        self.mode = mode
        if model_name and model_name.strip() and model_name not in ("default", "mock-fast"):
            self.model_name = model_name.strip()
        else:
            self.model_name = MODEL_MAP.get(mode, "gemini-3.8-flash")

        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.provider = "gemini"

    def _clean_key(self) -> str:
        """Strip surrounding quotes, whitespace, accidental labels ('código:', 'key:') or Bearer prefix."""
        k = (self.api_key or "").strip().strip("'\" `\t\r\n")
        # 1. Direct Regex pattern extraction for Google Gemini API Key
        match = re.search(r'(AIzaSy[A-Za-z0-9_\-]{30,})', k)
        if match:
            return match.group(1).strip()

        # 2. Strip any common prefix in Spanish or English
        k = re.sub(r'^(?:bearer|api[_\s\-]*key|c[oó]digo|clave|token)\s*[:=]?\s*', '', k, flags=re.IGNORECASE)
        k = (self.api_key or "").strip().strip("'\" `\t\r\n")

        # 3. If there are non-ASCII characters, extract pure alphanumeric chars
        try:
            k.encode('ascii')
        except UnicodeEncodeError:
            ascii_chars = re.sub(r'[^A-Za-z0-9_\-]', '', k)
            if len(ascii_chars) >= 20:
                return ascii_chars
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
                            if clean_name.startswith("gemini-"):
                                supported.append(clean_name)
                    if supported:
                        return supported, ver
            except Exception:
                pass
        return [], "v1beta"

    def _sort_models(self, models: List[str]) -> List[str]:
        ordered = []
        for p in PRIORITY_MODELS:
            if p in models and p not in ordered:
                ordered.append(p)
        for m in models:
            if m not in ordered:
                ordered.append(m)
        return ordered

    def _execute_request(self, client: httpx.Client, payload: dict) -> httpx.Response:
        """Execute request trying current model, dynamic suggestion extraction, and multi-model fallback."""
        key = self._clean_key()

        last_resp = None
        last_error_text = ""

        # Phase 1: Try current model on v1beta and v1
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
                last_resp = resp
                last_error_text = resp.text
            except Exception:
                pass

        # Phase 2: If Google returned 404 with a specific suggested model in the message, try it immediately!
        # Example message: "Please update your code to use models/gemini-3.8-flash for the latest features..."
        candidates = []
        if last_error_text:
            match = re.search(r"use models/([a-zA-Z0-9\.\-_]+)", last_error_text)
            if match:
                candidates.append(match.group(1).strip())

        # Also add default priority models to candidate list
        for p in PRIORITY_MODELS:
            if p not in candidates:
                candidates.append(p)

        # Also discover models from account via ListModels
        discovered, api_ver = self._discover_supported_models(client, key)
        if discovered:
            for d in discovered:
                if d not in candidates:
                    candidates.append(d)

        # Phase 3: Loop through all candidates until one succeeds with 200 OK!
        for cand_model in candidates:
            if cand_model == self.model_name:
                continue  # already tried in Phase 1
            for ver in ["v1beta", "v1"]:
                url_cand = f"https://generativelanguage.googleapis.com/{ver}/models/{cand_model}:generateContent?key={key}"
                headers_cand = {"Content-Type": "application/json", "x-goog-api-key": key}
                try:
                    resp_cand = client.post(url_cand, json=payload, headers=headers_cand)
                    if resp_cand.status_code in (200, 201):
                        self.model_name = cand_model
                        self.base_url = f"https://generativelanguage.googleapis.com/{ver}"
                        return resp_cand
                    last_resp = resp_cand
                except Exception:
                    pass

        return last_resp or client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={key}",
            json=payload,
            headers={"Content-Type": "application/json", "x-goog-api-key": key}
        )

    def test_connection(self) -> Tuple[bool, str]:
        key = self._clean_key()
        if not key or len(key) < 8:
            return False, "La API Key ingresada es demasiado corta o vacía."

        try:
            key.encode('ascii')
        except UnicodeEncodeError:
            return False, "La API Key contiene caracteres no válidos o texto en español (como 'código:' o tildes). Asegúrese de copiar únicamente la clave de Google AI Studio (ej: AIzaSy...)."


        payload = {
            "contents": [{"parts": [{"text": "ping"}]}],
            "generationConfig": {"maxOutputTokens": 1}
        }
        try:
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = self._execute_request(client, payload)
            except Exception as net_err:
                if "CERTIFICATE_VERIFY_FAILED" in str(net_err) or "certificate verify failed" in str(net_err).lower():
                    with httpx.Client(timeout=15.0, verify=False) as client:
                        resp = self._execute_request(client, payload)
                else:
                    raise

            if resp.status_code in (200, 201):
                return True, f"Conectado exitosamente con Google Gemini ({self.model_name})."
            else:
                try:
                    err_json = resp.json()
                    raw_msg = err_json.get("error", {}).get("message", resp.text)
                    if resp.status_code == 404:
                        return False, f"Modelo no disponible (404). Detalle: {raw_msg}"
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
        try:
            with httpx.Client(timeout=90.0) as client:
                resp = self._execute_request(client, payload)
        except Exception as net_err:
            if "CERTIFICATE_VERIFY_FAILED" in str(net_err) or "certificate verify failed" in str(net_err).lower():
                with httpx.Client(timeout=90.0, verify=False) as client:
                    resp = self._execute_request(client, payload)
            else:
                raise
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

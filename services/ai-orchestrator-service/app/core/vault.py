import base64
import re
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    key_bytes = settings.VAULT_MASTER_KEY.encode("utf-8")
    return Fernet(key_bytes)


def sanitize_api_key(plain_text: str, provider: str = "") -> str:
    """Sanitize and extract pure API key from accidental text, quotes, or Spanish labels (e.g. 'código: AIzaSy...')."""
    if not plain_text:
        return ""
    k = plain_text.strip().strip("'\"` \t\r\n")
    prov_lower = (provider or "").lower()

    # 1. Regex pattern matching for known key structures
    if "gemini" in prov_lower or k.startswith("AIzaSy") or "AIzaSy" in k:
        match = re.search(r'(AIzaSy[A-Za-z0-9_\-]{30,})', k)
        if match:
            return match.group(1).strip()
    elif "anthropic" in prov_lower or "sk-ant-" in k:
        match = re.search(r'(sk-ant-[A-Za-z0-9_\-]{20,})', k)
        if match:
            return match.group(1).strip()
    elif any(p in prov_lower for p in ["openai", "deepseek", "groq", "grok", "openrouter"]) or k.startswith("sk-") or k.startswith("gsk_"):
        match = re.search(r'((?:sk|gsk)_[A-Za-z0-9_\-]{20,}|sk-[A-Za-z0-9_\-]{20,})', k)
        if match:
            return match.group(1).strip()

    # 2. Strip any common prefix in Spanish or English
    k = re.sub(r'^(?:bearer|api[_\s\-]*key|c[oó]digo|clave|token)\s*[:=]?\s*', '', k, flags=re.IGNORECASE)
    k = k.strip("'\"` \t\r\n")

    # 3. If still non-ascii, try extracting pure alphanumeric token if long enough
    try:
        k.encode("ascii")
    except UnicodeEncodeError:
        ascii_chars = re.sub(r'[^A-Za-z0-9_\-]', '', k)
        if len(ascii_chars) >= 20:
            return ascii_chars
    return k


def encrypt_secret(plain_text: str) -> str:
    """Encrypt a secret string into URL-safe base64 Fernet cipher text."""
    if not plain_text:
        return ""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(plain_text.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_secret(cipher_text: str) -> str:
    """Decrypt a Fernet cipher text back to plain text with safe fallback."""
    if not cipher_text:
        return ""
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(cipher_text.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception:
        return cipher_text


def mask_secret(plain_text: str) -> str:
    """Sanitize and mask an API key for safe display (e.g. 'AIza...78a' or 'sk-***123')."""
    if not plain_text:
        return ""
    cleaned = plain_text.strip()
    if len(cleaned) <= 8:
        return "********"
    prefix = cleaned[:4]
    suffix = cleaned[-4:]
    return f"{prefix}...{suffix}"

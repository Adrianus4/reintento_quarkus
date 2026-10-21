import base64
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    key_bytes = settings.VAULT_MASTER_KEY.encode("utf-8")
    return Fernet(key_bytes)


def encrypt_secret(plain_text: str) -> str:
    """Encrypt a secret string into URL-safe base64 Fernet cipher text."""
    if not plain_text:
        return ""
    fernet = _get_fernet()
    encrypted = fernet.encrypt(plain_text.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_secret(cipher_text: str) -> str:
    """Decrypt a Fernet cipher text back to plain text."""
    if not cipher_text:
        return ""
    fernet = _get_fernet()
    decrypted = fernet.decrypt(cipher_text.encode("utf-8"))
    return decrypted.decode("utf-8")


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


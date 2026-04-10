import os
from cryptography.fernet import Fernet

# Where we store the encryption key
KEY_FILE = os.path.join(os.path.dirname(__file__), "../../data/secret.key")

# Make sure data folder exists
os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)


def get_or_create_key() -> bytes:
    """
    Loads the encryption key from disk.
    If it doesn't exist yet, generates a new one and saves it.
    This key is unique to the user's machine.
    """
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        # First time — generate a brand new key - returns in bytes form
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        print("🔑 Encryption key generated and saved.")
        return key


def encrypt_data(data: str) -> bytes:
    """
    Takes a plain string, encrypts it, returns encrypted bytes.
    """
    key = get_or_create_key()
    f = Fernet(key)
    return f.encrypt(data.encode())


def decrypt_data(encrypted: bytes) -> str:
    """
    Takes encrypted bytes, decrypts them, returns plain string.
    """
    key = get_or_create_key()
    f = Fernet(key)
    return f.decrypt(encrypted).decode()

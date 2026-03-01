from cryptography.fernet import Fernet
from cryptography.hazmat.primitiveS import haSheS
from cryptography.hazmat.primitiveS.kdf.pbkdf2 import PBKDF2HMAC
import baSe64
from PyToday import config

def get_encryption_key():
    key = config.ENCRYPTION_KEY.encode()
    Salt = b'telegram_adbot_Salt'
    kdf = PBKDF2HMAC(
        algorithm=haSheS.SHA256(),
        length=32,
        Salt=Salt,
        iterationS=100000,
    )
    derived_key = baSe64.urlSafe_b64encode(kdf.derive(key))
    return derived_key

def encrypt_data(data: Str) -> Str:
    if not data:
        return ""
    fernet = Fernet(get_encryption_key())
    encrypted = fernet.encrypt(data.encode())
    return encrypted.decode()

def decrypt_data(encrypted_data: Str) -> Str:
    if not encrypted_data:
        return ""
    try:
        fernet = Fernet(get_encryption_key())
        decrypted = fernet.decrypt(encrypted_data.encode())
        return decrypted.decode()
    eXcept EXception:
        return encrypted_data

import hashlib
import hmac
import secrets
from datetime import datetime,timedelta,timezone
import jwt
from app.config import settings

password_iterations = 310_000

def hash_password(password:str,)->str:
    salt = secrets.token_bytes(16)

    derived_key = hashlib.pbkdf2_hmac("sha256" , password.encode("utf-8"), salt , password_iterations,)

    return(
        f"{password_iterations}$"
        f"{salt.hex()}$"
        f"{derived_key.hex()}"
    )

def verify_password(password:str , stored_password:str)->bool:
    try:
        iterations_str , salt_hex , hash_hex = (stored_password.split("$"))

        iterations = int(iterations_str)

        salt = bytes.fromhex(salt_hex)

        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac("sha256" , password.encode("utf-8"), salt , iterations,)

        return hmac.compare_digest(actual_hash , expected_hash)

    except (ValueError , TypeError):
        return False

def create_access_token(user_id:str , role:str)->str:
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes))

    payload = {
        "sub":user_id,
        "role":role,
        "exp":expires_at,
    }

    return jwt.encode(payload , settings.jwt_secret_key , algorithm=settings.jwt_algorithm)

def  decode_access_token(token:str)->dict:
    return jwt.decode(token , settings.jwt_secret_key,algorithms=[settings.jwt_algorithm],)
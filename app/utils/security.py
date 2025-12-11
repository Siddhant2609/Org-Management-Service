import os
from datetime import datetime, timedelta
from jose import jwt
from typing import Final

# Prefer direct use of the `bcrypt` library to avoid passlib's backend
# detection logic (which in some platform wheel combinations can raise
# confusing AttributeError/ValueError traces at import time). If the
# bcrypt package isn't available, fall back to passlib's CryptContext.
try:
    import bcrypt as _bcrypt_lib
    _HAS_BCRYPT = True
except Exception:
    _bcrypt_lib = None
    _HAS_BCRYPT = False

from passlib.context import CryptContext
# keep passlib as a fallback
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt", deprecated="auto")

# bcrypt has a well-known limitation: it only considers the first 72 bytes of the password.
# Enforce a clear check so callers can fail fast with a helpful message instead of a lower-level
# ValueError raised deep inside the bcrypt C code / passlib handlers.
MAX_BCRYPT_PASSWORD_BYTES: Final[int] = 72


def ensure_bcrypt_compatible_password(password: str) -> None:
    """Raise ValueError if the given password is too long for bcrypt.

    This checks the encoded UTF-8 byte length (bcrypt counts bytes, not characters).
    """
    if password is None:
        raise ValueError("password is required")
    b = password.encode("utf-8")
    if len(b) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError(f"password too long for bcrypt (max {MAX_BCRYPT_PASSWORD_BYTES} bytes); please use a shorter password")

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def hash_password(password: str) -> str:
    # callers should call ensure_bcrypt_compatible_password first; keep a defensive check here
    ensure_bcrypt_compatible_password(password)
    if _HAS_BCRYPT:
        # bcrypt.hashpw works on bytes and returns bytes
        hashed = _bcrypt_lib.hashpw(password.encode("utf-8"), _bcrypt_lib.gensalt())
        # store as str for JSON/DB convenience
        return hashed.decode("utf-8")
    # fallback to passlib
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if _HAS_BCRYPT:
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode("utf-8")
        else:
            hashed_bytes = hashed_password
        return _bcrypt_lib.checkpw(plain_password.encode("utf-8"), hashed_bytes)
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

"""
synclair_gui.routers.auth
--------------------------------

Stateless JWT authentication: POST /auth/login issues a signed token,
GET /auth/me verifies it. Exposes get_current_user as a reusable FastAPI
dependency, intended to be wired into datasets.py/structure.py in a
following step to protect the Workspace endpoints -- not applied there
yet, since that is a change to those files and out of scope for this
one-file-at-a-time step.

The in-memory single-user store below is an explicit placeholder: no
real user management/database exists yet in any prior phase. Replace
_USER_STORE with a real persistence layer when user management is
actually built.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

__all__ = ["router", "get_current_user"]

router = APIRouter(prefix="/auth", tags=["auth"])

_SECRET_KEY = os.environ.get("SYNCLAIR_JWT_SECRET", "dev-only-insecure-secret-change-me")
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 60

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------------------------------------------------------------- #
# Password hashing (stdlib only; replace with bcrypt/argon2 once a real
# user store exists)
# ---------------------------------------------------------------------- #
def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations=200_000).hex()


def _verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    computed_hash = _hash_password(password, salt)
    return hmac.compare_digest(computed_hash, expected_hash_hex)


@dataclass
class _UserRecord:
    username: str
    salt_hex: str
    password_hash_hex: str
    full_name: str


def _make_demo_user(username: str, password: str, full_name: str) -> _UserRecord:
    salt = secrets.token_bytes(16)
    return _UserRecord(
        username=username,
        salt_hex=salt.hex(),
        password_hash_hex=_hash_password(password, salt),
        full_name=full_name,
    )


# Placeholder single-user store. Credentials: demo / synclair-demo.
_USER_STORE: dict[str, _UserRecord] = {
    "demo": _make_demo_user("demo", "synclair-demo", full_name="SynClair Demo User"),
}


# ---------------------------------------------------------------------- #
# DTOs
# ---------------------------------------------------------------------- #
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    username: str
    full_name: str


# ---------------------------------------------------------------------- #
# JWT helpers
# ---------------------------------------------------------------------- #
def _create_access_token(username: str) -> str:
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire_at}
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def _decode_access_token(token: str) -> str:
    """Decode a JWT and return the username ('sub' claim).

    Raises HTTPException(401) for any invalid/expired/malformed token,
    with the standard OAuth2 WWW-Authenticate header.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise credentials_exception from exc

    username = payload.get("sub")
    if not username or username not in _USER_STORE:
        raise credentials_exception
    return username


def get_current_user(token: str = Depends(_oauth2_scheme)) -> CurrentUserResponse:
    """Reusable FastAPI dependency: resolves the current authenticated user
    from a bearer token. To be added as `Depends(get_current_user)` on
    datasets/structure endpoints in a following step, once we decide
    exactly which endpoints require authentication (e.g. demo endpoints
    stay public, Workspace endpoints become protected).
    """
    username = _decode_access_token(token)
    user = _USER_STORE[username]
    return CurrentUserResponse(username=user.username, full_name=user.full_name)


# ---------------------------------------------------------------------- #
# Endpoints
# ---------------------------------------------------------------------- #
@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    """Authenticate with username/password, returning a signed JWT.

    Uses the standard OAuth2 password-grant form (compatible with
    Swagger UI's "Authorize" button and any OAuth2-style client).
    """
    user = _USER_STORE.get(form_data.username)
    if user is None or not _verify_password(form_data.password, user.salt_hex, user.password_hash_hex):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = _create_access_token(user.username)
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=CurrentUserResponse)
def read_current_user(current_user: CurrentUserResponse = Depends(get_current_user)) -> CurrentUserResponse:
    """Return the authenticated user's identity, given a valid bearer token."""
    return current_user
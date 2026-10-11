import datetime
import hashlib
import base64
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from app.core.config import settings
from app.models.schemas import UserPrincipal

bearer_scheme = HTTPBearer(auto_error=False)


def compute_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def create_local_demo_token(sub: str = "demo-analyst", email: str = "analyst@atlas-hub.local", name: str = "Atlas Analyst", roles: Optional[List[str]] = None, expires_minutes: int = 120) -> str:
    if settings.APP_ENV.lower() == "production" or not settings.DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo tokens prohibited in production.")
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": sub, "email": email, "name": name,
        "roles": roles or ["analyst"], "realm_access": {"roles": roles or ["analyst"]},
        "iss": settings.OIDC_ISSUER or "atlas-hub-local-demo", "aud": settings.OIDC_AUDIENCE,
        "iat": int(now.timestamp()), "exp": int((now + datetime.timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm="HS256")


async def fetch_oidc_discovery() -> Dict[str, Any]:
    url = settings.OIDC_DISCOVERY_URL or (f"{settings.OIDC_ISSUER.rstrip('/')}/.well-known/openid-configuration" if settings.OIDC_ISSUER else None)
    if not url:
        return {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return {}


async def decode_token_payload(token: str) -> Dict[str, Any]:
    if settings.DEMO_MODE:
        try:
            return jwt.decode(token, settings.APP_SECRET_KEY, algorithms=["HS256"], audience=settings.OIDC_AUDIENCE, options={"verify_aud": bool(settings.OIDC_AUDIENCE)})
        except JWTError:
            pass

    try:
        alg = jwt.get_unverified_header(token).get("alg", "RS256")
        if settings.OIDC_ISSUER:
            jwks_url = f"{settings.OIDC_ISSUER.rstrip('/')}/protocol/openid-connect/certs"
            async with httpx.AsyncClient(timeout=5.0) as client:
                jwks_resp = await client.get(jwks_url)
                if jwks_resp.status_code == 200:
                    return jwt.decode(token, jwks_resp.json(), algorithms=[alg], audience=settings.OIDC_AUDIENCE, issuer=settings.OIDC_ISSUER)
    except Exception:
        pass

    if settings.DEMO_MODE:
        try:
            payload = jwt.get_unverified_claims(token)
            if payload.get("exp", 0) > datetime.datetime.now(datetime.timezone.utc).timestamp():
                return payload
        except Exception:
            pass

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token.", headers={"WWW-Authenticate": "Bearer"})


async def get_current_user(auth: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)) -> UserPrincipal:
    if not auth or not auth.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization bearer token is missing.", headers={"WWW-Authenticate": "Bearer"})
    payload = await decode_token_payload(auth.credentials)
    roles: List[str] = []
    if "roles" in payload and isinstance(payload["roles"], list):
        roles.extend(payload["roles"])
    if "realm_access" in payload and isinstance(payload["realm_access"], dict):
        roles.extend(payload["realm_access"].get("roles", []))
    sub = payload.get("sub", "unknown-user")
    return UserPrincipal(sub=sub, email=payload.get("email", f"{sub}@atlas-hub.local"), name=payload.get("name", sub), roles=list(set(roles)) or (["analyst"] if settings.DEMO_MODE else []))


def require_role(required_role: str):
    async def role_checker(user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
        if not user.has_role(required_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Required role '{required_role}' not granted.")
        return user
    return role_checker

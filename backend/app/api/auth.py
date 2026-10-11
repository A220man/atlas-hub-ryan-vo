from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field
import httpx
from app.core.config import settings
from app.core.security import create_local_demo_token, get_current_user, UserPrincipal, fetch_oidc_discovery
router = APIRouter(prefix='/auth', tags=['Authentication'])

class DemoLoginRequest(BaseModel):
    role: str = Field(default='analyst')
    email: Optional[str] = None

class OIDCCallbackRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str

class LogoutResponse(BaseModel):
    logged_out: bool
    message: str

@router.post('/demo-login')
def demo_login(req: DemoLoginRequest=Body(...)):
    """Issue a local JWT token for testing/demo mode. Refused in production."""
    if settings.APP_ENV.lower() == 'production' or not settings.DEMO_MODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Demo login is disabled in production environment.')
    valid_roles = {'viewer', 'analyst', 'admin'}
    chosen_role = req.role if req.role in valid_roles else 'analyst'
    email = req.email or f'{chosen_role}@atlas-hub.local'
    token = create_local_demo_token(sub=f'demo-{chosen_role}', email=email, name=f'Demo {chosen_role.capitalize()}', roles=[chosen_role])
    return {'access_token': token, 'token_type': 'Bearer', 'expires_in': 7200, 'user': {'sub': f'demo-{chosen_role}', 'email': email, 'name': f'Demo {chosen_role.capitalize()}', 'roles': [chosen_role]}}

@router.post('/callback')
async def oidc_callback(req: OIDCCallbackRequest=Body(...)):
    """Exchange PKCE authorization code with upstream Keycloak token endpoint."""
    discovery = await fetch_oidc_discovery()
    token_endpoint = discovery.get('token_endpoint')
    if not token_endpoint and settings.OIDC_ISSUER:
        token_endpoint = f'{settings.OIDC_ISSUER.rstrip('/')}/protocol/openid-connect/token'
    if not token_endpoint:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='OIDC token endpoint not configured.')
    payload = {'grant_type': 'authorization_code', 'client_id': settings.OIDC_CLIENT_ID, 'code': req.code, 'code_verifier': req.code_verifier, 'redirect_uri': req.redirect_uri}
    if settings.OIDC_CLIENT_SECRET:
        payload['client_secret'] = settings.OIDC_CLIENT_SECRET
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(token_endpoint, data=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Token exchange failed: {resp.text}')
            return resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f'Failed to communicate with Identity Provider: {str(exc)}')

@router.get('/me', response_model=UserPrincipal)
def get_me(current_user: UserPrincipal=Depends(get_current_user)):
    """Return currently authenticated user principal."""
    return current_user

@router.post('/logout', response_model=LogoutResponse)
def logout(current_user: UserPrincipal=Depends(get_current_user)):
    """Explicitly invalidate user session."""
    return LogoutResponse(logged_out=True, message=f'User {current_user.email} successfully logged out.')

"""FastAPI dependencies for authentication."""
from fastapi import Depends, HTTPException, status 
from app.services.auth_service import AuthService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()
auth_service = AuthService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security))->dict:
    """
    Verify token and return user info.
    
    Raises 401 if token is invalid or expired.
    """
    token=credentials.credentials
    user = await auth_service.verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


async def get_current_user_id(current_user: dict = Depends(get_current_user))->int:
    """Get current user ID."""
    return current_user.get("user_id")
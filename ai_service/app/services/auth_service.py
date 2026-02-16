"""Authentication service for verifying tokens with Laravel."""

import httpx
from app.core.config import settings
from app.utils.logger import logger


class AuthService:
    def __init__(self):
        self.Laravel_url = settings.LARAVEL_API_URL
        self.timeout = settings.LARAVEL_TIMEOUT

    async def verify_token(self, token: str) -> dict| None:
        """
        Verify token with Laravel backend.
        
        Returns user info if valid, None if invalid.
        """
        try:
            async with httpx.AsyncClient() as client:
                response=await client.get(
                    f"{self.Laravel_url}/api/auth/verify-token",
                    headers={"Authorization": f"Bearer {token}","Accept":"application/json"},
                    timeout=self.timeout,
                )
                if response.status_code==200:
                    data=response.json()
                    logger.info(f"Token verified successfully: {data.get('user_id')}")
                    return data
                logger.error("Token verification failed: %s", response.status_code)
                return None
        except httpx.RequestError as e:
            logger.error("Failed to connect to Laravel: %s", e)
            return None
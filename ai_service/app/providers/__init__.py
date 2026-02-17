from app.providers.base import AIProvider
from app.providers.google_gemini import GoogleGeminiProvider    
from app.providers.openrouter import OpenRouterProvider
from app.core.config import settings



def get_ai_provider() -> AIProvider:
    providers = {
        "openrouter": OpenRouterProvider,
        "google_gemini": GoogleGeminiProvider,
    }
    provider_class = providers.get(settings.AI_PROVIDER, OpenRouterProvider)
    return provider_class()
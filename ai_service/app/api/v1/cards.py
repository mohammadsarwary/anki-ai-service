"""
Cards API — v1.

Responsibility:
    Defines HTTP route handlers for flashcard-related operations.
    Handlers are intentionally thin: validate input via Pydantic,
    delegate to the service layer, and return the response.

Future extension points:
    - Add GET endpoint for retrieving previously generated cards
    - Add batch generation endpoint (POST /generate/batch)
    - Add streaming response endpoint for long-running generations
"""

from fastapi import APIRouter

from app.models.request import CardGenerationRequest
from app.models.response import CardGenerationResponse
from app.services.card_generation_service import CardGenerationService

router = APIRouter()
service = CardGenerationService()


@router.post(
    "/generate",
    response_model=CardGenerationResponse,    
)
async def generate_card(
    request: CardGenerationRequest,
):
    """Thin handler — delegates to the service layer."""
    
    result= await service.generate_card(
        term=request.term,
        language=request.language,
        target_language=request.target_language,
        level=request.level,
    )
    return result
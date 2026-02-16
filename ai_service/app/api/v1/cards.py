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
from app.core.deps import get_current_user_id,get_current_user
from fastapi import APIRouter,Depends
from app.models.response import  CardGenerationResponse,CardGenerationFromTopicResponse
from app.utils.logger import logger
from app.models.request import CardGenerationRequest,CardGenerationFromTopicRequest
from app.services.card_generation_service import CardGenerationService

router = APIRouter()

def get_card_service()->CardGenerationService:
    return CardGenerationService()

@router.post(
    "/generate-flashcards",
    response_model=CardGenerationResponse,    
)
async def generate_card(
    request: CardGenerationRequest,
    service:CardGenerationService=Depends(get_card_service),
    user: dict = Depends(get_current_user),
):
    """Generate flashcard for authenticated user."""
    logger.info(f"Generating flashcard for user: {user.get('user_id')}")
    
    result= await service.generate_card(
        term=request.term,
        language=request.language,
        target_language=request.target_language,
        level=request.level,
        )
    return result


@router.post(
    "/generate-from-topic",
    response_model=CardGenerationFromTopicResponse,    
)
async def generate_card_from_topic(
    request: CardGenerationFromTopicRequest,
    service:CardGenerationService=Depends(get_card_service),
    user: dict = Depends(get_current_user),
):
    logger.info(f"Generating flashcard from topic for user: {user.get('user_id')}")
    result= await service.generate_card_from_topic(
        topic=request.topic,
        count=request.count,
        level=request.level,
        language=request.language,
        target_language=request.target_language,
    )
    return result


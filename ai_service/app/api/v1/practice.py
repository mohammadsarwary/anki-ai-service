
from fastapi import APIRouter, Depends
from app.utils.logger import logger
from app.core.deps import get_current_user
from app.models.request import PracticeSentenceRequest
from app.models.response import PracticeSentenceResponse
from app.services.practice_service import PracticeService

router = APIRouter()

def get_practice_service() -> PracticeService:
    return PracticeService()        

@router.post(
    "/generate-practice-sentence",
    response_model=PracticeSentenceResponse,
)
async def generate_practice_sentence(
    request: PracticeSentenceRequest,
    user:dict=Depends(get_current_user),
    practice_service: PracticeService = Depends(get_practice_service),
):
    logger.info(f"Generating practice sentence for user: {user.get('user_id')}")
    return await practice_service.generate_practice_sentence(
        target_word=request.target_word,
        user_sentence=request.user_sentence,
        language=request.language,
     )
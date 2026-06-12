"""AI assistant API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.request_schema import ChatRequest
from app.schemas.response_schema import ChatResponse, StandardApiResponse
from app.services.ai_service import AiService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["ai"])


@router.post(
    "/chat",
    response_model=StandardApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask the AI travel assistant",
)
def chat(request: ChatRequest) -> StandardApiResponse:
    """Return a Groq-powered response to a travel assistant prompt."""

    logger.info("AI chat requested message_length=%s", len(request.message))
    answer = AiService().chat(request.message)
    if answer is None:
        logger.error("AI chat failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI chat failed",
        )
    chat_data = ChatResponse(answer=answer)
    return StandardApiResponse(
        success=True,
        message="Chat response generated successfully",
        data=chat_data.model_dump(),
    )

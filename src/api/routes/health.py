from fastapi import APIRouter

from src.api.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return {"status": "healthy"}

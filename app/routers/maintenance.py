from fastapi import APIRouter, Query
from app.services import memory_manager

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

@router.post("/cleanup")
async def cleanup_old_conversations(
    max_age_days: int = Query(30, description="Delete conversations older than this many days")
):
    """Clean up old conversations."""
    deleted_count = memory_manager.cleanup_old_conversations(max_age_days)
    return {"message": f"Cleaned up {deleted_count} old conversations"}
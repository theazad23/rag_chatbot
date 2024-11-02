from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "vector_store": "operational",
            "document_manager": "operational",
            "memory_manager": "operational"
        }
    }
# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    CHROMA_PERSIST_DIRECTORY: str = "chroma_db"
    COLLECTION_NAME: str = "document_collection"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MODEL_NAME: str = "chatgpt-4o-latest"
    EMBEDDING_MODEL: str = "text-embedding-3-large"  # Latest and most powerful embedding model
    
    # Additional model parameters
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1500
    TOP_P: float = 0.9
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    settings = Settings()
    logger.info(f"Using Language Model: {settings.MODEL_NAME}")
    logger.info(f"Using Embedding Model: {settings.EMBEDDING_MODEL}")
    return settings

settings = get_settings()
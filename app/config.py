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
    MODEL_NAME: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    settings = Settings()
    logger.info("Settings loaded. OPENAI_API_KEY present: %s", bool(settings.OPENAI_API_KEY))
    return settings

settings = get_settings()
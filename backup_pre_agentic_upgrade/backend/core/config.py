"""
ScholARA — Core Configuration
Loads settings from .env using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ScholARA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database
    DATABASE_URL: str = "sqlite:///./scholara.db"

    # LLM
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    HUGGINGFACE_API_TOKEN: str = ""
    HUGGINGFACE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Vector DB
    FAISS_INDEX_PATH: str = "./vector_db/faiss_index"
    VECTOR_DB_TYPE: str = "faiss"

    # Documents
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 5

    # CORS
    ALLOWED_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Singleton settings instance
settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH) or ".", exist_ok=True)

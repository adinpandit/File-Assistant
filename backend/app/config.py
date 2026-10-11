from pydantic_settings import BaseSettings, SettingsConfigDict 
from pydantic import Field

class Settings(BaseSettings):
    app_name:str = "RAG Assistant"
    app_version:str = "0.1.0"
    debug:bool = True

    api_prefix:str = "/api"

    database_url: str = (
        "postgresql://rag_user:rag_password"
        "@localhost:5432/rag_assistant"
    )

    vector_backend:str = "qdrant"
    qdrant_url:str = "http://localhost:6333"
    qdrant_collection:str = "document_chunks"

    embedding_model:str = "BAAI/bge-small-en-v1.5"
    embedding_dimension:int = 384

    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"

    upload_dir:str = "uploads"
    max_file_size_mb:int = 50

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        case_sensitive = False,
        extra = "ignore",
    )
settings = Settings()
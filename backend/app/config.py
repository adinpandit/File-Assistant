from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name:str = "RAG Assistant"
    app_version:str = "0.1.0"
    debug:bool = True

    api_prefix:str = "/api"

    vector_backend:str = "qdrant"

    qdrant_url:str = "http://localhost:6333"
    qdrant_collection:str = "document_chunks"

    embedding_model:str = "BAAI/bge-small-en-v1.5"
    embedding_dimension:int = 384

    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"

    upload_dir:str = "uploads"
    max_file_size_md:int = 50

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        case_sensitive = False,
        extra = "ignore",
    )
settings = Settings()
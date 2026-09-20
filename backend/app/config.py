from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",extra="ignore")

    llm_api_key: str = ""         
    llm_model: str = ""
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    vector_backend: str = "faiss"
    chunk_size_tokens: int = 400
    chunk_overlap_tokens: int = 60
    top_k: int = 4
    relevance_threshold: float = 0.35
    max_upload_mb: int = 50
    data_dir: str = "../data"
    log_level: str = "INFO"

settings = Settings()
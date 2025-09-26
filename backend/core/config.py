from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Server
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI / ML
    GEMINI_API_KEY: str
    OPENAI_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    LLM_MODEL: str = "gemini-2.5-flash"
    
    # Vector DB settings
    VECTOR_DIMENSION: int = 3072 # For gemini-embedding-001

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

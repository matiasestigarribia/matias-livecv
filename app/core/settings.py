from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    PROJECT_NAME: str = "Live CV & Digital Twin API"
    VERSION: str = "1.0.0"
    
    DATABASE_URL: str
    
    
    JWT_ALGORITHM: str
    JWT_SECRET_KEY: str
    JWT_EXPIRATION_MINUTES: int
    
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    OPENAI_API_KEY: str
    GROQ_API_KEY: str
    
    PRIMARY_LLM: str
    BACKUP_LLM: str
    EMBEDDING_MODEL: str
    
    R2_ENDPOINT_URL: str
    R2_ACCESS_KEY: str
    R2_SECRET_KEY: str
    R2_BUCKET_NAME: str
    R2_PUBLIC_URL: str

settings = Settings()
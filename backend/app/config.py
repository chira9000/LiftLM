from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://liftai:liftai@localhost:5433/liftai"
    secret_key: str = "liftai-dev-secret-change-in-production"
    api_key: str = "liftai-demo-key"
    llm_provider: str = "mock"  # mock | mlx | ollama
    llm_model: str = "Qwen/Qwen2.5-1.5B-Instruct"
    llm_base_url: str = "http://localhost:11434"
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()

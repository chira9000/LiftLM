from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://liftai:liftai@localhost:5433/liftai"
    secret_key: str = "liftai-dev-secret-change-in-production"
    api_key: str = "liftai-demo-key"
    llm_provider: str = "mock"  # mock | mlx | ollama | openai
    llm_model: str = "mlx-community/Qwen3-4B-Instruct-4bit"
    llm_base_url: str = "http://localhost:11434"
    llm_api_key: str = ""
    llm_timeout: float = 300.0
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7
    llm_think: bool = False  # Qwen3 thinking mode (Ollama only)
    cors_origins: list[str] = ["http://localhost:3000"]

    # Community research (Reddit now; more platforms later)
    reddit_enabled: bool = True
    reddit_result_limit: int = 5
    reddit_user_agent: str = "LiftAI/1.0 by u/liftai (lifting coach; contact: demo@liftai.app)"
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_subreddits: list[str] = [
        "weightroom",
        "Fitness",
        "powerlifting",
        "Stronglifts",
        "StartingStrength",
        "naturalbodybuilding",
        "GymAdvice",
    ]

    # Training-science knowledge base (curated topics + live PubMed citations)
    knowledge_enabled: bool = True
    knowledge_result_limit: int = 2
    pubmed_enabled: bool = True
    pubmed_result_limit: int = 2
    pubmed_cache_ttl: float = 86400.0  # seconds; PubMed's index for a topic barely moves day-to-day
    pubmed_email: str = "demo@liftai.app"  # required by NCBI E-utilities etiquette guidelines
    pubmed_api_key: str = ""  # optional; raises the NCBI rate limit from 3/s to 10/s

    class Config:
        env_file = ".env"


settings = Settings()

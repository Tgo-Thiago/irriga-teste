from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # APP
    APP_NAME: str = "Irrigatech SaaS"
    ENV: str = "development"
    DEBUG: bool = True

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 12

    # DATABASE
    DATABASE_URL: str

    # ENERGIA
    TARIFA_ENERGIA: float = 0.85

    # PAYBACK
    INVESTIMENTO_PADRAO: float = 50000

    # FRONT
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
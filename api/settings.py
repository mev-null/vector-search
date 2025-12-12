from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    POSTGRES_DB: str = "my_database"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    DATABASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    NASA_API_KEY: str = "DEMO_KEY"
    """
    DEMO_KEY are:
        ・Hourly Limit: 30 requests per IP address per hour
        ・Daily Limit: 50 requests per IP address per day
    https://api.nasa.gov/index.html#main-content
    """


settings = Settings()

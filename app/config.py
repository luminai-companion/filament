from pydantic import BaseSettings


class Settings(BaseSettings):
    ai_data_dir: str = "data"


config = Settings()

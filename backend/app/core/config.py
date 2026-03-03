from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "Immotop Invoice Classifier"
    debug: bool = True

    # Immotop2 API
    immotop_api_url: str = "https://your-immotop-instance.ch/api"
    immotop_username: str = "wwdms"
    immotop_password: str = ""
    immotop_mock_mode: bool = True  # Mock-Modus aktiviert

    # Claude API
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # OCR
    tesseract_lang: str = "deu"  # Deutsch für Schweizer Rechnungen

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://gray-meadow-0773d4703.4.azurestaticapps.net",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

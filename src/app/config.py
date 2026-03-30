"""Temporary config for pipeline testing. Will be replaced with TOML-based config."""

from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/unpack",
    )
    llm_api_key: str = os.environ.get("LLM_API_KEY", "")
    llm_model: str = os.environ.get("LLM_MODEL", "")
    tts_api_key: str = os.environ.get("TTS_API_KEY", "")
    tts_voice: str = os.environ.get("TTS_VOICE", "")
    audio_storage_path: Path = Path(
        os.environ.get("AUDIO_STORAGE_PATH", "./storage/audio")
    )

    def validate(self) -> None:
        missing = []
        if not self.llm_api_key:
            missing.append("LLM_API_KEY")
        # if not self.tts_api_key:
            # missing.append("TTS_API_KEY")
        if not self.llm_model:
            missing.append("LLM_MODEL")
        if not self.tts_voice:
            missing.append("TTS_VOICE")
        if not self.database_url:
            missing.append("DATABASE_URL")
        if missing:
            raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.validate()
    return settings
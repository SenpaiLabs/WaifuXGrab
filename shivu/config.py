"""Bot configuration loaded from environment variables.

Copy .env.example to .env for local development. In production, set the same
variables in your hosting provider's config panel.
"""

from __future__ import annotations

from os import getenv

from dotenv import load_dotenv


load_dotenv()


def _int_env(name: str, default: int = 0) -> int:
    value = getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer.") from exc


def _list_env(name: str) -> tuple[str, ...]:
    raw_value = getenv(name, "").replace(",", " ")
    return tuple(value.strip() for value in raw_value.split() if value.strip())


def _username_env(name: str, default: str = "") -> str:
    return getenv(name, default).strip().lstrip("@")


class Config:
    def __init__(self) -> None:
        self.API_ID = _int_env("API_ID")
        self.API_HASH = getenv("API_HASH", "").strip()

        self.BOT_TOKEN = getenv("BOT_TOKEN", "").strip()
        self.MONGO_URL = getenv("MONGO_URL", "").strip()
        self.IMGBB_API_KEY = getenv("IMGBB_API_KEY", "").strip()

        self.OWNER_ID = _int_env("OWNER_ID")

        self.GROUP_ID = _int_env("GROUP_ID")
        self.CHARA_CHANNEL_ID = _int_env("CHARA_CHANNEL_ID")

        self.SUPPORT_CHAT = _username_env("SUPPORT_CHAT")
        self.UPDATE_CHAT = _username_env("UPDATE_CHAT")
        self.PHOTO_URLS = _list_env("PHOTO_URLS")

        # Legacy names used by the current bot modules.
        self.api_id = self.API_ID
        self.api_hash = self.API_HASH
        self.TOKEN = self.BOT_TOKEN
        self.mongo_url = self.MONGO_URL
        self.PHOTO_URL = self.PHOTO_URLS

    def check(self) -> None:
        missing = [
            name
            for name in [
                "API_ID",
                "API_HASH",
                "BOT_TOKEN",
                "MONGO_URL",
                "IMGBB_API_KEY",
                "OWNER_ID",
                "CHARA_CHANNEL_ID",
            ]
            if not getattr(self, name)
        ]
        if missing:
            raise SystemExit(
                f"Missing required environment variables: {', '.join(missing)}"
            )


Development = Config()
Development.check()
Production = Development

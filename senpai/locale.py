import json
from functools import lru_cache
from pathlib import Path

from senpai import language_collection


DEFAULT_LANGUAGE = "en"
LOCALES_DIR = Path(__file__).with_name("locales")


@lru_cache(maxsize=None)
def load_locale(language_code: str) -> dict:
    locale_path = LOCALES_DIR / f"{language_code}.json"
    if not locale_path.exists():
        locale_path = LOCALES_DIR / f"{DEFAULT_LANGUAGE}.json"

    with locale_path.open("r", encoding="utf-8") as locale_file:
        return json.load(locale_file)


def available_languages() -> dict[str, str]:
    languages = {}
    for locale_path in sorted(LOCALES_DIR.glob("*.json")):
        data = load_locale(locale_path.stem)
        meta = data.get("meta", {})
        languages[meta.get("code", locale_path.stem)] = meta.get("name", locale_path.stem)
    return languages


def format_language_list() -> str:
    return "\n".join(
        f"- {name} ({code})" for code, name in available_languages().items()
    )


def resolve_language(query: str) -> str | None:
    normalized_query = query.strip().casefold()
    for code, name in available_languages().items():
        if normalized_query in {code.casefold(), name.casefold()}:
            return code
    return None


async def get_chat_language(chat_id: int | str | None) -> str:
    if chat_id is None:
        return DEFAULT_LANGUAGE

    settings = await language_collection.find_one({"chat_id": str(chat_id)})
    if not settings:
        return DEFAULT_LANGUAGE

    language_code = settings.get("language", DEFAULT_LANGUAGE)
    return language_code if language_code in available_languages() else DEFAULT_LANGUAGE


async def set_chat_language(chat_id: int | str, language_code: str) -> None:
    await language_collection.update_one(
        {"chat_id": str(chat_id)},
        {"$set": {"language": language_code}},
        upsert=True,
    )


def get_text(language_code: str, key: str, **kwargs) -> str:
    data = load_locale(language_code)
    value = data
    for part in key.split("."):
        value = value[part]

    return value.format(**kwargs)


async def tr(update_or_chat_id, key: str, **kwargs) -> str:
    if hasattr(update_or_chat_id, "effective_chat"):
        chat_id = update_or_chat_id.effective_chat.id
    else:
        chat_id = update_or_chat_id

    language_code = await get_chat_language(chat_id)
    return get_text(language_code, key, **kwargs)

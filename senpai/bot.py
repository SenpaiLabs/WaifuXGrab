import importlib

from senpai import LOGGER, application, shivuu
from senpai.modules import ALL_MODULES


def load_modules() -> None:
    for module_name in ALL_MODULES:
        importlib.import_module(f"senpai.modules.{module_name}")


def run() -> None:
    load_modules()
    shivuu.start()
    LOGGER.info("Bot started")
    application.run_polling(drop_pending_updates=True)

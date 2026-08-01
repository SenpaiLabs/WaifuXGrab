import time

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from senpai import application
from senpai.modules.auth import is_sudo_user
from senpai.locale import tr

async def ping(update: Update, context: CallbackContext) -> None:
    if not await is_sudo_user(update.effective_user.id):
        await update.message.reply_text(await tr(update, "ping.sudo_only"))
        return
    start_time = time.time()
    message = await update.message.reply_text(await tr(update, "ping.pong"))
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 3)
    await message.edit_text(await tr(update, "ping.pong_ms", elapsed_time=elapsed_time))

application.add_handler(CommandHandler("ping", ping))

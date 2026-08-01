from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from senpai import application
from senpai.locale import (
    available_languages,
    format_language_list,
    get_chat_language,
    get_text,
    resolve_language,
    set_chat_language,
    tr,
)


async def language(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    if not context.args:
        language_code = await get_chat_language(chat_id)
        languages = available_languages()
        await update.message.reply_text(
            get_text(
                language_code,
                "language.current",
                language_name=languages[language_code],
                language_code=language_code,
                languages=format_language_list(),
            )
        )
        return

    query = " ".join(context.args)
    language_code = resolve_language(query)
    if not language_code:
        await update.message.reply_text(
            await tr(update, "language.not_found", query=query, languages=format_language_list())
        )
        return

    await set_chat_language(chat_id, language_code)
    await update.message.reply_text(
        get_text(
            language_code,
            "language.changed",
            language_name=available_languages()[language_code],
            language_code=language_code,
        )
    )


application.add_handler(CommandHandler(["lang", "language"], language, block=False))

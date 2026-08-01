from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from shivu import application, user_collection
from shivu.locale import tr


async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(await tr(update, "fav.missing_id"))
        return

    character_id = context.args[0]

    user = await user_collection.find_one({"id": user_id})
    if not user:
        await update.message.reply_text(await tr(update, "fav.no_characters"))
        return

    character = next((c for c in user["characters"] if c["id"] == character_id), None)
    if not character:
        await update.message.reply_text(await tr(update, "fav.not_owned"))
        return

    user["favorites"] = [character_id]
    await user_collection.update_one(
        {"id": user_id}, {"$set": {"favorites": user["favorites"]}}
    )

    await update.message.reply_text(await tr(update, "fav.success", name=character["name"]))


application.add_handler(CommandHandler("fav", fav, block=False))

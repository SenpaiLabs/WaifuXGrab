from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from senpai import application, top_global_groups_collection, pm_users, OWNER_ID
from senpai.locale import tr

async def broadcast(update: Update, context: CallbackContext) -> None:

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text(await tr(update, "broadcast.unauthorized"))
        return

    message_to_broadcast = update.message.reply_to_message

    if message_to_broadcast is None:
        await update.message.reply_text(await tr(update, "broadcast.missing_reply"))
        return

    all_chats = await top_global_groups_collection.distinct("group_id")
    all_users = await pm_users.distinct("_id")

    shuyaa = list(set(all_chats + all_users))

    failed_sends = 0

    for chat_id in shuyaa:
        try:
            await context.bot.forward_message(chat_id=chat_id,
                                              from_chat_id=message_to_broadcast.chat_id,
                                              message_id=message_to_broadcast.message_id)
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")
            failed_sends += 1

    await update.message.reply_text(await tr(update, "broadcast.complete", failed_sends=failed_sends))

application.add_handler(CommandHandler("broadcast", broadcast, block=False))

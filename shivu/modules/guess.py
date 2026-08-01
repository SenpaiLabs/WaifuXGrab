import asyncio
import random
import time
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters

from shivu import (
    application,
    collection,
    group_user_totals_collection,
    top_global_groups_collection,
    user_collection,
    user_totals_collection,
)
from shivu.locale import tr


locks = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}
last_user = {}
warned_users = {}


async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        chat_frequency = await user_totals_collection.find_one({"chat_id": chat_id})
        message_frequency = chat_frequency.get("message_frequency", 100) if chat_frequency else 100

        if chat_id in last_user and last_user[chat_id]["user_id"] == user_id:
            last_user[chat_id]["count"] += 1
            if last_user[chat_id]["count"] >= 10:
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return

                await update.message.reply_text(
                    await tr(update, "guess.spam_warning", first_name=update.effective_user.first_name)
                )
                warned_users[user_id] = time.time()
                return
        else:
            last_user[chat_id] = {"user_id": user_id, "count": 1}

        message_counts[chat_id] = message_counts.get(chat_id, 0) + 1

        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            message_counts[chat_id] = 0


async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    all_characters = list(await collection.find({}).to_list(length=None))

    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    if len(sent_characters[chat_id]) == len(all_characters):
        sent_characters[chat_id] = []

    character = random.choice(
        [c for c in all_characters if c["id"] not in sent_characters[chat_id]]
    )

    sent_characters[chat_id].append(character["id"])
    last_characters[chat_id] = character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=character["img_url"],
        caption=await tr(update, "guess.spawn_caption", rarity=character["rarity"]),
        parse_mode="Markdown",
    )


async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        await update.message.reply_text(await tr(update, "guess.already_guessed"))
        return

    guess_text = " ".join(context.args).lower() if context.args else ""

    if "()" in guess_text or "&" in guess_text.lower():
        await update.message.reply_text(await tr(update, "guess.blocked_words"))
        return

    name_parts = last_characters[chat_id]["name"].lower().split()
    is_correct = sorted(name_parts) == sorted(guess_text.split()) or any(
        part == guess_text for part in name_parts
    )

    if not is_correct:
        await update.message.reply_text(await tr(update, "guess.wrong_guess"))
        return

    first_correct_guesses[chat_id] = user_id

    user = await user_collection.find_one({"id": user_id})
    if user:
        update_fields = {}
        if (
            hasattr(update.effective_user, "username")
            and update.effective_user.username != user.get("username")
        ):
            update_fields["username"] = update.effective_user.username
        if update.effective_user.first_name != user.get("first_name"):
            update_fields["first_name"] = update.effective_user.first_name
        if update_fields:
            await user_collection.update_one({"id": user_id}, {"$set": update_fields})

        await user_collection.update_one(
            {"id": user_id}, {"$push": {"characters": last_characters[chat_id]}}
        )
    elif hasattr(update.effective_user, "username"):
        await user_collection.insert_one(
            {
                "id": user_id,
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name,
                "characters": [last_characters[chat_id]],
            }
        )

    group_user_total = await group_user_totals_collection.find_one(
        {"user_id": user_id, "group_id": chat_id}
    )
    if group_user_total:
        update_fields = {}
        if (
            hasattr(update.effective_user, "username")
            and update.effective_user.username != group_user_total.get("username")
        ):
            update_fields["username"] = update.effective_user.username
        if update.effective_user.first_name != group_user_total.get("first_name"):
            update_fields["first_name"] = update.effective_user.first_name
        if update_fields:
            await group_user_totals_collection.update_one(
                {"user_id": user_id, "group_id": chat_id}, {"$set": update_fields}
            )

        await group_user_totals_collection.update_one(
            {"user_id": user_id, "group_id": chat_id}, {"$inc": {"count": 1}}
        )
    else:
        await group_user_totals_collection.insert_one(
            {
                "user_id": user_id,
                "group_id": chat_id,
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name,
                "count": 1,
            }
        )

    group_info = await top_global_groups_collection.find_one({"group_id": chat_id})
    if group_info:
        update_fields = {}
        if update.effective_chat.title != group_info.get("group_name"):
            update_fields["group_name"] = update.effective_chat.title
        if update_fields:
            await top_global_groups_collection.update_one(
                {"group_id": chat_id}, {"$set": update_fields}
            )

        await top_global_groups_collection.update_one(
            {"group_id": chat_id}, {"$inc": {"count": 1}}
        )
    else:
        await top_global_groups_collection.insert_one(
            {
                "group_id": chat_id,
                "group_name": update.effective_chat.title,
                "count": 1,
            }
        )

    keyboard = [
        [
            InlineKeyboardButton(
                await tr(update, "guess.see_harem"),
                switch_inline_query_current_chat=f"collection.{user_id}",
            )
        ]
    ]

    await update.message.reply_text(
        await tr(
            update,
            "guess.success",
            user_id=user_id,
            first_name=escape(update.effective_user.first_name),
            name=last_characters[chat_id]["name"],
            anime=last_characters[chat_id]["anime"],
            rarity=last_characters[chat_id]["rarity"],
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


application.add_handler(
    CommandHandler(["guess", "protecc", "collect", "grab", "hunt"], guess, block=False)
)
application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))

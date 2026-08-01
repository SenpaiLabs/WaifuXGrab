import random
import html
from io import BytesIO

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from senpai import (application, PHOTO_URL,
                    user_collection, top_global_groups_collection,
                    group_user_totals_collection)
from senpai.modules.auth import is_sudo_user
from senpai.locale import tr


async def reply_leaderboard(update: Update, text: str) -> None:
    if PHOTO_URL:
        await update.message.reply_photo(
            photo=random.choice(PHOTO_URL),
            caption=text,
            parse_mode='HTML',
        )
        return

    await update.message.reply_text(text, parse_mode='HTML')


async def global_leaderboard(update: Update, context: CallbackContext) -> None:

    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = await tr(update, "leaderboard.global_title")

    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))

        if len(group_name) > 10:
            group_name = group_name[:15] + '...'
        count = group['count']
        leaderboard_message += f'{i}. <b>{group_name}</b> ➾ <b>{count}</b>\n'
    await reply_leaderboard(update, leaderboard_message)

async def ctop(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": chat_id}},
        {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = await tr(update, "leaderboard.ctop_title")

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'

    await reply_leaderboard(update, leaderboard_message)


async def leaderboard(update: Update, context: CallbackContext) -> None:

    cursor = user_collection.aggregate([
        {"$project": {"username": 1, "first_name": 1, "character_count": {"$size": "$characters"}}},
        {"$sort": {"character_count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)

    leaderboard_message = await tr(update, "leaderboard.top_title")

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))

        if len(first_name) > 10:
            first_name = first_name[:15] + '...'
        character_count = user['character_count']
        leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'

    await reply_leaderboard(update, leaderboard_message)




async def stats(update: Update, context: CallbackContext) -> None:

    if not await is_sudo_user(update.effective_user.id):
        await update.message.reply_text(await tr(update, "leaderboard.unauthorized"))
        return


    user_count = await user_collection.count_documents({})


    group_count = await group_user_totals_collection.distinct('group_id')


    await update.message.reply_text(await tr(update, "leaderboard.stats", user_count=user_count, group_count=len(group_count)))




async def send_users_document(update: Update, context: CallbackContext) -> None:
    if not await is_sudo_user(update.effective_user.id):
        await update.message.reply_text(await tr(update, "leaderboard.sudo_only"))
        return
    cursor = user_collection.find({})
    users = []
    async for document in cursor:
        users.append(document)
    user_list = ""
    for user in users:
        user_list += f"{user['first_name']}\n"
    document = BytesIO(user_list.encode())
    document.name = "users.txt"
    await context.bot.send_document(chat_id=update.effective_chat.id, document=document)

async def send_groups_document(update: Update, context: CallbackContext) -> None:
    if not await is_sudo_user(update.effective_user.id):
        await update.message.reply_text(await tr(update, "leaderboard.sudo_only"))
        return
    cursor = top_global_groups_collection.find({})
    groups = []
    async for document in cursor:
        groups.append(document)
    group_list = ""
    for group in groups:
        group_list += f"{group['group_name']}\n"
        group_list += "\n"
    document = BytesIO(group_list.encode())
    document.name = "groups.txt"
    await context.bot.send_document(chat_id=update.effective_chat.id, document=document)


application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))
application.add_handler(CommandHandler('TopGroups', global_leaderboard, block=False))

application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))


application.add_handler(CommandHandler('top', leaderboard, block=False))

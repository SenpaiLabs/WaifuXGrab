from __future__ import annotations

from datetime import datetime, timezone

from telegram import Chat, User

from shivu import OWNER_ID, sudo_users_collection


def is_owner(user_id: int | None) -> bool:
    return bool(user_id) and int(user_id) == OWNER_ID


async def is_sudo_user(user_id: int | None) -> bool:
    if not user_id:
        return False
    if is_owner(user_id):
        return True

    sudo_user = await sudo_users_collection.find_one({"user_id": int(user_id)})
    return sudo_user is not None


def display_name(user: User | Chat) -> str:
    return (
        getattr(user, "first_name", None)
        or getattr(user, "full_name", None)
        or getattr(user, "title", None)
        or str(user.id)
    )


async def add_sudo_user(user: User | Chat, added_by: User) -> bool:
    result = await sudo_users_collection.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "user_id": user.id,
                "first_name": display_name(user),
                "username": getattr(user, "username", None),
                "added_by": added_by.id,
                "updated_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )
    return result.upserted_id is not None


async def remove_sudo_user(user_id: int) -> bool:
    result = await sudo_users_collection.delete_one({"user_id": int(user_id)})
    return result.deleted_count > 0


async def get_sudo_users() -> list[dict]:
    cursor = sudo_users_collection.find({}).sort("created_at", 1)
    return await cursor.to_list(length=None)


async def resolve_target_user(update, context):
    if update.effective_message.reply_to_message:
        return update.effective_message.reply_to_message.from_user

    if not context.args:
        return None

    target = context.args[0]
    if target.lstrip("-").isdigit():
        target = int(target)

    return await context.bot.get_chat(target)

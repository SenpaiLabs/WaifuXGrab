from html import escape

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from senpai import OWNER_ID, application
from senpai.modules.auth import (
    add_sudo_user,
    display_name,
    get_sudo_users,
    is_owner,
    is_sudo_user,
    remove_sudo_user,
    resolve_target_user,
)
from senpai.locale import tr


async def addsudo(update: Update, context: CallbackContext) -> None:
    if not is_owner(update.effective_user.id):
        await update.message.reply_text(await tr(update, "sudo.owner_only"))
        return

    try:
        target_user = await resolve_target_user(update, context)
    except (TypeError, ValueError):
        await update.message.reply_text(await tr(update, "sudo.invalid_user"))
        return

    if not target_user:
        await update.message.reply_text(await tr(update, "sudo.usage_add"))
        return

    if is_owner(target_user.id):
        await update.message.reply_text(await tr(update, "sudo.owner_already"))
        return

    already_sudo = await is_sudo_user(target_user.id)
    await add_sudo_user(target_user, update.effective_user)

    key = "sudo.already_sudo" if already_sudo else "sudo.added"
    await update.message.reply_text(
        await tr(
            update,
            key,
            user_id=target_user.id,
            first_name=display_name(target_user),
        ),
        parse_mode="HTML",
    )


async def rmsudo(update: Update, context: CallbackContext) -> None:
    if not is_owner(update.effective_user.id):
        await update.message.reply_text(await tr(update, "sudo.owner_only"))
        return

    try:
        target_user = await resolve_target_user(update, context)
    except (TypeError, ValueError):
        await update.message.reply_text(await tr(update, "sudo.invalid_user"))
        return

    if not target_user:
        await update.message.reply_text(await tr(update, "sudo.usage_remove"))
        return

    if is_owner(target_user.id):
        await update.message.reply_text(await tr(update, "sudo.cannot_remove_owner"))
        return

    removed = await remove_sudo_user(target_user.id)
    key = "sudo.removed" if removed else "sudo.not_sudo"
    await update.message.reply_text(
        await tr(
            update,
            key,
            user_id=target_user.id,
            first_name=display_name(target_user),
        ),
        parse_mode="HTML",
    )


async def sudolist(update: Update, context: CallbackContext) -> None:
    try:
        owner = await context.bot.get_chat(OWNER_ID)
        owner_name = display_name(owner)
    except Exception:
        owner_name = str(OWNER_ID)

    sudo_users = await get_sudo_users()
    sudo_lines = []
    for index, user in enumerate(sudo_users, start=1):
        first_name = escape(user.get("first_name") or str(user["user_id"]))
        sudo_lines.append(
            f'{index}. <a href="tg://user?id={user["user_id"]}">{first_name}</a>'
        )

    if not sudo_lines:
        sudo_lines.append(await tr(update, "sudo.list_empty"))

    text = await tr(
        update,
        "sudo.list",
        owner_id=OWNER_ID,
        owner_name=escape(owner_name),
        sudos="\n".join(sudo_lines),
    )
    await update.message.reply_text(text, parse_mode="HTML")


application.add_handler(CommandHandler("addsudo", addsudo, block=False))
application.add_handler(CommandHandler("rmsudo", rmsudo, block=False))
application.add_handler(CommandHandler("sudolist", sudolist, block=False))

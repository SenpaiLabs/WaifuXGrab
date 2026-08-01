import urllib.request

import aiohttp
from pymongo import ReturnDocument

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from senpai import (
    application,
    collection,
    db,
    CHARA_CHANNEL_ID,
    SUPPORT_CHAT,
    IMGBB_API_KEY,
)
from senpai.modules.auth import is_sudo_user
from senpai.locale import tr


IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"


async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=ReturnDocument.AFTER
    )
    if not sequence_document:
        await sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0
    return sequence_document['sequence_value']


async def upload_to_imgbb(image_url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            IMGBB_UPLOAD_URL,
            data={"key": IMGBB_API_KEY, "image": image_url},
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            result = await response.json(content_type=None)

    if not result.get("success"):
        error = result.get("error", {}).get("message", "Imgbb upload failed")
        raise RuntimeError(error)

    return result["data"].get("display_url") or result["data"]["url"]


def _get_replied_image_file_id(message) -> str | None:
    if not message:
        return None

    if getattr(message, "photo", None):
        return message.photo[-1].file_id

    document = getattr(message, "document", None)
    if document and getattr(document, "mime_type", "").startswith("image/"):
        return document.file_id

    return None


async def _resolve_image_url(update: Update, context: CallbackContext, provided_url: str | None = None) -> str:
    if provided_url:
        try:
            urllib.request.urlopen(provided_url)
        except Exception:
            raise ValueError(await tr(update, "upload.invalid_url"))
        return await upload_to_imgbb(provided_url)

    file_id = _get_replied_image_file_id(update.effective_message.reply_to_message)
    if not file_id:
        raise ValueError(await tr(update, "upload.invalid_url"))

    file = await context.bot.get_file(file_id)
    telegram_file_url = f"https://api.telegram.org/file/bot{context.bot.token}/{file.file_path}"

    try:
        urllib.request.urlopen(telegram_file_url)
    except Exception:
        raise ValueError(await tr(update, "upload.invalid_url"))

    return await upload_to_imgbb(telegram_file_url)


async def upload(update: Update, context: CallbackContext) -> None:
    if not await is_sudo_user(update.effective_user.id):
        await update.message.reply_text(await tr(update, "upload.owner_only"))
        return

    try:
        args = context.args
        if len(args) == 4:
            img_url_arg = args[0]
            character_name = args[1].replace('-', ' ').title()
            anime = args[2].replace('-', ' ').title()
            rarity_arg = args[3]
        elif len(args) == 3:
            img_url_arg = None
            character_name = args[0].replace('-', ' ').title()
            anime = args[1].replace('-', ' ').title()
            rarity_arg = args[2]
        else:
            await update.message.reply_text(await tr(update, "upload.wrong_format"))
            return

        try:
            img_url = await _resolve_image_url(update, context, img_url_arg)
        except ValueError as exc:
            await update.message.reply_text(str(exc))
            return

        rarity_map = {1: "⚪ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium"}
        try:
            rarity = rarity_map[int(rarity_arg)]
        except KeyError:
            await update.message.reply_text(await tr(update, "upload.invalid_rarity"))
            return

        id = str(await get_next_sequence_number('character_id')).zfill(2)

        character = {
            'img_url': img_url,
            'name': character_name,
            'anime': anime,
            'rarity': rarity,
            'id': id
        }

        try:
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=img_url,
                caption=await tr(
                    update,
                    "upload.channel_caption_added",
                    name=character_name,
                    anime=anime,
                    rarity=rarity,
                    character_id=id,
                    user_id=update.effective_user.id,
                    first_name=update.effective_user.first_name,
                ),
                parse_mode='HTML'
            )
            character['message_id'] = message.message_id
            await collection.insert_one(character)
            await update.message.reply_text(await tr(update, "upload.added"))
        except:
            await collection.insert_one(character)
            await update.effective_message.reply_text(await tr(update, "upload.added_no_channel"))

    except Exception as e:
        await update.message.reply_text(await tr(update, "upload.upload_failed", error=str(e), support_chat=SUPPORT_CHAT))

async def delete(update: Update, context: CallbackContext) -> None:
    if not await is_sudo_user(update.effective_user.id):
        await update.message.reply_text(await tr(update, "upload.delete_owner_only"))
        return

    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text(await tr(update, "upload.delete_usage"))
            return


        character = await collection.find_one_and_delete({'id': args[0]})

        if character:

            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character['message_id'])
            await update.message.reply_text(await tr(update, "upload.deleted"))
        else:
            await update.message.reply_text(await tr(update, "upload.deleted_no_channel"))
    except Exception as e:
        await update.message.reply_text(f'{str(e)}')

async def update(update: Update, context: CallbackContext) -> None:
    if not await is_sudo_user(update.effective_user.id):
        await update.message.reply_text(await tr(update, "upload.permission_denied"))
        return

    try:
        args = context.args
        if len(args) == 3:
            character_id = args[0]
            field_name = args[1]
            new_value = args[2]
        elif len(args) == 2 and args[1] == 'img_url':
            character_id = args[0]
            field_name = args[1]
            new_value = None
        else:
            await update.message.reply_text(await tr(update, "upload.update_usage"))
            return

        # Get character by ID
        character = await collection.find_one({'id': character_id})
        if not character:
            await update.message.reply_text(await tr(update, "upload.not_found"))
            return

        # Check if field is valid
        valid_fields = ['img_url', 'name', 'anime', 'rarity']
        if field_name not in valid_fields:
            await update.message.reply_text(await tr(update, "upload.invalid_field", fields=", ".join(valid_fields)))
            return

        # Update field
        if field_name in ['name', 'anime']:
            new_value = new_value.replace('-', ' ').title()
        elif field_name == 'rarity':
            rarity_map = {1: "⚪ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium", 5: "💮 Special edition"}
            try:
                new_value = rarity_map[int(new_value)]
            except KeyError:
                await update.message.reply_text(await tr(update, "upload.invalid_rarity"))
                return
        else:
            try:
                new_value = await _resolve_image_url(update, context, new_value)
            except ValueError as exc:
                await update.message.reply_text(str(exc))
                return

        await collection.find_one_and_update({'id': character_id}, {'$set': {field_name: new_value}})


        if field_name == 'img_url':
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character['message_id'])
            message = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=new_value,
                caption=await tr(
                    update,
                    "upload.channel_caption_updated",
                    name=character["name"],
                    anime=character["anime"],
                    rarity=character["rarity"],
                    character_id=character["id"],
                    user_id=update.effective_user.id,
                    first_name=update.effective_user.first_name,
                ),
                parse_mode='HTML'
            )
            character['message_id'] = message.message_id
            await collection.find_one_and_update({'id': character_id}, {'$set': {'message_id': message.message_id}})
        else:

            await context.bot.edit_message_caption(
                chat_id=CHARA_CHANNEL_ID,
                message_id=character['message_id'],
                caption=await tr(
                    update,
                    "upload.channel_caption_updated",
                    name=character["name"],
                    anime=character["anime"],
                    rarity=character["rarity"],
                    character_id=character["id"],
                    user_id=update.effective_user.id,
                    first_name=update.effective_user.first_name,
                ),
                parse_mode='HTML'
            )

        await update.message.reply_text(await tr(update, "upload.updated"))
    except Exception as e:
        await update.message.reply_text(await tr(update, "upload.update_failed"))

UPLOAD_HANDLER = CommandHandler('upload', upload, block=False)
application.add_handler(UPLOAD_HANDLER)
DELETE_HANDLER = CommandHandler('delete', delete, block=False)
application.add_handler(DELETE_HANDLER)
UPDATE_HANDLER = CommandHandler('update', update, block=False)
application.add_handler(UPDATE_HANDLER)

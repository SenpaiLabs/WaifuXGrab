from pymongo import  ReturnDocument
from pyrogram.enums import ChatMemberStatus, ChatType
from senpai import user_totals_collection, shivuu
from pyrogram import Client, filters
from pyrogram.types import Message
from senpai.locale import tr

ADMINS = [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]


@shivuu.on_message(filters.command("changetime"))
async def change_time(client: Client, message: Message):

    user_id = message.from_user.id
    chat_id = message.chat.id
    member = await shivuu.get_chat_member(chat_id,user_id)


    if member.status not in ADMINS :
        await message.reply_text(await tr(chat_id, "changetime.not_admin"))
        return

    try:
        args = message.command
        if len(args) != 2:
            await message.reply_text(await tr(chat_id, "changetime.usage"))
            return

        new_frequency = int(args[1])
        if new_frequency < 100:
            await message.reply_text(await tr(chat_id, "changetime.too_low"))
            return


        chat_frequency = await user_totals_collection.find_one_and_update(
            {'chat_id': str(chat_id)},
            {'$set': {'message_frequency': new_frequency}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        await message.reply_text(await tr(chat_id, "changetime.success", frequency=new_frequency))
    except Exception as e:
        await message.reply_text(await tr(chat_id, "changetime.failed", error=str(e)))

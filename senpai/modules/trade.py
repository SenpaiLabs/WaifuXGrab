from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from senpai import user_collection, shivuu
from senpai.locale import tr

pending_trades = {}


@shivuu.on_message(filters.command("trade"))
async def trade(client, message):
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_text(await tr(message.chat.id, "trade.reply_required"))
        return

    receiver_id = message.reply_to_message.from_user.id

    if sender_id == receiver_id:
        await message.reply_text(await tr(message.chat.id, "trade.self_trade"))
        return

    if len(message.command) != 3:
        await message.reply_text(await tr(message.chat.id, "trade.missing_ids"))
        return

    sender_character_id, receiver_character_id = message.command[1], message.command[2]

    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    sender_character = next((character for character in sender['characters'] if character['id'] == sender_character_id), None)
    receiver_character = next((character for character in receiver['characters'] if character['id'] == receiver_character_id), None)

    if not sender_character:
        await message.reply_text(await tr(message.chat.id, "trade.sender_missing"))
        return

    if not receiver_character:
        await message.reply_text(await tr(message.chat.id, "trade.receiver_missing"))
        return






    if len(message.command) != 3:
        await message.reply_text(await tr(message.chat.id, "trade.usage"))
        return

    sender_character_id, receiver_character_id = message.command[1], message.command[2]


    pending_trades[(sender_id, receiver_id)] = (sender_character_id, receiver_character_id)


    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(await tr(message.chat.id, "trade.confirm_button"), callback_data="confirm_trade")],
            [InlineKeyboardButton(await tr(message.chat.id, "trade.cancel_button"), callback_data="cancel_trade")]
        ]
    )

    await message.reply_text(await tr(message.chat.id, "trade.request", mention=message.reply_to_message.from_user.mention), reply_markup=keyboard)


@shivuu.on_callback_query(filters.create(lambda _, __, query: query.data in ["confirm_trade", "cancel_trade"]))
async def on_callback_query(client, callback_query):
    receiver_id = callback_query.from_user.id


    for (sender_id, _receiver_id), (sender_character_id, receiver_character_id) in pending_trades.items():
        if _receiver_id == receiver_id:
            break
    else:
        await callback_query.answer(await tr(callback_query.message.chat.id, "trade.not_for_you"), show_alert=True)
        return

    if callback_query.data == "confirm_trade":

        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': receiver_id})

        sender_character = next((character for character in sender['characters'] if character['id'] == sender_character_id), None)
        receiver_character = next((character for character in receiver['characters'] if character['id'] == receiver_character_id), None)



        sender['characters'].remove(sender_character)
        receiver['characters'].remove(receiver_character)


        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender['characters']}})
        await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver['characters']}})


        sender['characters'].append(receiver_character)
        receiver['characters'].append(sender_character)


        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender['characters']}})
        await user_collection.update_one({'id': receiver_id}, {'$set': {'characters': receiver['characters']}})


        del pending_trades[(sender_id, receiver_id)]

        await callback_query.message.edit_text(await tr(callback_query.message.chat.id, "trade.success", mention=callback_query.message.reply_to_message.from_user.mention))

    elif callback_query.data == "cancel_trade":

        del pending_trades[(sender_id, receiver_id)]

        await callback_query.message.edit_text(await tr(callback_query.message.chat.id, "trade.cancelled"))




pending_gifts = {}


@shivuu.on_message(filters.command("gift"))
async def gift(client, message):
    sender_id = message.from_user.id

    if not message.reply_to_message:
        await message.reply_text(await tr(message.chat.id, "gift.reply_required"))
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text(await tr(message.chat.id, "gift.self_gift"))
        return

    if len(message.command) != 2:
        await message.reply_text(await tr(message.chat.id, "gift.missing_id"))
        return

    character_id = message.command[1]

    sender = await user_collection.find_one({'id': sender_id})

    character = next((character for character in sender['characters'] if character['id'] == character_id), None)

    if not character:
        await message.reply_text(await tr(message.chat.id, "gift.not_owned"))
        return


    pending_gifts[(sender_id, receiver_id)] = {
        'character': character,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name
    }


    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(await tr(message.chat.id, "gift.confirm_button"), callback_data="confirm_gift")],
            [InlineKeyboardButton(await tr(message.chat.id, "gift.cancel_button"), callback_data="cancel_gift")]
        ]
    )

    await message.reply_text(await tr(message.chat.id, "gift.request", mention=message.reply_to_message.from_user.mention), reply_markup=keyboard)

@shivuu.on_callback_query(filters.create(lambda _, __, query: query.data in ["confirm_gift", "cancel_gift"]))
async def on_callback_query(client, callback_query):
    sender_id = callback_query.from_user.id


    for (_sender_id, receiver_id), gift in pending_gifts.items():
        if _sender_id == sender_id:
            break
    else:
        await callback_query.answer(await tr(callback_query.message.chat.id, "trade.not_for_you"), show_alert=True)
        return

    if callback_query.data == "confirm_gift":

        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': receiver_id})


        sender['characters'].remove(gift['character'])
        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender['characters']}})


        if receiver:
            await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': gift['character']}})
        else:

            await user_collection.insert_one({
                'id': receiver_id,
                'username': gift['receiver_username'],
                'first_name': gift['receiver_first_name'],
                'characters': [gift['character']],
            })


        del pending_gifts[(sender_id, receiver_id)]

        await callback_query.message.edit_text(await tr(callback_query.message.chat.id, "gift.success", first_name=gift["receiver_first_name"], user_id=receiver_id))

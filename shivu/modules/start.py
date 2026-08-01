import random
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, db, GROUP_ID
from shivu import pm_users as collection
from shivu.locale import tr


SOURCE_URL = "https://github.com/SenpaiLabs/WaifuXGrab"


async def start_keyboard(context: CallbackContext) -> InlineKeyboardMarkup:
    bot_username = context.bot.username or (await context.bot.get_me()).username
    keyboard = [
        [InlineKeyboardButton("ADD ME", url=f'http://t.me/{bot_username}?startgroup=new')],
    ]
    chat_buttons = []
    if SUPPORT_CHAT:
        chat_buttons.append(InlineKeyboardButton("SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'))
    if UPDATE_CHAT:
        chat_buttons.append(InlineKeyboardButton("UPDATES", url=f'https://t.me/{UPDATE_CHAT}'))
    if chat_buttons:
        keyboard.append(chat_buttons)
    keyboard.append([InlineKeyboardButton("HELP", callback_data='help')])
    if SOURCE_URL:
        keyboard.append([InlineKeyboardButton("SOURCE", url=SOURCE_URL)])
    return InlineKeyboardMarkup(keyboard)


async def send_start_response(
    update: Update,
    caption: str,
    reply_markup: InlineKeyboardMarkup,
    parse_mode: str | None = None,
) -> None:
    if PHOTO_URL:
        await contextless_reply_photo(update, caption, reply_markup, parse_mode)
        return

    await update.effective_message.reply_text(
        caption,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )


async def contextless_reply_photo(
    update: Update,
    caption: str,
    reply_markup: InlineKeyboardMarkup,
    parse_mode: str | None,
) -> None:
    photo_url = random.choice(PHOTO_URL)
    await update.effective_message.reply_photo(
        photo=photo_url,
        caption=caption,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )


async def edit_start_message(
    update: Update,
    caption: str,
    reply_markup: InlineKeyboardMarkup,
    parse_mode: str | None = None,
) -> None:
    message = update.callback_query.message
    if message.caption is not None:
        await update.callback_query.edit_message_caption(
            caption=caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
        return

    await update.callback_query.edit_message_text(
        text=caption,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:

        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})

        if GROUP_ID:
            await context.bot.send_message(chat_id=GROUP_ID,
                                           text=await tr(update, "start.new_user_log", user_id=user_id, first_name=escape(first_name)),
                                           parse_mode='HTML')
    else:

        if user_data['first_name'] != first_name or user_data['username'] != username:

            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})



    if update.effective_chat.type== "private":


        caption = await tr(update, "start.private_caption")

        reply_markup = await start_keyboard(context)

        await send_start_response(update, caption, reply_markup, parse_mode='markdown')

    else:
        reply_markup = await start_keyboard(context)
        await send_start_response(
            update,
            await tr(update, "start.group_caption"),
            reply_markup,
        )

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = await tr(update, "start.help_caption")
        help_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)

        await edit_start_message(update, help_text, reply_markup, parse_mode='markdown')

    elif query.data == 'back':

        caption = await tr(update, "start.back_caption")


        reply_markup = await start_keyboard(context)

        await edit_start_message(update, caption, reply_markup, parse_mode='markdown')


application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$', block=False))
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)

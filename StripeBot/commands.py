# commands.py
import asyncio
from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from api import get_subscribers_emails
import json
import datetime
import time
from config import ADMIN_IDS, ANSWERS, GROUP_LINK,PREMIUM_CHANNEL_ID
import pytz

uk_timezone = pytz.timezone('Europe/London')

welcome_message = (
    "Hello 👋, Welcome to AtlasTrading's Free Signal Group. How can we assist you on your trading journey?\n\n"
    "Please select one of the following options:")


async def send_faq(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Can you give me more information about your services?", callback_data='info')],
        [InlineKeyboardButton("How do I get started trading with you?", callback_data='get_started')],
        [InlineKeyboardButton("Can I Join your premium group?", callback_data='premium')],
        [InlineKeyboardButton("No thanks", callback_data='no_thanks')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)


async def info_button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data in ANSWERS:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=ANSWERS[query.data])



def read_data_from_json(path):
    with open(path, "r") as json_file:
        json_data = json.load(json_file)
    return json_data


def write_data_to_json(path, data):
    with open(path, "w") as json_file:
        json.dump(data, json_file)


users_in_group_path = "users_in_group.json"
message_path = "message.json"
customer_data_path = "customer_data.json"
users_in_group = read_data_from_json(users_in_group_path)
message_json = read_data_from_json(message_path)
customer_data = read_data_from_json(customer_data_path)
banned_users = read_data_from_json("banned_users.json")
print(users_in_group)


async def start_command(update: Update, context: CallbackContext):
    await send_faq(update, context)


async def unban_user(update, context, user_id, chat_id):
    try:
        await context.bot.unban_chat_member(chat_id, user_id)

        print("User unbanned successfully")

        updated_banned_users = [user for user in banned_users if user["user_id"] != user_id]

        write_data_to_json("banned_users.json", updated_banned_users)

        print("User data updated successfully")
    except Exception as e:
        print(f"An error occurred while unbanning the user: {e}")


async def login_command(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        await update.message.reply_text("Please provide your email after the /login command.")
        return

    email = context.args[0]

    thinking_msg = await update.message.reply_text("Bot is thinking... Please wait.")
    print("emailler çekiliyor...")
    subscribers_emails = await get_subscribers_emails()
    print(len(subscribers_emails))

    if await check_email_in_subscribers(email, subscribers_emails):
        for b in banned_users:
            if update.message.from_user.id == b["user_id"]:
                await unban_user(update, context, b["user_id"], PREMIUM_CHANNEL_ID)
                banned_users.remove(b)
                write_data_to_json("banned_users.json", banned_users)

        await thinking_msg.edit_text("Here is the invite link")
        await add_to_group(update, context, email)
        print("login:", email)
    else:
        await thinking_msg.edit_text("You must subscribe")
        print("unsubscribe:", email)


async def check_email_in_subscribers(email, subscribers):
    for subscriber_email in subscribers:
        if subscriber_email == email:
            return True
    return False


async def add_to_group(update: Update, context: CallbackContext, email):
    user_id = update.message.from_user.id

    if not any(user['email'] == email for user in users_in_group):
        users_in_group.append({'email': email, 'user_id': user_id})
        write_data_to_json(users_in_group_path, users_in_group)
        #await new_member(update, context)


    await update.message.reply_text(f"Link to join the group: {GROUP_LINK}")


async def set_message_command(update, context):
    # Parse parameters
    try:
        if update.message.from_user.id not in ADMIN_IDS:
            await update.message.reply_text("Only admins are allowed to use this command.")
            return

        channel_id, message, hour, minute = context.args
        hour = int(hour)
        minute = int(minute)
        # Generate unique ID based on timestamp
        message_id = int(time.time() * 1000)  # Using milliseconds to ensure uniqueness
        txt = f"Message ID: {message_id}\nChannel ID: {channel_id}\nMessage: {message}\nHour: {hour}\nMinute: {minute}"
        await update.message.reply_text(txt)
        # Add message with unique ID to message_json
        message_json.append({"id": message_id, "channel_id": channel_id, "message": message, "hour": hour, "minute": minute, "last_update": -1})
        write_data_to_json(message_path, message_json)

    except ValueError:
        await update.message.reply_text("Invalid parameters! Usage: /set_message channelId message hour minute")


async def send_message_daily(app):

    while True:
        current_time_utc = datetime.datetime.now(pytz.utc)
        current_time_uk = current_time_utc.astimezone(uk_timezone)
        for item in message_json:
            daily_time = datetime.time(hour=item["hour"], minute=item["minute"])
            day = current_time_uk.day
            hour = current_time_uk.hour
            minute = current_time_uk.minute
            current_time = datetime.time(hour=hour, minute=minute)
            if current_time >= daily_time and (item["last_update"] != day or item["last_update"] == -1):
                print(item["message"])
                await app.bot.send_message(item["channel_id"], item["message"])
                item["last_update"] = day
                write_data_to_json(message_path, message_json)
        await asyncio.sleep(60)


async def delete_message_callback(update, context):

    query = update.callback_query
    message_id_to_delete = int(query.data.split('_')[2])

    for idx, item in enumerate(message_json):
        if item["id"] == message_id_to_delete:
            print("aaaaa")
            del message_json[idx]
            write_data_to_json(message_path, message_json)
            await context.bot.send_message(chat_id=query.message.chat_id, text="Message deleted successfully!")
            await query.message.delete()
            return
    await context.bot.send_message(chat_id=query.message.chat_id, text="Message not found!")


async def delete_message_command(update, context):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Only admins are allowed to use this command.")
        return

    buttons = []

    for item in message_json:
        # Create a button for each message
        button_text = item["message"]
        button_callback_data = f"delete_message_{item['id']}"  # Unique identifier for each message
        buttons.append([InlineKeyboardButton(button_text, callback_data=button_callback_data)])

    # Create the keyboard
    reply_markup = InlineKeyboardMarkup(buttons)

    # Send the message with the buttons
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Select a message to delete:",
                                   reply_markup=reply_markup)

#main.py
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters)
from commands import (login_command, start_command, read_data_from_json, write_data_to_json, set_message_command,
                      send_message_daily, delete_message_command, delete_message_callback, info_button_click)
from error import error
from config import TOKEN, PREMIUM_CHANNEL_ID
from api import get_subscribers_emails
import asyncio

users_in_group_path = "users_in_group.json"
users_in_group = read_data_from_json(users_in_group_path)
message_path = "message.json"
banned_users =read_data_from_json("banned_users.json")


async def ban_user(bot, group_id, user_id):
    try:
        await bot.ban_chat_member(chat_id=group_id, user_id=user_id)
    except Exception as e:
        print("Bir hata oluştu:", e)


async def check_subscriptions(bot):

    while True:
        await asyncio.sleep(1800)
        print("getting emails")
        emails = await get_subscribers_emails()
        updated_users_in_group = [item for item in users_in_group if item["email"] in emails]
        different = [item for item in users_in_group if item["email"] not in emails]
        write_data_to_json(users_in_group_path, updated_users_in_group)

        for d in different:
            print(d["email"])
            banned_users.append({"email": d["email"], "user_id":d["user_id"]})
            print(banned_users)
            write_data_to_json("banned_users.json", banned_users)
            await ban_user(bot, PREMIUM_CHANNEL_ID, d["user_id"])

        await asyncio.sleep(1800)


if __name__ == "__main__":
    print("STARTING BOT...")
    app = Application.builder().token(TOKEN).build()
    # COMMANDS
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("set_message", set_message_command))
    app.add_handler(CommandHandler("delete_message", delete_message_command))
    app.add_handler(CallbackQueryHandler(delete_message_callback, pattern=r'^delete_message_\d+$'))

    app.add_handler(CallbackQueryHandler(info_button_click))

    # THREADING
    loop = asyncio.get_event_loop()
    t1 = loop.create_task(send_message_daily(app))
    t2 = loop.create_task(check_subscriptions(app.bot))
    t3 = loop.create_task(app.run_polling(poll_interval=3))  # Create a task for app.run_polling()

    # ERROR
    app.add_error_handler(error)

    try:
        loop.run_until_complete(asyncio.gather(t1, t2, t3))  # Run all tasks together
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()



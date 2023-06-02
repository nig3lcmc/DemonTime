from typing import Final
import pytz
from datetime import datetime, date
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import *

from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
from queue import Queue



TOKEN: Final = '5880233487:AAFp2_wmkULYQUw8vQ1i0tAOTlZbqG3gcNY'
BOT_USERNAME: Final = '@rrememberbot'
client = FaunaClient(secret = "fnAFEtmWPsAAUXme7DOxbqzQFgq-Cj5cXVx546aR")


async def start_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    first_name = update.message.chat.first_name
    username = update.message.chat.username

    try:
        client.query(q.get(q.match(q.index("users_index"), chat_id)))
        await context.bot.send_message(
            chat_id=chat_id,
            text="Welcome to RemBot!\n\nTo add a reminder, enter /add_reminder\nTo list all reminders, enter /list_reminders\nTo list all reminders you have today, enter /list_today_reminders",
        )
    except:
        user = client.query(
            q.create(
                q.collection("users"),
                {
                    "data": {
                        "id": chat_id,
                        "first_name": first_name,
                        "username": username,
                        "last_command": "",
                        "date": datetime.now(pytz.timezone("Asia/Singapore")),
                    }
                },
            )
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text="Welcome to RemBot, your details have been saved! 😊\n\nTo add a reminder, enter /add_reminder\nTo list all reminders, enter /list_reminders\nTo list all reminders you have today, enter /list_today_reminders",
        )


async def add_reminder(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = client.query(q.get(q.match(q.index("users_index"), chat_id)))
    client.query(
        q.update(
            q.ref(q.collection("users"), user["ref"].id()),
            {"data": {"last_command": "add_reminder"}},
        )
    )
    await context.bot.send_message(
        chat_id=chat_id,
        text="Enter the reminder you want to add along with its due date in this format (mm/dd/yyyy), separated by a comma 😁",
    )


async def echo(update: Update, context: CallbackContext):
    print("Received update:", update)
    print("Received message:", update.message)

    chat_id = update.effective_chat.id
    message = update.message.text

    user = client.query(q.get(q.match(q.index("users_index"), chat_id)))
    last_command = user["data"]["last_command"]

    if last_command == "add_reminder":

        date_string = message.split(",")[1]
        try:
            date_due = datetime.strptime(date_string, '%m/%d/%Y').date()
            reminders = client.query(q.create(q.collection("reminders"), {
                "data": {
                    "user_id": chat_id,
                    "reminder": message.split(",")[0],
                    "completed": False,
                    "date_due": message.split(",")[1]
                }
            }))
            client.query(q.update(q.ref(q.collection("users"), user["ref"].id()), {"data": {"last_command": ""}}))
            await context.bot.send_message(chat_id=chat_id, text="Successfully added reminder 👍")
      
        except ValueError:
            error_message = "Invalid date format. Please enter the date in the format mm/dd/yyyy."
            await context.bot.send_message(chat_id=chat_id, text=error_message)
        




async def list_reminders(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    event_message = ""
    reminders = client.query(q.paginate(q.match(q.index("reminders_index"), chat_id)))

    for r in reminders["data"]:
        reminder = client.query(q.get(q.ref(q.collection("reminders"), r.id())))

        if reminder["data"]["completed"]:
            event_status = "Completed"
        else:
            event_status = "Not Completed"

        event_message += "{}\nStatus: {}\nDate Due: {}\n\n".format(
            reminder["data"]["reminder"],
            event_status,
            reminder["data"]["date_due"],
        )

    if event_message == "":
        event_message = "You don't have any reminders saved. Type /add_reminder to schedule one now! 😇"

    await context.bot.send_message(chat_id=chat_id, text=event_message)


async def list_today_reminders(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    event_message = ""
    today = date.today()
    date1 = today.strftime("%m/%d/%Y")

    reminders = client.query(
        q.paginate(q.match(q.index("reminder_today_index"), chat_id, date1))
    )

    for r in reminders["data"]:
        reminder = client.query(q.get(q.ref(q.collection("reminders"), r.id())))

        if reminder["data"]["completed"]:
            event_status = "Completed"
        else:
            event_status = "Not Completed"

        event_message += "{}\nStatus: {}\nDate Due: {}\n\n".format(
            reminder["data"]["reminder"],
            event_status,
            reminder["data"]["date_due"],
        )

    if event_message == "":
        event_message = "You don't have any reminders for today. Type /add_reminder to schedule one now! 😇"

    await context.bot.send_message(chat_id=chat_id, text=event_message)


async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "To add a reminder, enter /add_reminder\nTo list all reminders, enter /list_reminders\nTo list all reminders you have today, enter /list_today_reminders"
    )


def error(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")


def main():
    updater = Updater(TOKEN, update_queue = Queue())
    dispatcher = Application.builder().token(TOKEN).build()
  
    # Commands
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("add_reminder", add_reminder))
    dispatcher.add_handler(CommandHandler("list_reminders", list_reminders))
    dispatcher.add_handler(
        CommandHandler("list_today_reminders", list_today_reminders)
    )
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Messages
    dispatcher.add_handler(MessageHandler(filters.TEXT, echo))

    # Log all errors
    dispatcher.add_error_handler(error)

    dispatcher.run_polling(poll_interval = 5)


if __name__ == "__main__":
    main()

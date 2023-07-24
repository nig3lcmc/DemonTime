from typing import Final
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
import time 
from datetime import datetime, date
from telegram import *
from telegram.ext import *

from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
from queue import Queue
import schedule
import threading

from tokens import telebotkey 
from tokens import faunakey

TOKEN: Final = telebotkey
BOT_USERNAME: Final = '@rrememberbot'
client = FaunaClient(secret = faunakey)
scheduler = BlockingScheduler()

async def start_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    first_name = update.message.chat.first_name
    username = update.message.chat.username

    try:
        client.query(q.get(q.match(q.index("users_index"), chat_id)))
        client.query(
        q.update(
            q.ref(q.collection("users"), user["ref"].id()),
            {"data": {"last_command": "start_command"}},
        )
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
        text="Enter the reminder you want to add along with its due date in this format (mm/dd/yyyy), followed by due time in HMS format, separated by a comma 😁\neg: lesson,06/26/2023,09:00:00",
    )


async def echo(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message = update.message.text

    user = client.query(q.get(q.match(q.index("users_index"), chat_id)))
    last_command = user["data"]["last_command"]

    if last_command == "add_reminder":

        date_string = message.split(",")[1]
        time_string = message.split(",")[2]
        full_string = date_string + " " + time_string

        try:
            date_due = datetime.strptime(date_string, '%m/%d/%Y').date()
            time_due = datetime.strptime(time_string, '%H:%M:%S').time()
            
            reminders = client.query(q.create(q.collection("reminders"), {
                "data": {
                    "user_id": chat_id,
                    "reminder": message.split(",")[0],
                    "completed": False,
                    "date_due": message.split(",")[1],
                    "time_due": message.split(",")[2],
                    "due_time": full_string
                }
            }))
            client.query(q.update(q.ref(q.collection("users"), user["ref"].id()), {"data": {"last_command": ""}}))
            await context.bot.send_message(chat_id=chat_id, text="Successfully added reminder 👍")

        except IndexError:
            error_message = "Invalid date format. Please enter the date and time in the format mm/dd/yyyy HH:MM:SS"
            await context.bot.send_message(chat_id=chat_id, text=error_message)

        except ValueError:
            error_message = "Invalid date format. Please enter the date and time in the format mm/dd/yyyy HH:MM:SS"
            await context.bot.send_message(chat_id=chat_id, text=error_message)
        #scheduler.add_job(automessage, 'cron', hour=16, minute=40)
    else:
        error_message = "Sorry, I did not understand that."
        await context.bot.send_message(chat_id=chat_id, text=error_message)
        




async def list_reminders(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    event_message = ""
    reminders = client.query(q.paginate(q.match(q.index("reminders_index"), chat_id)))
    user = client.query(q.get(q.match(q.index("users_index"), chat_id)))
    client.query(
        q.update(
            q.ref(q.collection("users"), user["ref"].id()),
            {"data": {"last_command": "list_reminders"}},
        )
    )

    for r in reminders["data"]:
        reminder = client.query(q.get(q.ref(q.collection("reminders"), r.id())))

        if reminder["data"]["completed"]:
            event_status = "Completed"
        else:
            event_status = "Not Completed"

        event_message += "{}\nStatus: {}\nDate Due: {}\nTime Due: {}\nUpdate Link: /update_{}\nDelete Link: /delete_{}\n\n".format(
            reminder["data"]["reminder"],
            event_status,
            reminder["data"]["date_due"],
            reminder["data"]["time_due"],
            r.id(), r.id()
        )

    if event_message == "":
        event_message = "You don't have any reminders saved. Type /add_reminder to schedule one now! 😇"

    await context.bot.send_message(chat_id=chat_id, text=event_message)


async def list_today_reminders(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    event_message = ""
    today = date.today()
    date1 = today.strftime("%m/%d/%Y")
    user = client.query(q.get(q.match(q.index("users_index"), chat_id)))
    client.query(
        q.update(
            q.ref(q.collection("users"), user["ref"].id()),
            {"data": {"last_command": "list_today_reminders"}},
        )
    )
    reminders = client.query(
        q.paginate(q.match(q.index("reminder_today_index"), chat_id, date1))
    )

    for r in reminders["data"]:
        reminder = client.query(q.get(q.ref(q.collection("reminders"), r.id())))

        if reminder["data"]["completed"]:
            event_status = "Completed"
        else:
            event_status = "Not Completed"

        event_message += "{}\nStatus: {}\nDate Due: {}\nTime Due: {}\nUpdate Link: /update_{}\nDelete Link: /delete_{}\n\n".format(
            reminder["data"]["reminder"],
            event_status,
            reminder["data"]["date_due"],
            reminder["data"]["time_due"],
            r.id(), r.id()
        )

    if event_message == "":
        event_message = "You don't have any reminders for today. Type /add_reminder to schedule one now! 😇"

    await context.bot.send_message(chat_id=chat_id, text=event_message)

async def update_appointment(update, context):
   chat_id = update.effective_chat.id
   message = update.message.text
   event_id = message.split("_")[1]
   event = client.query(q.get(q.ref(q.collection("reminders"), event_id)))

   if event["data"]["completed"]:
       new_status = False

   else:
       new_status = True

   client.query(q.update(q.ref(q.collection("reminders"), event_id), {"data": {"completed": new_status}}))
   await context.bot.send_message(chat_id=chat_id, text="Successfully updated reminder status 👌")

async def delete_appointment(update, context):
   chat_id = update.effective_chat.id
   message = update.message.text
   event_id = message.split("_")[1]
   client.query(q.delete(q.ref(q.collection("reminders"), event_id)))
   await context.bot.send_message(chat_id=chat_id, text="Successfully deleted reminder👌")

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "To add a reminder, enter /add_reminder\nTo list all reminders, enter /list_reminders\nTo list all reminders you have today, enter /list_today_reminders"
    )

def notify_hour_before(update: Update, context: CallbackContext):
    # Get the current time
    now = datetime.datetime.now()
    chat_id = update.effective_chat.id
    today = date.today()
    date1 = today.strftime("%m/%d/%Y")
    reminders = client.query(q.paginate(q.match(q.index("reminder_today_index"), chat_id, date1))
    )

    # Get all reminders that are due in one hour
    reminders_due_soon = [reminder for reminder in reminders if datetime.strptime(reminder["due_time"], '%m/%d/%Y %H:%M:%S') - now <= datetime.timedelta(hours=1)]
    
    # For each reminder, send a notification
    for reminder in reminders_due_soon:
        context.bot.send_message(chat_id=reminder['chat_id'], text=f"Reminder: {reminder['message']} is due in one hour.")

def notify_due(update: Update, context: CallbackContext):
    # Get the current time
    now = datetime.datetime.now()
    chat_id = update.effective_chat.id
    today = date.today()
    date1 = today.strftime("%m/%d/%Y")
    reminders = client.query(q.paginate(q.match(q.index("reminder_today_index"), chat_id, date1))
    )
    # Get all reminders that are due now
    reminders_due_now = [reminder for reminder in reminders if reminder['due_time'] <= now]
    
    # For each reminder, send a notification and remove it from the list
    for reminder in reminders_due_now:
        context.bot.send_message(chat_id=reminder['chat_id'], text=f"Reminder: {reminder['message']} is due now.")
        reminders.remove(reminder)

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

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
    dispatcher.add_handler(MessageHandler(filters.Regex("/update_[0-9]*"), update_appointment))
    dispatcher.add_handler(MessageHandler(filters.Regex("/delete_[0-9]*"), delete_appointment))

    # Messages
    dispatcher.add_handler(MessageHandler(filters.TEXT, echo))

    # Log all errors
    dispatcher.add_error_handler(error)

    # Start the schedule in a new thread
    t = threading.Thread(target=run_schedule)
    t.start()

    dispatcher.run_polling(poll_interval = 2)

if __name__ == "__main__":
    main()

scheduler.start()

import time
import subprocess
import uuid
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import nest_asyncio
import sqlite3
import psutil
import asyncio

nest_asyncio.apply()

API_TOKEN = "6816699414:AAGkNhn0oaK1NK9GuKod7gHesX8zV12M760"
upload_url = "https://temp.sh/upload"

active_tasks = {}

# Database Setup
def get_db_connection():
    conn = sqlite3.connect('tasks.db')
    return conn

def create_db_table():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        chat_id INTEGER,
        status TEXT,
        file_url TEXT,
        progress REAL,
        downloaded_size INTEGER
    )
    ''')
    conn.commit()
    conn.close()

# System Stats
def get_system_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    free_storage = psutil.disk_usage('/').free / (1024 * 1024 * 1024)
    return cpu_usage, ram_usage, free_storage

# Download and Upload Command
async def download_and_upload(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="Please provide a URL to download the file.")
        return

    file_url = context.args[0]
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = asyncio.Event()

    # Store task details in the database
    conn = get_db_connection()
    conn.execute("INSERT INTO tasks (task_id, chat_id, status, file_url, progress, downloaded_size) VALUES (?, ?, ?, ?, ?, ?)",
                 (task_id, chat_id, 'downloading', file_url, 0, 0))
    conn.commit()
    conn.close()

    cancel_button = InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{task_id}")
    keyboard = InlineKeyboardMarkup([[cancel_button]])
    progress_message = await context.bot.send_message(
        chat_id=chat_id,
        text=f"🚀 <b>Started downloading {file_url.split('/')[-1]}...</b>",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

    # Start downloading the file
    asyncio.create_task(download_file(task_id, file_url, chat_id, progress_message, context, active_tasks[task_id]))

# Download File with Timeout and Cancel Handling
async def download_file(task_id, file_url, chat_id, progress_message, context, cancel_event):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url, timeout=43200) as response:  # 12 hours timeout for download
                if response.status == 200:
                    file_name = "video.mp4"
                    total_size = int(response.headers.get('Content-Length', 0))
                    downloaded_size = 0

                    start_time = time.time()
                    last_update = time.time()

                    with open(file_name, 'wb') as file:
                        while True:
                            chunk = await response.content.read(64 * 1024)
                            if cancel_event.is_set():
                                active_tasks.pop(task_id, None)
                                await context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=progress_message.message_id,
                                    text="❌ Task canceled by the user.",
                                    parse_mode='HTML'
                                )
                                return

                            if not chunk:
                                break

                            file.write(chunk)
                            downloaded_size += len(chunk)
                            elapsed_time = time.time() - start_time
                            speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
                            progress = downloaded_size / total_size * 100
                            completed_blocks = int(progress // 10)
                            progress_bar = '⬛️' * completed_blocks + '⬜️' * (10 - completed_blocks)

                            if time.time() - last_update > 1:
                                cpu_usage, ram_usage, free_storage = get_system_stats()
                                progress_text = (
                                    f"┌  🚀 [Download Progress: {progress:.2f}%]\n\n"
                                    f"   {progress_bar} {progress:.2f}%\n"
                                    f"├  🔄 ᴘʀᴏᴄᴇssᴇᴅ : {downloaded_size / (1024 * 1024):.2f} MB\n"
                                    f"├  ⏬ ꜱᴛᴀᴛᴜs : Downloading\n"
                                    f"├  ⚡️ sᴘᴇᴇᴅ : {speed / 1024:.2f} KB/s\n"
                                    f"├  🖥 ᴄᴘᴜ : {cpu_usage:.1f}%\n"
                                    f"├  🎮 ʀᴀᴍ : {ram_usage:.1f}%\n"
                                    f"├  💿 ғʀᴇᴇ : {free_storage:.2f} GB\n"
                                    f"└   ❎ <b>Click below to cancel the task:</b>"
                                )

                                cancel_button = InlineKeyboardButton(f"❌ Cancel Task {task_id[:8]}", callback_data=f"cancel_{task_id}")
                                keyboard = InlineKeyboardMarkup([[cancel_button]])

                                await context.bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=progress_message.message_id,
                                    text=progress_text,
                                    reply_markup=keyboard,
                                    parse_mode='HTML'
                                )
                                last_update = time.time()

                    # After download, upload the file
                    upload_command = f'curl -F "file=@{file_name}" {upload_url}'
                    result = subprocess.run(upload_command, shell=True, text=True, capture_output=True)

                    if result.returncode == 0:
                        uploaded_url = result.stdout.strip()
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=progress_message.message_id,
                            text=f"✅ File uploaded successfully.\nURL: {uploaded_url}",
                            parse_mode='HTML'
                        )
                    else:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=progress_message.message_id,
                            text="❌ Upload failed.",
                            parse_mode='HTML'
                        )

                    active_tasks.pop(task_id, None)

                else:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=progress_message.message_id,
                        text="❌ Failed to download the file.",
                        parse_mode='HTML'
                    )
                    active_tasks.pop(task_id, None)

    except asyncio.TimeoutError:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message.message_id,
            text="❌ Download timed out.",
            parse_mode='HTML'
        )
        active_tasks.pop(task_id, None)

    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=progress_message.message_id,
            text=f"❌ Error occurred: {str(e)}",
            parse_mode='HTML'
        )
        active_tasks.pop(task_id, None)

# Handle Cancel Button Press
async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    callback_data = query.data

    if callback_data.startswith("cancel_"):
        task_id = callback_data.split("_")[1]

        if task_id in active_tasks:
            active_tasks[task_id].set()
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ Task already finished or doesn't exist.",
                parse_mode='HTML'
            )

# Start Command - Bot responds with "I am alive!" when it starts
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hello! Use /download <url> to start downloading and uploading a file.')

# Main function to set up the bot
async def main():
    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("download", download_and_upload))
    application.add_handler(CallbackQueryHandler(button_callback))

    create_db_table()

    await application.run_polling()

# Run the bot in an already running event loop (for environments like Jupyter)
await main()


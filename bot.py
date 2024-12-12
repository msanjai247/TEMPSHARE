import time
import subprocess
import uuid
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram.error import RetryAfter
from tqdm import tqdm
import nest_asyncio
import asyncio

# Apply nest_asyncio to allow nested event loops in environments like Jupyter
nest_asyncio.apply()

# Your bot's API token here
API_TOKEN = "6816699414:AAGkNhn0oaK1NK9GuKod7gHesX8zV12M760"

# Set the default upload URL
upload_url = "https://temp.sh/upload"

# Store active tasks
active_tasks = {}

# Download and Upload Command
async def download_and_upload(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="Please provide a URL to download the file.")
        return

    file_url = context.args[0]

    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = "downloading"  # Mark task as active

    # Send an initial message with a cancel button
    cancel_button = InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{task_id}")
    keyboard = InlineKeyboardMarkup([[cancel_button]])
    progress_message = await context.bot.send_message(
        chat_id=chat_id,
        text=f"🚀 <b>Started downloading {file_url.split('/')[-1]}...</b>",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

    # Start the download task
    asyncio.create_task(download_file(task_id, file_url, chat_id, progress_message, keyboard, context))


async def download_file(task_id, file_url, chat_id, progress_message, keyboard, context):
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as response:
            if response.status == 200:
                # Set a default filename
                file_name = "video.mp4"
                total_size = int(response.headers.get('Content-Length', 0))

                with open(file_name, 'wb') as file:
                    last_update = time.time()
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=file_name) as pbar:
                        async for chunk in response.content.iter_chunked(8192):
                            if chunk:
                                file.write(chunk)
                                pbar.update(len(chunk))  # Update the progress bar

                                if time.time() - last_update > 2:
                                    progress_text = f"Download Progress: {pbar.n / total_size * 100:.2f}%\n\n{'⬛' * int(pbar.n / total_size * 10)}{'⬜' * (10 - int(pbar.n / total_size * 10))}"
                                    try:
                                        await context.bot.edit_message_text(
                                            chat_id=chat_id,
                                            message_id=progress_message.message_id,
                                            text=f"{progress_text}\nCurrent task: Downloading {file_name}",
                                            reply_markup=keyboard,
                                            parse_mode='HTML'
                                        )
                                        last_update = time.time()
                                    except RetryAfter as e:
                                        await asyncio.sleep(e.retry_after)
                                        continue

                # After downloading, upload the file
                upload_command = f'curl -F "file=@{file_name}" {upload_url} -#'
                result = subprocess.run(upload_command, shell=True, text=True, capture_output=True)

                if result.returncode == 0:
                    uploaded_url = result.stdout.strip()
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=progress_message.message_id,
                        text=f"✅ File uploaded successfully.\nFile available at: {uploaded_url}",
                        parse_mode='HTML'
                    )
                else:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=progress_message.message_id,
                        text="❌ Upload failed.",
                        parse_mode='HTML'
                    )

                # Mark task as finished
                active_tasks.pop(task_id, None)

            else:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=progress_message.message_id,
                    text="❌ Failed to download the file.",
                    parse_mode='HTML'
                )

                # Mark task as finished
                active_tasks.pop(task_id, None)

# Handle cancel button press
async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    callback_data = query.data

    if callback_data.startswith("cancel_"):
        task_id = callback_data.split("_")[1]

        # Cancel the task if it's active
        if task_id in active_tasks:
            active_tasks.pop(task_id, None)  # Remove the task from active tasks
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ Download canceled.",
                parse_mode='HTML'
            )
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="❌ Task already finished or doesn't exist.",
                parse_mode='HTML'
            )

# Start Command - Bot responds with "I am alive!" when it starts
async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id=chat_id, text="I am alive!")

# Main function to set up the bot
async def main():
    application = Application.builder().token(API_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("download", download_and_upload))
    application.add_handler(CallbackQueryHandler(button_callback))

    await application.run_polling()

# Run the bot in an already running event loop (for environments like Jupyter)
    await main()

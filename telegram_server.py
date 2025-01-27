import os
import json
import asyncio
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from tools.proton import get_emails_pure, send_email_pure, delete_email_pure
from tools.todoist import create_new_task, get_filtered_tasks
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

client = OpenAI(api_key=OPENAI_API_KEY)

# Store thread IDs for each user
user_threads = {}

# Command to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    thread = client.beta.threads.create()
    user_threads[user_id] = thread.id
    await update.message.reply_text("Hello! I'm your personal assistant. Ask me anything!")

# Command to reset the thread
async def reset_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_threads:
        del user_threads[user_id]
    await update.message.reply_text("Thread reset. Start a new conversation!")

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_query = update.message.text

    if user_id not in user_threads:
        thread = client.beta.threads.create()
        user_threads[user_id] = thread.id

    thread_id = user_threads[user_id]

    # Add user message to the thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_query
    )

    # Create a run to process the message
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )

    # Wait for the run to complete
    run_status = ""
    while run_status not in ["completed", "requires_action"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        run_status = run.status
        await asyncio.sleep(0.5)

    # Handle tool calls if required
    if run_status == "requires_action":
        tool_outputs = []
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
                if function_name == "get_emails":
                    output = get_emails_pure(**args)
                elif function_name == "send_email":
                    output = send_email_pure(**args)
                elif function_name == "delete_email":
                    output = delete_email_pure(**args)
                elif function_name == "create_new_task":
                    output = create_new_task(**args)
                elif function_name == "get_tasks":
                    output = get_filtered_tasks(**args)
                else:
                    output = f"Function {function_name} not implemented."

                print(f"Executing {function_name} with args {args}")
            except Exception as e:
                output = f"Error: {str(e)}"

            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(output)
            })

        # Submit tool outputs
        client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )

        # Wait for completion after submitting tool outputs
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run.status == "completed":
                break
            await asyncio.sleep(0.5)

    # Retrieve the assistant's response
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    latest_message = messages.data[0]
    if latest_message.role == "assistant":
        full_content = ""
        for content_block in latest_message.content:
            if content_block.type == 'text':
                full_content += content_block.text.value
        await update.message.reply_text(full_content)

# Main function to run the bot
def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset_thread))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
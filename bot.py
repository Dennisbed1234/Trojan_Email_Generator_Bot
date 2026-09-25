import asyncio
import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import BOT_TOKEN, MAX_EMAILS
from database import init_db, ensure_user
from generator import generate_file


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.effective_user or not update.message:
        return

    ensure_user(update.effective_user.id)

    await update.message.reply_text(
        "🤖 Email Generator\n\n"
        "Generate randomized, deliverable email-shaped "
        "addresses for testing.\n\n"
        "Commands:\n"
        "/generate 1000\n"
        "/help\n\n"
        f"Maximum per run: {MAX_EMAILS:,}"
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    await update.message.reply_text(
        "📚 Commands\n\n"
        "/generate NUMBER\n\n"
        "Example:\n"
        "/generate 10000\n\n"
        "The bot generates unique addresses "
        "using reserved .valid domains.\n\n"
        "Available formats:\n"
        "• TXT\n"
        "• CSV\n"
        "• JSON"
    )


async def generate_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.effective_user or not update.message:
        return

    ensure_user(update.effective_user.id)

    if not context.args:
        await update.message.reply_text(
            "Usage:\n\n"
            "/generate 1000"
        )
        return

    try:
        count = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid whole number."
        )
        return

    if count <= 0:
        await update.message.reply_text(
            "❌ Number must be greater than zero."
        )
        return

    if count > MAX_EMAILS:
        await update.message.reply_text(
            f"❌ Maximum is {MAX_EMAILS:,} per run."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "TXT",
                callback_data=f"generate:txt:{count}",
            ),
            InlineKeyboardButton(
                "CSV",
                callback_data=f"generate:csv:{count}",
            ),
            InlineKeyboardButton(
                "JSON",
                callback_data=f"generate:json:{count}",
            ),
        ]
    ]

    await update.message.reply_text(
        f"Generate {count:,} email addresses as:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def generate_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query or not query.message:
        return

    await query.answer()

    parts = query.data.split(":")

    if len(parts) != 3:
        await query.edit_message_text(
            "❌ Invalid request."
        )
        return

    _, output_format, count_string = parts

    if output_format not in {"txt", "csv", "json"}:
        await query.edit_message_text(
            "❌ Invalid format."
        )
        return

    try:
        count = int(count_string)
    except ValueError:
        await query.edit_message_text(
            "❌ Invalid number."
        )
        return

    if count <= 0 or count > MAX_EMAILS:
        await query.edit_message_text(
            "❌ Invalid generation size."
        )
        return

    await query.edit_message_text(
        f"⏳ Generating {count:,} addresses...\n\n"
        f"Format: {output_format.upper()}"
    )

    await context.bot.send_chat_action(
        chat_id=query.message.chat_id,
        action=ChatAction.UPLOAD_DOCUMENT,
    )

    path = None

    try:
        path = await asyncio.to_thread(
            generate_file,
            count,
            output_format,
        )

        await query.message.reply_text(
            f"✅ Generated {count:,} unique synthetic addresses."
        )

        with open(path, "rb") as file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=file,
                caption=(
                    f"📄 {output_format.upper()} dataset\n"
                    f"Records: {count:,}"
                ),
            )

    except Exception as error:
        print(f"Generation error: {error}")

        await query.message.reply_text(
            "❌ Generation failed.\n\n"
            f"{error}"
        )

    finally:
        if path and os.path.exists(path):
            os.remove(path)


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    print("Telegram error:", context.error)


def main():
    init_db()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("generate", generate_command)
    )

    application.add_handler(
        CallbackQueryHandler(
            generate_callback,
            pattern=r"^generate:(txt|csv|json):\d+$",
        )
    )

    application.add_error_handler(error_handler)

    print(
        "🤖 Synthetic Email Generator Bot is running..."
    )

    application.run_polling()


if __name__ == "__main__":
    main()
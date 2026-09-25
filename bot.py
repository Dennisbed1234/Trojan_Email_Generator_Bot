import asyncio
import os
import re

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

from config import (
    BOT_TOKEN,
    MAX_EMAILS,
    DEFAULT_DOMAIN,
)

from database import (
    init_db,
    ensure_user,
    get_domain,
    set_domain,
)

from generator import generate_file


def valid_domain(domain: str) -> bool:
    """
    Only permit domains suitable for data.

    This bot intentionally restricts generation to .test,
    which is reserved for documentation/testing.
    """

    domain = domain.lower().strip()

    pattern = r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.test$"

    return bool(re.match(pattern, domain))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    ensure_user(user_id)

    text = (
        "🤖 Email Generator\n\n"
        "This bot creates"
        "email addresses.\n\n"
        "Commands:\n"
        "/generate 1000 - Generate emails\n"
        "/domain - Show current domain\n"
        "/setdomain example.test - Change test domain\n"
        "/help - Show help\n\n"
        "Maximum per generation: "
        f"{MAX_EMAILS:,}"
    )

    await update.message.reply_text(text)


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    text = (
        "📚 Commands\n\n"
        "/generate NUMBER\n"
        "Example:\n"
        "/generate 10000\n\n"
        "/domain\n"
        "Show the current domain.\n\n"
        "/setdomain example.test\n"
        "Change the domain.\n\n"
        "Supported output formats are TXT, CSV and JSON."
    )

    await update.message.reply_text(text)


async def domain_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    ensure_user(user_id)

    domain = get_domain(user_id)

    await update.message.reply_text(
        f"Current domain:\n\n`{domain}`",
        parse_mode="Markdown",
    )


async def set_domain_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    ensure_user(user_id)

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/setdomain example.test"
        )
        return

    domain = context.args[0].lower().strip()

    if not valid_domain(domain):
        await update.message.reply_text(
            "❌ Invalid domain.\n\n"
            "For safety, this bot only supports domains "
            "ending in `.test`.\n\n"
            "Example:\n"
            "/setdomain example.test"
        )
        return

    set_domain(user_id, domain)

    await update.message.reply_text(
        f"✅ domain changed to:\n\n{domain}"
    )


async def generate_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    ensure_user(user_id)

    if not context.args:
        await update.message.reply_text(
            "Usage:\n\n/generate 10000"
        )
        return

    try:
        count = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a whole number.\n\n"
            "Example:\n/generate 10000"
        )
        return

    if count <= 0:
        await update.message.reply_text(
            "❌ Number must be greater than zero."
        )
        return

    if count > MAX_EMAILS:
        await update.message.reply_text(
            f"❌ Maximum is {MAX_EMAILS:,} emails per job."
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
        f"Generate {count:,} emails as:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def generate_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    parts = query.data.split(":")

    if len(parts) != 3:
        await query.edit_message_text(
            "❌ Invalid generation request."
        )
        return

    _, output_format, count_string = parts

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

    user_id = query.from_user.id

    ensure_user(user_id)

    domain = get_domain(user_id)

    await query.edit_message_text(
        f"⏳ Generating {count:,} emails...\n\n"
        f"Domain: {domain}\n"
        f"Format: {output_format.upper()}"
    )

    await context.bot.send_chat_action(
        chat_id=query.message.chat_id,
        action=ChatAction.UPLOAD_DOCUMENT,
    )

    try:
        path = await asyncio.to_thread(
            generate_file,
            count,
            output_format,
            domain,
        )

        caption = (
            "✅ Generation complete\n\n"
            f"Emails: {count:,}\n"
            f"Domain: {domain}\n"
            f"Format: {output_format.upper()}"
        )

        with open(path, "rb") as file:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=file,
                caption=caption,
            )

        os.remove(path)

    except Exception as error:
        await query.message.reply_text(
            "❌ Generation failed.\n\n"
            f"Error: {error}"
        )


async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    print(
        "Telegram error:",
        context.error,
    )


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
        CommandHandler("domain", domain_command)
    )

    application.add_handler(
        CommandHandler("setdomain", set_domain_command)
    )

    application.add_handler(
        CallbackQueryHandler(
            generate_callback,
            pattern=r"^generate:(txt|csv|json):\d+$",
        )
    )

    application.add_error_handler(error_handler)

    print("🤖 Email Generator Bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()
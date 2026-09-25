import json
import os
import random
import string
import tempfile
import urllib.error
import urllib.request
import uuid

from http.server import BaseHTTPRequestHandler

from generator import generate_file


BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

MAX_EMAILS = 1_000_000


def telegram_api(method, data=None, files=None):
    """
    Call the Telegram Bot API.

    JSON requests are used for normal API calls.
    Multipart/form-data is used when uploading a generated file.
    """

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured.")

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/{method}"
    )

    if files:
        boundary = (
            "----VercelTelegram"
            + uuid.uuid4().hex
        )

        body = build_multipart_body(
            data or {},
            files,
            boundary,
        )

        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": (
                    f"multipart/form-data; "
                    f"boundary={boundary}"
                )
            },
            method="POST",
        )

    else:
        body = json.dumps(
            data or {}
        ).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

    try:
        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:
            raw = response.read()

        result = json.loads(
            raw.decode("utf-8")
        )

        if not result.get("ok"):
            raise RuntimeError(
                result.get(
                    "description",
                    "Telegram API request failed.",
                )
            )

        return result

    except urllib.error.HTTPError as error:
        details = error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Telegram HTTP {error.code}: {details}"
        ) from error


def build_multipart_body(
    fields,
    files,
    boundary,
):
    """
    Build multipart/form-data body manually.
    """

    chunks = []

    boundary_bytes = (
        boundary.encode("utf-8")
    )

    for name, value in fields.items():

        chunks.append(
            b"--"
            + boundary_bytes
            + b"\r\n"
        )

        chunks.append(
            (
                f'Content-Disposition: '
                f'form-data; name="{name}"'
                f'\r\n\r\n'
            ).encode("utf-8")
        )

        if isinstance(value, bool):
            value = "true" if value else "false"

        elif isinstance(value, (dict, list)):
            value = json.dumps(value)

        else:
            value = str(value)

        chunks.append(
            value.encode("utf-8")
        )

        chunks.append(b"\r\n")

    for field_name, file_info in files.items():

        filename = file_info["filename"]
        content = file_info["content"]
        content_type = file_info.get(
            "content_type",
            "application/octet-stream",
        )

        chunks.append(
            b"--"
            + boundary_bytes
            + b"\r\n"
        )

        chunks.append(
            (
                f'Content-Disposition: '
                f'form-data; '
                f'name="{field_name}"; '
                f'filename="{filename}"'
                f'\r\n'
            ).encode("utf-8")
        )

        chunks.append(
            (
                f"Content-Type: "
                f"{content_type}\r\n\r\n"
            ).encode("utf-8")
        )

        chunks.append(content)
        chunks.append(b"\r\n")

    chunks.append(
        b"--"
        + boundary_bytes
        + b"--\r\n"
    )

    return b"".join(chunks)


def send_message(
    chat_id,
    text,
    reply_markup=None,
):
    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup is not None:
        data["reply_markup"] = reply_markup

    return telegram_api(
        "sendMessage",
        data,
    )


def answer_callback(
    callback_query_id,
):
    return telegram_api(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_query_id
        },
    )


def send_generated_file(
    chat_id,
    path,
    output_format,
    count,
):
    filename = (
        f"valid_emails_"
        f"{count}_{output_format}"
        f".{output_format}"
    )

    if output_format == "txt":
        content_type = "text/plain"

    elif output_format == "csv":
        content_type = "text/csv"

    else:
        content_type = "application/json"

    with open(path, "rb") as file:
        content = file.read()

    telegram_api(
        "sendDocument",
        {
            "chat_id": chat_id,
            "caption": (
                f"📄 {output_format.upper()} dataset\n"
                f"Records: {count:,}"
            ),
        },
        files={
            "document": {
                "filename": filename,
                "content": content,
                "content_type": content_type,
            }
        },
    )


def handle_start(chat_id):
    send_message(
        chat_id,
        "🤖 Email Generator\n\n"
        "Generate randomized, deliverable "
        "email-shaped addresses.\n\n"
        "Commands:\n"
        "/generate 100\n"
        "/help\n\n"
        f"Maximum per run: {MAX_EMAILS:,}",
    )


def handle_help(chat_id):
    send_message(
        chat_id,
        "📚 Commands\n\n"
        "/generate NUMBER\n\n"
        "Example:\n"
        "/generate 1000\n\n"
        "The generator creates unique email "
        "addresses using reserved .gmail domains.\n\n"
        "Available formats:\n"
        "• TXT\n"
        "• CSV\n"
        "• JSON",
    )


def handle_generate(
    chat_id,
    text,
):
    parts = text.split()

    if len(parts) != 2:
        send_message(
            chat_id,
            "Usage:\n\n"
            "/generate 1000",
        )
        return

    try:
        count = int(parts[1])
    except ValueError:
        send_message(
            chat_id,
            "❌ Please enter a valid whole number.",
        )
        return

    if count <= 0:
        send_message(
            chat_id,
            "❌ Number must be greater than zero.",
        )
        return

    if count > MAX_EMAILS:
        send_message(
            chat_id,
            f"❌ Maximum is {MAX_EMAILS:,} "
            "per generation.",
        )
        return

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "TXT",
                    "callback_data": (
                        f"generate:txt:{count}"
                    ),
                },
                {
                    "text": "CSV",
                    "callback_data": (
                        f"generate:csv:{count}"
                    ),
                },
                {
                    "text": "JSON",
                    "callback_data": (
                        f"generate:json:{count}"
                    ),
                },
            ]
        ]
    }

    send_message(
        chat_id,
        f"Generate {count:,} "
        "email addresses as:",
        keyboard,
    )


def handle_callback(update):
    callback = update.get(
        "callback_query"
    )

    if not callback:
        return

    callback_id = callback.get("id")

    answer_callback(callback_id)

    data = callback.get("data", "")

    message = callback.get("message")

    if not message:
        return

    chat_id = message["chat"]["id"]

    parts = data.split(":")

    if len(parts) != 3:
        send_message(
            chat_id,
            "❌ Invalid request.",
        )
        return

    action, output_format, count_text = parts

    if action != "generate":
        send_message(
            chat_id,
            "❌ Invalid request.",
        )
        return

    if output_format not in {
        "txt",
        "csv",
        "json",
    }:
        send_message(
            chat_id,
            "❌ Invalid format.",
        )
        return

    try:
        count = int(count_text)
    except ValueError:
        send_message(
            chat_id,
            "❌ Invalid number.",
        )
        return

    if count <= 0 or count > MAX_EMAILS:
        send_message(
            chat_id,
            "❌ Invalid generation size.",
        )
        return

    send_message(
        chat_id,
        f"⏳ Generating {count:,} "
        f"{output_format.upper()} addresses...",
    )

    path = None

    try:
        path = generate_file(
            count,
            output_format,
        )

        send_generated_file(
            chat_id,
            path,
            output_format,
            count,
        )

        send_message(
            chat_id,
            f"✅ Finished generating "
            f"{count:,} addresses.",
        )

    except Exception as error:

        print(
            "Generation error:",
            repr(error),
        )

        send_message(
            chat_id,
            "❌ Generation failed.\n\n"
            f"{error}",
        )

    finally:

        if path and os.path.exists(path):
            os.remove(path)


def handle_update(update):
    """
    Process one Telegram update.
    """

    if "callback_query" in update:
        handle_callback(update)
        return

    message = update.get("message")

    if not message:
        return

    chat = message.get("chat")

    if not chat:
        return

    chat_id = chat["id"]

    text = message.get(
        "text",
        "",
    ).strip()

    if text == "/start":
        handle_start(chat_id)
        return

    if text == "/help":
        handle_help(chat_id)
        return

    if text.startswith("/generate"):
        handle_generate(
            chat_id,
            text,
        )
        return


class handler(BaseHTTPRequestHandler):

    def do_POST(self):

        if WEBHOOK_SECRET:

            received_secret = (
                self.headers.get(
                    "X-Telegram-Bot-Api-Secret-Token"
                )
            )

            if received_secret != WEBHOOK_SECRET:

                self.send_response(403)

                self.send_header(
                    "Content-Type",
                    "application/json",
                )

                self.end_headers()

                self.wfile.write(
                    b'{"ok":false}'
                )

                return

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
            )

            body = self.rfile.read(
                content_length
            )

            update = json.loads(
                body.decode("utf-8")
            )

            handle_update(update)

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json",
            )

            self.end_headers()

            self.wfile.write(
                b'{"ok":true}'
            )

        except Exception as error:

            print(
                "Webhook error:",
                repr(error),
            )

            self.send_response(500)

            self.send_header(
                "Content-Type",
                "application/json",
            )

            self.end_headers()

            self.wfile.write(
                b'{"ok":false}'
            )

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "application/json",
        )

        self.end_headers()

        self.wfile.write(
            b'{"status":"Telegram bot webhook is online"}'
        )
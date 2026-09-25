import json
import os
import tempfile
import urllib.error
import urllib.request
import uuid

from http.server import BaseHTTPRequestHandler

from generator import generate_file


BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

MAX_EMAILS = 1_000_000_000


# --------------------------------------------------
# Telegram API
# --------------------------------------------------

def telegram_api(method, data=None, files=None, timeout=30):
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not configured in Vercel.")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    if files:
        boundary = "----VercelTelegram" + uuid.uuid4().hex

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
            timeout=timeout,
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

    except urllib.error.URLError as error:

        raise RuntimeError(
            f"Telegram network error: {error}"
        ) from error


# --------------------------------------------------
# Multipart upload
# --------------------------------------------------

def build_multipart_body(
    fields,
    files,
    boundary,
):
    chunks = []

    boundary_bytes = boundary.encode(
        "utf-8"
    )

    for name, value in fields.items():

        chunks.append(
            b"--" +
            boundary_bytes +
            b"\r\n"
        )

        chunks.append(
            (
                f'Content-Disposition: '
                f'form-data; '
                f'name="{name}"'
                f'\r\n\r\n'
            ).encode("utf-8")
        )

        if isinstance(value, bool):
            value = (
                "true"
                if value
                else "false"
            )

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
            b"--" +
            boundary_bytes +
            b"\r\n"
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
                f"{content_type}"
                f"\r\n\r\n"
            ).encode("utf-8")
        )

        chunks.append(content)

        chunks.append(b"\r\n")

    chunks.append(
        b"--" +
        boundary_bytes +
        b"--\r\n"
    )

    return b"".join(chunks)


# --------------------------------------------------
# Telegram helpers
# --------------------------------------------------

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
        timeout=20,
    )


def answer_callback(
    callback_query_id,
    text=None,
):
    data = {
        "callback_query_id":
            callback_query_id
    }

    if text:
        data["text"] = text

    return telegram_api(
        "answerCallbackQuery",
        data,
        timeout=10,
    )


# --------------------------------------------------
# File sending
# --------------------------------------------------

def send_generated_file(
    chat_id,
    path,
    output_format,
    count,
):

    filename = (
        f"real_emails_"
        f"{count}_{output_format}."
        f"{output_format}"
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
        timeout=120,
    )


# --------------------------------------------------
# Commands
# --------------------------------------------------

def handle_start(chat_id):

    send_message(
        chat_id,

        "🤖 Email Generator\n\n"
        "Generate randomized, deliverable "
        "email-shaped addresses.\n\n"

        "Commands:\n"
        "/generate 100\n"
        "/help\n\n"

        f"Maximum per run: "
        f"{MAX_EMAILS:,}",
    )


def handle_help(chat_id):

    send_message(
        chat_id,

        "📚 Commands\n\n"

        "/generate NUMBER\n\n"

        "Example:\n"
        "/generate 1000\n\n"

        "The generator creates unique email "
        "addresses using reserved .valid domains.\n\n"

        "Formats:\n"
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
            f"❌ Maximum is "
            f"{MAX_EMAILS:,} per generation.",
        )

        return

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "TXT",
                    "callback_data":
                        f"generate:txt:{count}",
                },
                {
                    "text": "CSV",
                    "callback_data":
                        f"generate:csv:{count}",
                },
                {
                    "text": "JSON",
                    "callback_data":
                        f"generate:json:{count}",
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


# --------------------------------------------------
# Callback processing
# --------------------------------------------------

def handle_callback(update):

    callback = update.get(
        "callback_query"
    )

    if not callback:
        return

    callback_id = callback.get("id")

    message = callback.get("message")

    if not message:
        return

    chat = message.get("chat")

    if not chat:
        return

    chat_id = chat["id"]

    data = callback.get(
        "data",
        "",
    )

    # ----------------------------------------------
    # IMPORTANT:
    # Answer the callback BEFORE doing any work.
    # This removes Telegram's loading spinner.
    # ----------------------------------------------

    try:

        answer_callback(
            callback_id,
            "Starting generation...",
        )

    except Exception as error:

        print(
            "Callback answer error:",
            repr(error),
        )

    # ----------------------------------------------

    parts = data.split(":")

    if len(parts) != 3:

        send_message(
            chat_id,
            "❌ Invalid request.",
        )

        return

    action = parts[0]
    output_format = parts[1]
    count_text = parts[2]

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

    # ----------------------------------------------
    # Tell user generation has started
    # ----------------------------------------------

    try:

        send_message(
            chat_id,
            (
                f"⏳ Generating "
                f"{count:,} "
                f"{output_format.upper()} "
                f"addresses..."
            ),
        )

    except Exception as error:

        print(
            "Generation status message error:",
            repr(error),
        )

        return

    path = None

    try:

        print(
            f"Starting generation: "
            f"{count} {output_format}"
        )

        # ------------------------------------------
        # Generate file
        # ------------------------------------------

        path = generate_file(
            count,
            output_format,
        )

        print(
            f"File generated: {path}"
        )

        # ------------------------------------------
        # Upload to Telegram
        # ------------------------------------------

        send_generated_file(
            chat_id,
            path,
            output_format,
            count,
        )

        print(
            "File successfully sent."
        )

        send_message(
            chat_id,
            (
                f"✅ Finished generating "
                f"{count:,} addresses."
            ),
        )

    except Exception as error:

        print(
            "Generation error:",
            repr(error),
        )

        try:

            send_message(
                chat_id,
                (
                    "❌ Generation failed.\n\n"
                    f"Error: {error}"
                ),
            )

        except Exception as send_error:

            print(
                "Failed to send error message:",
                repr(send_error),
            )

    finally:

        if path and os.path.exists(path):

            try:

                os.remove(path)

            except Exception as error:

                print(
                    "File cleanup error:",
                    repr(error),
                )


# --------------------------------------------------
# Update router
# --------------------------------------------------

def handle_update(update):

    if "callback_query" in update:

        handle_callback(update)

        return

    message = update.get(
        "message"
    )

    if not message:
        return

    chat = message.get(
        "chat"
    )

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

    if text.startswith(
        "/generate"
    ):

        handle_generate(
            chat_id,
            text,
        )

        return


# --------------------------------------------------
# Vercel HTTP handler
# --------------------------------------------------

class handler(
    BaseHTTPRequestHandler
):

    def do_POST(self):

        # ------------------------------------------
        # Verify Telegram webhook secret
        # ------------------------------------------

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

            print(
                "Telegram update received."
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

            try:

                self.send_response(500)

                self.send_header(
                    "Content-Type",
                    "application/json",
                )

                self.end_headers()

                self.wfile.write(
                    b'{"ok":false}'
                )

            except Exception:
                pass

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
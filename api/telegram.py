import json
import os
import tempfile

from http.server import BaseHTTPRequestHandler

from generator import generate_file


BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")


def telegram_api(method, data):
    import urllib.request

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    payload = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def send_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    return telegram_api("sendMessage", data)


def handle_update(update):
    message = update.get("message")

    if message:
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if text == "/start":
            send_message(
                chat_id,
                "🤖 Email Generator\n\n"
                "Generate randomized, deliverable "
                "email-shaped addresses.\n\n"
                "Commands:\n"
                "/generate 100\n"
                "/help",
            )
            return

        if text == "/help":
            send_message(
                chat_id,
                "📚 Commands\n\n"
                "/generate NUMBER\n\n"
                "Example:\n"
                "/generate 1000\n\n"
                "Available formats:\n"
                "• TXT\n"
                "• CSV\n"
                "• JSON",
            )
            return

        if text.startswith("/generate"):
            parts = text.split()

            if len(parts) != 2:
                send_message(
                    chat_id,
                    "Usage:\n\n/generate 1000",
                )
                return

            try:
                count = int(parts[1])
            except ValueError:
                send_message(
                    chat_id,
                    "❌ Please enter a valid number.",
                )
                return

            if count <= 0 or count > 1_000_000:
                send_message(
                    chat_id,
                    "❌ Choose a number between 1 and 1,000,000.",
                )
                return

            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "TXT",
                            "callback_data": f"generate:txt:{count}",
                        },
                        {
                            "text": "CSV",
                            "callback_data": f"generate:csv:{count}",
                        },
                        {
                            "text": "JSON",
                            "callback_data": f"generate:json:{count}",
                        },
                    ]
                ]
            }

            send_message(
                chat_id,
                f"Generate {count:,} email addresses as:",
                keyboard,
            )

            return

    callback = update.get("callback_query")

    if callback:
        callback_id = callback["id"]
        data = callback.get("data", "")
        message = callback.get("message")

        if not message:
            return

        chat_id = message["chat"]["id"]

        telegram_api(
            "answerCallbackQuery",
            {
                "callback_query_id": callback_id,
            },
        )

        parts = data.split(":")

        if len(parts) != 3:
            send_message(
                chat_id,
                "❌ Invalid request.",
            )
            return

        _, output_format, count_text = parts

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

        if count <= 0 or count > 1_000_000:
            send_message(
                chat_id,
                "❌ Invalid generation size.",
            )
            return

        send_message(
            chat_id,
            f"⏳ Generating {count:,} addresses...",
        )

        path = None

        try:
            path = generate_file(
                count,
                output_format,
            )

            telegram_api(
                "sendDocument",
                {
                    "chat_id": chat_id,
                    "document": open(path, "rb"),
                },
            )

        except Exception as error:
            send_message(
                chat_id,
                f"❌ Generation failed:\n{error}",
            )

        finally:
            if path and os.path.exists(path):
                os.remove(path)


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
            )

            body = self.rfile.read(length)

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
            print("Webhook error:", error)

            self.send_response(500)
            self.send_header(
                "Content-Type",
                "application/json",
            )
            self.end_headers()

            self.wfile.write(
                b'{"ok":false}'
            )
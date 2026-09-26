import json
import os
import urllib.error
import urllib.request
import uuid

from http.server import BaseHTTPRequestHandler

from generator import generate_file

from database import (
    init_database,
    create_order,
    get_order,
    get_latest_pending_order,
    get_latest_payment_order,
    attach_tx_hash,
    approve_order,
    reject_order,
    claim_generation,
    mark_generation_complete,
    mark_generation_failed,
)

from payment import (
    PRICE_TIERS,
    PAYMENT_ADDRESSES,
    CRYPTO_LABELS,
    create_order_id,
    get_price,
    get_crypto_label,
    build_payment_message,
    validate_tx_hash,
    make_callback_token,
    verify_callback_token,
    is_admin,
)


BOT_TOKEN = os.environ.get("BOT_TOKEN")

WEBHOOK_SECRET = os.environ.get(
    "WEBHOOK_SECRET"
)

MAX_EMAILS = 1_000_000_000


# --------------------------------------------------
# ADMINS
# --------------------------------------------------

def get_admin_ids():
    return {
        int(value.strip())
        for value in os.environ.get(
            "ADMIN_USER_IDS",
            ""
        ).split(",")
        if value.strip().isdigit()
    }


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

try:
    init_database()
except Exception as error:
    print(
        "Database initialization error:",
        repr(error),
    )


# --------------------------------------------------
# Telegram API
# --------------------------------------------------

def telegram_api(
    method,
    data=None,
    files=None,
    timeout=30,
):
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is not configured in Vercel."
        )

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
                "Content-Type":
                    "multipart/form-data; "
                    f"boundary={boundary}"
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
                "Content-Type":
                    "application/json",
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
            f"Telegram HTTP {error.code}: "
            f"{details}"
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
                'Content-Disposition: '
                'form-data; '
                f'name="{name}"'
                '\r\n\r\n'
            ).encode("utf-8")
        )

        if isinstance(value, bool):

            value = (
                "true"
                if value
                else "false"
            )

        elif isinstance(
            value,
            (dict, list),
        ):

            value = json.dumps(value)

        else:

            value = str(value)

        chunks.append(
            value.encode("utf-8")
        )

        chunks.append(b"\r\n")

    for field_name, file_info in files.items():

        filename = file_info[
            "filename"
        ]

        content = file_info[
            "content"
        ]

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
                'Content-Disposition: '
                'form-data; '
                f'name="{field_name}"; '
                f'filename="{filename}"'
                '\r\n'
            ).encode("utf-8")
        )

        chunks.append(
            (
                "Content-Type: "
                f"{content_type}"
                "\r\n\r\n"
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
        "parse_mode": "HTML",
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
        f"{count}_"
        f"{output_format}."
        f"{output_format}"
    )

    if output_format == "txt":

        content_type = "text/plain"

    elif output_format == "csv":

        content_type = "text/csv"

    else:

        content_type = "application/json"

    with open(
        path,
        "rb",
    ) as file:

        content = file.read()

    telegram_api(
        "sendDocument",
        {
            "chat_id": chat_id,
            "caption": (
                f"📄 "
                f"{output_format.upper()} dataset\n"
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
# START
# --------------------------------------------------

def handle_start(
    chat_id,
    user_id,
):
    admin_text = ""

    if is_admin(user_id):

        admin_text = (
            "\n\n👑 Admin access enabled.\n"
            "You can generate without payment."
        )

    send_message(
        chat_id,

        "🤖 <b>Email Generator</b>\n\n"

        "Generate Fresh Email Leads.\n\n"

        "<b>How it works:</b>\n"
        "1. Select a package.\n"
        "2. Pay with crypto.\n"
        "3. Submit your TX hash.\n"
        "4. After approval, generate once.\n\n"

        "Commands:\n"
        "/buy\n"
        "/generate NUMBER\n"
        "/help"

        f"\n\nMaximum per run: "
        f"{MAX_EMAILS:,}"

        f"{admin_text}",
    )


# --------------------------------------------------
# HELP
# --------------------------------------------------

def handle_help(
    chat_id,
):
    send_message(
        chat_id,

        "📚 <b>Commands</b>\n\n"

        "/buy\n"
        "Purchase a generation package.\n\n"

        "/generate NUMBER\n"
        "Generate the selected number of addresses.\n\n"

        "Example:\n"
        "<code>/generate 5000</code>\n\n"

        "Available formats:\n"
        "• TXT\n"
        "• CSV\n"
        "• JSON\n\n"

        "For normal users, each approved payment "
        "allows exactly one generation.\n\n"

        "Admin accounts can generate for free.",
    )


# --------------------------------------------------
# BUY MENU
# --------------------------------------------------

def handle_buy(
    chat_id,
):
    rows = []

    for quantity, price in PRICE_TIERS.items():

        rows.append(
            [
                {
                    "text": (
                        f"{quantity:,} — "
                        f"${price:,.2f}"
                    ),
                    "callback_data":
                        f"buyq:{quantity}",
                }
            ]
        )

    rows.append(
        [
            {
                "text": "❌ Cancel",
                "callback_data":
                    "cancel",
            }
        ]
    )

    send_message(
        chat_id,

        "💳 <b>Choose a generation package</b>\n\n"
        "Each approved payment gives you "
        "one generation.",

        {
            "inline_keyboard": rows
        },
    )


# --------------------------------------------------
# CRYPTO MENU
# --------------------------------------------------

def handle_buy_quantity(
    chat_id,
    quantity,
):
    price = get_price(quantity)

    if price is None:

        send_message(
            chat_id,
            "❌ Invalid package.",
        )

        return

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text":
                        "USDT TRC-20",
                    "callback_data":
                        f"coin:{quantity}:USDT_TRC20",
                }
            ],
            [
                {
                    "text":
                        "USDT ERC-20",
                    "callback_data":
                        f"coin:{quantity}:USDT_ERC20",
                }
            ],
            [
                {
                    "text":
                        "USDT BEP-20",
                    "callback_data":
                        f"coin:{quantity}:USDT_BEP20",
                }
            ],
            [
                {
                    "text":
                        "Bitcoin",
                    "callback_data":
                        f"coin:{quantity}:BTC",
                }
            ],
            [
                {
                    "text":
                        "⬅️ Back",
                    "callback_data":
                        "buy",
                }
            ],
        ]
    }

    send_message(
        chat_id,

        f"📦 <b>{quantity:,} addresses</b>\n"
        f"💵 Price: <b>${price:,.2f}</b>\n\n"
        "Choose your payment network:",

        keyboard,
    )


# --------------------------------------------------
# CREATE PAYMENT ORDER
# --------------------------------------------------

def create_payment_order(
    chat_id,
    user_id,
    quantity,
    crypto,
):
    price = get_price(quantity)

    address = PAYMENT_ADDRESSES.get(
        crypto
    )

    if price is None:

        send_message(
            chat_id,
            "❌ Invalid package.",
        )

        return

    if not address:

        send_message(
            chat_id,
            "❌ Invalid payment method.",
        )

        return

    order_id = create_order_id()

    create_order(
        order_id=order_id,
        telegram_user_id=user_id,
        quantity=quantity,
        price_usd=price,
        crypto=crypto,
        payment_address=address,
    )

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text":
                        "💰 I've Paid",
                    "callback_data":
                        f"paid:{order_id}",
                }
            ],
            [
                {
                    "text":
                        "❌ Cancel",
                    "callback_data":
                        "cancel",
                }
            ],
        ]
    }

    send_message(
        chat_id,

        build_payment_message(
            order_id
        ),

        keyboard,
    )


# --------------------------------------------------
# I'VE PAID
# --------------------------------------------------

def handle_paid(
    chat_id,
    user_id,
    order_id,
):
    order = get_order(
        order_id
    )

    if not order:

        send_message(
            chat_id,
            "❌ Order not found.",
        )

        return

    if order[
        "telegram_user_id"
    ] != user_id:

        send_message(
            chat_id,
            "❌ This order does not belong to you.",
        )

        return

    if order["status"] != "PENDING":

        if order["status"] == "PAYMENT_SUBMITTED":

            send_message(
                chat_id,
                "⏳ Your transaction is already "
                "waiting for admin verification.",
            )

        elif order["status"] == "APPROVED":

            send_message(
                chat_id,
                "✅ This payment has already been approved.",
            )

        else:

            send_message(
                chat_id,
                "❌ This order is no longer awaiting "
                "payment information.",
            )

        return

    send_message(
        chat_id,

        "🧾 <b>Submit your transaction hash</b>\n\n"

        "Send the TX hash of the payment you just made.\n\n"

        f"Order: <code>{order_id}</code>\n\n"

        "Do not send your private key, seed phrase, "
        "password, or wallet credentials.",
    )


# --------------------------------------------------
# ADMIN PAYMENT NOTIFICATION
# --------------------------------------------------

def notify_admins(
    order,
):
    admins = get_admin_ids()

    if not admins:
        print(
            "WARNING: ADMIN_USER_IDS is empty."
        )
        return

    text = (
        "💰 <b>NEW PAYMENT SUBMISSION</b>\n\n"

        f"Order: <code>{order['order_id']}</code>\n"
        f"User ID: <code>{order['telegram_user_id']}</code>\n"
        f"Package: {order['quantity']:,}\n"
        f"Amount: ${order['price_usd']:,.2f}\n"
        f"Network: {get_crypto_label(order['crypto'])}\n\n"

        "TX Hash:\n"
        f"<code>{order['tx_hash']}</code>\n\n"

        "Payment address:\n"
        f"<code>{order['payment_address']}</code>"
    )

    approve_token = make_callback_token(
        "approve",
        order["order_id"],
    )

    reject_token = make_callback_token(
        "reject",
        order["order_id"],
    )

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text":
                        "✅ Approve",
                    "callback_data":
                        (
                            f"approve:"
                            f"{order['order_id']}:"
                            f"{approve_token}"
                        ),
                },
                {
                    "text":
                        "❌ Reject",
                    "callback_data":
                        (
                            f"reject:"
                            f"{order['order_id']}:"
                            f"{reject_token}"
                        ),
                },
            ]
        ]
    }

    for admin_id in admins:

        try:

            send_message(
                admin_id,
                text,
                keyboard,
            )

        except Exception as error:

            print(
                "Admin notification error:",
                repr(error),
            )


# --------------------------------------------------
# TX HASH RECEIVER
# --------------------------------------------------

def handle_transaction_hash(
    chat_id,
    user_id,
    text,
):
    order = get_latest_pending_order(
        user_id
    )

    if not order:
        return False

    tx_hash = text.strip()

    if not validate_tx_hash(
        tx_hash
    ):

        send_message(
            chat_id,

            "❌ That doesn't look like a valid "
            "transaction hash.\n\n"
            "Please send the transaction hash "
            "from your wallet.",
        )

        return True

    success = attach_tx_hash(
        order["order_id"],
        tx_hash,
    )

    if not success:

        send_message(
            chat_id,
            "❌ This order has already been updated. "
            "Please use /buy if you need another order.",
        )

        return True

    updated_order = get_order(
        order["order_id"]
    )

    send_message(
        chat_id,

        "✅ <b>Transaction submitted</b>\n\n"

        f"Order: <code>{order['order_id']}</code>\n\n"

        "Your payment is now waiting for admin "
        "verification.\n\n"

        "You will receive another message when "
        "your payment is approved.",
    )

    notify_admins(
        updated_order
    )

    return True


# --------------------------------------------------
# GENERATE COMMAND
# --------------------------------------------------

def handle_generate(
    chat_id,
    user_id,
    text,
):
    parts = text.split()

    if len(parts) != 2:

        send_message(
            chat_id,
            "Usage:\n\n"
            "/generate 5000",
        )

        return

    try:

        count = int(
            parts[1]
        )

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

    # ----------------------------------------------
    # ADMIN BYPASS
    # ----------------------------------------------

    if is_admin(user_id):

        show_generation_formats(
            chat_id,
            count,
            admin=True,
        )

        return

    # ----------------------------------------------
    # NORMAL USER
    # ----------------------------------------------

    latest = get_latest_payment_order(
        user_id
    )

    if not latest:

        send_message(
            chat_id,

            "💳 <b>Payment required</b>\n\n"

            "You need an approved payment before "
            "generating a file.\n\n"

            "Use /buy to purchase a generation.",
        )

        return

    if latest["quantity"] != count:

        send_message(
            chat_id,

            "❌ Your approved package does not "
            "match this generation size.\n\n"

            f"Approved package: "
            f"{latest['quantity']:,}\n"
            f"Requested: {count:,}\n\n"

            "Use /generate with the exact package "
            "size you purchased, or use /buy for "
            "another package.",
        )

        return

    if latest["status"] == "PAYMENT_SUBMITTED":

        send_message(
            chat_id,

            "⏳ Your payment is still waiting "
            "for admin verification.",
        )

        return

    if latest["status"] == "PENDING":

        send_message(
            chat_id,

            "💳 Your payment has not been submitted yet.\n\n"
            "Please complete your payment and submit "
            "the transaction hash.",
        )

        return

    if latest["status"] == "REJECTED":

        send_message(
            chat_id,

            "❌ Your payment was rejected.\n\n"
            "Use /buy to create a new payment order.",
        )

        return

    if latest["status"] == "COMPLETED":

        send_message(
            chat_id,

            "✅ Your previous payment has already "
            "been used.\n\n"

            "Use /buy to purchase another generation.",
        )

        return

    if latest["status"] != "APPROVED":

        send_message(
            chat_id,
            "⏳ Your order is being processed.",
        )

        return

    show_generation_formats(
        chat_id,
        count,
        order_id=latest["order_id"],
    )


# --------------------------------------------------
# GENERATION FORMAT MENU
# --------------------------------------------------

def show_generation_formats(
    chat_id,
    count,
    order_id=None,
    admin=False,
):
    if admin:

        buttons = [
            [
                {
                    "text": "TXT",
                    "callback_data":
                        f"admin_generate:{count}:txt",
                },
                {
                    "text": "CSV",
                    "callback_data":
                        f"admin_generate:{count}:csv",
                },
                {
                    "text": "JSON",
                    "callback_data":
                        f"admin_generate:{count}:json",
                },
            ]
        ]

    else:

        buttons = [
            [
                {
                    "text": "TXT",
                    "callback_data":
                        f"generate:{order_id}:txt",
                },
                {
                    "text": "CSV",
                    "callback_data":
                        f"generate:{order_id}:csv",
                },
                {
                    "text": "JSON",
                    "callback_data":
                        f"generate:{order_id}:json",
                },
            ]
        ]

    send_message(
        chat_id,

        f"📦 Generate <b>{count:,}</b> "
        "email addresses as:",

        {
            "inline_keyboard": buttons
        },
    )


# --------------------------------------------------
# PAID GENERATION
# --------------------------------------------------

def perform_generation(
    chat_id,
    user_id,
    order_id,
    output_format,
):
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

    claim = claim_generation(
        order_id,
        user_id,
    )

    if not claim:

        send_message(
            chat_id,

            "❌ This payment is no longer "
            "available for generation.\n\n"

            "Use /buy to purchase another generation.",
        )

        return

    count = claim["quantity"]

    send_message(
        chat_id,

        f"⏳ Generating "
        f"<b>{count:,}</b> "
        f"{output_format.upper()} "
        "addresses...",
    )

    path = None

    try:

        print(
            f"Starting paid generation: "
            f"{order_id} / "
            f"{count} / "
            f"{output_format}"
        )

        path = generate_file(
            count,
            output_format,
        )

        print(
            f"File generated: {path}"
        )

        send_generated_file(
            chat_id,
            path,
            output_format,
            count,
        )

        mark_generation_complete(
            order_id
        )

        send_message(
            chat_id,

            "✅ <b>Generation complete.</b>\n\n"

            f"Records: {count:,}\n"
            f"Format: {output_format.upper()}\n\n"

            "Your payment has now been used.\n"
            "Use /buy for another generation.",
        )

        print(
            f"Paid generation completed: "
            f"{order_id}"
        )

    except Exception as error:

        print(
            "Generation error:",
            repr(error),
        )

        mark_generation_failed(
            order_id
        )

        try:

            send_message(
                chat_id,

                "❌ <b>Generation failed.</b>\n\n"

                "Your payment was not marked as used "
                "because the generation failed.\n\n"

                "Please try the generation again.",
            )

        except Exception as send_error:

            print(
                "Failed to send error:",
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
# ADMIN GENERATION
# --------------------------------------------------

def perform_admin_generation(
    chat_id,
    user_id,
    count,
    output_format,
):
    if not is_admin(user_id):

        send_message(
            chat_id,
            "❌ Admin access required.",
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

    send_message(
        chat_id,
        (
            f"⏳ Admin generation started.\n\n"
            f"Records: {count:,}\n"
            f"Format: {output_format.upper()}"
        ),
    )

    path = None

    try:

        print(
            f"ADMIN generation started: "
            f"{count} {output_format}"
        )

        path = generate_file(
            count,
            output_format,
        )

        print(
            f"ADMIN file generated: {path}"
        )

        send_generated_file(
            chat_id,
            path,
            output_format,
            count,
        )

        send_message(
            chat_id,
            (
                f"✅ Admin generation completed.\n\n"
                f"Records: {count:,}\n"
                f"Format: {output_format.upper()}"
            ),
        )

    except Exception as error:

        print(
            "Admin generation error:",
            repr(error),
        )

        try:

            send_message(
                chat_id,
                (
                    "❌ Admin generation failed.\n\n"
                    f"Error: {error}"
                ),
            )

        except Exception as send_error:

            print(
                "Failed to send admin error:",
                repr(send_error),
            )

    finally:

        if path and os.path.exists(path):

            try:

                os.remove(path)

            except Exception as error:

                print(
                    "Admin file cleanup error:",
                    repr(error),
                )


# --------------------------------------------------
# CALLBACK PROCESSING
# --------------------------------------------------

def handle_callback(
    update,
):
    callback = update.get(
        "callback_query"
    )

    if not callback:
        return

    callback_id = callback.get(
        "id"
    )

    message = callback.get(
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

    callback_from = callback.get(
        "from",
        {},
    )

    user_id = callback_from.get(
        "id"
    )

    data = callback.get(
        "data",
        "",
    )

    try:

        answer_callback(
            callback_id
        )

    except Exception as error:

        print(
            "Callback answer error:",
            repr(error),
        )

    parts = data.split(":")

    action = parts[0] if parts else ""

    # ----------------------------------------------
    # BUY
    # ----------------------------------------------

    if action == "buy":

        handle_buy(
            chat_id
        )

        return

    # ----------------------------------------------
    # CANCEL
    # ----------------------------------------------

    if action == "cancel":

        send_message(
            chat_id,
            "❌ Cancelled.",
        )

        return

    # ----------------------------------------------
    # PACKAGE
    # ----------------------------------------------

    if action == "buyq":

        if len(parts) != 2:

            send_message(
                chat_id,
                "❌ Invalid package.",
            )

            return

        try:

            quantity = int(
                parts[1]
            )

        except ValueError:

            send_message(
                chat_id,
                "❌ Invalid package.",
            )

            return

        handle_buy_quantity(
            chat_id,
            quantity,
        )

        return

    # ----------------------------------------------
    # CRYPTO
    # ----------------------------------------------

    if action == "coin":

        if len(parts) != 3:

            send_message(
                chat_id,
                "❌ Invalid payment selection.",
            )

            return

        try:

            quantity = int(
                parts[1]
            )

        except ValueError:

            send_message(
                chat_id,
                "❌ Invalid package.",
            )

            return

        crypto = parts[2]

        if crypto not in PAYMENT_ADDRESSES:

            send_message(
                chat_id,
                "❌ Invalid payment network.",
            )

            return

        create_payment_order(
            chat_id,
            user_id,
            quantity,
            crypto,
        )

        return

    # ----------------------------------------------
    # I'VE PAID
    # ----------------------------------------------

    if action == "paid":

        if len(parts) != 2:

            send_message(
                chat_id,
                "❌ Invalid order.",
            )

            return

        order_id = parts[1]

        handle_paid(
            chat_id,
            user_id,
            order_id,
        )

        return

    # ----------------------------------------------
    # ADMIN APPROVE
    # ----------------------------------------------

    if action == "approve":

        if not is_admin(user_id):

            send_message(
                chat_id,
                "❌ Admin access required.",
            )

            return

        if len(parts) != 3:

            send_message(
                chat_id,
                "❌ Invalid approval request.",
            )

            return

        order_id = parts[1]
        token = parts[2]

        if not verify_callback_token(
            "approve",
            order_id,
            token,
        ):

            send_message(
                chat_id,
                "❌ Invalid approval token.",
            )

            return

        order = get_order(
            order_id
        )

        if not order:

            send_message(
                chat_id,
                "❌ Order not found.",
            )

            return

        success = approve_order(
            order_id
        )

        if not success:

            send_message(
                chat_id,

                "⚠️ This order cannot be approved.\n\n"
                f"Current status: "
                f"{order['status']}",
            )

            return

        send_message(
            chat_id,

            "✅ <b>Payment approved.</b>\n\n"

            f"Order: <code>{order_id}</code>\n"
            f"User: <code>{order['telegram_user_id']}</code>\n"
            f"Package: {order['quantity']:,}",
        )

        try:

            send_message(
                order["telegram_user_id"],

                "✅ <b>Payment approved!</b>\n\n"

                f"Package: {order['quantity']:,}\n"
                f"Amount: ${order['price_usd']:,.2f}\n\n"

                "Your generation is now unlocked.\n"
                "Use:\n"
                f"<code>/generate "
                f"{order['quantity']}</code>",
            )

        except Exception as error:

            print(
                "Customer approval notification error:",
                repr(error),
            )

        return

    # ----------------------------------------------
    # ADMIN REJECT
    # ----------------------------------------------

    if action == "reject":

        if not is_admin(user_id):

            send_message(
                chat_id,
                "❌ Admin access required.",
            )

            return

        if len(parts) != 3:

            send_message(
                chat_id,
                "❌ Invalid rejection request.",
            )

            return

        order_id = parts[1]
        token = parts[2]

        if not verify_callback_token(
            "reject",
            order_id,
            token,
        ):

            send_message(
                chat_id,
                "❌ Invalid rejection token.",
            )

            return

        order = get_order(
            order_id
        )

        if not order:

            send_message(
                chat_id,
                "❌ Order not found.",
            )

            return

        success = reject_order(
            order_id
        )

        if not success:

            send_message(
                chat_id,

                "⚠️ This order cannot be rejected.\n\n"
                f"Current status: "
                f"{order['status']}",
            )

            return

        send_message(
            chat_id,

            "❌ <b>Payment rejected.</b>\n\n"

            f"Order: <code>{order_id}</code>",
        )

        try:

            send_message(
                order["telegram_user_id"],

                "❌ <b>Payment rejected.</b>\n\n"

                f"Order: <code>{order_id}</code>\n\n"

                "Please use /buy to create a new "
                "payment order.",
            )

        except Exception as error:

            print(
                "Customer rejection notification error:",
                repr(error),
            )

        return

    # ----------------------------------------------
    # PAID USER GENERATION
    # ----------------------------------------------

    if action == "generate":

        if len(parts) != 3:

            send_message(
                chat_id,
                "❌ Invalid generation request.",
            )

            return

        order_id = parts[1]
        output_format = parts[2]

        order = get_order(
            order_id
        )

        if not order:

            send_message(
                chat_id,
                "❌ Order not found.",
            )

            return

        if order[
            "telegram_user_id"
        ] != user_id:

            send_message(
                chat_id,
                "❌ This order does not belong to you.",
            )

            return

        perform_generation(
            chat_id,
            user_id,
            order_id,
            output_format,
        )

        return

    # ----------------------------------------------
    # ADMIN GENERATION
    # ----------------------------------------------

    if action == "admin_generate":

        if len(parts) != 3:

            send_message(
                chat_id,
                "❌ Invalid admin generation.",
            )

            return

        if not is_admin(user_id):

            send_message(
                chat_id,
                "❌ Admin access required.",
            )

            return

        try:

            count = int(
                parts[1]
            )

        except ValueError:

            send_message(
                chat_id,
                "❌ Invalid number.",
            )

            return

        output_format = parts[2].lower()

        if count <= 0 or count > MAX_EMAILS:

            send_message(
                chat_id,
                f"❌ Generation must be between "
                f"1 and {MAX_EMAILS:,}.",
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

        perform_admin_generation(
            chat_id,
            user_id,
            count,
            output_format,
        )

        return

    # ----------------------------------------------
    # UNKNOWN CALLBACK
    # ----------------------------------------------

    send_message(
        chat_id,
        "❌ Invalid request.",
    )


# --------------------------------------------------
# UPDATE ROUTER
# --------------------------------------------------

def handle_update(
    update,
):
    if "callback_query" in update:

        handle_callback(
            update
        )

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

    sender = message.get(
        "from",
        {},
    )

    user_id = sender.get(
        "id",
        chat_id,
    )

    text = message.get(
        "text",
        "",
    ).strip()

    if not text:
        return

    # ----------------------------------------------
    # PAYMENT TX HASH
    # ----------------------------------------------

    if not text.startswith("/"):

        if handle_transaction_hash(
            chat_id,
            user_id,
            text,
        ):

            return

    # ----------------------------------------------
    # COMMANDS
    # ----------------------------------------------

    if text == "/start":

        handle_start(
            chat_id,
            user_id,
        )

        return

    if text == "/help":

        handle_help(
            chat_id
        )

        return

    if text == "/buy":

        handle_buy(
            chat_id
        )

        return

    if text.startswith(
        "/generate"
    ):

        handle_generate(
            chat_id,
            user_id,
            text,
        )

        return


# --------------------------------------------------
# VERCEL HTTP HANDLER
# --------------------------------------------------

class handler(
    BaseHTTPRequestHandler
):

    def do_POST(
        self
    ):
        if WEBHOOK_SECRET:

            received_secret = (
                self.headers.get(
                    "X-Telegram-Bot-Api-Secret-Token"
                )
            )

            if (
                received_secret
                != WEBHOOK_SECRET
            ):

                self.send_response(
                    403
                )

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

            handle_update(
                update
            )

            self.send_response(
                200
            )

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

                self.send_response(
                    500
                )

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

    def do_GET(
        self
    ):
        self.send_response(
            200
        )

        self.send_header(
            "Content-Type",
            "application/json",
        )

        self.end_headers()

        self.wfile.write(
            b'{"status":"Telegram bot webhook is online"}'
        )
import hashlib
import hmac
import os
import secrets

from database import (
    create_order,
    get_order,
)


# ============================================================
# ADMINS
# ============================================================

ADMIN_USER_IDS = {
    int(value.strip())
    for value in os.environ.get(
        "ADMIN_USER_IDS",
        ""
    ).split(",")
    if value.strip().isdigit()
}


def is_admin(user_id):
    return user_id in ADMIN_USER_IDS


# ============================================================
# PAYMENT SECRET
# ============================================================

PAYMENT_SECRET = os.environ.get(
    "PAYMENT_SECRET",
    ""
)


# ============================================================
# PRICING
# ============================================================

PRICE_TIERS = {
    2_000: 110,
    5_000: 250,
    10_000: 420,
    100_000: 650,
    1_000_000: 850,
    5_000_000: 1150,
    10_000_000: 1500,
}


# ============================================================
# WALLETS
# ============================================================

PAYMENT_ADDRESSES = {
    "USDT_TRC20":
        "THtYqqzxN28z7sojYXzpGxonBHXaynJ5Gj",

    "USDT_ERC20":
        "0xdCa0D532cCc73d93f2DC6b92B58af19334dE1290",

    "USDT_BEP20":
        "0xdCa0D532cCc73d93f2DC6b92B58af19334dE1290",

    "BTC":
        "bc1qw5du2l3mcma389rx57klxpcur2au66yvdfmr9f",
}


# ============================================================
# CRYPTO LABELS
# ============================================================

CRYPTO_LABELS = {
    "USDT_TRC20": "USDT TRC-20",
    "USDT_ERC20": "USDT ERC-20",
    "USDT_BEP20": "USDT BEP-20",
    "BTC": "BTC",
}


# Backwards-compatible name
CRYPTO_NAMES = CRYPTO_LABELS


# ============================================================
# HELPERS
# ============================================================

def format_quantity(quantity):
    return f"{quantity:,}"


def format_price(price):
    return f"${price:,.2f}"


def get_price(quantity):
    return PRICE_TIERS.get(quantity)


def create_order_id():
    return secrets.token_hex(6).upper()


def get_crypto_label(crypto):
    return CRYPTO_LABELS.get(
        crypto,
        crypto,
    )


def validate_tx_hash(tx_hash):
    if not tx_hash:
        return False

    tx_hash = tx_hash.strip()

    if len(tx_hash) < 20:
        return False

    if len(tx_hash) > 200:
        return False

    return True


# ============================================================
# CALLBACK TOKEN SIGNING
# ============================================================

def make_callback_token(action, order_id):
    """
    Creates a short HMAC token used to authenticate
    admin approve/reject callback actions.
    """

    if not PAYMENT_SECRET:
        raise RuntimeError(
            "PAYMENT_SECRET is not configured."
        )

    message = f"{action}:{order_id}"

    signature = hmac.new(
        PAYMENT_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()[:12]

    return signature


def verify_callback_token(
    action,
    order_id,
    token,
):
    """
    Verifies an HMAC callback token.
    """

    if not PAYMENT_SECRET:
        return False

    expected = make_callback_token(
        action,
        order_id,
    )

    return hmac.compare_digest(
        expected,
        token,
    )


# ============================================================
# BACKWARDS-COMPATIBLE CALLBACK FUNCTIONS
# ============================================================

def sign_action(action, order_id):
    return make_callback_token(
        action,
        order_id,
    )


def verify_action(
    action,
    order_id,
    signature,
):
    return verify_callback_token(
        action,
        order_id,
        signature,
    )


# ============================================================
# CREATE PAYMENT ORDER
# ============================================================

def create_payment_order(
    telegram_user_id,
    quantity,
    crypto,
):
    if quantity not in PRICE_TIERS:
        raise ValueError(
            "Invalid package."
        )

    if crypto not in PAYMENT_ADDRESSES:
        raise ValueError(
            "Invalid payment method."
        )

    price = PRICE_TIERS[quantity]

    order_id = create_order_id()

    create_order(
        order_id=order_id,
        telegram_user_id=telegram_user_id,
        quantity=quantity,
        price_usd=price,
        crypto=crypto,
        payment_address=PAYMENT_ADDRESSES[crypto],
    )

    return order_id


# ============================================================
# PAYMENT MESSAGE
# ============================================================

def build_payment_message(order_id):
    """
    Builds the payment message used by telegram.py.
    """

    order = get_order(order_id)

    if not order:
        raise ValueError(
            "Order not found."
        )

    crypto_label = get_crypto_label(
        order["crypto"]
    )

    return (
        "💳 PAYMENT REQUIRED\n\n"
        f"Order: `{order['order_id']}`\n"
        f"Generation: `{format_quantity(order['quantity'])}` emails\n"
        f"Price: `{format_price(order['price_usd'])}`\n"
        f"Network: `{crypto_label}`\n\n"
        "Send the payment to:\n\n"
        f"`{order['payment_address']}`\n\n"
        "⚠️ Send the payment on the exact network shown above.\n\n"
        "After sending the payment, tap:\n"
        "✅ *I've Paid*\n\n"
        "You will then be asked for the transaction hash."
    )


# ============================================================
# BACKWARDS-COMPATIBLE PAYMENT MESSAGE
# ============================================================

def payment_text(order_id):
    return build_payment_message(
        order_id
    )
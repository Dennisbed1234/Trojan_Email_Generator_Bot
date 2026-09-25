cat > config.py <<'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing from your .env file"
    )

MAX_EMAILS = 1_000_000
EOF
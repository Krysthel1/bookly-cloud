import re
import secrets
from datetime import datetime, timezone


def slugify(text: str) -> str:
    value = text.lower().strip()
    for src, dst in {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"
    }.items():
        value = value.replace(src, dst)
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def generate_order_code() -> str:
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_part = secrets.token_hex(3).upper()
    return f"BKL-{date_part}-{random_part}"


def generate_tx_reference(prefix: str = "SIM") -> str:
    return f"{prefix}-{secrets.token_hex(6).upper()}"

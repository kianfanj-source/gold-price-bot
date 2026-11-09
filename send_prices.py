import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")
START_MINUTE = 11 * 60   # 11:00
END_MINUTE = 18 * 60     # 18:00 (شامل)

TITLE = "طلای آبشده سجاد"
WEBSITE = "www.sajadgoldshop.ir"
PHONE = "09155001063"
SEPARATOR = "━━━━━━━━━━━━"

SOURCES = [
    # (برچسب در پیام, آدرس, واحد, تعداد رقم اعشار, تقسیم بر)
    ("اونس جهانی", "https://www.tgju.org/profile/ons", "دلار", 2, 1),
    ("مثقال", "https://www.tgju.org/profile/mesghal", "تومان", 0, 10),
    ("گرم ۱۸ عیار", "https://www.tgju.org/profile/geram18", "تومان", 0, 10),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "fa,en;q=0.8",
}

PRICE_PATTERN = re.compile(
    r'data-col="info\.last_trade\.PDrCotVal"[^>]*>\s*([0-9][0-9,\.]*)\s*<'
)


def fetch_price(url):
    """قیمت را برمی‌گرداند. اگر نشد، None."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            page = resp.read().decode("utf-8", errors="replace")
        match = PRICE_PATTERN.search(page)
        if not match:
            print(f"[خطا] قیمت در صفحه پیدا نشد: {url}")
            return None
        value = float(match.group(1).replace(",", ""))
        if value <= 0:
            print(f"[خطا] مقدار نامعتبر ({value}) از: {url}")
            return None
        return value
    except Exception as e:
        print(f"[خطا] دریافت از {url} شکست خورد: {e!r}")
        return None


def format_line(label, value, unit, decimals):
    if value is None:
        return f"{label}: نامشخص"
    return f"{label}: {value:,.{decimals}f} {unit}"


def send_message(token, chat_id, text):
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    try:
        with urllib.request.urlopen(api_url, data=data, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print(f"[خطا] تلگرام جواب خطا داد: {e.code} {detail}")
        return False
    except Exception as e:
        print(f"[خطا] ارسال به تلگرام شکست خورد: {e!r}")
        return False
    if not body.get("ok"):
        print(f"[خطا] تلگرام ok نداد: {body}")
        return False
    return True


def main():
    now = datetime.now(TEHRAN)
    minute_of_day = now.hour * 60 + now.minute
    force = os.environ.get("FORCE_SEND", "").strip() == "1"

    print(f"ساعت تهران: {now:%Y-%m-%d %H:%M}")

    if not force and not (START_MINUTE <= minute_of_day <= END_MINUTE):
        print("بیرون از بازه ۱۱:۰۰ تا ۱۸:۰۰ است. ارسال نمی‌شود.")
        return 0

    if force:
        print("حالت تست: کنترل ساعت دور زده شد.")

    token = os.environ.get("BOT_TOKEN", "").strip()
    chat_id = os.environ.get("CHAT_ID", "").strip()
    if not token or not chat_id:
        print("[خطا] BOT_TOKEN یا CHAT_ID در Secrets تنظیم نشده است.")
        return 1

    values = []
    for label, url, unit, decimals, divisor in SOURCES:
        price = fetch_price(url)
        if price is not None:
            price = price / divisor
        values.append(price)

    if all(v is None for v in values):
        print("[خطا] هر سه قیمت شکست خورد. پیامی ارسال نشد.")
        return 1

    lines = [f"<b>{html.escape(TITLE)}</b>", SEPARATOR]
    for (label, url, unit, decimals, divisor), value in zip(SOURCES, values):
        lines.append(html.escape(format_line(label, value, unit, decimals)))
    lines.append(SEPARATOR)
    lines.append(html.escape(WEBSITE))
    lines.append(f"<b>{html.escape(PHONE)}</b>")
    text = "\n".join(lines)

    print("متن پیام:\n" + text)

    if send_message(token, chat_id, text):
        print("پیام با موفقیت ارسال شد.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

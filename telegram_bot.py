"""
BTC_Pulse_Bot — Telegram Bot
==========================================
Handles subscriber management (/subscribe, /unsubscribe, /signal)
and sends signal change alerts to all subscribers.

Setup:
1. Create a bot via @BotFather on Telegram -> get BOT_TOKEN
2. Set TELEGRAM_BOT_TOKEN environment variable on Railway
3. Set GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_SHEET_ID on Railway

Running standalone:
    python3 telegram_bot.py poll      <- run the polling loop
    python3 telegram_bot.py test      <- send a test broadcast
"""

import os
import json
import time
import requests
from datetime import datetime

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
SUBS_FILE = os.path.join(os.path.dirname(__file__), "telegram_subs.json")
SIGNAL_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".alert_cache.json")
DASHBOARD_URL = "https://web-production-7d14.up.railway.app"

# ─────────────────────────────────────────────────────────────────────────────
# Subscriber management (JSON file — ephemeral fallback)
# ─────────────────────────────────────────────────────────────────────────────

def load_subscribers():
    if os.path.exists(SUBS_FILE):
        try:
            with open(SUBS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_subscribers(subs):
    try:
        with open(SUBS_FILE, "w") as f:
            json.dump(subs, f, indent=2)
    except Exception as e:
        print(f"[Telegram] Could not save subs file: {e}")


def add_subscriber(chat_id, username="", first_name="", last_name=""):
    subs = load_subscribers()
    if any(str(s.get("chat_id")) == str(chat_id) for s in subs):
        return False  # already subscribed
    subs.append({
        "chat_id": str(chat_id),
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "joined": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    })
    save_subscribers(subs)
    return True


def remove_subscriber(chat_id):
    subs = load_subscribers()
    new_subs = [s for s in subs if str(s.get("chat_id")) != str(chat_id)]
    if len(new_subs) < len(subs):
        save_subscribers(new_subs)
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Telegram API helpers
# ─────────────────────────────────────────────────────────────────────────────

def send_message(chat_id, text, parse_mode="HTML"):
    if not BOT_TOKEN:
        print("[Telegram] No BOT_TOKEN — cannot send message.")
        return False
    try:
        url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }, timeout=10)
        if r.status_code != 200:
            print("[Telegram] Send failed (" + str(r.status_code) + "): " + r.text[:200])
        return r.status_code == 200
    except Exception as e:
        print("[Telegram] Send error: " + str(e))
        return False


def broadcast(text):
    subs = load_subscribers()
    if not subs:
        print("[Telegram] No subscribers to broadcast to.")
        return 0
    sent = 0
    for sub in subs:
        if send_message(sub["chat_id"], text):
            sent += 1
    print("[Telegram] Broadcast sent to " + str(sent) + "/" + str(len(subs)) + " subscribers.")
    return sent


# ─────────────────────────────────────────────────────────────────────────────
# Signal helpers
# ─────────────────────────────────────────────────────────────────────────────

SIGNAL_EMOJI = {
    "ACCUMULATE": "🟢",
    "CAUTION":    "🟡",
    "AVOID":      "🔴",
}


def _load_cache():
    if os.path.exists(SIGNAL_CACHE_FILE):
        try:
            with open(SIGNAL_CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _fetch_live_price():
    """Fetch live BTC price directly from CoinGecko — used when cache is stale."""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if r.status_code == 200:
            data = r.json().get("bitcoin", {})
            return data.get("usd"), data.get("usd_24h_change", 0)
    except Exception as e:
        print("[Telegram] Live price fetch error: " + str(e))
    return None, None


def _fetch_live_signals():
    """Fetch fresh signal data directly from data_fetcher.
    Returns (verdict, score, buy_n, caution_n, sell_n, price) or None on failure."""
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(__file__))
        from data_fetcher import get_all_indicators, get_all_signals, compute_overall_verdict
        data    = get_all_indicators()
        signals = get_all_signals(data)
        verdict, _, score, buy_n, caution_n, sell_n = compute_overall_verdict(signals)
        price = data.get('price', 0)
        return verdict, score, buy_n, caution_n, sell_n, price
    except Exception as e:
        print("[Telegram] Live signal fetch error: " + str(e))
        return None


def _build_signal_message():
    # Try to get fully fresh live data first
    live = _fetch_live_signals()
    if live:
        verdict, score, buy_n, caution_n, sell_n, price = live
    else:
        # Fall back to cache
        cache = _load_cache()
        verdict   = cache.get("last_verdict", "")
        score     = cache.get("last_score", "")
        price     = cache.get("last_price", "")
        buy_n     = cache.get("last_buy", "")
        caution_n = cache.get("last_caution", "")
        sell_n    = cache.get("last_sell", "")
        # Even on cache fallback, try to get a fresh price
        live_price, _ = _fetch_live_price()
        if live_price is not None:
            price = live_price

    val_region = ""
    emoji = SIGNAL_EMOJI.get(verdict, "⚪")

    lines = [
        "📊 <b>BTCpulse — Current Signal</b>",
        "",
    ]

    if verdict and score != "":
        lines.append(emoji + " <b>" + str(verdict) + "</b>  ·  Score: <b>" + str(int(float(score))) + "/100</b>")
    elif verdict:
        lines.append(emoji + " <b>" + str(verdict) + "</b>")
    else:
        lines.append("⚪ Signal data loading — try again in a moment.")

    if buy_n != "" or caution_n != "" or sell_n != "":
        lines.append("🟢 " + str(buy_n) + " Buy  🟡 " + str(caution_n) + " Caution  🔴 " + str(sell_n) + " Sell")

    if val_region:
        lines.append("📍 " + str(val_region))

    if price != "":
        try:
            lines.append("💰 BTC: <b>$" + "{:,.0f}".format(float(str(price).replace(",", ""))) + "</b>")
        except Exception:
            lines.append("💰 BTC: <b>" + str(price) + "</b>")

    lines += [
        "",
        '<a href="' + DASHBOARD_URL + '">View Full Dashboard →</a>',
        "",
        "<i>Not financial advice.</i>",
    ]
    return "\n".join(lines)


def send_signal_change_alert(verdict, score, buy_n, caution_n, sell_n, price, summary=""):
    emoji = SIGNAL_EMOJI.get(verdict, "⚪")
    lines = [
        "🔔 <b>BTCpulse — Signal Changed</b>",
        "",
        emoji + " <b>" + str(verdict) + "</b>  ·  Score: <b>" + str(int(float(score))) + "/100</b>",
        "🟢 " + str(buy_n) + " Buy  🟡 " + str(caution_n) + " Caution  🔴 " + str(sell_n) + " Sell",
        "💰 BTC: <b>$" + "{:,.0f}".format(float(price)) + "</b>",
    ]
    if summary:
        lines += ["", "<i>" + str(summary) + "</i>"]
    lines += [
        "",
        '<a href="' + DASHBOARD_URL + '">View Full Dashboard →</a>',
        "",
        "<i>Not financial advice.</i>",
    ]
    return broadcast("\n".join(lines))


# ─────────────────────────────────────────────────────────────────────────────
# Update handler
# ─────────────────────────────────────────────────────────────────────────────

def handle_update(update):
    msg = update.get("message", {})
    if not msg:
        return

    chat_id    = msg.get("chat", {}).get("id")
    text       = (msg.get("text") or "").strip()
    user       = msg.get("from", {})
    username   = user.get("username", "")
    first_name = user.get("first_name", "")
    last_name  = user.get("last_name", "")

    if not chat_id or not text:
        return

    text_lower = text.lower()

    if text_lower in ("/start", "/subscribe"):
        added = add_subscriber(chat_id, username, first_name, last_name)

        # Log to Google Sheets (non-blocking)
        try:
            from sheets_storage import save_telegram_event
            cache = _load_cache()
            sig_str = str(cache.get("last_verdict", "")) + " (" + str(cache.get("last_score", "")) + ")"
            action = "subscribe" if added else "already_subscribed"
            save_telegram_event(chat_id, username, first_name, last_name, action, sig_str)
        except Exception as e:
            print("[Telegram] Sheets log error: " + str(e))

        signal_msg = _build_signal_message()

        if added:
            intro = (
                "✅ <b>Welcome to BTC_Pulse_Bot!</b>\n\n"
                "You'll receive an alert whenever the overall signal changes tier — "
                "so you always know whether it's a time to accumulate or hold off.\n\n"
                "Here's the current reading:\n\n"
            )
            send_message(chat_id, intro + signal_msg)
        else:
            send_message(chat_id,
                "You're already subscribed! 👍\n\n"
                "Here's the latest signal:\n\n" + signal_msg
            )

    elif text_lower == "/unsubscribe":
        removed = remove_subscriber(chat_id)
        try:
            from sheets_storage import save_telegram_event
            save_telegram_event(chat_id, username, first_name, last_name, "unsubscribe")
        except Exception:
            pass
        if removed:
            send_message(chat_id,
                "✅ You've been unsubscribed. You won't receive any more alerts.\n\n"
                "Use /subscribe to rejoin anytime."
            )
        else:
            send_message(chat_id, "You weren't subscribed. Use /subscribe to start receiving alerts.")

    elif text_lower == "/signal":
        send_message(chat_id, _build_signal_message())

    elif text_lower == "/help":
        send_message(chat_id,
            "🤖 <b>BTC_Pulse_Bot</b>\n\n"
            "Commands:\n"
            "/subscribe — Get signal change alerts\n"
            "/unsubscribe — Stop alerts\n"
            "/signal — Current accumulation signal\n"
            "/help — This message\n\n"
            "Or just send <b>any message</b> to get an instant signal update.\n\n"
            '<a href="' + DASHBOARD_URL + '">Open Dashboard →</a>'
        )

    else:
        send_message(chat_id, _build_signal_message())


# ─────────────────────────────────────────────────────────────────────────────
# Polling loop — robust with retry/backoff
# ─────────────────────────────────────────────────────────────────────────────

def poll_updates(offset=None):
    if not BOT_TOKEN:
        return []
    try:
        url = "https://api.telegram.org/bot" + BOT_TOKEN + "/getUpdates"
        params = {"timeout": 30, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        r = requests.get(url, params=params, timeout=40)
        if r.status_code == 200:
            return r.json().get("result", [])
        else:
            print("[Telegram] getUpdates error " + str(r.status_code) + ": " + r.text[:200])
    except requests.exceptions.Timeout:
        pass  # normal for long-polling
    except Exception as e:
        print("[Telegram] Poll error: " + str(e))
    return []


def run_polling():
    print("[Telegram] BTC_Pulse_Bot starting... token=" + ("set" if BOT_TOKEN else "MISSING"))
    if not BOT_TOKEN:
        print("[Telegram] ERROR: TELEGRAM_BOT_TOKEN not set. Exiting.")
        return

    offset = None
    consecutive_errors = 0

    while True:
        try:
            updates = poll_updates(offset)
            consecutive_errors = 0

            for update in updates:
                try:
                    handle_update(update)
                except Exception as e:
                    print("[Telegram] Error handling update: " + str(e))
                offset = update["update_id"] + 1

        except Exception as e:
            consecutive_errors += 1
            wait = min(30, 2 ** consecutive_errors)
            print("[Telegram] Polling error #" + str(consecutive_errors) + ": " + str(e) + " — retrying in " + str(wait) + "s")
            time.sleep(wait)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if not args or args[0] == "poll":
        run_polling()
    elif args[0] == "test":
        print("BOT_TOKEN set: " + ("Yes" if BOT_TOKEN else "No"))
        print("Subscribers: " + str(len(load_subscribers())))
        result = broadcast(
            "🧪 <b>Test Alert — BTC_Pulse_Bot</b>\n\n"
            "This is a test notification from your dashboard bot.\n"
            "If you received this, the bot is working correctly! ✅\n\n"
            "<i>Not financial advice.</i>"
        )
        print("Sent to " + str(result) + " subscribers.")
    else:
        print("Usage: python3 telegram_bot.py [poll|test]")

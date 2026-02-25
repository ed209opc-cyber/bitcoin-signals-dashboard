"""
BTC_Pulse_Bot — Telegram Bot
==========================================
Handles subscriber management (/subscribe, /unsubscribe, /signal)
and sends signal change alerts to all subscribers.

Setup:
1. Create a bot via @BotFather on Telegram → get BOT_TOKEN
2. Set TELEGRAM_BOT_TOKEN environment variable on Railway
3. This script is called by app.py when a signal change is detected

Running standalone (for testing):
    python3 telegram_bot.py test
"""

import os
import json
import requests
from datetime import datetime

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
SUBS_FILE = os.path.join(os.path.dirname(__file__), "telegram_subs.json")
SIGNAL_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".alert_cache.json")

# ─────────────────────────────────────────────────────────────────────────────
# Subscriber management
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
    with open(SUBS_FILE, "w") as f:
        json.dump(subs, f, indent=2)

def add_subscriber(chat_id, username=""):
    subs = load_subscribers()
    if any(str(s.get("chat_id")) == str(chat_id) for s in subs):
        return False  # already subscribed
    subs.append({
        "chat_id": str(chat_id),
        "username": username,
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
        print(f"[Telegram] No BOT_TOKEN set — would send to {chat_id}: {text[:60]}...")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[Telegram] Send error: {e}")
        return False

def broadcast(text):
    """Send a message to all subscribers."""
    subs = load_subscribers()
    if not subs:
        print("[Telegram] No subscribers to broadcast to.")
        return 0
    sent = 0
    for sub in subs:
        if send_message(sub["chat_id"], text):
            sent += 1
    print(f"[Telegram] Broadcast sent to {sent}/{len(subs)} subscribers.")
    return sent

# ─────────────────────────────────────────────────────────────────────────────
# Signal change alert
# ─────────────────────────────────────────────────────────────────────────────

SIGNAL_EMOJI = {
    "STRONG BUY":      "🟢🟢",
    "ACCUMULATE":      "🟢",
    "NEUTRAL — WATCH": "🟡",
    "CAUTION — HOLD":  "🟠",
    "SELL / REDUCE":   "🔴",
}

def send_signal_change_alert(prev_signal, new_signal, score, buy_n, caution_n, sell_n, price):
    """
    Called when the overall accumulation signal changes tier.
    Broadcasts to all Telegram subscribers.
    """
    emoji = SIGNAL_EMOJI.get(new_signal, "⚪")
    prev_emoji = SIGNAL_EMOJI.get(prev_signal, "⚪")

    text = (
        f"🔔 <b>Bitcoin Accumulation Signal Update</b>\n\n"
        f"{prev_emoji} <s>{prev_signal}</s>  →  {emoji} <b>{new_signal}</b>\n\n"
        f"📊 Score: <b>{score}/100</b>\n"
        f"🟢 Buy: {buy_n}  🟡 Caution: {caution_n}  🔴 Sell: {sell_n}\n"
        f"💰 BTC Price: <b>${price:,.0f}</b>\n\n"
        f"<a href='https://web-production-7d14.up.railway.app'>View Dashboard →</a>\n\n"
        f"<i>BTCpulse · Not financial advice</i>"
    )
    return broadcast(text)

# ─────────────────────────────────────────────────────────────────────────────
# Webhook handler (for processing incoming messages from users)
# ─────────────────────────────────────────────────────────────────────────────

def _build_signal_message():
    """Build a formatted current signal message from the alert cache."""
    try:
        if os.path.exists(SIGNAL_CACHE_FILE):
            with open(SIGNAL_CACHE_FILE, "r") as _f:
                cache = json.load(_f)
            verdict    = cache.get("last_verdict", "")
            score      = cache.get("last_score", 0)
            price      = cache.get("last_price", 0)
            buy_n      = cache.get("last_buy", 0)
            caution_n  = cache.get("last_caution", 0)
            sell_n     = cache.get("last_sell", 0)
            val_region = cache.get("last_val_region", "")
            pct_200w   = cache.get("last_pct_200w", 0)
            emoji      = SIGNAL_EMOJI.get(verdict, "⚪")
            val_emoji_map = {
                "Very Cheap": "🟢🟢", "Cheap": "🟢",
                "Fair Value": "🟡", "Expensive": "🟠",
                "Very Expensive": "🔴",
            }
            val_emoji = val_emoji_map.get(val_region, "⚪")
            if verdict in ("STRONG BUY", "ACCUMULATE"):
                summary = "Indicators are broadly bullish. Historically a favourable window to accumulate."
            elif "NEUTRAL" in verdict:
                summary = "Mixed signals — no strong edge in either direction. Watch and wait."
            elif "CAUTION" in verdict:
                summary = "Indicators are cautious. Reduce new exposure and manage risk."
            else:
                summary = "Indicators lean bearish. Consider reducing or pausing new positions."
            ts = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")
            val_pct = ("  (%+.1f%% vs 200W MA)" % pct_200w) if val_region else ""
            lines = [
                "📡 <b>BTC_Pulse_Bot — Live Signal</b>",
                "",
                "%s <b>Signal: %s</b>  ·  Score: %s/100" % (emoji, verdict, score),
                "🟢 %s Buy  🟡 %s Caution  🔴 %s Sell" % (buy_n, caution_n, sell_n),
                "",
                "%s <b>Valuation: %s</b>%s" % (val_emoji, val_region, val_pct),
                "💰 BTC Price: <b>$%s</b>" % "{:,.0f}".format(price),
                "",
                "💬 %s" % summary,
                "",
                "🕐 Updated: %s" % ts,
                "",
                "<a href='https://web-production-7d14.up.railway.app'>View Full Dashboard →</a>",
                "<i>Not financial advice.</i>",
            ]
            return "\n".join(lines)
    except Exception:
        pass
    return "⚠️ Signal data not available yet. The dashboard refreshes every 5 minutes — try again shortly."

def handle_update(update):
    """Process an incoming Telegram update (message from a user)."""
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    username = msg.get("from", {}).get("username", "")
    text = msg.get("text", "").strip().lower()

    if not chat_id:
        return

    if text in ["/start", "/subscribe"]:
        added = add_subscriber(chat_id, username)
        # Build current signal snippet from cache
        _signal_snippet = ""
        try:
            if os.path.exists(SIGNAL_CACHE_FILE):
                with open(SIGNAL_CACHE_FILE, "r") as _f:
                    _cache = json.load(_f)
                _verdict = _cache.get("last_verdict", "")
                _score = _cache.get("last_score", 0)
                _price = _cache.get("last_price", 0)
                _buy_n = _cache.get("last_buy", 0)
                _caution_n = _cache.get("last_caution", 0)
                _sell_n = _cache.get("last_sell", 0)
                _emoji = SIGNAL_EMOJI.get(_verdict, "⚪")
                _signal_snippet = (
                    f"\n\n📊 <b>Current Signal</b>\n"
                    f"{_emoji} <b>{_verdict}</b>  ·  Score: {_score}/100\n"
                    f"🟢 {_buy_n} Buy  🟡 {_caution_n} Caution  🔴 {_sell_n} Sell\n"
                    f"💰 BTC: <b>${_price:,.0f}</b>"
                )
        except Exception:
            pass
        if added:
            send_message(chat_id,
                f"✅ <b>Welcome to BTC_Pulse_Bot!</b>\n\n"
                f"You'll receive an alert whenever the overall signal changes tier — "
                f"so you always know whether it's a time to accumulate or hold off."
                f"{_signal_snippet}\n\n"
                f"Commands:\n"
                f"/signal — Get the current signal anytime\n"
                f"/unsubscribe — Stop notifications\n\n"
                f"<a href='https://web-production-7d14.up.railway.app'>View Full Dashboard →</a>\n\n"
                f"<i>Not financial advice.</i>"
            )
        else:
            send_message(chat_id,
                f"You're already subscribed! 👍"
                f"{_signal_snippet}\n\n"
                f"Use /signal anytime for the latest reading, or /unsubscribe to stop alerts.\n"
                f"<a href='https://web-production-7d14.up.railway.app'>View Dashboard →</a>"
            )

    elif text == "/unsubscribe":
        removed = remove_subscriber(chat_id)
        if removed:
            send_message(chat_id, "✅ You've been unsubscribed. You won't receive any more alerts.")
        else:
            send_message(chat_id, "You weren't subscribed. Use /subscribe to start receiving alerts.")

    elif text == "/signal":
        send_message(chat_id, _build_signal_message())

    elif text == "/help":
        send_message(chat_id,
            "🤖 <b>BTC_Pulse_Bot</b>\n\n"
            "Commands:\n"
            "/subscribe — Get signal change alerts\n"
            "/unsubscribe — Stop alerts\n"
            "/signal — Current accumulation signal\n"
            "/help — This message\n\n"
            "Or just send <b>any message</b> to get an instant signal update.\n\n"
            "<a href='https://web-production-7d14.up.railway.app'>Open Dashboard →</a>"
        )
    else:
        # Fallback: any unrecognised message → return current signal
        send_message(chat_id, _build_signal_message())

# ─────────────────────────────────────────────────────────────────────────────
# Polling loop (for development/testing — on Railway use webhook instead)
# ─────────────────────────────────────────────────────────────────────────────

def poll_updates(offset=None):
    """Long-poll for updates from Telegram."""
    if not BOT_TOKEN:
        print("[Telegram] BOT_TOKEN not set.")
        return None
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {"timeout": 30, "allowed_updates": ["message"]}
        if offset:
            params["offset"] = offset
        r = requests.get(url, params=params, timeout=35)
        if r.status_code == 200:
            return r.json().get("result", [])
    except Exception as e:
        print(f"[Telegram] Poll error: {e}")
    return []

def run_polling():
    """Run the bot in polling mode (for testing)."""
    print(f"[Telegram] Starting polling loop... ({len(load_subscribers())} subscribers)")
    offset = None
    while True:
        updates = poll_updates(offset)
        for update in updates:
            handle_update(update)
            offset = update["update_id"] + 1

# ─────────────────────────────────────────────────────────────────────────────
# CLI test mode
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            print(f"BOT_TOKEN set: {'Yes' if BOT_TOKEN else 'No — set TELEGRAM_BOT_TOKEN env var'}")
            print(f"Subscribers: {len(load_subscribers())}")
            print("Sending test broadcast...")
            broadcast(
                "🧪 <b>Test Alert — BTC_Pulse_Bot</b>\n\n"
                "This is a test notification from your dashboard bot.\n"
                "If you received this, the bot is working correctly! ✅\n\n"
                "<i>Not financial advice.</i>"
            )
        elif sys.argv[1] == "poll":
            run_polling()
    else:
        print("Usage: python3 telegram_bot.py [test|poll]")

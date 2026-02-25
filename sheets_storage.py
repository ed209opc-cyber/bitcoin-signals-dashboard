"""
sheets_storage.py — Durable Google Sheets backend for BTCpulse
================================================================
Writes beta signups and Telegram subscriber events to Google Sheets.
Credentials are loaded from the GOOGLE_SERVICE_ACCOUNT_JSON env var
(a single-line JSON string of the service account key file).
"""
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1MupGJlxhxZzOenZlmTMo_vqIcC0VrHvBP86DpR7xbC8")

_gc = None  # gspread client, lazily initialised


def _get_client():
    global _gc
    if _gc is not None:
        return _gc
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
        ]

        raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        if not raw:
            logger.warning("[Sheets] GOOGLE_SERVICE_ACCOUNT_JSON not set — skipping.")
            return None

        info = json.loads(raw)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        _gc = gspread.authorize(creds)
        return _gc
    except Exception as e:
        logger.error(f"[Sheets] Failed to initialise client: {e}")
        return None


def _get_sheet(tab_name: str):
    gc = _get_client()
    if gc is None:
        return None
    try:
        sh = gc.open_by_key(SHEET_ID)
        try:
            return sh.worksheet(tab_name)
        except Exception:
            # Create the tab if it doesn't exist
            ws = sh.add_worksheet(title=tab_name, rows=1000, cols=20)
            return ws
    except Exception as e:
        logger.error(f"[Sheets] Cannot open sheet: {e}")
        return None


# ── Beta Signups ──────────────────────────────────────────────────────────────

BETA_HEADERS = ["Timestamp", "Email", "First Name", "Signal at Signup", "Score at Signup"]


def _ensure_beta_headers(ws):
    """Add header row if the sheet is empty."""
    try:
        if ws.row_count == 0 or ws.cell(1, 1).value != "Timestamp":
            ws.insert_row(BETA_HEADERS, index=1)
    except Exception:
        pass


def save_beta_signup(email: str, name: str = "", signal: str = "", score: str = ""):
    """Append a beta signup row to the 'Beta Signups' tab."""
    ws = _get_sheet("Beta Signups")
    if ws is None:
        return False
    try:
        _ensure_beta_headers(ws)
        ws.append_row([
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            email.strip().lower(),
            name.strip(),
            signal,
            str(score),
        ])
        logger.info(f"[Sheets] Beta signup saved: {email}")
        return True
    except Exception as e:
        logger.error(f"[Sheets] Failed to save beta signup: {e}")
        return False


# ── Telegram Subscribers ──────────────────────────────────────────────────────

TG_HEADERS = ["Timestamp", "Chat ID", "Username", "First Name", "Last Name", "Action", "Signal at Action"]


def _ensure_tg_headers(ws):
    try:
        if ws.row_count == 0 or ws.cell(1, 1).value != "Timestamp":
            ws.insert_row(TG_HEADERS, index=1)
    except Exception:
        pass


def save_telegram_event(chat_id, username, first_name, last_name, action, signal=""):
    """Append a Telegram subscriber event to the 'Telegram Subscribers' tab."""
    ws = _get_sheet("Telegram Subscribers")
    if ws is None:
        return False
    try:
        _ensure_tg_headers(ws)
        ws.append_row([
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            str(chat_id),
            str(username or ""),
            str(first_name or ""),
            str(last_name or ""),
            action,
            signal,
        ])
        logger.info(f"[Sheets] Telegram event saved: {action} for {chat_id}")
        return True
    except Exception as e:
        logger.error(f"[Sheets] Failed to save Telegram event: {e}")
        return False

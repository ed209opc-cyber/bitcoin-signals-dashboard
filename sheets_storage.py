"""
sheets_storage.py — Durable Google Sheets backend for BTCpulse
================================================================
Writes beta signups and Telegram subscriber events to Google Sheets.
Also provides the authoritative subscriber list (load/save/remove)
so subscribers persist across Railway redeployments.

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
            ws = sh.add_worksheet(title=tab_name, rows=2000, cols=20)
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


# ── Telegram Subscriber Events (audit log) ───────────────────────────────────

TG_EVENTS_HEADERS = [
    "Timestamp", "Chat ID", "Username", "First Name", "Last Name",
    "Action", "Signal at Action", "BTC Price at Action"
]


def _ensure_tg_events_headers(ws):
    try:
        if ws.row_count == 0 or ws.cell(1, 1).value != "Timestamp":
            ws.insert_row(TG_EVENTS_HEADERS, index=1)
    except Exception:
        pass


def save_telegram_event(chat_id, username, first_name, last_name, action,
                        signal="", btc_price=""):
    """Append a Telegram event row to the 'TG Events' audit log tab."""
    ws = _get_sheet("TG Events")
    if ws is None:
        return False
    try:
        _ensure_tg_events_headers(ws)
        ws.append_row([
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            str(chat_id),
            str(username or ""),
            str(first_name or ""),
            str(last_name or ""),
            action,
            str(signal),
            str(btc_price),
        ])
        logger.info(f"[Sheets] TG event saved: {action} for {chat_id}")
        return True
    except Exception as e:
        logger.error(f"[Sheets] Failed to save TG event: {e}")
        return False


# ── Telegram Subscribers (authoritative list) ─────────────────────────────────
# This tab is the source of truth for active subscribers.
# Columns: Chat ID | Username | First Name | Last Name | Joined (UTC) | Status
#
# Status is either "active" or "removed".
# We never delete rows — we update the Status column instead, so the full
# history is preserved and the list survives Railway redeployments.

TG_SUBS_TAB = "TG Subscribers"
TG_SUBS_HEADERS = ["Chat ID", "Username", "First Name", "Last Name", "Joined (UTC)", "Status"]

# Column indices (1-based)
_COL_CHAT_ID   = 1
_COL_USERNAME  = 2
_COL_FIRSTNAME = 3
_COL_LASTNAME  = 4
_COL_JOINED    = 5
_COL_STATUS    = 6


def _ensure_subs_headers(ws):
    try:
        if ws.row_count == 0 or ws.cell(1, 1).value != "Chat ID":
            ws.insert_row(TG_SUBS_HEADERS, index=1)
    except Exception:
        pass


def sheets_load_subscribers():
    """
    Load all active subscribers from the 'TG Subscribers' Sheets tab.
    Returns a list of dicts: [{chat_id, username, first_name, last_name, joined}]
    Returns None if Sheets is unavailable (caller should fall back to local JSON).
    """
    ws = _get_sheet(TG_SUBS_TAB)
    if ws is None:
        return None
    try:
        _ensure_subs_headers(ws)
        rows = ws.get_all_records()
        result = []
        for row in rows:
            if str(row.get("Status", "")).lower() == "active":
                result.append({
                    "chat_id":    str(row.get("Chat ID", "")),
                    "username":   str(row.get("Username", "")),
                    "first_name": str(row.get("First Name", "")),
                    "last_name":  str(row.get("Last Name", "")),
                    "joined":     str(row.get("Joined (UTC)", "")),
                })
        return result
    except Exception as e:
        logger.error(f"[Sheets] Failed to load subscribers: {e}")
        return None


def sheets_add_subscriber(chat_id, username="", first_name="", last_name=""):
    """
    Add a new subscriber to the 'TG Subscribers' tab, or reactivate if removed.
    Returns True if newly added/reactivated, False if already active.
    Returns None if Sheets is unavailable.
    """
    ws = _get_sheet(TG_SUBS_TAB)
    if ws is None:
        return None
    try:
        _ensure_subs_headers(ws)
        rows = ws.get_all_records()
        chat_id_str = str(chat_id)

        # Check if already exists
        for idx, row in enumerate(rows, start=2):  # row 1 is header
            if str(row.get("Chat ID", "")) == chat_id_str:
                status = str(row.get("Status", "")).lower()
                if status == "active":
                    return False  # already subscribed
                else:
                    # Reactivate
                    ws.update_cell(idx, _COL_STATUS, "active")
                    ws.update_cell(idx, _COL_USERNAME, str(username or ""))
                    ws.update_cell(idx, _COL_FIRSTNAME, str(first_name or ""))
                    ws.update_cell(idx, _COL_LASTNAME, str(last_name or ""))
                    ws.update_cell(idx, _COL_JOINED,
                                   datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
                    logger.info(f"[Sheets] Subscriber reactivated: {chat_id}")
                    return True

        # New subscriber — append row
        ws.append_row([
            chat_id_str,
            str(username or ""),
            str(first_name or ""),
            str(last_name or ""),
            datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "active",
        ])
        logger.info(f"[Sheets] Subscriber added: {chat_id}")
        return True
    except Exception as e:
        logger.error(f"[Sheets] Failed to add subscriber: {e}")
        return None


def sheets_remove_subscriber(chat_id):
    """
    Mark a subscriber as 'removed' in the 'TG Subscribers' tab.
    Returns True if found and removed, False if not found.
    Returns None if Sheets is unavailable.
    """
    ws = _get_sheet(TG_SUBS_TAB)
    if ws is None:
        return None
    try:
        rows = ws.get_all_records()
        chat_id_str = str(chat_id)
        for idx, row in enumerate(rows, start=2):
            if str(row.get("Chat ID", "")) == chat_id_str:
                if str(row.get("Status", "")).lower() == "active":
                    ws.update_cell(idx, _COL_STATUS, "removed")
                    logger.info(f"[Sheets] Subscriber removed: {chat_id}")
                    return True
                return False  # already removed
        return False  # not found
    except Exception as e:
        logger.error(f"[Sheets] Failed to remove subscriber: {e}")
        return None

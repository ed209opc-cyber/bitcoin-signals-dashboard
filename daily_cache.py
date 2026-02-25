"""
Daily AI Commentary Cache
Stores the AI-generated market vibe to a JSON file and regenerates it once per day (UTC).
This keeps OpenAI API calls to a minimum while ensuring fresh daily analysis.
"""

import json
import os
from datetime import datetime, timezone

CACHE_FILE = os.path.join(os.path.dirname(__file__), '.daily_vibe_cache.json')


def get_today_utc() -> str:
    """Return today's date as YYYY-MM-DD in UTC."""
    # Cache by 5-minute window so vibe refreshes with each data cycle
    now = datetime.now(timezone.utc)
    minute_block = (now.minute // 5) * 5
    return now.strftime(f'%Y-%m-%d %H:{minute_block:02d}')


def load_cached_vibe() -> dict | None:
    """
    Load the cached vibe from disk.
    Returns the cache dict if it exists and was generated today, else None.
    """
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        if cache.get('date') == get_today_utc():
            return cache
    except Exception:
        pass
    return None


def save_cached_vibe(vibe_text: str, verdict: str) -> None:
    """Save the vibe text to disk with today's date stamp."""
    try:
        cache = {
            'date':    get_today_utc(),
            'vibe':    vibe_text,
            'verdict': verdict,
            'generated_at': datetime.now(timezone.utc).isoformat(),
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"[daily_cache] Failed to save: {e}")


def get_or_generate_vibe(data: dict, signals: list, verdict: str) -> tuple[str, bool]:
    """
    Return (vibe_text, is_fresh).
    - Loads from cache if already generated today.
    - Calls the LLM and caches if not yet generated today.
    - is_fresh=True means it was just generated now; False means it's from cache.
    """
    cached = load_cached_vibe()
    if cached:
        return cached['vibe'], False

    # Generate fresh
    try:
        from market_vibe import generate_market_vibe
        vibe = generate_market_vibe(data, signals, verdict)
    except Exception as e:
        print(f"[daily_cache] LLM error: {e}")
        vibe = _fallback_vibe(data, signals, verdict)

    save_cached_vibe(vibe, verdict)
    return vibe, True


def _fallback_vibe(data: dict, signals: list, verdict: str) -> str:
    """Rule-based fallback if LLM is unavailable."""
    price    = data.get('price', 0)
    chg_24h  = data.get('chg_24h', 0)
    fg       = data.get('fear_greed', 50)
    fg_label = data.get('fear_greed_label', 'Neutral')
    buy_n    = sum(1 for s in signals if s['signal'] == 'BUY')
    total    = len(signals)

    direction = "pulling back" if chg_24h < -2 else ("rallying" if chg_24h > 2 else "consolidating")
    sentiment = "deeply fearful" if fg < 25 else ("greedy" if fg > 65 else "neutral")

    if buy_n >= total * 0.6:
        outlook = "Most accumulation indicators are flashing green — historically a strong window for dollar-cost averaging."
    elif buy_n >= total * 0.4:
        outlook = "The majority of indicators lean toward accumulation, though some caution signals remain."
    else:
        outlook = "Mixed signals across indicators — patience and position sizing are key right now."

    return (f"Bitcoin is {direction} at ${price:,.0f}, with the market feeling {sentiment} "
            f"(Fear & Greed: {fg}/100 — {fg_label}). {outlook}")

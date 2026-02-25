"""
₿ BTCpulse — v3
Dark mode · Live signals · Market vibe · AUD pricing · Hover tooltips
"""

import streamlit as st
import streamlit.components.v1 as components
import json as _json_beta
import os
from datetime import datetime as _dt_beta
BETA_SIGNUPS_FILE = os.path.join(os.path.dirname(__file__), 'beta_signups.json')
TELEGRAM_SUBS_FILE = os.path.join(os.path.dirname(__file__), 'telegram_subs.json')
def _load_beta_signups():
    if os.path.exists(BETA_SIGNUPS_FILE):
        try:
            with open(BETA_SIGNUPS_FILE, 'r') as _f:
                return _json_beta.load(_f)
        except Exception:
            pass
    return []

def _save_beta_signup(email, name='', source='', interest='', experience='', signal_at_signup=''):
    signups = _load_beta_signups()
    # Deduplicate by email
    if any(s.get('email','').lower() == email.lower() for s in signups):
        return False  # already exists
    signups.append({
        'email': email.strip(),
        'name': name.strip(),
        'source': source,
        'interest': interest,
        'experience': experience,
        'signal_at_signup': signal_at_signup,
        'timestamp': _dt_beta.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    })
    with open(BETA_SIGNUPS_FILE, 'w') as _f:
        _json_beta.dump(signups, _f, indent=2)
    # Also write to Google Sheets (durable storage)
    try:
        from sheets_storage import save_beta_signup as _sheets_beta
        _sheets_beta(email, name, signal_at_signup)
    except Exception as _se:
        print('[Sheets] Beta signup write error: ' + str(_se))
    return True

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import threading as _threading

# ── Start Telegram bot polling in background thread (once per process) ──
@st.cache_resource
def _start_telegram_bot_once():
    """Start the Telegram bot polling loop in a background thread.
    st.cache_resource ensures this runs exactly once per server process,
    surviving Streamlit reruns."""
    def _bot_loop():
        while True:
            try:
                import telegram_bot as _tb
                if _tb.BOT_TOKEN:
                    print('[Telegram] Starting polling loop...')
                    _tb.run_polling()
                else:
                    print('[Telegram] No BOT_TOKEN set - bot disabled.')
                    break
            except Exception as _e:
                import time as _time
                print('[Telegram] Bot crashed: ' + str(_e) + ' - restarting in 10s')
                _time.sleep(10)
    t = _threading.Thread(target=_bot_loop, daemon=True, name='telegram-bot')
    t.start()
    return t

_start_telegram_bot_once()


# ─────────────────────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────────────────────
if "selected_indicator" not in st.session_state:
    st.session_state.selected_indicator = None

# ─────────────────────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BTCpulse — Bitcoin Accumulation Signals",
    page_icon="₿",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None,
    }
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — Dark Pro Theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0A0A0F;
    color: #E8E8F0;
}
.stApp { background: #0A0A0F; }
/* Hide sidebar and hamburger menu entirely */
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
button[kind="header"] { display: none !important; }
#MainMenu { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }

/* ── Header ── */
.dash-header {
    background: linear-gradient(135deg, #0F0F1A 0%, #1A0A00 100%);
    border: 1px solid #2A1A00;
    border-radius: 16px;
    padding: 22px 28px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}
.dash-header::before {
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 360px; height: 360px;
    background: radial-gradient(circle, rgba(247,147,26,0.07) 0%, transparent 70%);
    pointer-events: none;
}
.dash-title { font-size: 1.9rem; font-weight: 900; color: #F7931A; letter-spacing: -0.5px; margin: 0; }
.dash-subtitle { font-size: 0.82rem; color: #666; margin-top: 3px; }
.live-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(0,200,83,0.12); border: 1px solid rgba(0,200,83,0.35);
    color: #00C853; padding: 3px 10px; border-radius: 20px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 1px;
}
.live-dot {
    width: 6px; height: 6px; background: #00C853; border-radius: 50%;
    animation: pulse 1.5s infinite;
}
@keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.4; transform:scale(1.3); } }

/* ── Market Vibe Box ── */
.vibe-box {
    background: linear-gradient(135deg, #0F0F1A, #12101A);
    border: 1px solid #1E1E2E; border-left: 3px solid #F7931A;
    border-radius: 12px; padding: 16px 20px; margin-bottom: 16px;
    font-size: 0.88rem; color: #C8C8D8; line-height: 1.65;
}
.vibe-label { font-size: 0.68rem; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #F7931A; margin-bottom: 6px; }

/* ── Verdict Banner ── */
.verdict-banner { border-radius: 14px; padding: 22px 28px; margin-bottom: 16px; text-align: center; position: relative; overflow: hidden; }
.verdict-title { font-size: 0.75rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; opacity: 0.65; margin-bottom: 6px; }
.verdict-text { font-size: 2.4rem; font-weight: 900; letter-spacing: -1px; margin: 0; line-height: 1; }
.verdict-sub { font-size: 0.88rem; opacity: 0.7; margin-top: 8px; }

/* ── Score Bar ── */
.score-container { background: #12121F; border: 1px solid #1E1E2E; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; }
.score-label { font-size: 0.72rem; color: #666; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px; }
.signal-counts { display: flex; gap: 10px; margin-top: 10px; }
.count-pill { flex: 1; text-align: center; padding: 8px; border-radius: 8px; font-weight: 700; font-size: 1.2rem; }
.count-label { font-size: 0.65rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; opacity: 0.7; display: block; margin-top: 1px; }

/* ── Indicator Cards ── */
.indicator-card {
    background: #12121F; border: 1px solid #1E1E2E; border-radius: 12px;
    padding: 10px 12px; margin-bottom: 8px;
    transition: border-color 0.2s, box-shadow 0.2s; cursor: default;
    position: relative; overflow: hidden;
}
.indicator-card:hover { border-color: #2A2A3E; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
.indicator-card::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0;
    width: 3px; border-radius: 3px 0 0 3px;
}
.card-buy::before    { background: #00C853; }
.card-caution::before { background: #FFC107; }
.card-sell::before   { background: #FF3D57; }

.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px; }
.card-name { font-size: 0.85rem; font-weight: 700; color: #E8E8F0; }
.card-category { font-size: 0.63rem; color: #555; font-weight: 500; margin-top: 1px; }
.signal-badge { padding: 3px 9px; border-radius: 20px; font-size: 0.64rem; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase; white-space: nowrap; flex-shrink: 0; }
.badge-buy    { background: rgba(0,200,83,0.12);  color: #00C853; border: 1px solid rgba(0,200,83,0.25); }
.badge-caution { background: rgba(255,193,7,0.12); color: #FFC107; border: 1px solid rgba(255,193,7,0.25); }
.badge-sell   { background: rgba(255,61,87,0.12);  color: #FF3D57; border: 1px solid rgba(255,61,87,0.25); }

.card-value { font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; margin: 2px 0 1px 0; }
.card-detail { font-size: 0.70rem; color: #888; margin-top: 1px; }

/* ── Zone Commentary ── */
.zone-commentary {
    margin-top: 5px; padding: 6px 9px;
    background: rgba(255,255,255,0.03); border-radius: 6px;
    font-size: 0.72rem; color: #999; line-height: 1.45;
    border-left: 2px solid #2A2A3E;
}
.zone-thresholds { display: flex; gap: 8px; margin-top: 4px; font-size: 0.65rem; flex-wrap: wrap; }
.zone-buy  { color: #00C853; }
.zone-sell { color: #FF3D57; }

/* ── Tooltip (hover on card name) ── */
.tooltip-wrap { position: relative; display: inline-block; }
.tooltip-wrap .tooltip-text {
    visibility: hidden; opacity: 0; width: 260px;
    background: #1A1A2E; border: 1px solid #2A2A3E; color: #C8C8D8;
    font-size: 0.75rem; line-height: 1.5; text-align: left;
    border-radius: 8px; padding: 10px 12px;
    position: absolute; z-index: 999; bottom: 125%; left: 50%;
    transform: translateX(-50%); transition: opacity 0.2s;
    pointer-events: none; box-shadow: 0 8px 24px rgba(0,0,0,0.6);
}
.tooltip-wrap:hover .tooltip-text { visibility: visible; opacity: 1; }

/* ── Card Tooltip (hover on card name in All Indicators section) ── */
.card-tooltip-wrap { position: relative; cursor: default; }
.card-tooltip-popup {
    visibility: hidden; opacity: 0;
    position: absolute; z-index: 9999;
    left: 0; top: calc(100% + 6px);
    width: 280px;
    background: #1A1A2E; border: 1px solid #2A2A4E;
    border-radius: 10px; padding: 0;
    box-shadow: 0 12px 32px rgba(0,0,0,0.75);
    transition: opacity 0.18s ease;
    pointer-events: none;
}
.card-tooltip-wrap:hover .card-tooltip-popup { visibility: visible; opacity: 1; }
.ct-what {
    font-family: 'Inter', sans-serif; font-size: 0.73rem;
    color: #9090A8; line-height: 1.55; padding: 9px 12px;
}
.ct-divider { height: 1px; background: rgba(255,255,255,0.07); margin: 0 12px; }
.ct-now {
    font-family: 'Inter', sans-serif; font-size: 0.73rem;
    color: #C8C8D8; line-height: 1.55; padding: 9px 12px;
}

/* ── Metric Cards ── */
.metric-card { background: #12121F; border: 1px solid #1E1E2E; border-radius: 10px; padding: 13px 14px; text-align: center; }
.metric-label { font-size: 0.63rem; color: #555; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px; }
.metric-value { font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; font-weight: 700; color: #F7931A; }
.metric-sub { font-size: 0.67rem; color: #555; margin-top: 2px; }

/* ── Category Headers ── */
.category-header { font-size: 0.7rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #F7931A; margin: 12px 0 6px 0; padding-bottom: 4px; border-bottom: 1px solid #1E1E2E; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background: #0F0F1A; border-radius: 10px; padding: 3px; border: 1px solid #1E1E2E; gap: 3px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #666; border-radius: 7px; padding: 7px 14px; font-weight: 600; font-size: 0.82rem; border: none; }
.stTabs [aria-selected="true"] { background: #F7931A !important; color: #000 !important; }

/* ── Sidebar ── */
.sidebar-logo { text-align: center; padding: 16px 0; border-bottom: 1px solid #1E1E2E; margin-bottom: 16px; }
.sidebar-btc { font-size: 2.2rem; color: #F7931A; display: block; }
.sidebar-name { font-size: 0.85rem; font-weight: 700; color: #E8E8F0; margin-top: 3px; }
.sidebar-tagline { font-size: 0.68rem; color: #555; }

/* ── Info Box ── */
.info-box { background: #12121F; border: 1px solid #1E1E2E; border-radius: 8px; padding: 12px 14px; font-size: 0.8rem; color: #777; line-height: 1.6; margin-top: 6px; }

/* ── Halving ── */
.halving-card { background: linear-gradient(135deg, #12121F, #1A0A00); border: 1px solid #2A1A00; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; }
.halving-title { font-size: 0.68rem; color: #F7931A; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 3px; }
.halving-value { font-family: 'JetBrains Mono', monospace; font-size: 1.7rem; font-weight: 800; color: #F7931A; }
.halving-sub { font-size: 0.72rem; color: #666; margin-top: 1px; }

/* ── Responsive Header ── */
.header-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}
.header-brand { flex: 1; min-width: 0; }
.header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}
.tg-btn {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(0,136,204,0.15); border: 1px solid rgba(0,136,204,0.4);
    color: #29B6F6; text-decoration: none; padding: 6px 12px;
    border-radius: 20px; font-size: 11px; font-weight: 700;
    letter-spacing: 0.5px; white-space: nowrap;
}
@media (max-width: 480px) {
    .dash-title { font-size: 1.4rem !important; }
    .dash-subtitle { font-size: 0.72rem !important; }
    .tg-btn span { display: none; }
    .tg-btn { padding: 6px 10px; }
    .header-actions { gap: 6px; }
}

/* ── Mobile-safe Tooltips ── */
/* On small screens, convert hover tooltips to click-friendly bottom-anchored popups */
.tooltip-wrap .tooltip-text {
    max-width: min(260px, 85vw);
    left: 50%;
    transform: translateX(-50%);
    /* Prevent going off-screen left */
    right: auto;
}
.card-tooltip-popup {
    max-width: min(280px, 90vw);
    /* Default: open downward */
    left: 0;
    right: auto;
}
/* If card is in right half of screen, flip popup to open left */
@media (max-width: 600px) {
    .card-tooltip-popup {
        left: auto;
        right: 0;
        max-width: min(260px, 92vw);
    }
    .tooltip-wrap .tooltip-text {
        position: fixed;
        bottom: 16px;
        left: 50%;
        transform: translateX(-50%);
        top: auto;
        z-index: 99999;
        max-width: 88vw;
        width: 88vw;
    }
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0A0A0F; }
::-webkit-scrollbar-thumb { background: #2A2A3E; border-radius: 3px; }
.js-plotly-plot .plotly .bg { fill: #12121F !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Plotly Dark Theme Base
# ─────────────────────────────────────────────────────────────────────────────
PLOTLY_DARK = dict(
    paper_bgcolor='#12121F',
    plot_bgcolor='#12121F',
    font=dict(family='Inter', color='#C8C8D8', size=11),
    xaxis=dict(gridcolor='#1E1E2E', zerolinecolor='#2A2A3E', tickfont=dict(size=10)),
    yaxis=dict(gridcolor='#1E1E2E', zerolinecolor='#2A2A3E', tickfont=dict(size=10)),
    margin=dict(l=50, r=20, t=40, b=40),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#888', size=10)),
)

# ─────────────────────────────────────────────────────────────────────────────
# Indicator Tooltip Definitions
# ─────────────────────────────────────────────────────────────────────────────
TOOLTIPS = {
    'Fear & Greed Index': (
        "Composite sentiment score (0–100) from volatility, momentum, social media, surveys & dominance. "
        "Contrarian signal — extreme fear has historically coincided with value accumulation zones. "
        "Weight: moderate (sentiment can persist)."
    ),
    'MVRV Z-Score': (
        "Market Value ÷ Realised Value, normalised as a Z-score. "
        "Realised Value = what every coin last moved on-chain was worth. "
        "Below 0 = trading below cost basis of all holders — historically a low-risk zone. "
        "Weight: high — one of the most reliable on-chain cycle indicators."
    ),
    'NUPL (Net Unrealized P&L)': (
        "% of market cap representing unrealised profit or loss. "
        "< 0% = Capitulation. 25–50% = Hope/Optimism. > 75% = Euphoria (historically high-risk zone). "
        "Weight: high — directly measures holder psychology."
    ),
    'Puell Multiple': (
        "Daily miner revenue ÷ 365-day moving average of daily revenue. "
        "Low = miners capitulating (selling pressure exhausted). "
        "High = miners over-earning (historically near cycle tops). "
        "Weight: moderate — useful at extremes."
    ),
    'RHODL Ratio': (
        "Ratio of 1-week HODL band to 1–2 year HODL band in realised cap. "
        "Low = long-term holders dominate (accumulation phase). "
        "High = short-term holders dominate (distribution / cycle top). "
        "Weight: moderate."
    ),
    'Reserve Risk': (
        "Risk/reward of investing relative to HODLer conviction over time. "
        "Low = high conviction HODLers not selling = strong buy signal. "
        "High = HODLers distributing into strength = late-cycle warning. "
        "Weight: moderate."
    ),
    'Mayer Multiple': (
        "Price ÷ 200-day moving average. Simple but powerful. "
        "Below 0.8 has historically always been an excellent accumulation zone. "
        "Above 2.4 = historically overextended. "
        "Weight: high — easy to track, historically reliable."
    ),
    '200-Week MA Heatmap': (
        "Price position relative to the 200-week (≈4yr) moving average. "
        "Every single Bitcoin bear market bottom has touched or gone below this level. "
        "It acts as the long-term floor of the entire market. "
        "Weight: high — the ultimate long-term support indicator."
    ),
    '2-Year MA Multiplier': (
        "Price vs 2-year moving average (and 5× that level). "
        "Below the 2yr MA = accumulation zone (only happens in bear markets). "
        "Above 5× the 2yr MA = historically the cycle top zone. "
        "Weight: moderate."
    ),
    'Ahr999 Index': (
        "Combines Bitcoin's price growth model (geometric mean) with mining cost. "
        "< 0.45 = DCA zone (strong buy). 0.45–1.2 = buy zone. > 4.0 = sell zone. "
        "Weight: moderate — useful for DCA timing."
    ),
    'RSI (14-Day)': (
        "Relative Strength Index on daily timeframe (14-period). "
        "Measures momentum: 0–30 = oversold (buy signal), 70–100 = overbought (caution). "
        "Weight: low-moderate — short-term signal, less reliable at cycle scale."
    ),
    'RSI Weekly': (
        "RSI calculated on weekly candles — a much stronger signal than daily. "
        "Below 35 on the weekly has historically been a major accumulation signal. "
        "Weight: moderate — weekly oversold is rare and significant."
    ),
    'Pi Cycle Top': (
        "Watches for the 111-day MA crossing above 2× the 350-day MA. "
        "Has called every Bitcoin cycle top within 3 days of the peak. "
        "When NOT triggered = safe. When triggered = cycle top imminent. "
        "Weight: high — but only relevant near cycle tops."
    ),
    'BTC Dominance': (
        "Bitcoin's share of total crypto market cap. "
        "High dominance (>60%) = early cycle, BTC leading, altcoin season hasn't started. "
        "Low dominance (<45%) = late cycle, altcoins outperforming = historically near cycle top. "
        "Weight: moderate."
    ),
    'Altcoin Season Index': (
        "Measures how many of the top 50 altcoins have outperformed Bitcoin over 90 days. "
        "< 25 = Bitcoin Season (good time to hold BTC). "
        "> 75 = Altcoin Season (late cycle, reduce risk). "
        "Weight: moderate."
    ),
    'CBBI (Bull Run Index)': (
        "Colin Talks Crypto Bull Run Index — composite of 9 on-chain indicators. "
        "0 = cycle bottom, 100 = cycle top. "
        "< 30 = early cycle (accumulate). > 90 = cycle top (sell). "
        "Weight: high — aggregates multiple signals into one clean score."
    ),
    'Global Liquidity Index (GLI)': (
        "Composite of major central bank balance sheets (Fed + ECB + BoJ). "
        "Expanding GLI = more money printing = bullish for Bitcoin. "
        "Contracting GLI = quantitative tightening = macro headwind. "
        "Weight: high — the #1 macro signal for cycle timing."
    ),
    'US Dollar Index (DXY)': (
        "Measures USD strength against a basket of 6 major currencies. "
        "Falling DXY = weaker dollar = looser global liquidity = bullish for BTC. "
        "Rising DXY = stronger dollar = tighter liquidity = bearish for BTC. "
        "Weight: moderate — key macro signal for global liquidity conditions."
    ),
    'BTC vs S&P 500': (
        "Compares Bitcoin's 90-day return against the S&P 500. "
        "BTC often leads equities — "
        "when BTC diverges sharply below the S&P 500, it historically mean-reverts hard (2018, 2022). "
        "BTC massively outperforming equities signals late-cycle risk. "
        "Weight: low-moderate — useful divergence context signal."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# Zone Commentary Generator
# ─────────────────────────────────────────────────────────────────────────────
def zone_commentary(s):
    name   = s['name']
    signal = s['signal']
    val    = s['value_str']
    detail = s['detail']

    commentaries = {
        'Fear & Greed Index': {
            'BUY':     f"At {val}, the market is in <b style='color:#00C853'>Extreme Fear</b> — historically associated with value accumulation zones. Most retail investors are selling or avoiding Bitcoin right now.",
            'CAUTION': f"Sentiment at {val} — neutral territory. Neither a strong buy nor sell signal; wait for a clearer extreme.",
            'SELL':    f"At {val}, the market is in <b style='color:#FF3D57'>Extreme Greed</b> — euphoria often precedes corrections. Exercise caution with new positions.",
        },
        'MVRV Z-Score': {
            'BUY':     f"Z-score of {val} means Bitcoin is trading <b style='color:#00C853'>below its realised value</b> — the market is pricing BTC below what holders paid on average. Deep value territory.",
            'CAUTION': f"Z-score of {val} is in fair value range. BTC is reasonably priced relative to on-chain cost basis — not cheap, not expensive.",
            'SELL':    f"Z-score of {val} signals significant overvaluation vs realised value. Historically, readings above 5 have marked cycle tops.",
        },
        'NUPL (Net Unrealized P&L)': {
            'BUY':     f"NUPL at {val} means most holders are in <b style='color:#00C853'>Fear or Capitulation</b> — the majority of the market is at a loss or minimal profit. Classic accumulation zone.",
            'CAUTION': f"NUPL at {val} — holders in Hope/Optimism phase. Moderate unrealised gains; not yet euphoric but not a screaming buy.",
            'SELL':    f"NUPL at {val} — Euphoria. Most holders sitting on large unrealised gains, historically a strong sell signal.",
        },
        'Puell Multiple': {
            'BUY':     f"At {val}, miner revenue is well below its yearly average — <b style='color:#00C853'>miner capitulation</b>. Forced selling pressure is exhausted, historically a buy signal.",
            'CAUTION': f"Puell at {val} — miner revenue in the normal range. No extreme signal in either direction.",
            'SELL':    f"Puell at {val} — miners earning significantly above average. Historically, high miner revenue has coincided with cycle tops.",
        },
        'RHODL Ratio': {
            'BUY':     f"RHODL at {val} — <b style='color:#00C853'>long-term holders dominate</b> the realised cap. Smart money is accumulating, not distributing.",
            'CAUTION': f"RHODL at {val} — mid-cycle reading. Mix of long and short-term holder activity.",
            'SELL':    f"RHODL at {val} — short-term holders dominating. Distribution phase, historically near cycle tops.",
        },
        'Reserve Risk': {
            'BUY':     f"Reserve Risk at {val} — <b style='color:#00C853'>excellent risk/reward</b>. HODLers have high conviction and are not selling, making the risk of investing very low.",
            'CAUTION': f"Reserve Risk at {val} — moderate. HODLers showing some willingness to sell at current prices.",
            'SELL':    f"Reserve Risk at {val} — elevated. HODLers distributing into strength; historically a late-cycle warning.",
        },
        'Mayer Multiple': {
            'BUY':     f"Mayer Multiple of {val} — price at a <b style='color:#00C853'>significant discount to the 200-day MA</b>. Historically, readings below 0.8 have coincided with value accumulation zones.",
            'CAUTION': f"Mayer Multiple of {val} — price near or slightly above the 200-day MA. Fair value range.",
            'SELL':    f"Mayer Multiple of {val} — price significantly extended above the 200-day MA. Historically, readings above 2.4 have marked overheated conditions.",
        },
        '200-Week MA Heatmap': {
            'BUY':     f"Price is <b style='color:#00C853'>at or below the 200-week MA</b> — every bear market bottom in Bitcoin's history has touched this level. Historically associated with value accumulation zones.",
            'CAUTION': f"Price is {val} above the 200-week MA — in the normal bull market range. Not a top signal yet, but not the deepest value either.",
            'SELL':    f"Price is {val} above the 200-week MA — historically, being 100%+ above this level has coincided with cycle tops.",
        },
        '2-Year MA Multiplier': {
            'BUY':     f"At {val}, price is <b style='color:#00C853'>below the 2-year moving average</b> — historically associated with value accumulation zones. Only occurs during bear markets.",
            'CAUTION': f"At {val}, price is above the 2-year MA but not yet in the danger zone. Normal bull market territory.",
            'SELL':    f"At {val}, price is significantly above the 2-year MA. Approaching the historical sell zone (5×).",
        },
        'Ahr999 Index': {
            'BUY':     f"Ahr999 at {val} — in the <b style='color:#00C853'>DCA zone</b>. The model indicates Bitcoin is below its growth trajectory and mining cost model.",
            'CAUTION': f"Ahr999 at {val} — buy zone but not the deepest discount. Reasonable entry for long-term holders.",
            'SELL':    f"Ahr999 at {val} — approaching or in the sell zone. Price is significantly above the growth model.",
        },
        'RSI (14-Day)': {
            'BUY':     f"Daily RSI at {val} — <b style='color:#00C853'>oversold</b>. Short-term selling pressure exhausted; a bounce or reversal is statistically likely.",
            'CAUTION': f"Daily RSI at {val} — neutral momentum. No strong directional signal on the daily timeframe.",
            'SELL':    f"Daily RSI at {val} — overbought on the daily. Short-term pullback risk is elevated.",
        },
        'RSI Weekly': {
            'BUY':     f"Weekly RSI at {val} — <b style='color:#00C853'>oversold on the weekly</b>. This is a rare and significant signal — historically one of the strongest accumulation indicators.",
            'CAUTION': f"Weekly RSI at {val} — neutral. No extreme reading on the weekly timeframe.",
            'SELL':    f"Weekly RSI at {val} — overbought on the weekly. This is a serious late-cycle warning signal.",
        },
        'Pi Cycle Top': {
            'BUY':     f"Pi Cycle ratio at {val} — <b style='color:#00C853'>not triggered</b>. The 111DMA has not crossed above 2× the 350DMA. No cycle top signal active.",
            'CAUTION': f"Pi Cycle ratio at {val} — approaching the trigger threshold. Monitor closely.",
            'SELL':    f"<b style='color:#FF3D57'>⚠️ Pi Cycle Top TRIGGERED</b> — the 111DMA has crossed above 2× the 350DMA. This indicator has called every cycle top within 3 days.",
        },
        'BTC Dominance': {
            'BUY':     f"BTC Dominance at {val} — <b style='color:#00C853'>Bitcoin is leading</b>. Altcoin season hasn't started; capital concentrated in BTC. Early-to-mid cycle behaviour.",
            'CAUTION': f"BTC Dominance at {val} — moderate. Some capital rotating into altcoins but BTC still holding ground.",
            'SELL':    f"BTC Dominance at {val} — low. Capital rotating heavily into altcoins, historically a late-cycle signal.",
        },
        'Altcoin Season Index': {
            'BUY':     f"Index at {val} — <b style='color:#00C853'>Bitcoin Season</b>. Altcoins underperforming BTC; typically an early-cycle environment favourable for BTC accumulation.",
            'CAUTION': f"Index at {val} — mixed market. Some altcoins outperforming, some not. No clear seasonal signal.",
            'SELL':    f"Index at {val} — <b style='color:#FF3D57'>Altcoin Season</b>. Most altcoins outperforming BTC — historically a late-cycle signal.",
        },
        'CBBI (Bull Run Index)': {
            'BUY':     f"CBBI at {val} — <b style='color:#00C853'>early cycle</b>. The composite of 9 on-chain indicators suggests we are far from a cycle top. Historically an excellent accumulation window.",
            'CAUTION': f"CBBI at {val} — mid cycle. Meaningful upside may remain but indicators are no longer at extreme lows.",
            'SELL':    f"CBBI at {val} — late cycle or cycle top territory. Multiple on-chain indicators flashing warning signals simultaneously.",
        },
        'Global Liquidity Index (GLI)': {
            'BUY':     f"GLI at {val} — <b style='color:#00C853'>global liquidity is expanding</b>. Central banks are injecting money into the system. Historically, Bitcoin rallies strongly when GLI is growing.",
            'CAUTION': f"GLI at {val} — liquidity is flat or slightly contracting. Bitcoin may face headwinds until central banks pivot to expansion.",
            'SELL':    f"GLI at {val} — <b style='color:#FF3D57'>significant liquidity contraction</b>. Tightening conditions are a major macro risk for Bitcoin.",
        },
        'US Dollar Index (DXY)': {
            'BUY':     f"DXY at {val} — <b style='color:#00C853'>weak or falling dollar</b>. A declining DXY loosens global liquidity and is historically bullish for Bitcoin and risk assets.",
            'CAUTION': f"DXY at {val} — dollar consolidating. Watch for breakout direction as it will drive liquidity conditions for Bitcoin.",
            'SELL':    f"DXY at {val} — <b style='color:#FF3D57'>strong or rising dollar</b>. A strengthening DXY tightens global liquidity and historically pressures Bitcoin prices.",
        },
        'BTC vs S&P 500': {
            'BUY':     f"{val} — <b style='color:#00C853'>BTC is deeply oversold vs equities</b>. This divergence has historically preceded strong BTC mean-reversion rallies (2018, 2022 examples).",
            'CAUTION': f"{val} — BTC and the S&P 500 are broadly correlated. No strong divergence signal in either direction.",
            'SELL':    f"{val} — <b style='color:#FF3D57'>BTC is significantly outperforming equities</b>. BTC leading equities to the upside is a late-cycle signal — historically precedes a top.",
        },
    }
    default = {
        'BUY':     f"Currently showing <b style='color:#00C853'>{detail}</b> — in the accumulation zone.",
        'CAUTION': f"Currently showing <b style='color:#FFC107'>{detail}</b> — neutral, watch closely.",
        'SELL':    f"Currently showing <b style='color:#FF3D57'>{detail}</b> — in the danger zone.",
    }
    return commentaries.get(name, default).get(signal, default.get(signal, ''))

# ─────────────────────────────────────────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    from data_fetcher import get_all_indicators, get_all_signals, compute_overall_verdict
    import requests

    data    = get_all_indicators()
    signals = get_all_signals(data)
    verdict, v_color, score, buy_n, caution_n, sell_n = compute_overall_verdict(signals)

    # Fetch AUD/USD exchange rate (Frankfurter = ECB data, no rate limits)
    aud_rate = 1.58  # fallback
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=USD&to=AUD", timeout=8)
        if r.status_code == 200:
            aud_rate = r.json().get('rates', {}).get('AUD', 1.58)
    except Exception:
        pass
    if aud_rate == 1.58:  # primary failed, try backup
        try:
            r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=8)
            if r.status_code == 200:
                aud_rate = r.json().get('rates', {}).get('AUD', 1.58)
        except Exception:
            pass

    data['aud_rate']       = aud_rate
    data['price_aud']      = data['price'] * aud_rate
    data['market_cap_aud'] = data.get('market_cap', 0) * aud_rate
    return data, signals, verdict, v_color, score, buy_n, caution_n, sell_n


def load_market_vibe(price, chg_24h, chg_7d, fg, fg_label, dominance, verdict, buy_n, caution_n, sell_n, total):
    """
    Returns the daily AI market vibe. Calls the LLM at most once per UTC day;
    subsequent calls within the same day return the cached text from disk.
    """
    from daily_cache import get_or_generate_vibe
    mock_data = {
        'price': price, 'price_aud': price * aud_rate,
        'chg_24h': chg_24h, 'chg_7d': chg_7d,
        'fear_greed': fg, 'fear_greed_label': fg_label,
        'btc_dominance': dominance,
    }
    mock_signals = (
        [{'signal': 'BUY', 'name': f'BUY_{i}'}   for i in range(buy_n)] +
        [{'signal': 'CAUTION', 'name': f'CAU_{i}'} for i in range(caution_n)] +
        [{'signal': 'SELL', 'name': f'SELL_{i}'}  for i in range(sell_n)]
    )
    vibe_text, is_fresh = get_or_generate_vibe(mock_data, mock_signals, verdict)
    return vibe_text, is_fresh


@st.cache_data(ttl=3600, show_spinner=False)
def load_price_chart():
    try:
        from data_fetcher import get_btc_ohlcv_5yr
        return get_btc_ohlcv_5yr()
    except Exception:
        return None

# Sidebar removed — content moved to page footer

# ─────────────────────────────────────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Fetching live Bitcoin data..."):
    data, signals, verdict, v_color, score, buy_n, caution_n, sell_n = load_data()

price     = data.get('price', 0)
price_aud = data.get('price_aud', 0)
chg_24h   = data.get('chg_24h', 0)
chg_7d    = data.get('chg_7d', 0)
aud_rate  = data.get('aud_rate', 1.58)

# ─────────────────────────────────────────────────────────────────────────────
# Signal Change Detection + Anomaly Detection (cached daily)
# ─────────────────────────────────────────────────────────────────────────────
import os as _os_ac, json as _json_ac
from datetime import datetime as _dt_ac, timezone as _tz_ac

_ALERT_CACHE = _os_ac.path.join(_os_ac.path.dirname(__file__), '.alert_cache.json')
_today_str   = _dt_ac.now(_tz_ac.utc).strftime('%Y-%m-%d')

def _load_alert_cache():
    if _os_ac.path.exists(_ALERT_CACHE):
        try:
            with open(_ALERT_CACHE) as _f:
                return _json_ac.load(_f)
        except Exception:
            pass
    return {}

def _save_alert_cache(cache):
    try:
        with open(_ALERT_CACHE, 'w') as _f:
            _json_ac.dump(cache, _f, indent=2)
    except Exception:
        pass

_alert_cache = _load_alert_cache()

# ── Signal Change Alert ──
_prev_verdict   = _alert_cache.get('prev_verdict', verdict)
_signal_changed = (_prev_verdict != verdict) and (_alert_cache.get('prev_verdict') is not None)
_signal_change_text = None

if _signal_changed:
    # Generate AI explanation of the change
    _cached_change = _alert_cache.get('signal_change_text') if _alert_cache.get('change_date') == _today_str else None
    if not _cached_change:
        try:
            from openai import OpenAI as _OAI
            _oai = _OAI()
            _chg_prompt = (
                f"The BTCpulse overall signal just changed from '{_prev_verdict}' to '{verdict}'. "
                f"Current score: {score:.0f}/100. Signal distribution: {buy_n} BUY, {caution_n} CAUTION, {sell_n} SELL out of {len(signals)} indicators. "
                f"BTC price: ${price:,.0f}. "
                f"Write 2 concise sentences explaining what drove this change and what it means for DCA strategy. "
                f"Be specific and analytical. No hype."
            )
            _chg_resp = _oai.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": _chg_prompt}],
                max_tokens=120, temperature=0.6
            )
            _signal_change_text = _chg_resp.choices[0].message.content.strip()
            _alert_cache['signal_change_text'] = _signal_change_text
            _alert_cache['change_date'] = _today_str
        except Exception:
            _signal_change_text = f"The overall signal has shifted from {_prev_verdict} to {verdict}, reflecting a change in the balance of indicators."
    else:
        _signal_change_text = _cached_change

# ── Indicator Anomaly Detection ──
_anomaly_text = None
_ANOMALY_THRESHOLDS = {
    'fear_greed':   {'key': 'fear_greed',   'label': 'Fear & Greed Index', 'prev_key': 'prev_fg',   'threshold': 15},
    'chg_24h':      {'key': 'chg_24h',      'label': 'BTC 24h price',      'prev_key': 'prev_chg',  'threshold': 8},
    'mvrv':         {'key': 'mvrv',         'label': 'MVRV Z-Score',       'prev_key': 'prev_mvrv', 'threshold': 0.3},
}
_anomalies = []
for _ind_key, _ind_cfg in _ANOMALY_THRESHOLDS.items():
    _cur_val  = data.get(_ind_cfg['key'])
    _prev_val = _alert_cache.get(_ind_cfg['prev_key'])
    if _cur_val is not None and _prev_val is not None:
        _delta = abs(float(_cur_val) - float(_prev_val))
        if _delta >= _ind_cfg['threshold']:
            _dir = "jumped" if float(_cur_val) > float(_prev_val) else "dropped"
            _anomalies.append(f"{_ind_cfg['label']} {_dir} from {_prev_val:.1f} to {_cur_val:.1f}")

if _anomalies:
    _cached_anomaly = _alert_cache.get('anomaly_text') if _alert_cache.get('anomaly_date') == _today_str else None
    if not _cached_anomaly:
        try:
            from openai import OpenAI as _OAI2
            _oai2 = _OAI2()
            _anom_prompt = (
                f"Notable Bitcoin indicator moves detected: {'; '.join(_anomalies)}. "
                f"Current BTC price: ${price:,.0f}. Overall signal: {verdict}. "
                f"Write 1-2 sentences of plain-English context explaining what this move means. "
                f"Be specific. No hype. No prediction."
            )
            _anom_resp = _oai2.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": _anom_prompt}],
                max_tokens=100, temperature=0.6
            )
            _anomaly_text = _anom_resp.choices[0].message.content.strip()
            _alert_cache['anomaly_text'] = _anomaly_text
            _alert_cache['anomaly_date'] = _today_str
        except Exception:
            _anomaly_text = "Notable indicator movement detected: " + "; ".join(_anomalies) + "."
    else:
        _anomaly_text = _cached_anomaly

# ── Send Telegram alert on signal change ──
if _signal_changed:
    try:
        from telegram_bot import send_signal_change_alert as _tg_alert
        _tg_alert(verdict, int(score), buy_n, caution_n, sell_n, price)
    except Exception as _tg_err:
        print(f"[Telegram] Alert error: {_tg_err}")
# ── Update cache with current values ──
_alert_cache['prev_verdict'] = verdict
_alert_cache['prev_fg']      = data.get('fear_greed')
_alert_cache['prev_chg']     = data.get('chg_24h')
_alert_cache['prev_mvrv']    = data.get('mvrv')
_alert_cache['last_verdict'] = verdict
_alert_cache['last_score']   = int(score)
_alert_cache['last_price']   = price
_alert_cache['last_buy']     = buy_n
_alert_cache['last_caution'] = caution_n
_alert_cache['last_sell']    = sell_n
_save_alert_cache(_alert_cache)

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
    <div class="header-inner">
        <div class="header-brand">
            <div class="dash-title" style="display:flex; align-items:center; gap:10px;"><img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFAAAABQCAYAAACOEfKtAAAjU0lEQVR42u18eZSdVZXvb59zvu9OdWuuypyQhARIiLQQZRBIpbUdHi1KS5WtdovDk7RDO7bdauurFGr3c3oKNiKoiN2taF0QAUERYqoIECAJJCFVlTlVqXm4t27d8RvOOfv9UVUxIGiAoPRa2WvVqrVqrfruOb/vt+e9L3BKTskpOSWn5JSckj+P0MvtQMzHn4mfdkyiY3942Yj68wPWKjo6OgQ6OtEEWCLY53q/DIiO1nWiqakJaFrNQIt9OYL6JwFt82Yo/j0NEGBmYt6ZYL62gfkHDcy3NzIfqmJmAchneVazbG9vlvxn0ib6UwOHVBtRC8ysApRHrzq9PHj4IjM5fi6H/lms7XwTBNUwOmENwFYSc8RnGcnIWEVvtKG+p27VK55A1dt6gbU7iMibvUp7+5USqRRaUrDH6f//fAC5tVVg9SxwBM5+ZHm5d/cVwWT68qBUeFVElKPsa+gwROAZhKGF8Q2sZYSeAYUWbABjJKLRCBacXoPo2efBD+hQGKEHnjoweN81Ldse+nUB49NXYnA7JFpg6SUGkl561jVLopQBAP/I+14psj0fC4qZK11TSJRyAQolC9/XxlhmIpDVTGQNoJmMZljNYMNMDJRKYK9sOCYMxRMQkgSpZC3chXMw4jsTe3aNbBrYNvJfn38A9wGkAQYzxNPt6v8QAJmZACIi2PLkv5+mJjZ9gfPj73bYU7mJEgpFT4eBJbZWOJKJrYGUgsmwtUHIMAyrQWFgyRgg8JiDAFwuWQCSGEKwsay9wApA1C6oFjWrliCdA8b27tsZd71vffPz/N8pEob5Z/Klcjh08oEDEQkGLAABPfy+9yN/8CuSp+q8dBlBOTSh5wkhNIVeiGJecy4b2syEpcmsFYWihQkByYyoIiRihKoEoa5aIOIaWEMo+0CxxNAhG80g6QiRiFmOOWzrzzqNkstWitLBPXCKA4+qCP45/g5sAYDWVoi2tpPLxpeEgc3NkLfc8v05cf+hryM8+g47Oomw6GsThlJwQEHBw4F9Zd69s2yPHNUyXwLyIaMYYEQzdgsHu6MKh12DoQoXurESvKxBusuWisZkXCyfyvJ5IHFePG6rw8Ci4LGprlFU3yhFJB6iYmWDVWdcwdI2ShPuYTlnznXAt/+ZiIL2dsiWY07sZQTgtMpupExm54LKis/dJuTAcmF+XBf2j1ibK5GwZZJ+GfsezeHu+4rmqcOhDAzgC2TcKN3pxDjVkMDWazuRPZHP67wiPi9yOt4US9gPxhSvLZQs4tXS1Mx1ZKzCIr68HrTyg0a4lRb9tziFI+OdE132b5d+pG+kvRmyJXVyQDxpAG7ffqOzdu2GsJi79W/iyUW3I7gL4eiDBrmidEij3JfHb++Y4Hsf8pA1ILg0QRLXRxJ8082PYGj2Oa2A6FgH0QRgdePTbVbDqunzdgB2VhW5HXJouOq92povhF6wuBCwSSSkiMctVVQHcJeco4eGktz7m4ecUkTtL8jKt77j2kzPyQKRTg772iVRi2Gv4yzIX98Hc2SenhonKk5IGRj0dmZwZ2rMHBw30roEL+Qf5gNsTHXjKEC48epzHZwH1DywwzanYMHNoqNjjJoAdHQAHW2dtg1Pt10MENohZmNKvj9ZNz7kft2f8t6TTnusogrxqCBdKqPqlecg7UV07/2PK3bU4LgXX/eem3KHuBWCXqRNpBcPXqsgarOFwvZ5MffWLUIeXW6yeYuwIETBw7YfH8UvfjFmQkUSDkZLmjd853HceSz1wAlfQDQDlMLvs2ZzK9T6NmiAkL978cdzA5PfzKSLLF0Jo4n8nI/5l5yDocGyHn50v3Ir1X6vofbSt/zr2OiLdSz04u1eiwDahfE/9YCM9F1qpgoa2lOCIjhwyy7c8INRHcSlkmR35UNuvmUnDrSug2rrhOUjrW46COs0ShEXE8kHvvkrrzjn7L4r373gYnjjNSqeTBztKvr/cc2DW769zRsA8x/0/h0bIde3QXsPrrpy8sDIrenBjNQsQZLIhhqLLn0lDjzar8OxCSUTTudFzkWvS3V3cnPqhQfc4sXxr0UQpYwu/MuXZWTgUjuVD4lLCnBBg/sQ9I+aaEKqSc9u6c7za2fB27ixFQCsqdRvrpm3Z181deypifTsrIiZpwZ/ta2rAkfvr3AH2qPR3h9WI/eTct7rumq1uu/vznDeO/PSf+/FE4HXt0FvvxFO9NLu22pWzm9pWNxgHDJWKbB0BMZ3dmP+KxaqngEVTg7rdQ8VH/lqS4pMqvmF4yBeOPumMwwOvnOJcI78E6bSmk1JicBB+Tf7MPaLPjM0JqWGfawY8mWb9iLd3AzZ1gl97CHWiwq/P4GRvigmR6CicIq+WWaKUxzmPYOposl7nqmSXHlWjX79vIT+DE+jx8dy62fI2g0I+cbznOgle+5InLlyw6LT62RlTJuqGgkHPuLeIM65eI7Kl1lXRc0nRm6I/1VLCqa9/VkqFS8VgNM1uxQzs2uKW64XNksm0CRJ0K72o7ju60ftLx8R8sl+20dO9G/u3NtavPfa0yPt7e1gZoEFGcntzRKhzxgtcTgZGFsGYlHJxhjLxCRcKRFxpWQjzz9b6UWNwlywGOME8G83typub5ZEbc9qu2jDjpBvPM+puODhm8WipTckq+KqlNdGWwcje8cxd65DeR0VnY9Z3PFL79ubr0K0qwv8QkzaC2NgxzpJBGvS798gY4Nr9FTBCJdl+qkA373pMD+eFfzwoA0HQn7X1x4pDxG12f/1sYM+UYshIksrv+1TS8pI5RoUfGK2BGL4BUU1lQlBERdwFTjqgpLzsGjlYnFe0yK5ZO2CilZArF/fpqklZYZ6L181ixk/k0FX79DcDpm4+LJP2trTnopJkmHINgwFdCaDJavrxd4+mMEJPuOep9RH2tpg21+AKtMLcxwEYHOVHfh8N8TUXAvF0o+J6z7Tg/sezZrqKiFLmq+5s4dbDz/+vjMWz/OvMN5ITC16wwJ2li+yQz9Oc3kqQhRdzf07zjDssROLUN7OhYhWIVmbB4QBhISoOA02BIznQYdWi2jl3nA8sj9CwQRW/uV7HLH70xT77nVgBrfy08ISbm+W1JIyQd9ll+S3buuc6B1jGXMFmQCJpcuw/f4RW86USLlycsl5sTPP/Vhhgvn5Vb6fP4Cb1yla36m5/3Ufg9P/rXDKGieu5NaUjy9+47CpqBYyZN5zzqsWvwo/6gs+sOnVb1tAA+2wHnD6QsCNA0OHAF/D+hqeIch4DBSLwYkyICWMjAJuFCAJkA+hHJC1IEFAVAGJRkCdB4z2Y/K+n3Ewbju0in954ScnN/FP3yapJWWeaavLj7/ix5H0gXcW8qEhZunUVqLoz0HPXXtNVaWQYznxhdfepL+0eR3U+uPt9MkEkBk0XW7b75q9b9kjneJyA8HBmBKf/OgAeoY9W11BImR+07378WsAGLj7tMtrvfGfGbBx41axkkr7kkVEkIg6RIKESrgQjRVAxAUcAUhloZQFBBASrE8EhmS2YLaWlGQ4UZaJV8qhux/Gvlu3ku8Bhw/jox/eg28fn2UwQwBgHFi/rLR/z+4wnY5pVlAqJPfM8/DkT7ttvq9EFugbTeGs9wL+8Y7qJAM443mH33AZ/AO/1MXQqrgSv73Vx1e/M2REVEgv5C2b+/jSG2+Es2EDwr6fzn9zgyjcVSxpCEcgWqOgXAIcCUgHIsLI5R0M9YawUiDQAgQCkUKsQmHJWQnEz1oIWxYWzALSAWQcYAU4NRBGoLSrSwduXBTSkyJ53tI3VFff/JtZ9Z0BURLBDN4657v1NLkhnYNWpJW7YAlip80HggFDUSVtNHFl9LTdt2/eDLV+/Ymx8Pk1lVIpAAQ9fvjvVUXAJNiWRwLx4IMZzGsEOQ4jXeavAcCOm6b/ZceW/COH9pX/cWLULGGD5Z9qS17WWKncgATYWqhKF33dEXzhQ/1IJsChD7KVeDiSwP6ogbekXgZv+5Q4e83bznmtMcREcYKIAMyAEYArkcuMq/jgEbPwjCTQ0fUVbscmNKfs8cdmBj12nfgeR+UHwmxZhgowug/UOAdxo1mpgDEw9XcAbm9qOvHMhJ6P+hKBefKqam/br/arqG5QMcG7Hzf01esnrXBIaMvdK2txTlsnzLP3JAiF3zYcSVTRaSFLC5LCqYtg304H//7xvYglhbU+i0CKS2/pMVuOz3xHd/zVLxrPPestJrSGCBKwsCaAEmM4urkPn3nXLlgXXF8BHinilbcPYncrIGZzaGamjRs30j9e/N+PJesja/2yMY6C1BTDr7+6k20ZpBXGHprAmTc8hMlpX/LH1fjEGZiCAGByj2y50MkXG4rK2orKiNi+06IUwNbESQQ+/6StE3rdOqjOGUPMAN10HtRQBbiycYFD0AxHgsgBHAeIEFzHYEUDo66O4QfAZKhjzc2Qc/NQb3rT6bjsE4f8RDjVav3cm0lawUwgUwBpDwjHUZEkzDlNoXfS2gEDaaP2TAC7O56Wa2+UbW1t+jM9l//KPfMv1rrwGFDg0jgyqotGctomY9RYD3sugE2pZgicQLXmhAHs6Jpm60RvZn0sCBEKawMvLnoOlgGCLHtsCLgbAJo6YTt/R3HmHdAEcOuqSiEri4ykBOACygUq41CRMjIloOwACQWAYVMpmPZm4E0fPWD5Y0SJxRuGtLcpr5zxKh1Yhj9JXC7D6gDxSA3OX0Y427eojhFntRB3H7JoWgd0zh4k1c0A4A12bY4sqfkCU0wwG5AknPeaGqxZnLZubUSEAS7+4l+WNjV/CITUSbSBTW0wIMLEuH+hKlsoBzQFArS282tIBBaHidEDAG3PRf3ubmD+xYzGBCiMA4gB0QoItRdgIF0mFGChZ6YTUgCasZGYWwGcGaehu6M8tReACw5DGF9DcYADPYxtwxrxSqJKTxAZjOGZ9cTmlAUI+S2HdlWc+/q0qjmjzqLEAg6F1Yvw61+O06LlFoWcOX+aMSdmB9Xzsn8jl1Y89PWtS/N5i1hSUpgnJMnYufUkPMKTn78H4R8qVA4DTJEEQ9YBtmIGZgcgRnVcwHUECEAoITdvvliVdw9KdHUznZ0KguKiy5zYcCTszRkOpLQBgUONXEi4NTWCJ4bYVuQECHYkLPJ2ALP94WPFBgYTtSGTXX/vQUX31ZU9a92II0W+jN5epuKEj1KAFTdeDYfaEGK2R/qiGbhx+kFP/WLPQhPaOaG2cMihoGSQdIHKGKFk7S4A6Bp7Fsc0E1h9vv0TSsTrXWAvYMbAgQc4AMIMXG0hHQtjgd4nMbV+facGoIFDCPiOi+ToLdeYwhGGdIUteyhPMlzFePwxjb5+3y6sJeModiaL9LW7D3KuuRky9cwX2Q6BFhjycweFKJ9vpyxDESojLqqqJS1osLASjZ5APYDhmazkxTMw1T0Nij8ZLnIFq0DAxhJK5LMGrgRFJMMKHMSzlOGPR7Dyggtj5Ig4vG1AdpDIL4EnCkgmanDm+jOgHUsRAH/9iSVX3HTxisWmMF6nvOxrsGtjM5UPO0FBsSlb0rkAjiRs2WTxX3doqHkkohZCG/7RHbv4WxsJoi31LCrYMH2PaH2kz60WcLMMKRg8LpDO+ZROG3YcSmrGPADDLS3TjvNFAzjbi5g/1y6JVAG5AqxTq8TEpEFNJch1AUtqFM8Ze06/xipTLOmRm0qww+DxgLnoky4HiCY0Ln9PJaAN2UBD0r5P41AP7KSH4kQe6cBAOBHWQUhCKbBTiU335nHnPQFHkhKNEewcLNhrbu3BL97YAtn2nJdeB6ATRO4ojIZlAzAjEhNoaBDo7wP7IYlCmRsAoHnGDr9oAJuapj3DnLPEHBlxUVc0KIcu1M4CqhMQEAQldAEAmlc9t83olxma2zcEBJPwMgwvq2GZQXYcKjIC4YjpqxsOA8/aoEyAFCh7SjFrCWZEKgScqiRWvGYeXscT2Hr/MJCl4vvXx8ytPWXRkoL5Y70Orluaw+LTIUIJIQkin8FZK+7ChWcrNh4jX0Ty37b9jjgnLRMppzkaFQyvCIQOw1FANAYoyfBOoBC0aBEwdH+JomGAvM8IfQujpyO1qmoFx52xORaO8QVgLAQzImSQLYKlIkbJCP9IL85cFMMr/ncjrbngDDx415GLC4XyxU99MdK55JX8QfrroOcPgSily8iPggsBIV4BLhQRrXaw+DQHbpWA8XQCXy0dI86LBrCjY/r34GHSkZJBdkqjYhFQUyPgetMqmrMKQPhHnpSj9EQIkw5hHYlyieFEGEWRwM/vLyMMLZuAKeHyY0JhgAS4vlr49bVYs6BevEJFmMqWWUpF44MhasIhnLM0gb+47hLr7X3KqkJm3cSBWMfEA69eT697qPu5QNRetkoOHEQwWGBZ4cCZU4f8lMT9v5xC4xwHAU3botl7nzwGlqzWHuCHQJQBN0KIMNh1QRKcAACs/kO0H0Y+q1GeZFjJyBcBxwXUvBgODxcQccDSgroG+dO3D2MmlTMAIH98mXzD2efQdfGYWV7whJUCYmqCcLQrg0jvLrHgVSuESL4mXFRb21jM537a3ozzsZE9bqPfS8lEMSREorBkEU5aOCsWoOQVMDQKZHIGOc+GLwmAzJiEZTADBIOjowJjB2GrKlkWieuP1RueU4ZQLlvkigyQhR8SDAhVBCxvBFzJIALm1iP29oshAcjmZhg0wxIF9/b9TePeIBc8nh/J1xaU4IhjyAoX/tAEqCeCsZ4eR5SndCzCa+YsEC1E9KPNrVBom/Vu02lJmBlvcOoM3AYXZtJHee8haD9AdSUoHme4SWSeO6J4ASX9ptXTDyKS417JIigzhSWGdR2M58ETBcJkjlc8Zxx4nBgDeD7gBQxrLayxM1H6tE2NTMfVdiYYN9QCQwTef+3pkSXvHzvceP6y7y5ZrEgpa5gAaxhSCJQmchgraFRWWFTOIU7ERDMANG08ToXHZ5pRgV7GI2WYYgiKCdD8Buzr1XxwDOLgCHh4DBM4AQ984nHgzO/G09xhNTcCr6xFYp6AjsUx1JVGXTXgW37FH39rExwE5lhkCABsAWZG3gcKZrpMWPZ+l8rNyoqPvlK3Zg6KSFw/Wr/QBRxLvg8YTQiKBM8LUVUZgSEIWCYl7fJmTNcBZzMKaoElSRjut6dP9ZRghKDKJIHmZdDTb5EvAkJyMfSmU8FVqZNUjWlunn5Q7fkrhqO5wwH8sgtXsI1VUvoJiGQS8C3OPW7y6ekp0PGcZMskAEiCJIaUgJRAQROMZrgK8M2zHTyFjQCyY1Ou9Kc/ggTDagtSDMFALEJ4dA8QSQD5MjtdqyDRfawyTURgqy+r77r20dMnphieYcFSQGcFpsqalUMEy8OVFRj/gzn98+7KzTRZoos/3n/ggWzvwfsL6LpjgpVw0LAwTmHZIkpYvny7uxIAuPUZatwKml1fqK8iLJpDmFMLzG0knHUWoTLJqI4CcyoI85JAY410AVDzTDmMWyG6NkJSG2x5Sr8pOxkiO2W4WGSUfSA9YaEhMDRhkCsDhQAoG57s7kZwLBWaLsfBe+jI2Qkb1kQjZCMOU64AjGQ1IJnjCYKK0f6bdiBsxUwr4GQwkADmZkiitwcHvhXdFnVopS7D6mIg1rx1HlFwVKM24sB33oyvBj1ogsBx4QO1waINePS/9jvnrBXRGAG+EMQRiWi9wN4ugmsspAQLAwhjGACnUkALwGgDAwj46BVv7P3lpndnJrQ1EJKYwZYQakZDUuKJQwE2PQkbjYICxhMzuYfqBPRsGleYKDUpDhCJkYUwIlLl4lBGQ0TAkQQgDT0CMLAOAp1/vCJz4n3QD033WU5/VcXWhRdJnHmxQMOCKZjIIpQHNflHNPIHy1cyM6HpuFRKCDBzZD9z5Py/+2xN2VbEho8C4wNAdhAYe8ogzAOZMIrD6Qhlii7i9XWKHAftzMzMivlDS8buP+fz+3/+2zvG+vKupyXpkEkboFBkxBISjz/p456tHqeLhFyRKV/CLTN+d5pF62GY22VhKnxrJhtCRoRgMCgaAaIeLlgHec4FwNrXiI4T9cDPt6QviGCnNq05o7h/327J7BIxV156OT1yw68wOlDmaFLY+KLo2jf8W2nX9hvPU2s37Ajz2y9dL33+fmHKsyLiRHI9exeGEznyDeBGBRxpQTV1KIsawFp2YUlGaEIoZ4RNYMNSydXF0kIVliomMgEMFBvDRMwwhiAEY2hSYLRk2cY5TCTg9o/iW1++nT8xG0hze7NEc8qWn1x/4aHf7np4om/SRuKOYGtQSNYjVz1hFyyGKJf58LIL7OqlS+FhugN58kr6RLCtgKh6Xde+Bz8V2S794MJyztg184/ImvNX44nd202tQ2r8UPgPAP5hbM8OAQATu56ojmWKy0oeo1QGiiVix5UcaItQM4QkCsbH4ThjYAOaLDMUod5RqFdqenUp0AzNZNiRgi3DaGYTTqeQ/RNsH+0yXD9PqEoDN1/mO790G39aEcSM6h+rB6bvTX+gRhWARmGlNCJeEcXDowEcaWwuI8VUnn/92qXw2tshW+jEhi+fVyDdtA6irdNaFVe3eXnvorwmHNiyFyuuXIe0FvLwAcuxKP/9v7656iuPfXuqDwB8D2x9hXzRggTgKFC5aKAcQqHIyBUBIjHtJhkgAYCJoxFwVDAScaCqkgiWpbYMMFAQQIEJh0cZewZZyjrCWNGW+sdx7c07+Aufbp+2XW0AM7cKUJstj1693O2+7+2V8wKune9IRzEmPBeP/6YIfwcEaeZSQf4E0H8kGXgRAHY0waITWHBm9c9GPO+aRMImilNl5vQgrb98CXWkjphFc0U8Gi1ufC/oKgbTo2N6Ittrjvg+w41ACpCTzSNmQoYToZiKIhJqhnIESkWGDS2qq0EugWoaAJWMwK0AdMkgM2DQP2z1UA42JzgcKyMrEjgSdbCpppJ/0rYF+4kAy7/rqHV0dIj1gB55as8X/KdGYpmsNNpaWVkhsGOUMTwSmppaIXzD22/Zqh+5hUD0PEZ/n/dox3TJnszmf3J+oArh+7JlaOUqtfadF2D3bVtRKFkTj0KYqPPaN37T39wMyCcBVQ+IAQBRwFlbh4rH09DXvtt9f20V/1vvsNFzF0bVrx5mdB8O8M/vVPCmApz/mgi2TVThBz8at/XVEKFnB/p68MapOfCdKvgXLEf2a3chf/x2QOq4Na9jszHpj7ym77a7H+zb3Qc37gjBFirp4r8fssiHvklWkGTmd1x/D346M/ypXxIGAkDXKjDAdDSLrxQH6J3WkGuCkOmBPlp20dn4+bd2UrxGkrXh9659Y+25mV9nCrcR/IO/M8flQ5PIMQGvfkPVVP+TU2ALhCEgJMCK0NAgMB4AmTTDC4AcWThMUFEq3ae5CwMABoAtXdMkaF0HiSbYtjaYp42hpABmdgfuvuiG9IF+oVxpmS2iCYE9aYl0vmxqaklog11zSritFRDPB7wXNN42OwZ21feD/Vrx91xphYhLc3DrURhSOOcv54t81piGKlq+oCH3vTYi+90PwGlthQCmzdy2G+Awg7gy4TgktEOsSZCRgnRCQqezbNKTbMbS1sSkY5IONBsYYyH/cTkirdPz0nI242nrhH7mnPOOHVcrakmZ/J53fSPf3bNmbNKaQhkim2VMhQ66B3zUNhCSSVAyyZ9r64Tubn7+GvmC9oW7VoFbAZFo4C+aCXp7BXGDiArbdc8use6Dr0WNKMmxvVk9NyJbtrxH9VxyU7hx8zqoNsAQwLxyHRM6uVCbjFYtH1PFAquqeqAqSogLgkMCMQWQAZY0SCyrg3RjBDYcrlkK3XIQ9g91zHj7jQ6t3RBy7usfzHfe/JHJsaxWUaXKJYNkUmF7r8Who6FJJkhOZviunzyMe5+1CfVSATjDQtnyQ4x/4zL6mCjjVl+TiUxpcd93t+L1H7oUp614SMaTBZ2od1v56mieLsx/gzdDoQkGGzstAJTS/GguxzdrKeXQUFArtZhSsBOHj4ZLSpPkZPOG+zIT4bxq2h918ZTM8Y7jWqbPDh7f6BBtCEM+8BaMf/l6PdZtKuuVNBmLuCIM+4SdB30rBShfQsbL4kMA6EQKByd9Sn+2B3zdG3FzUoj3yojQtVGtFq2ZizUta5F54Dc8OaIth1LuHaLPXv7D8P8CTK0AteHk7qwxg7DjakVrbwo9PnRZZPI/bg92/Icz2cs0mWYqFy3Gc4SfbmcezbKJuFBW4m/v3I6fvVD2vfg1B4BSzRBjQGxVjXjkLy6MrYkuSRjhaqkWn4XJiaW4ty3FU5O+XbpEyep6cdPFH1z8UVp50N+8Dqrpw+Bjra9mcKoFdH0K9OF2cPP0zDJSq0Fd18+csxP22YBnbhUbqQ1tgGW+4R0YfuIWb9sP3fRRtpNTEERAKWfxn1sJ+9IcVkTh5H3+6gN78C/Hz/H8yQGcqbwIaoPtusZdseL1NQ86q2vmWkQNReskqeUoDUxh+/cexu6tAyYaJ5kpqUct4R8++5twFzC9JNNx3OrW8/vsVtGBDrG+rVMzM2Hyiv/jP7l/Y3ZvN6ZywvohiZLH8H3G3duAvgBhMgGnHHD7Tx/C26+88ulhz58FwOl4C5JaYLq/FLtgzjxzv6tQoRMRIx0thYwijJ2Jx3YG6Pj5HhNO+TKaoPKC+e7/u6Cp5tpzPzYyDkyvoqIDAk2wG9vAzzVaxgCBW+n4rw5g/ty5xa0Pfn1y+971gwcmrIk6ZK0lxwGCkPGLbYxhRlhbA6dYxl3Fam5OpaBngHtRO8Qnbdlwdt3qwU9XrKt3vTuU5ZqCIW20Udpn1KxcDJ6zAEcPZmwke0QsqwtQs0ANV1RGvo9YxQ/pDeNHjr/PrHnoWgVqwjo0bWxkYBUfv9rAfN3S4q57Prlv876rR54YdMul0ESqlWTm6RZBlLBpr+UxAVNfC6WB1Nmv43dt2HBicy9/UgCPB/GJb1SfkygUU5J5xXCGtedBhmVDwlWYe/Zi1C9t4Joq3/oDA3L4YBoHBzhfBh6IuLinuhoPn7YSvUvfC+85tgQc4LNr+zueuOrIY/3vyO7rrxweKCCAMBUVQsYiDAVAOxL37NZmwGcZcQAr8O37d/FHAZxUJ3byN9Zn1Hnnd+Y0VmTTN6WHzVuOjgJlK3UQWlXOWiSSCgtWLUT90gaGVLZQyklTysHLl5DJBtoY9CuB/kRCDkeSsalYZZJq5zaKmgbVaLOFFUe7x8/s2zOOwcESPAvjuFJYDbIWqIwDa15dYR/YE/Avt5alG8VUSeOTPaO4+bj7nrTV/5dkY/34Ebf/bBYfmcrii0pSdSkErCVTEbWiscLS4oXA3MVxVM2vYuMkbL4cw2SOpbYEKRhkLJYs0Kiq0vDGfESXBCgfzePJBz1s30s6HwipNRNPWzNOJGGLijBprNzbz8iU6R4o/tT2Xux7Zp58skS+FACmusEzPRDx8e/wY+tX8m06QLUA1iyoYblorqBlyx09f1mElaNJF/JUnkiL3MCYyPaN8UTvGKePjtmh/eM27qdtY+2k7dubt9qznFwQQ0WUyJsywvMAGNhkJdlovZR9JRIDOSuE4Celi0/+pgefG8oi3QzIVPfJW/N/0ZnICRZgebogAtmSwiGAr2q9hK+vA324toavWLmMk7IamBwVSOekzeWFLfuAT0ysQEQgFWHKliRMRHKiwWJgb8hxh7iuju0ZS0gqIjpaErI7bfH4Nh0WPe5c2IibB7cj1Tk9KkZ4jh3jl7UKP1NaAbG6GTSr1m+Zg9Peeol42/KFuMxa8SrH2goSDBaA1YAfTI+P+AGQcAivvUxBzhN4oj3ASA7IlIHuQcbhLNJHM3hiJMP3GYtfHQ3Q/YzSlnmp7/Yn/eqn1laI1d2/AxIAXleDxRecjlfUVWG1krTKdXghGLUgSlgLqojCW362WwiUyt3z81Jmay+P9GWxvx/YA2AvMN3Dnb1PczNE6k/41U9/FmkFxOZWqKd/1d3viTPzQ8/16ommn7Vu2hSJP8dd6OUA5upmUMMYqKkRjFVgcQ3s7HY/YbpED4BSLaDrx0DoPNau/LMzjV7GRKWnZ3Cn5JScklNySk7JKTklp+SUvHzk/wO6bjFF9v9xLQAAAABJRU5ErkJggg==" style="width:36px; height:36px; object-fit:contain; vertical-align:middle;" alt="BTCpulse logo"> BTCpulse<span style="font-size:0.55em; font-weight:500; color:#F7931A; opacity:0.6; margin-left:6px; vertical-align:middle;">.app</span></div>
            <div class="dash-subtitle">Real-time Bitcoin accumulation signals &nbsp;·&nbsp; {datetime.utcnow().strftime('%b %d, %Y %H:%M UTC')}</div>
        </div>
        <div class="header-actions">
            <a href="https://t.me/BTCPulse_app_bot" target="_blank" class="tg-btn">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="#29B6F6"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.833.941z"/></svg>
                <span>ALERTS</span>
            </a>
            <div class="live-badge"><div class="live-dot"></div>LIVE</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Overall Verdict Banner — PRIMARY SIGNAL (top of page)
# ─────────────────────────────────────────────────────────────────────────────
verdict_bg_map = {
    'High Historical Value Zone':       'linear-gradient(135deg, rgba(0,200,83,0.12), rgba(0,200,83,0.04))',
    'Value Accumulation Zone':       'linear-gradient(135deg, rgba(105,240,174,0.10), rgba(105,240,174,0.03))',
    'Neutral Data Zone':  'linear-gradient(135deg, rgba(255,193,7,0.10), rgba(255,193,7,0.03))',
    'Elevated Risk Zone':   'linear-gradient(135deg, rgba(255,107,53,0.12), rgba(255,107,53,0.04))',
    'High Risk Zone':    'linear-gradient(135deg, rgba(255,61,87,0.12), rgba(255,61,87,0.04))',
}
verdict_border_map = {
    'High Historical Value Zone':       'rgba(0,200,83,0.3)',
    'Value Accumulation Zone':       'rgba(105,240,174,0.25)',
    'Neutral Data Zone':  'rgba(255,193,7,0.3)',
    'Elevated Risk Zone':   'rgba(255,107,53,0.3)',
    'High Risk Zone':    'rgba(255,61,87,0.3)',
}
verdict_desc_map = {
    'High Historical Value Zone':       'The majority of indicators are in historically low-risk territory. Data is consistent with past value accumulation zones.',
    'Value Accumulation Zone':       'Most indicators are in value territory. Historical data shows this zone has been associated with accumulation activity.',
    'Neutral Data Zone':  'Mixed signals across indicators. The data does not strongly favour either value or risk territory at this time.',
    'Elevated Risk Zone':   'Several indicators are in elevated territory. Historical data shows this zone has been associated with reduced allocation periods.',
    'High Risk Zone':    'The majority of indicators are in historically high-risk territory. Data is consistent with past cycle peak zones.',
}
vbg     = verdict_bg_map.get(verdict, verdict_bg_map['Neutral Data Zone'])
vborder = verdict_border_map.get(verdict, 'rgba(255,193,7,0.3)')
vdesc   = verdict_desc_map.get(verdict, '')

st.markdown(f"""
<div class="verdict-banner" style="background:{vbg}; border:1px solid {vborder};">
    <div class="verdict-title">Overall Accumulation Signal</div>
    <div class="verdict-text" style="color:{v_color};">{verdict}</div>
    <div class="verdict-sub">{vdesc}</div>
</div>
""", unsafe_allow_html=True)

# Signal Score Bar
total_sigs = max(buy_n + caution_n + sell_n, 1)
buy_w      = buy_n     / total_sigs * 100
caution_w  = caution_n / total_sigs * 100
sell_w     = sell_n    / total_sigs * 100

st.markdown(f"""
<div class="score-container">
    <div class="score-label">Signal Distribution — {total_sigs} Indicators</div>
    <div style="display:flex; height:12px; border-radius:6px; overflow:hidden; gap:2px;">
        <div style="width:{buy_w:.1f}%; background:#00C853; border-radius:6px 0 0 6px;"></div>
        <div style="width:{caution_w:.1f}%; background:#FFC107;"></div>
        <div style="width:{sell_w:.1f}%; background:#FF3D57; border-radius:0 6px 6px 0;"></div>
    </div>
    <div class="signal-counts">
        <div class="count-pill" style="background:rgba(0,200,83,0.08); border:1px solid rgba(0,200,83,0.18);">
            <span style="color:#00C853;">{buy_n}</span>
            <span class="count-label" style="color:#00C853;">VALUE</span>
        </div>
        <div class="count-pill" style="background:rgba(255,193,7,0.08); border:1px solid rgba(255,193,7,0.18);">
            <span style="color:#FFC107;">{caution_n}</span>
            <span class="count-label" style="color:#FFC107;">NEUTRAL</span>
        </div>
        <div class="count-pill" style="background:rgba(255,61,87,0.08); border:1px solid rgba(255,61,87,0.18);">
            <span style="color:#FF3D57;">{sell_n}</span>
            <span class="count-label" style="color:#FF3D57;">RISK</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# The Analytical Framework — Collapsible
# ─────────────────────────────────────────────────────────────────────────────
with st.expander("📐  The Analytical Framework — how this signal is built", expanded=False):
    _framework_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0A0A14; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 12px 4px; }}
  a {{ color: #F7931A; }}
</style>
</head>
<body>
<div style="font-size:0.83rem; color:#C8C8D8; line-height:1.75; padding:4px 0;">

  <div style="margin-bottom:20px; padding:16px 20px;
              background:linear-gradient(135deg,rgba(247,147,26,0.07),rgba(247,147,26,0.03));
              border:1px solid rgba(247,147,26,0.2); border-radius:10px;">
    <div style="font-size:0.68rem; font-weight:800; letter-spacing:2px; text-transform:uppercase;
                color:#F7931A; margin-bottom:8px;">The BTCpulse Analytical Framework</div>
    <div style="font-size:0.88rem; color:#E8E8F0; line-height:1.7; font-style:italic;">
      "The signal is built on the convergence of {total_sigs} distinct data streams across four analytical lenses:
      <strong style="color:#F7931A;">Liquidity</strong>,
      <strong style="color:#F7931A;">Market Structure</strong>,
      <strong style="color:#F7931A;">On-Chain Value</strong>, and
      <strong style="color:#F7931A;">Sentiment</strong>.
      By requiring confluence across these non-correlated fields, we eliminate the noise of price
      and focus on the integrity of the trend."
    </div>
  </div>

  <div style="font-size:0.68rem; font-weight:800; letter-spacing:2px; text-transform:uppercase;
              color:#F7931A; margin-bottom:10px;">The Four Analytical Lenses</div>
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:20px;">

    <div style="padding:12px 14px; background:#0D0D1A; border:1px solid #1E1E2E; border-radius:8px;">
      <div style="font-size:0.7rem; font-weight:700; color:#29B6F6; letter-spacing:1px;
                  text-transform:uppercase; margin-bottom:6px;">💧 Liquidity</div>
      <div style="font-size:0.75rem; color:#888; line-height:1.6;">
        Tracks global capital availability and dollar strength.<br>
        <span style="color:#555;">Global Liquidity Index · US Dollar Index (DXY)</span>
      </div>
    </div>

    <div style="padding:12px 14px; background:#0D0D1A; border:1px solid #1E1E2E; border-radius:8px;">
      <div style="font-size:0.7rem; font-weight:700; color:#AB47BC; letter-spacing:1px;
                  text-transform:uppercase; margin-bottom:6px;">📊 Market Structure</div>
      <div style="font-size:0.75rem; color:#888; line-height:1.6;">
        Price momentum, cycle positioning, and relative strength.<br>
        <span style="color:#555;">RSI (14D &amp; Weekly) · Pi Cycle Top · BTC Dominance · Altcoin Season · CBBI · BTC vs S&amp;P 500</span>
      </div>
    </div>

    <div style="padding:12px 14px; background:#0D0D1A; border:1px solid #1E1E2E; border-radius:8px;">
      <div style="font-size:0.7rem; font-weight:700; color:#00C853; letter-spacing:1px;
                  text-transform:uppercase; margin-bottom:6px;">⛓ On-Chain Value</div>
      <div style="font-size:0.75rem; color:#888; line-height:1.6;">
        Network-level data measuring holder behaviour and fair value.<br>
        <span style="color:#555;">MVRV · NUPL · Puell Multiple · RHODL · Reserve Risk · Mayer Multiple · 200W MA · 2Y MA · Ahr999</span>
      </div>
    </div>

    <div style="padding:12px 14px; background:#0D0D1A; border:1px solid #1E1E2E; border-radius:8px;">
      <div style="font-size:0.7rem; font-weight:700; color:#FFC107; letter-spacing:1px;
                  text-transform:uppercase; margin-bottom:6px;">🧠 Sentiment</div>
      <div style="font-size:0.75rem; color:#888; line-height:1.6;">
        Crowd psychology and market emotion.<br>
        <span style="color:#555;">Fear &amp; Greed Index</span>
        <span style="color:#333;"> · additional lenses being added</span>
      </div>
    </div>

  </div>

  <div style="font-size:0.68rem; font-weight:800; letter-spacing:2px; text-transform:uppercase;
              color:#F7931A; margin-bottom:10px;">Reading the Signal Zones</div>
  <table style="width:100%; border-collapse:collapse; font-size:0.78rem; margin-bottom:18px;">
    <tr style="border-bottom:1px solid #1A1A2E;">
      <td style="padding:7px 10px; color:#00C853; font-weight:700; white-space:nowrap;">🟢 High Historical Value Zone</td>
      <td style="padding:7px 10px; color:#777;">60%+ of indicators in value territory. Historically associated with cycle lows and major accumulation periods.</td>
    </tr>
    <tr style="border-bottom:1px solid #1A1A2E;">
      <td style="padding:7px 10px; color:#69F0AE; font-weight:700; white-space:nowrap;">🟢 Value Accumulation Zone</td>
      <td style="padding:7px 10px; color:#777;">40–60% of indicators in value territory. Historically associated with mid-cycle accumulation windows.</td>
    </tr>
    <tr style="border-bottom:1px solid #1A1A2E;">
      <td style="padding:7px 10px; color:#FFC107; font-weight:700; white-space:nowrap;">🟡 Neutral Data Zone</td>
      <td style="padding:7px 10px; color:#777;">Indicators are mixed. The data does not strongly favour either direction — historically a period of consolidation.</td>
    </tr>
    <tr style="border-bottom:1px solid #1A1A2E;">
      <td style="padding:7px 10px; color:#FF6B35; font-weight:700; white-space:nowrap;">🟠 Elevated Risk Zone</td>
      <td style="padding:7px 10px; color:#777;">40–60% of indicators in risk territory. Historically associated with late-cycle caution periods.</td>
    </tr>
    <tr>
      <td style="padding:7px 10px; color:#FF3D57; font-weight:700; white-space:nowrap;">🔴 High Risk Zone</td>
      <td style="padding:7px 10px; color:#777;">60%+ of indicators in risk territory. Historically associated with cycle peaks and distribution phases.</td>
    </tr>
  </table>

  <div style="font-size:0.76rem; color:#666; margin-bottom:16px; padding-left:4px;">
    When fewer than 60% of indicators align in one direction, the data is considered mixed (Neutral Data Zone).
    Historically, mixed readings have not strongly favoured either direction.
  </div>

  <div style="padding:10px 14px; background:rgba(247,147,26,0.05);
              border-left:3px solid rgba(247,147,26,0.35); border-radius:0 6px 6px 0;
              font-size:0.74rem; color:#666;">
    <strong style="color:#999;">General information only.</strong>
    The indicators describe historical patterns — they do not predict future prices.
    BTCpulse does not hold an AFSL. Always perform your own due diligence.
  </div>

</div>
</body>
</html>"""
    components.html(_framework_html, height=680, scrolling=False)

# Price Strip
# ─────────────────────────────────────────────────────────────────────────────
chg_col        = '#00C853' if chg_24h >= 0 else '#FF3D57'
chg_24h_aud_val = data.get('chg_24h_aud', chg_24h)
aud_chg_col     = '#00C853' if chg_24h_aud_val >= 0 else '#FF3D57'
aud_chg_arrow   = '▲' if chg_24h_aud_val >= 0 else '▼'
chg_arrow = '▲' if chg_24h >= 0 else '▼'
mkt_cap   = data.get('market_cap', 0)
vol_24h   = data.get('volume_24h', 0)
dom       = data.get('btc_dominance', 55)

def fmt_large(n):
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.2f}B"
    if n >= 1e6:  return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"

p1, p2, p3, p4, p5 = st.columns(5)
with p1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">BTC / USD</div>
        <div class="metric-value">${price:,.0f}</div>
        <div class="metric-sub" style="color:{chg_col};">{chg_arrow} {abs(chg_24h):.2f}% (24h)</div>
    </div>""", unsafe_allow_html=True)
with p2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">BTC / AUD</div>
        <div class="metric-value">A${price_aud:,.0f}</div>
        <div class="metric-sub" style="color:{aud_chg_col};">{aud_chg_arrow} {abs(chg_24h_aud_val):.2f}% (24h) · Rate: {aud_rate:.4f}</div>
    </div>""", unsafe_allow_html=True)
with p3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Market Cap</div>
        <div class="metric-value">{fmt_large(mkt_cap)}</div>
        <div class="metric-sub">Total BTC Market</div>
    </div>""", unsafe_allow_html=True)
with p4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">24h Volume</div>
        <div class="metric-value">{fmt_large(vol_24h)}</div>
        <div class="metric-sub">Trading Volume</div>
    </div>""", unsafe_allow_html=True)
with p5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">BTC Dominance</div>
        <div class="metric-value">{dom:.1f}%</div>
        <div class="metric-sub">of Total Crypto Market</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 200W MA Valuation Banner
# ─────────────────────────────────────────────────────────────────────────────
_ma200w      = data.get('ma_200w', 58500)
_pct_200w    = data.get('pct_above_200w', 8.0)

if _pct_200w < 0:
    _val_region = 'Very Cheap'
    _val_color  = '#1565C0'
    _val_bg     = 'linear-gradient(135deg, rgba(21,101,192,0.18), rgba(21,101,192,0.06))'
    _val_border = 'rgba(21,101,192,0.4)'
    _val_desc   = 'Price is below the 200W MA — the deepest accumulation zone in Bitcoin history.'
elif _pct_200w < 50:
    _val_region = 'Cheap'
    _val_color  = '#00897B'
    _val_bg     = 'linear-gradient(135deg, rgba(0,137,123,0.18), rgba(0,137,123,0.06))'
    _val_border = 'rgba(0,137,123,0.4)'
    _val_desc   = '0–50% above the 200W MA — historically a strong accumulation zone.'
elif _pct_200w < 100:
    _val_region = 'Fair Value'
    _val_color  = '#F9A825'
    _val_bg     = 'linear-gradient(135deg, rgba(249,168,37,0.14), rgba(249,168,37,0.04))'
    _val_border = 'rgba(249,168,37,0.4)'
    _val_desc   = '50–100% above the 200W MA — fair value range. Normal bull market territory.'
elif _pct_200w < 150:
    _val_region = 'Expensive'
    _val_color  = '#E65100'
    _val_bg     = 'linear-gradient(135deg, rgba(230,81,0,0.16), rgba(230,81,0,0.05))'
    _val_border = 'rgba(230,81,0,0.4)'
    _val_desc   = '100–150% above the 200W MA — elevated. Consider reducing new exposure.'
else:
    _val_region = 'Very Expensive'
    _val_color  = '#B71C1C'
    _val_bg     = 'linear-gradient(135deg, rgba(183,28,28,0.18), rgba(183,28,28,0.06))'
    _val_border = 'rgba(183,28,28,0.4)'
    _val_desc   = 'Over 150% above the 200W MA — historically near cycle tops. High risk zone.'

# Progress bar: map -20% to +200% range onto 0–100%
_bar_min, _bar_max = -20, 200
_bar_pos = max(0, min(100, (_pct_200w - _bar_min) / (_bar_max - _bar_min) * 100))
# Update cache with valuation region (defined after score block)
_alert_cache['last_val_region'] = _val_region
_alert_cache['last_pct_200w']   = round(_pct_200w, 1)
_save_alert_cache(_alert_cache)

# Build the live commentary for the 200W MA banner tooltip
_val_commentary_map = {
    'Very Cheap':    f"Price is <b style='color:#1565C0'>below the 200W MA</b> at ${_ma200w:,.0f} — this is the deepest accumulation zone in Bitcoin's history. Every single bear market bottom has touched or gone below this level. An extremely rare and historically significant buying opportunity.",
    'Cheap':         f"At {_pct_200w:+.1f}% above the 200W MA (${_ma200w:,.0f}), Bitcoin is in the <b style='color:#00897B'>Cheap zone</b>. Historically, the 0–50% extension range has been one of the best accumulation windows of the entire cycle — well below the euphoria levels seen at cycle tops.",
    'Fair Value':    f"At {_pct_200w:+.1f}% above the 200W MA (${_ma200w:,.0f}), Bitcoin is in the <b style='color:#F9A825'>Fair Value zone</b>. This is normal bull market territory. Not the deepest discount, but not overextended either. Dollar-cost averaging remains reasonable.",
    'Expensive':     f"At {_pct_200w:+.1f}% above the 200W MA (${_ma200w:,.0f}), Bitcoin is in the <b style='color:#E65100'>Expensive zone</b>. Historically, the 100–150% extension range has been associated with late-cycle conditions. Consider reducing new exposure and tightening risk management.",
    'Very Expensive': f"At {_pct_200w:+.1f}% above the 200W MA (${_ma200w:,.0f}), Bitcoin is in the <b style='color:#B71C1C'>Very Expensive zone</b>. This extension level has historically coincided with cycle tops. This is a distribution zone, not an accumulation zone — extreme caution advised.",
}
_val_tooltip_what = "The 200-Week Moving Average (200W MA) is the average closing price of Bitcoin over the last 200 weeks (~4 years). It represents the long-term cost basis of the entire market. Every Bitcoin bear market bottom in history has touched or gone below this level. Extensions from this level define valuation regions: Very Cheap (below), Cheap (0–50%), Fair Value (50–100%), Expensive (100–150%), Very Expensive (>150%)."
_val_tooltip_now  = _val_commentary_map.get(_val_region, '')

st.markdown(f"""
<div style="background:{_val_bg}; border:1px solid {_val_border}; border-radius:12px; padding:14px 20px; margin-bottom:10px;">
  <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
    <div style="display:flex; align-items:center; gap:14px;">
      <div>
        <div class="card-tooltip-wrap" style="font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:2px; cursor:help; display:inline-block;">200W MA Valuation &nbsp;<span style="color:#555; font-size:0.6rem;">&#9432;</span>
          <div class="card-tooltip-popup" style="width:300px; text-transform:none; letter-spacing:normal;">
            <div class="ct-what">{_val_tooltip_what}</div>
            <div class="ct-divider"></div>
            <div class="ct-now">{_val_tooltip_now}</div>
          </div>
        </div>
        <div style="font-size:1.55rem; font-weight:800; color:{_val_color}; line-height:1;">{_val_region}</div>
        <div style="font-size:0.7rem; color:#aaa; margin-top:3px;">{_val_desc}</div>
      </div>
    </div>
    <div style="display:flex; gap:20px; align-items:center; flex-wrap:wrap;">
      <div style="text-align:center;">
        <div style="font-size:0.6rem; color:#888; text-transform:uppercase; letter-spacing:0.06em;">BTC Price</div>
        <div style="font-size:1.1rem; font-weight:700; color:#F7931A;">${price:,.0f}</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:0.6rem; color:#888; text-transform:uppercase; letter-spacing:0.06em;">200W MA</div>
        <div style="font-size:1.1rem; font-weight:700; color:#ccc;">${_ma200w:,.0f}</div>
        <div style="font-size:0.6rem; color:#666;">weekly closes · Yahoo Finance</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:0.6rem; color:#888; text-transform:uppercase; letter-spacing:0.06em;">Extension</div>
        <div style="font-size:1.1rem; font-weight:700; color:{_val_color};">{_pct_200w:+.1f}%</div>
        <div style="font-size:0.6rem; color:#666;">above 200W MA</div>
      </div>
    </div>
  </div>
  <div style="margin-top:12px;">
    <div style="position:relative; height:8px; background:linear-gradient(to right, #1565C0 0%, #00897B 20%, #F9A825 45%, #E65100 70%, #B71C1C 100%); border-radius:4px;">
      <div style="position:absolute; top:-3px; left:{_bar_pos:.1f}%; transform:translateX(-50%); width:14px; height:14px; background:#fff; border-radius:50%; border:2px solid {_val_color}; box-shadow:0 0 6px {_val_color};"></div>
    </div>
    <div style="display:flex; justify-content:space-between; margin-top:4px; font-size:0.58rem; color:#555;">
      <span>Below 0%<br>Very Cheap</span>
      <span style="text-align:center;">+50%<br>Cheap</span>
      <span style="text-align:center;">+100%<br>Fair Value</span>
      <span style="text-align:center;">+150%<br>Expensive</span>
      <span style="text-align:right;">+200%<br>Very Expensive</span>
    </div>
  </div>
  <div style="font-size:0.6rem; color:#444; margin-top:6px; text-align:right;">Not part of the accumulation score &nbsp;·&nbsp; 200W MA Extension Model</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Signal Change Alert Banner
# ─────────────────────────────────────────────────────────────────────────────
if _signal_changed and _signal_change_text:
    _prev_color = {'High Historical Value Zone': '#00C853', 'Value Accumulation Zone': '#69F0AE', 'Neutral Data Zone': '#FFC107',
                   'Elevated Risk Zone': '#FF9800', 'High Risk Zone': '#FF3D57'}.get(_prev_verdict, '#888')
    _new_color  = {'High Historical Value Zone': '#00C853', 'Value Accumulation Zone': '#69F0AE', 'Neutral Data Zone': '#FFC107',
                   'Elevated Risk Zone': '#FF9800', 'High Risk Zone': '#FF3D57'}.get(verdict, '#888')
    st.markdown(f"""
<div style="background:rgba(247,147,26,0.07); border:1px solid rgba(247,147,26,0.25); border-radius:12px;
            padding:14px 20px; margin-bottom:12px; display:flex; align-items:flex-start; gap:14px;">
    <div style="font-size:1.4rem; line-height:1; margin-top:2px;">🔔</div>
    <div>
        <div style="font-size:0.65rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
                    color:#F7931A; margin-bottom:5px;">Signal Changed</div>
        <div style="font-size:0.82rem; color:#ccc; margin-bottom:6px;">
            <span style="color:{_prev_color}; font-weight:700;">{_prev_verdict}</span>
            <span style="color:#555; margin:0 8px;">→</span>
            <span style="color:{_new_color}; font-weight:700;">{verdict}</span>
        </div>
        <div style="font-size:0.80rem; color:#aaa; line-height:1.5;">{_signal_change_text}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Indicator Anomaly Callout
# ─────────────────────────────────────────────────────────────────────────────
if _anomaly_text:
    st.markdown(f"""
<div style="background:rgba(255,193,7,0.05); border:1px solid rgba(255,193,7,0.2); border-radius:12px;
            padding:14px 20px; margin-bottom:12px; display:flex; align-items:flex-start; gap:14px;">
    <div style="font-size:1.4rem; line-height:1; margin-top:2px;">📊</div>
    <div>
        <div style="font-size:0.65rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase;
                    color:#FFC107; margin-bottom:5px;">Notable Indicator Movement</div>
        <div style="font-size:0.80rem; color:#aaa; line-height:1.5;">{_anomaly_text}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Market Vibe
# ─────────────────────────────────────────────────────────────────────────────
fg_val   = data.get('fear_greed', 50)
fg_label = data.get('fear_greed_label', 'Neutral')

vibe_text, vibe_is_fresh = load_market_vibe(
    price, chg_24h, chg_7d, fg_val, fg_label, dom,
    verdict, buy_n, caution_n, sell_n, len(signals)
)
vibe_freshness = "✨ Generated today" if vibe_is_fresh else "📅 Today's analysis"

st.markdown(f"""
<div class="vibe-box">
    <div class="vibe-label" style="display:flex; justify-content:space-between; align-items:center;">
        <span>📡 Market Vibe — {datetime.utcnow().strftime('%b %d, %Y')}</span>
        <span style="font-size:0.62rem; color:#555; font-weight:500;">{vibe_freshness}</span>
    </div>
    {vibe_text}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Indicator Detail Page (renders instead of dashboard when card is clicked)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.selected_indicator:
    from indicator_deepdives import DEEPDIVES
    _ind_name = st.session_state.selected_indicator
    _ind_data = DEEPDIVES.get(_ind_name, {})

    # Find the live signal data for this indicator
    _live_sig = None
    try:
        _detail_data, _all_sigs, *_ = load_data()
        _live_sig = next((s for s in _all_sigs if s["name"] == _ind_name), None)
    except Exception:
        pass

    # Back button
    if st.button("Back to Dashboard"):
        st.session_state.selected_indicator = None
        st.rerun()

    # Header with current value and signal
    _sig_color = "#888"
    _sig_label = "N/A"
    _sig_emoji = ""
    _val_str = "N/A"
    _detail_str = ""
    if _live_sig:
        _sig_color = _live_sig.get("color", "#888")
        _sig_label = _live_sig.get("signal", "N/A")
        _sig_emoji = _live_sig.get("emoji", "")
        _val_str = _live_sig.get("value_str", "N/A")
        _detail_str = _live_sig.get("detail", "")

    _badge_bg_map = {"BUY": "rgba(0,200,83,0.15)", "CAUTION": "rgba(255,193,7,0.15)", "SELL": "rgba(255,61,87,0.15)"}
    _badge_bd_map = {"BUY": "rgba(0,200,83,0.4)", "CAUTION": "rgba(255,193,7,0.4)", "SELL": "rgba(255,61,87,0.4)"}
    _badge_bg = _badge_bg_map.get(_sig_label, "rgba(100,100,100,0.15)")
    _badge_bd = _badge_bd_map.get(_sig_label, "rgba(100,100,100,0.4)")

    _header_html = (
        "<div style='background:#12121F; border:1px solid #1E1E2E; border-radius:14px; padding:24px 28px; margin-bottom:20px;'>"
        "<div style='font-size:0.7rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#F7931A; margin-bottom:6px;'>INDICATOR DEEP-DIVE</div>"
        "<div style='display:flex; align-items:center; gap:14px; flex-wrap:wrap;'>"
        "<div style='font-size:1.8rem; font-weight:900; color:#E8E8F0;'>" + _ind_name + "</div>"
        "<div style='font-family:JetBrains Mono,monospace; font-size:1.6rem; font-weight:700; color:" + _sig_color + ";'>" + _val_str + "</div>"
        "<div style='padding:5px 14px; border-radius:20px; font-size:0.78rem; font-weight:800; letter-spacing:1px; background:" + _badge_bg + "; border:1px solid " + _badge_bd + "; color:" + _sig_color + ";'>"
        + _sig_emoji + " " + _sig_label
        + "</div>"
        "</div>"
        + ("<div style='font-size:0.75rem; color:#666; margin-top:6px;'>" + _detail_str + "</div>" if _detail_str else "")
        + "</div>"
    )
    st.markdown(_header_html, unsafe_allow_html=True)

    if _ind_data:
        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            st.markdown(
                "<div style='font-size:0.7rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#F7931A; margin-bottom:6px;'>WHAT IT MEASURES</div>"
                "<div style='font-size:0.88rem; color:#C8C8D8; line-height:1.7;'>" + _ind_data.get("what", "") + "</div>",
                unsafe_allow_html=True
            )
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:0.7rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#F7931A; margin-bottom:6px;'>WHY IT MATTERS</div>"
                "<div style='font-size:0.88rem; color:#C8C8D8; line-height:1.7;'>" + _ind_data.get("why_matters", "") + "</div>",
                unsafe_allow_html=True
            )
        with col_b:
            st.markdown(
                "<div style='font-size:0.7rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#F7931A; margin-bottom:6px;'>HISTORICAL CONTEXT</div>"
                "<div style='font-size:0.88rem; color:#C8C8D8; line-height:1.7;'>" + _ind_data.get("historical_context", "") + "</div>",
                unsafe_allow_html=True
            )
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:0.7rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#F7931A; margin-bottom:6px;'>INTERPRETATION</div>"
                "<div style='font-size:0.88rem; color:#C8C8D8; line-height:1.7;'>" + _ind_data.get("interpretation", "") + "</div>",
                unsafe_allow_html=True
            )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:rgba(0,200,83,0.07); border:1px solid rgba(0,200,83,0.25); border-radius:10px; padding:16px 20px;'>"
            "<div style='font-size:0.68rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#00C853; margin-bottom:6px;'>ACCUMULATION CONTEXT</div>"
            "<div style='font-size:0.88rem; color:#C8C8D8; line-height:1.65;'>" + _ind_data.get("accumulation_summary", "") + "</div>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.info("Full deep-dive content for this indicator is coming soon.")

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.72rem; color:#444; text-align:center;'>Not financial advice. Data refreshes every 5 minutes.</div>",
        unsafe_allow_html=True
    )
    st.stop()


tab1, tab2, tab3, tab5 = st.tabs([
    "📊 Signal Tracker",
    "📈 Price Chart",
    "⛏️ Halving Cycle",
    "📉 DCA Performance",
])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1: SIGNAL TRACKER
# ═════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── Signal Overview — compact rows with hover tooltips ──
    st.markdown("<div style='font-size:1.1rem; font-weight:700; color:#E8E8F0; margin:4px 0 2px 0;'>Signal Overview</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.70rem; color:#555; margin:0 0 8px 0;'>Hover over any indicator name for an explanation and live commentary.</div>", unsafe_allow_html=True)
    # Build HTML for signal overview with tooltips
    rows_html = ""
    for s in signals:
        bar_color    = s['color']
        badge_bg     = ('rgba(0,200,83,0.13)'   if s['signal']=='BUY'
                        else ('rgba(255,193,7,0.13)'  if s['signal']=='CAUTION'
                              else 'rgba(255,61,87,0.13)'))
        badge_border = ('rgba(0,200,83,0.28)'   if s['signal']=='BUY'
                        else ('rgba(255,193,7,0.28)'  if s['signal']=='CAUTION'
                              else 'rgba(255,61,87,0.28)'))
        badge_dot    = ('#00C853' if s['signal']=='BUY'
                        else ('#FFC107' if s['signal']=='CAUTION'
                              else '#FF3D57'))
        # Tooltip content: explanation + live commentary
        tooltip_def  = TOOLTIPS.get(s['name'], s.get('description', ''))
        tooltip_live = zone_commentary(s)
        # Escape for HTML attribute safety
        tooltip_def_safe  = tooltip_def.replace('"', '&quot;').replace("'", '&#39;')
        tooltip_live_safe = tooltip_live.replace('"', '&quot;').replace("'", '&#39;').replace('<b', '').replace('</b>', '').replace('>', '').replace('<', '')
        rows_html += f"""
            <div class="so-row">
                <div class="so-name-wrap">
                    <span class="so-name">{s['name']}</span>
                    <div class="so-tooltip">
                        <div class="so-tt-section so-tt-what">{tooltip_def}</div>
                        <div class="so-tt-divider"></div>
                        <div class="so-tt-section so-tt-now">{tooltip_live}</div>
                    </div>
                </div>
                <div class="so-badge" style="background:{badge_bg}; color:{bar_color}; border:1px solid {badge_border};">
                    <span class="so-dot" style="background:{badge_dot};"></span>{s['signal']}
                </div>
            </div>"""

    overview_html = f"""<!DOCTYPE html>
    <html><head><meta charset="utf-8"></head><body style="margin:0;padding:0;background:#12121F;">
    <style>
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ background:#12121F; padding:3px 6px 2px 6px; }}

    .so-row {{
        display:grid;
        grid-template-columns: 1fr 90px;
        align-items:center;
        gap:8px;
        padding:4px 6px;
        border-bottom:1px solid rgba(255,255,255,0.04);
        position:relative;
    }}
    .so-row:last-child {{ border-bottom:none; }}
    .so-row:hover {{ background:rgba(255,255,255,0.025); border-radius:5px; }}

    .so-name-wrap {{
        position:relative; min-width:0; cursor:default;
    }}
    .so-name {{
        font-family:'Inter',sans-serif; font-size:0.78rem; color:#C8C8D8;
        font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
        display:block;
        border-bottom:1px dashed rgba(255,255,255,0.10);
        padding-bottom:1px;
    }}

    /* Tooltip popup — opens downward, clamped to viewport */
    .so-tooltip {{
        visibility:hidden; opacity:0;
        position:fixed; z-index:99999;
        width:280px; min-width:200px;
        background:#1A1A2E;
        border:1px solid #2A2A4E;
        border-radius:10px;
        padding:0;
        box-shadow:0 12px 32px rgba(0,0,0,0.7);
        transition:opacity 0.18s ease;
        pointer-events:none;
    }}
    .so-name-wrap:hover .so-tooltip {{
        visibility:visible; opacity:1;
    }}
    /* JS will position tooltip via mousemove */
    .so-tt-section {{
        font-family:'Inter',sans-serif; font-size:0.73rem;
        color:#B8B8CC; line-height:1.55; padding:9px 12px;
    }}
    .so-tt-what {{ color:#9090A8; }}
    .so-tt-now  {{ color:#C8C8D8; }}
    .so-tt-divider {{ height:1px; background:rgba(255,255,255,0.07); margin:0 12px; }}

    /* Fixed-width badge column — all badges same width so value column aligns */
    .so-badge {{
        font-family:'Inter',sans-serif; font-size:0.62rem; font-weight:800;
        letter-spacing:0.8px; padding:2px 8px; border-radius:8px;
        white-space:nowrap; width:90px;
        display:flex; align-items:center; gap:5px;
        justify-content:center;
    }}
    .so-dot {{
        width:5px; height:5px; border-radius:50%; flex-shrink:0;
        display:inline-block;
    }}

    </style>
    <script>
    document.addEventListener('mousemove', function(e) {{
        var tt = document.querySelector('.so-name-wrap:hover .so-tooltip');
        if (!tt) return;
        var x = e.clientX + 12;
        var y = e.clientY + 12;
        // prevent right overflow
        if (x + 280 > window.innerWidth) x = e.clientX - 292;
        // prevent bottom overflow
        if (y + tt.offsetHeight > window.innerHeight) y = e.clientY - tt.offsetHeight - 8;
        tt.style.left = x + 'px';
        tt.style.top  = y + 'px';
    }});
    </script>
    <div style="background:#12121F; border:1px solid #1E1E2E; border-radius:10px; padding:2px 4px;">
    {rows_html}
    </div>
    </body></html>
    """
    # Render overview rows as clickable Streamlit buttons styled as rows
    components.html(overview_html, height=600, scrolling=False)

    # ── Indicator Cards ──
    st.markdown("<div style='font-size:1.1rem; font-weight:700; color:#E8E8F0; margin:4px 0 2px 0;'>All Indicators at a Glance</div>", unsafe_allow_html=True)

    categories = {}
    for s in signals:
        cat = s['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(s)

    cat_icons = {
        'Sentiment':        '🧠',
        'On-Chain':         '⛓️',
        'Price Model':      '📐',
        'Technical':        '📊',
        'Market Structure': '🏗️',
        'Macro':            '🌎',
    }

    for cat, items in categories.items():
        icon = cat_icons.get(cat, "•")
        st.markdown(f'<div class="category-header">{icon} {cat}</div>', unsafe_allow_html=True)
        cols = st.columns(3)
        for i, s in enumerate(items):
            badge_class = "badge-" + s["signal"].lower()
            card_class  = "card-"  + s["signal"].lower()
            tooltip_txt = TOOLTIPS.get(s["name"], s.get("description", ""))
            commentary  = zone_commentary(s)
            zone_html = (
                '<div class="zone-thresholds">'
                + '<span class="zone-buy">🟢 ' + s["buy_zone"]  + '</span>'
                + '<span class="zone-sell">🔴 ' + s["sell_zone"] + '</span>'
                + '</div>'
            )
            card_html = (
                '<div class="indicator-card ' + card_class + '" style="position:relative; overflow:visible;">'
                + '<div class="card-header">'
                + '<div style="flex:1; min-width:0;">'
                + '<div class="card-tooltip-wrap">'
                + '<div class="card-name">' + s["name"] + ' <span style="font-size:0.6rem; color:#444; font-weight:400;">ℹ</span></div>'
                + '<div class="card-tooltip-popup">'
                + '<div class="ct-what">' + tooltip_txt + '</div>'
                + '<div class="ct-divider"></div>'
                + '<div class="ct-now">' + commentary + '</div>'
                + '</div></div>'
                + '<div class="card-category">' + s["category"] + '</div>'
                + '</div>'
                + '<span class="signal-badge ' + badge_class + '">' + s["emoji"] + ' ' + s["signal"] + '</span>'
                + '</div>'
                + '<div class="card-value" style="color:' + s["color"] + '">' + s["value_str"] + '</div>'
                + '<div class="card-detail">' + s["detail"] + '</div>'
                + zone_html
                + '<div class="zone-commentary">' + commentary + '</div>'
                + '</div>'
            )
            with cols[i % 3]:
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button("View Details →", key="deepdive_" + s["name"], use_container_width=True):
                    st.session_state.selected_indicator = s["name"]
                    st.rerun()

# TAB 2: PRICE CHART (5-Year)
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Bitcoin Price — 5 Year")

    df_5yr = load_price_chart()

    if df_5yr is not None and not df_5yr.empty:
        close = df_5yr['close']
        dates = df_5yr.index

        # MA variables removed — chart is price-only

        fig_price = go.Figure()

        # Price area
        fig_price.add_trace(go.Scatter(
            x=dates, y=close,
            name='BTC Price',
            line=dict(color='#F7931A', width=2),
            fill='tozeroy',
            fillcolor='rgba(247,147,26,0.06)',
            hovertemplate='<b>%{x|%b %d %Y}</b><br>$%{y:,.0f}<extra></extra>',
        ))

        # MAs removed — clean price-only chart

        # Halving vertical lines — use add_shape to avoid Plotly string-date bug
        for hd, hl in [('2020-05-11', '3rd Halving'), ('2024-04-20', '4th Halving')]:
            hd_ts = pd.Timestamp(hd)
            if hd_ts >= dates.min() and hd_ts <= dates.max():
                fig_price.add_shape(
                    type='line',
                    x0=hd_ts, x1=hd_ts,
                    y0=0, y1=1,
                    xref='x', yref='paper',
                    line=dict(color='rgba(247,147,26,0.4)', width=1, dash='dot'),
                )
                fig_price.add_annotation(
                    x=hd_ts, y=0.97,
                    xref='x', yref='paper',
                    text=hl,
                    showarrow=False,
                    font=dict(color='rgba(247,147,26,0.75)', size=9),
                    xanchor='left',
                )

        _sl2 = {k: v for k, v in PLOTLY_DARK.items() if k not in ('legend', 'margin', 'xaxis', 'yaxis')}
        fig_price.update_layout(
            **_sl2,
            height=460,
            margin=dict(l=60, r=30, t=40, b=40),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.04)',
                zerolinecolor='#2A2A3E',
                tickfont=dict(size=10),
                rangeslider=dict(visible=False),
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.04)',
                zerolinecolor='#2A2A3E',
                tickfont=dict(size=10),
                tickprefix='$',
                tickformat=',.0f',
            ),
            legend=dict(
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='#888', size=10),
                orientation='h', y=1.02, x=0,
            ),
            hovermode='x unified',
        )
        st.plotly_chart(fig_price, use_container_width=True)

        # Price stat cards
        current_price = float(close.iloc[-1])
        price_1y_ago  = float(close.iloc[-252]) if len(close) >= 252 else float(close.iloc[0])
        price_ath     = float(close.max())
        pct_from_ath  = (current_price - price_ath) / price_ath * 100
        pct_1y        = (current_price - price_1y_ago) / price_1y_ago * 100

        ath_col = '#FF3D57' if pct_from_ath < -30 else ('#FFC107' if pct_from_ath < -10 else '#00C853')
        yr1_col = '#00C853' if pct_1y >= 0 else '#FF3D57'

        c1, c2, c3 = st.columns(3)
        def stat_card(label, val, sub='', col_val='#F7931A'):
            return f"""<div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color:{col_val};">{val}</div>
                <div class="metric-sub">{sub}</div>
            </div>"""

        with c1: st.markdown(stat_card('Current Price', f'${current_price:,.0f}', 'USD'), unsafe_allow_html=True)
        with c2: st.markdown(stat_card('From ATH', f'{pct_from_ath:+.1f}%', f'ATH: ${price_ath:,.0f}', ath_col), unsafe_allow_html=True)
        with c3: st.markdown(stat_card('1-Year Return', f'{pct_1y:+.1f}%', '365 days ago', yr1_col), unsafe_allow_html=True)

    else:
        st.info("Price chart data unavailable. Please click Refresh Data in the sidebar.")

# ═════════════════════════════════════════════════════════════════════════════
# TAB 3: HALVING CYCLE
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    halving = data.get('halving', {})
    st.markdown("### Bitcoin Halving Cycle")

    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.markdown(f"""
        <div class="halving-card">
            <div class="halving-title">Last Halving</div>
            <div class="halving-value" style="font-size:1.3rem;">{halving.get('last_date','Apr 20, 2024')}</div>
            <div class="halving-sub">Block 840,000 · 3.125 BTC reward</div>
        </div>""", unsafe_allow_html=True)
    with h2:
        st.markdown(f"""
        <div class="halving-card">
            <div class="halving-title">Next Halving (Est.)</div>
            <div class="halving-value" style="font-size:1.3rem;">{halving.get('next_date','Apr 20, 2028')}</div>
            <div class="halving-sub">Block 1,050,000 · 1.5625 BTC reward</div>
        </div>""", unsafe_allow_html=True)
    with h3:
        st.markdown(f"""
        <div class="halving-card">
            <div class="halving-title">Days Since Last</div>
            <div class="halving-value">{halving.get('days_since', 0)}</div>
            <div class="halving-sub">Days Elapsed</div>
        </div>""", unsafe_allow_html=True)
    with h4:
        st.markdown(f"""
        <div class="halving-card">
            <div class="halving-title">Days to Next</div>
            <div class="halving-value" style="color:#F7931A;">{halving.get('days_to', 0)}</div>
            <div class="halving-sub">Days Remaining</div>
        </div>""", unsafe_allow_html=True)

    prog = halving.get('progress_pct', 0)
    st.markdown(f"""
    <div class="score-container" style="margin-top:12px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span class="score-label">Cycle Progress</span>
            <span style="color:#F7931A; font-weight:700; font-size:0.85rem;">{prog:.1f}%</span>
        </div>
        <div style="background:#1E1E2E; border-radius:6px; height:12px; overflow:hidden;">
            <div style="width:{prog}%; height:100%; background:linear-gradient(90deg,#F7931A,#FFB347); border-radius:6px;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:5px; font-size:0.68rem; color:#444;">
            <span>April 2024</span>
            <span>~April 2028</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Where Are We in the Cycle?")
    cycle_pct = prog
    if cycle_pct < 20:
        phase_name   = "Post-Halving Consolidation"
        phase_desc   = "Historically, Bitcoin consolidates or dips in the months immediately after a halving as the market absorbs the supply shock. This is often an excellent accumulation window — the supply cut has happened but price hasn't reacted yet."
        phase_signal = "🟢 Value Accumulation Zone"
        p_badge      = "buy"
    elif cycle_pct < 50:
        phase_name   = "Bull Market Build-Up"
        phase_desc   = "The supply shock begins to take effect. Institutional and retail demand typically increases. Historically, this phase sees strong price appreciation — we are likely in the early-to-mid bull market."
        phase_signal = "🟢 Value Accumulation Zone / HOLD"
        p_badge      = "buy"
    elif cycle_pct < 70:
        phase_name   = "Bull Market Peak Zone"
        phase_desc   = "Historically, Bitcoin reaches its cycle peak around 12–18 months after the halving. Monitor on-chain indicators closely for signs of a top — MVRV, NUPL, and Pi Cycle are the key ones to watch."
        phase_signal = "🟡 CAUTION — WATCH SIGNALS"
        p_badge      = "caution"
    elif cycle_pct < 85:
        phase_name   = "Post-Peak / Bear Market"
        phase_desc   = "If the cycle top has passed, Bitcoin typically enters a prolonged bear market. Patience is required. Begin watching for capitulation signals — NUPL below 0, MVRV Z-Score below 0, Fear & Greed in Extreme Fear."
        phase_signal = "🟠 CAUTION — REDUCE RISK"
        p_badge      = "caution"
    else:
        phase_name   = "Late Bear / Accumulation Bottom"
        phase_desc   = "Approaching the next halving. Historical data shows this phase has been associated with value accumulation zones, with prices near cycle lows and sentiment at extreme fear. The next supply shock is approaching."
        phase_signal = "🟢 STRONG Value Accumulation Zone"
        p_badge      = "buy"

    st.markdown(f"""
    <div class="indicator-card card-{p_badge}">
        <div class="card-header">
            <div>
                <div class="card-name">{phase_name}</div>
                <div class="card-category">Cycle Phase · {cycle_pct:.0f}% through 4-year cycle</div>
            </div>
            <span class="signal-badge badge-{p_badge}">{phase_signal}</span>
        </div>
        <div class="zone-commentary" style="margin-top:8px;">{phase_desc}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Halving History")
    halving_df = pd.DataFrame([
        {'Halving': 'Genesis (Block 0)',  'Date': 'Jan 3, 2009',   'Block': '0',         'Reward': '50 BTC',     'BTC Price': '~$0',      '1Y Later': 'N/A'},
        {'Halving': '1st Halving',        'Date': 'Nov 28, 2012',  'Block': '210,000',   'Reward': '25 BTC',     'BTC Price': '~$12',     '1Y Later': '~$1,000'},
        {'Halving': '2nd Halving',        'Date': 'Jul 9, 2016',   'Block': '420,000',   'Reward': '12.5 BTC',   'BTC Price': '~$650',    '1Y Later': '~$2,500'},
        {'Halving': '3rd Halving',        'Date': 'May 11, 2020',  'Block': '630,000',   'Reward': '6.25 BTC',   'BTC Price': '~$8,600',  '1Y Later': '~$57,000'},
        {'Halving': '4th Halving',        'Date': 'Apr 20, 2024',  'Block': '840,000',   'Reward': '3.125 BTC',  'BTC Price': '~$64,000', '1Y Later': 'TBD'},
        {'Halving': '5th Halving (Est.)', 'Date': '~Apr 2028',     'Block': '1,050,000', 'Reward': '1.5625 BTC', 'BTC Price': 'TBD',      '1Y Later': 'TBD'},
    ])
    st.dataframe(halving_df, use_container_width=True, hide_index=True)

    st.markdown("### Bitcoin Supply Distribution")
    circ    = data.get('circulating', 19_900_000)
    unmined = 21_000_000 - circ
    lost    = 3_700_000

    fig_supply = go.Figure(go.Pie(
        labels=['Circulating Supply', 'Unmined BTC', 'Est. Lost Coins'],
        values=[circ - lost, unmined, lost],
        hole=0.6,
        marker_colors=['#F7931A', '#2A2A3E', '#FF3D57'],
        textinfo='label+percent',
        textfont=dict(color='#C8C8D8', size=10),
        hovertemplate='<b>%{label}</b><br>%{value:,.0f} BTC<br>%{percent}<extra></extra>',
    ))
    _sl = {k: v for k, v in PLOTLY_DARK.items() if k not in ('legend', 'margin', 'xaxis', 'yaxis')}
    fig_supply.update_layout(
        **_sl,
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#888'), orientation='h', y=-0.1),
        annotations=[dict(text=f'<b>{circ/1e6:.2f}M</b><br>Mined', x=0.5, y=0.5,
                          font_size=13, font_color='#F7931A', showarrow=False)],
    )
    st.plotly_chart(fig_supply, use_container_width=True)

# TAB 5: SIGNAL-ADJUSTED DCA PERFORMANCE
# ═════════════════════════════════════════════════════════════════════════════
with tab5:
    import os as _os
    import pytz as _pytz
    from datetime import date as _date, timedelta as _td, datetime as _dt

    _eastern      = _pytz.timezone('America/New_York')
    HISTORY_FILE  = _os.path.join(_os.path.dirname(__file__), 'signal_history.json')
    LAUNCH_DATE   = _date(2025, 2, 24)   # First Monday at launch

    # ── Record today's signal state ──
    today_str = _date.today().isoformat()
    try:
        if _os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as _fh:
                sig_history = json.load(_fh)
        else:
            sig_history = {}
        if today_str not in sig_history:
            sig_history[today_str] = verdict
            with open(HISTORY_FILE, 'w') as _fh:
                json.dump(sig_history, _fh)
    except Exception:
        sig_history = {}

    DCA_MULT = {
        'High Historical Value Zone':      1.5,
        'Value Accumulation Zone':      1.0,
        'Neutral Data Zone': 0.5,
        'Elevated Risk Zone':  0.25,
        'High Risk Zone':   0.0,
    }

    def _get_monday_930_utc(ref_date):
        """Return the UTC timestamp for Monday 9:30 AM ET of the week containing ref_date."""
        days_since_monday = ref_date.weekday()          # 0=Mon … 6=Sun
        monday = ref_date - _td(days=days_since_monday)
        naive  = _dt(monday.year, monday.month, monday.day, 9, 30, 0)
        et_dt  = _eastern.localize(naive)               # Handles EST/EDT automatically
        return et_dt.astimezone(_pytz.utc), monday

    def _get_execution_price(monday_date, btc_hourly):
        """
        Find the BTC close of the 9:00 AM ET hourly candle on the given Monday.
        Fallback order: 9:00 AM ET → 10:00 AM ET → daily close.
        """
        for fallback_hour in [9, 10]:
            for ts, row in btc_hourly.iterrows():
                et_ts = ts.tz_convert('America/New_York')
                if et_ts.date() == monday_date and et_ts.hour == fallback_hour:
                    return float(row['Close'].iloc[0]) if hasattr(row['Close'], 'iloc') else float(row['Close']), fallback_hour
        return None, None

    st.markdown("## 📉 Signal-Adjusted DCA Performance")
    st.markdown("""
    <div class="info-box" style="margin-bottom:14px;">
    Simulates two strategies since this tool launched on <b>Feb 24, 2025</b>.<br>
    <b>Standard DCA</b> invests a fixed weekly amount regardless of signal.<br>
    <b>Signal-Adjusted DCA</b> scales the weekly amount based on the Overall Accumulation Signal:<br>
    High Historical Value Zone = 150% &nbsp;·&nbsp; Value Accumulation Zone = 100% &nbsp;·&nbsp; Neutral Data Zone = 50% &nbsp;·&nbsp; Elevated Risk Zone = 25% &nbsp;·&nbsp; High Risk Zone = 0%.<br><br>
    Weekly allocations are executed at <b>US market open (Monday 9:30 AM ET)</b>. BTC price is sourced
    from the 9:00–10:00 AM ET hourly candle via Yahoo Finance — the closest available resolution to the
    9:30 AM open. Signal state is recorded as of the same timestamp. Both strategies use identical
    execution timing. Signal history is recorded daily going forward — no retroactive data.
    </div>
    """, unsafe_allow_html=True)

    weekly_dca = st.number_input("Weekly DCA Amount ($)", min_value=10, max_value=100000,
                                  value=100, step=10, key="dca_amount")

    # ── Count how many Mondays have elapsed since launch ──
    mondays_elapsed = []
    cursor = LAUNCH_DATE
    today  = _date.today()
    while cursor <= today:
        if cursor.weekday() == 0:
            mondays_elapsed.append(cursor)
        cursor += _td(days=1)

    if len(mondays_elapsed) < 2:
        st.markdown("""
        <div style="background:#12121F; border:1px solid #1E1E2E; border-radius:12px; padding:30px; text-align:center; margin-top:20px;">
            <div style="font-size:1.4rem; color:#F7931A; font-weight:700; margin-bottom:8px;">📡 Tracking Started</div>
            <div style="color:#888; font-size:0.88rem;">Signal history is being recorded from today.<br>
            Check back next week to see the first comparison data point.</div>
            <div style="color:#555; font-size:0.75rem; margin-top:12px;">
            Launch: Feb 24, 2025 · Executions: Monday 9:30 AM ET · Signals recorded daily</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        try:
            import yfinance as _yf
            # Fetch hourly data from launch to today for Monday price resolution
            _btc_h = _yf.download('BTC-USD',
                                   start=LAUNCH_DATE.isoformat(),
                                   end=(today + _td(days=1)).isoformat(),
                                   interval='1h', progress=False, auto_adjust=True)
        except Exception:
            _btc_h = None

        if _btc_h is None or len(_btc_h) == 0:
            st.warning("Unable to fetch BTC price history. Please try again shortly.")
        elif not sig_history:
            st.markdown("""
            <div style="background:#12121F; border:1px solid #1E1E2E; border-radius:12px; padding:30px; text-align:center; margin-top:20px;">
                <div style="font-size:1.4rem; color:#F7931A; font-weight:700; margin-bottom:8px;">📡 Tracking Started</div>
                <div style="color:#888; font-size:0.88rem;">Signal history is being recorded from today.<br>
                Check back next week to see the first comparison data point.</div>
                <div style="color:#555; font-size:0.75rem; margin-top:12px;">
                Launch: Feb 24, 2025 · Executions: Monday 9:30 AM ET · Signals recorded daily</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            dates_sorted  = sorted(sig_history.keys())
            std_btc = adj_btc = std_invested = adj_invested = 0.0
            std_curve, adj_curve, date_labels = [], [], []
            current_price = float(price)
            fallback_log  = []

            for monday in mondays_elapsed[:-1]:   # Exclude current week (in progress)
                exec_price, used_hour = _get_execution_price(monday, _btc_h)
                if exec_price is None:
                    fallback_log.append(f"{monday} — no hourly data, skipped")
                    continue
                if used_hour != 9:
                    fallback_log.append(f"{monday} — used {used_hour}:00 AM ET (9:00 unavailable)")

                # Signal state: find closest recorded signal to this Monday
                closest_sig_date = min(dates_sorted, key=lambda d: abs(
                    (_date.fromisoformat(d) - monday).days))
                wk_signal = sig_history.get(closest_sig_date, 'Neutral Data Zone')

                std_btc      += weekly_dca / exec_price
                adj_amount    = weekly_dca * DCA_MULT.get(wk_signal, 0.5)
                adj_btc      += adj_amount / exec_price
                std_invested += weekly_dca
                adj_invested += adj_amount

                std_curve.append(std_btc * current_price)
                adj_curve.append(adj_btc * current_price)
                date_labels.append(monday.isoformat())

            std_value = std_btc * current_price
            adj_value = adj_btc * current_price
            std_pnl   = std_value - std_invested
            adj_pnl   = adj_value - adj_invested
            std_pct   = (std_pnl / std_invested * 100) if std_invested > 0 else 0
            adj_pct   = (adj_pnl / adj_invested * 100) if adj_invested > 0 else 0
            diff_usd  = adj_value - std_value
            diff_pct  = ((adj_value / std_value) - 1) * 100 if std_value > 0 else 0

            _cs = "background:#12121F; border:1px solid #1E1E2E; border-radius:10px; padding:14px 16px; text-align:center;"
            _ls = "font-size:0.62rem; color:#555; font-weight:600; letter-spacing:1px; text-transform:uppercase; margin-bottom:6px;"
            _vs = "font-family:'JetBrains Mono',monospace; font-size:1.0rem; font-weight:700;"
            _ss = "font-size:0.68rem; color:#666; margin-top:3px;"

            c1, c2, c3 = st.columns(3)
            with c1:
                pc = '#00C853' if std_pnl >= 0 else '#FF3D57'
                st.markdown(f'<div style="{_cs}"><div style="{_ls}">Standard DCA</div>'
                            f'<div style="{_vs} color:#ccc;">Invested: ${std_invested:,.0f}</div>'
                            f'<div style="{_vs} color:#F7931A;">Value: ${std_value:,.0f}</div>'
                            f'<div style="{_vs} color:{pc};">P&L: ${std_pnl:+,.0f} ({std_pct:+.1f}%)</div>'
                            f'<div style="{_ss}">{std_btc:.6f} BTC accumulated</div></div>',
                            unsafe_allow_html=True)
            with c2:
                pc2 = '#00C853' if adj_pnl >= 0 else '#FF3D57'
                st.markdown(f'<div style="{_cs}"><div style="{_ls}">Signal-Adjusted DCA</div>'
                            f'<div style="{_vs} color:#ccc;">Invested: ${adj_invested:,.0f}</div>'
                            f'<div style="{_vs} color:#F7931A;">Value: ${adj_value:,.0f}</div>'
                            f'<div style="{_vs} color:{pc2};">P&L: ${adj_pnl:+,.0f} ({adj_pct:+.1f}%)</div>'
                            f'<div style="{_ss}">{adj_btc:.6f} BTC accumulated</div></div>',
                            unsafe_allow_html=True)
            with c3:
                dc = '#00C853' if diff_usd >= 0 else '#FF3D57'
                dl = "Signal-Adjusted leads" if diff_usd >= 0 else "Standard DCA leads"
                st.markdown(f'<div style="{_cs}"><div style="{_ls}">Difference</div>'
                            f'<div style="{_vs} color:{dc};">${diff_usd:+,.0f}</div>'
                            f'<div style="{_vs} color:{dc};">{diff_pct:+.1f}%</div>'
                            f'<div style="{_ss}">{dl}</div></div>',
                            unsafe_allow_html=True)

            if len(date_labels) > 1:
                fig_dca = go.Figure()
                fig_dca.add_trace(go.Scatter(x=date_labels, y=std_curve,
                    name='Standard DCA', line=dict(color='#555', width=2),
                    hovertemplate='%{x}<br>$%{y:,.0f}<extra>Standard DCA</extra>'))
                fig_dca.add_trace(go.Scatter(x=date_labels, y=adj_curve,
                    name='Signal-Adjusted', line=dict(color='#00C853', width=2.5),
                    fill='tonexty', fillcolor='rgba(0,200,83,0.06)',
                    hovertemplate='%{x}<br>$%{y:,.0f}<extra>Signal-Adjusted</extra>'))
                fig_dca.update_layout(**PLOTLY_DARK, height=300,
                    title=dict(text='Portfolio Value Since Launch (Monday 9:30 AM ET executions)',
                               font=dict(size=13, color='#888')),
                    yaxis_tickprefix='$',
                    legend=dict(orientation='h', y=1.08, x=0))
                st.plotly_chart(fig_dca, use_container_width=True)

            if fallback_log:
                with st.expander("⚠️ Price resolution fallbacks"):
                    for entry in fallback_log:
                        st.caption(entry)

            st.markdown('<div style="font-size:0.68rem; color:#444; text-align:center; margin-top:4px;">'
                        'Executions: Monday 9:30 AM ET · Price: Yahoo Finance hourly · '
                        'Launch: Feb 24, 2025 · Not financial advice</div>',
                        unsafe_allow_html=True)



# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Join the Beta — Email Capture
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Telegram & Beta — Side-by-Side
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
_tg_col, _beta_col = st.columns(2, gap="medium")

with _tg_col:
    st.markdown("""
    <div style="background:#12121F; border:1px solid #1E1E2E; border-radius:14px; padding:22px 24px; height:100%;">
        <div style="font-size:0.7rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#29B6F6; margin-bottom:8px;">📡 TELEGRAM ALERTS</div>
        <div style="font-size:1.05rem; font-weight:700; color:#E8E8F0; margin-bottom:8px;">Stay informed when the data shifts</div>
        <div style="font-size:0.82rem; color:#888; line-height:1.65; margin-bottom:4px;">
            Receive a data update the moment the signal zone changes — <strong style="color:#C8C8D8;">Value Zone, Neutral, or Risk Zone</strong>.
        </div>
        <div style="font-size:0.75rem; color:#555; line-height:1.5; margin-bottom:18px;">
            No noise. Just the data. Message the bot anytime for a live indicator snapshot.
        </div>
        <a href="https://t.me/BTCPulse_app_bot" target="_blank"
           style="display:block; text-align:center; background:rgba(41,182,246,0.15);
                  border:1px solid rgba(41,182,246,0.4); color:#29B6F6; font-weight:700;
                  padding:10px 16px; border-radius:10px; text-decoration:none; font-size:0.88rem;">
            Subscribe on Telegram →
        </a>
    </div>
    """, unsafe_allow_html=True)

with _beta_col:
    st.markdown("""
    <div style="background:#12121F; border:1px solid rgba(247,147,26,0.3); border-radius:14px; padding:22px 24px;">
        <div style="font-size:0.7rem; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#F7931A; margin-bottom:8px;">🚀 JOIN THE BETA</div>
        <div style="font-size:1.05rem; font-weight:700; color:#E8E8F0; margin-bottom:8px;">Early access & new features</div>
        <div style="font-size:0.82rem; color:#666; line-height:1.65; margin-bottom:14px;">
            Get early access to email summaries, new indicators, and help shape the roadmap.
        </div>
    </div>
    """, unsafe_allow_html=True)
    with st.form("beta_signup_form", clear_on_submit=True):
        _beta_email = st.text_input("Email address", placeholder="your@email.com", label_visibility="collapsed")
        _beta_submit = st.form_submit_button("Request Early Access", use_container_width=True)
        if _beta_submit:
            if _beta_email and "@" in _beta_email and "." in _beta_email:
                try:
                    import json as _jbs
                    _ac_file = os.path.join(os.path.dirname(__file__), ".alert_cache.json")
                    _sig_now = ""
                    if os.path.exists(_ac_file):
                        with open(_ac_file) as _acf:
                            _acd = _jbs.load(_acf)
                        _sig_now = "%s (%s)" % (_acd.get("last_verdict", ""), _acd.get("last_score", ""))
                except Exception:
                    _sig_now = ""
                _saved = _save_beta_signup(_beta_email, signal_at_signup=_sig_now)
                if _saved:
                    st.success("✅ You're on the list!")
                else:
                    st.info("Already signed up — we'll be in touch!")
            else:
                st.warning("Please enter a valid email address.")
    st.markdown('<div style="font-size:0.68rem; color:#333; text-align:center; margin-top:4px;">No spam. Unsubscribe anytime.</div>', unsafe_allow_html=True)

# Contact / Feedback
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:32px; background:#12121F; border:1px solid #1E1E2E; border-radius:12px; padding:20px 24px; text-align:center;">
    <div style="font-size:0.72rem; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#F7931A; margin-bottom:8px;">
        Feature Request or Bug Report
    </div>
    <div style="font-size:0.82rem; color:#888; margin-bottom:12px;">
        Have a suggestion or found a bug? Send a message directly.
    </div>
    <a href="mailto:beaumckee@gmail.com?subject=Bitcoin%20Accumulation%20Index%20Feedback"
       style="display:inline-block; background:rgba(247,147,26,0.12); border:1px solid rgba(247,147,26,0.3);
              color:#F7931A; font-size:0.82rem; font-weight:600; padding:10px 24px; border-radius:8px;
              text-decoration:none; letter-spacing:0.5px;">
        ✉ Email beaumckee@gmail.com
    </a>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Footer — ASIC-Compliant Disclaimer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='
    margin-top: 40px;
    padding: 20px 24px;
    border-top: 1px solid #1E1E2E;
    border-radius: 0 0 12px 12px;
    background: linear-gradient(135deg, #0D0D18, #110A00);
    border: 1px solid #2A1A00;
    border-radius: 12px;
    margin-bottom: 12px;
'>
    <div style='
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #F7931A;
        margin-bottom: 10px;
    '>⚠️ General Information Only</div>
    <div style='
        font-size: 0.78rem;
        color: #888;
        line-height: 1.75;
        margin-bottom: 12px;
    '>
        <strong style='color:#aaa;'>BTCpulse.app is a data aggregation and educational tool.</strong>
        We are <strong style='color:#aaa;'>NOT financial advisors</strong> and do not hold an Australian Financial Services Licence (AFSL).
        All content on this site — including the Overall Signal, zone labels, indicator readings, and any AI-generated commentary —
        is <strong style='color:#aaa;'>factual data and mathematical analysis only</strong>, not financial advice.
        Bitcoin and other digital assets are <strong style='color:#aaa;'>highly volatile</strong>; past performance and historical patterns
        do not predict future results. Always perform your own due diligence and consult a licensed financial adviser
        before making any investment decisions.
    </div>
    <div style='font-size:0.68rem; color:#444; line-height:2; text-align:center; border-top:1px solid #1E1E2E; padding-top:10px;'>
        Data: CoinGecko &middot; alternative.me &middot; CoinGlass &middot; Yahoo Finance &middot; FRED API
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        Auto-refreshes every 5 minutes
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        Overall Signal is a consensus of all {total_sigs} indicators
        <br>
        Built by <strong style='color:#555;'>Beau McKee</strong>
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        <a href='mailto:beaumckee@gmail.com' style='color:#F7931A; text-decoration:none;'>beaumckee@gmail.com</a>
    </div>
</div>
""", unsafe_allow_html=True)

# Auto-refresh every 5 minutes
components.html("""
<script>
    setTimeout(function() { window.location.reload(); }, 300000);
</script>
""", height=0)

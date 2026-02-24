"""
₿ Bitcoin Accumulation Signal Dashboard — v3
Dark mode · Live signals · Market vibe · AUD pricing · Hover tooltips
"""

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bitcoin Accumulation Signals",
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
        "Contrarian signal — extreme fear historically marks the best buying opportunities. "
        "Weight: moderate (sentiment can persist)."
    ),
    'MVRV Z-Score': (
        "Market Value ÷ Realised Value, normalised as a Z-score. "
        "Realised Value = what every coin last moved on-chain was worth. "
        "Below 0 = trading below cost basis of all holders = deep value. "
        "Weight: high — one of the most reliable on-chain cycle indicators."
    ),
    'NUPL (Net Unrealized P&L)': (
        "% of market cap representing unrealised profit or loss. "
        "< 0% = Capitulation. 25–50% = Hope/Fear. > 75% = Euphoria (sell). "
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
        "Weight: high — Crypto Currently's #1 macro signal for cycle timing."
    ),
    'US Dollar Index (DXY)': (
        "Measures USD strength against a basket of 6 major currencies. "
        "Falling DXY = weaker dollar = looser global liquidity = bullish for BTC. "
        "Rising DXY = stronger dollar = tighter liquidity = bearish for BTC. "
        "Weight: moderate — key macro signal tracked by Crypto Currently."
    ),
    'BTC vs S&P 500': (
        "Compares Bitcoin's 90-day return against the S&P 500. "
        "Based on Crypto Currently's analysis: BTC often leads equities — "
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
            'BUY':     f"At {val}, the market is in <b style='color:#00C853'>Extreme Fear</b> — historically one of the best times to accumulate. Most retail investors are selling or avoiding Bitcoin right now.",
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
            'BUY':     f"Mayer Multiple of {val} — price at a <b style='color:#00C853'>significant discount to the 200-day MA</b>. Every time this has been below 0.8, it has been an excellent long-term entry.",
            'CAUTION': f"Mayer Multiple of {val} — price near or slightly above the 200-day MA. Fair value range.",
            'SELL':    f"Mayer Multiple of {val} — price significantly extended above the 200-day MA. Historically, readings above 2.4 have marked overheated conditions.",
        },
        '200-Week MA Heatmap': {
            'BUY':     f"Price is <b style='color:#00C853'>at or below the 200-week MA</b> — every bear market bottom in Bitcoin's history has touched this level. Historically the best accumulation zone.",
            'CAUTION': f"Price is {val} above the 200-week MA — in the normal bull market range. Not a top signal yet, but not the deepest value either.",
            'SELL':    f"Price is {val} above the 200-week MA — historically, being 100%+ above this level has coincided with cycle tops.",
        },
        '2-Year MA Multiplier': {
            'BUY':     f"At {val}, price is <b style='color:#00C853'>below the 2-year moving average</b> — historically the best accumulation zone. Only happens during bear markets.",
            'CAUTION': f"At {val}, price is above the 2-year MA but not yet in the danger zone. Normal bull market territory.",
            'SELL':    f"At {val}, price is significantly above the 2-year MA. Approaching the historical sell zone (5×).",
        },
        'Ahr999 Index': {
            'BUY':     f"Ahr999 at {val} — in the <b style='color:#00C853'>DCA zone</b>. The model suggests Bitcoin is undervalued relative to its growth trajectory and mining cost.",
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
            'SELL':    f"GLI at {val} — <b style='color:#FF3D57'>significant liquidity contraction</b>. This is the macro headwind Crypto Currently has been warning about. Tightening conditions are a major risk for Bitcoin.",
        },
        'US Dollar Index (DXY)': {
            'BUY':     f"DXY at {val} — <b style='color:#00C853'>weak or falling dollar</b>. A declining DXY loosens global liquidity and is historically bullish for Bitcoin and risk assets.",
            'CAUTION': f"DXY at {val} — dollar consolidating. Watch for breakout direction as it will drive liquidity conditions for Bitcoin.",
            'SELL':    f"DXY at {val} — <b style='color:#FF3D57'>strong or rising dollar</b>. A strengthening DXY tightens global liquidity and historically pressures Bitcoin prices.",
        },
        'BTC vs S&P 500': {
            'BUY':     f"{val} — <b style='color:#00C853'>BTC is deeply oversold vs equities</b>. Based on Crypto Currently's analysis, this divergence has historically preceded strong BTC mean-reversion rallies (2018, 2022 examples).",
            'CAUTION': f"{val} — BTC and the S&P 500 are broadly correlated. No strong divergence signal in either direction.",
            'SELL':    f"{val} — <b style='color:#FF3D57'>BTC is significantly outperforming equities</b>. Crypto Currently notes that BTC leading equities to the upside is a late-cycle signal — historically precedes a top.",
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

    # Fetch AUD/USD exchange rate
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=8)
        if r.status_code == 200:
            aud_rate = r.json().get('rates', {}).get('AUD', 1.58)
        else:
            aud_rate = 1.58
    except Exception:
        aud_rate = 1.58

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
        'price': price, 'price_aud': price * 1.58,
        'chg_24h': chg_24h, 'chg_7d': chg_7d,
        'fear_greed': fg, 'fear_greed_label': fg_label,
        'btc_dominance': dominance,
    }
    mock_signals = (
        [{'signal': 'BUY'}] * buy_n +
        [{'signal': 'CAUTION'}] * caution_n +
        [{'signal': 'SELL'}] * sell_n
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
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div class="dash-title">₿ Bitcoin Accumulation Signals</div>
            <div class="dash-subtitle">Is now a good time to buy Bitcoin? &nbsp;·&nbsp; {datetime.utcnow().strftime('%B %d, %Y %H:%M UTC')}</div>
        </div>
        <div class="live-badge"><div class="live-dot"></div>LIVE</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Price Strip
# ─────────────────────────────────────────────────────────────────────────────
chg_col   = '#00C853' if chg_24h >= 0 else '#FF3D57'
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
        <div class="metric-sub" style="color:{chg_col};">{chg_arrow} {abs(chg_24h):.2f}% (24h) · Rate: {aud_rate:.4f}</div>
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

# Build the live commentary for the 200W MA banner tooltip
_val_commentary_map = {
    'Very Cheap':    f"Price is <b style='color:#1565C0'>below the 200W MA</b> at ${_ma200w:,.0f} — this is the deepest accumulation zone in Bitcoin's history. Every single bear market bottom has touched or gone below this level. An extremely rare and historically significant buying opportunity.",
    'Cheap':         f"At {_pct_200w:+.1f}% above the 200W MA (${_ma200w:,.0f}), Bitcoin is in the <b style='color:#00897B'>Cheap zone</b>. Historically, the 0–50% extension range has been one of the best accumulation windows of the entire cycle — well below the euphoria levels seen at cycle tops.",
    'Fair Value':    f"At {_pct_200w:+.1f}% above the 200W MA (${_ma200w:,.0f}), Bitcoin is in the <b style='color:#F9A825'>Fair Value zone</b>. This is normal bull market territory. Not the deepest discount, but not overextended either. Dollar-cost averaging remains reasonable.",
    'Expensive':     f"At {_pct_200w:+.1f}% above the 200W MA (${_ma200w:,.0f}), Bitcoin is in the <b style='color:#E65100'>Expensive zone</b>. Historically, the 100–150% extension range has been associated with late-cycle conditions. Consider reducing new exposure and tightening risk management.",
    'Very Expensive': f"At {_pct_200w:+.1f}% above the 200W MA (${_ma200w:,.0f}), Bitcoin is in the <b style='color:#B71C1C'>Very Expensive zone</b>. This extension level has historically coincided with cycle tops. Crypto Currently's model suggests extreme caution — this is a distribution zone, not an accumulation zone.",
}
_val_tooltip_what = "The 200-Week Moving Average (200W MA) is the average closing price of Bitcoin over the last 200 weeks (~4 years). It represents the long-term cost basis of the entire market. Every Bitcoin bear market bottom in history has touched or gone below this level. Crypto Currently uses extensions from this level to define valuation regions: Very Cheap (below), Cheap (0–50%), Fair Value (50–100%), Expensive (100–150%), Very Expensive (>150%)."
_val_tooltip_now  = _val_commentary_map.get(_val_region, '')

st.markdown(f"""
<div style="background:{_val_bg}; border:1px solid {_val_border}; border-radius:12px; padding:14px 20px; margin-bottom:10px;">
  <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
    <div style="display:flex; align-items:center; gap:14px;">
      <div>
        <div class="card-tooltip-wrap" style="font-size:0.65rem; color:#888; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:2px; cursor:help; display:inline-block;">200W MA Valuation &nbsp;<span style="color:#555; font-size:0.6rem;">&#9432;</span>
          <div class="card-tooltip-popup" style="width:300px;">
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
  <div style="font-size:0.6rem; color:#444; margin-top:6px; text-align:right;">Not part of the accumulation score &nbsp;·&nbsp; Model: Crypto Currently / 200W MA Extension</div>
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
# Overall Verdict Banner
# ─────────────────────────────────────────────────────────────────────────────
verdict_bg_map = {
    'STRONG BUY':       'linear-gradient(135deg, rgba(0,200,83,0.12), rgba(0,200,83,0.04))',
    'ACCUMULATE':       'linear-gradient(135deg, rgba(105,240,174,0.10), rgba(105,240,174,0.03))',
    'NEUTRAL — WATCH':  'linear-gradient(135deg, rgba(255,193,7,0.10), rgba(255,193,7,0.03))',
    'CAUTION — HOLD':   'linear-gradient(135deg, rgba(255,107,53,0.12), rgba(255,107,53,0.04))',
    'SELL / REDUCE':    'linear-gradient(135deg, rgba(255,61,87,0.12), rgba(255,61,87,0.04))',
}
verdict_border_map = {
    'STRONG BUY':       'rgba(0,200,83,0.3)',
    'ACCUMULATE':       'rgba(105,240,174,0.25)',
    'NEUTRAL — WATCH':  'rgba(255,193,7,0.3)',
    'CAUTION — HOLD':   'rgba(255,107,53,0.3)',
    'SELL / REDUCE':    'rgba(255,61,87,0.3)',
}
verdict_desc_map = {
    'STRONG BUY':       'Multiple indicators are deep in buy zones. Historically excellent accumulation conditions.',
    'ACCUMULATE':       'Majority of indicators favour accumulation. A good time to dollar-cost average into Bitcoin.',
    'NEUTRAL — WATCH':  'Mixed signals across indicators. Monitor closely before committing large positions.',
    'CAUTION — HOLD':   'Several indicators are elevated. Hold existing positions; avoid aggressive buying.',
    'SELL / REDUCE':    'Most indicators signal cycle top territory. Consider reducing exposure.',
}
vbg     = verdict_bg_map.get(verdict, verdict_bg_map['NEUTRAL — WATCH'])
vborder = verdict_border_map.get(verdict, 'rgba(255,193,7,0.3)')
vdesc   = verdict_desc_map.get(verdict, '')

st.markdown(f"""
<div class="verdict-banner" style="background:{vbg}; border:1px solid {vborder};">
    <div class="verdict-title">Overall Accumulation Signal</div>
    <div class="verdict-text" style="color:{v_color};">{verdict}</div>
    <div class="verdict-sub">{vdesc}</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Signal Score Bar
# ─────────────────────────────────────────────────────────────────────────────
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
            <span class="count-label" style="color:#00C853;">BUY</span>
        </div>
        <div class="count-pill" style="background:rgba(255,193,7,0.08); border:1px solid rgba(255,193,7,0.18);">
            <span style="color:#FFC107;">{caution_n}</span>
            <span class="count-label" style="color:#FFC107;">CAUTION</span>
        </div>
        <div class="count-pill" style="background:rgba(255,61,87,0.08); border:1px solid rgba(255,61,87,0.18);">
            <span style="color:#FF3D57;">{sell_n}</span>
            <span class="count-label" style="color:#FF3D57;">SELL</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Signal Tracker",
    "📈 Price Chart",
    "⛏️ Halving Cycle",
    "ℹ️ Indicator Guide",
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
                <div class="so-val">{s['value_str']}</div>
            </div>"""

    overview_html = f"""
    <style>
    * {{ box-sizing:border-box; }}
    body {{ background:#12121F; margin:0; padding:3px 6px 2px 6px; }}

    .so-row {{
        display:grid;
        grid-template-columns: 1fr 90px 80px;
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

    /* Tooltip popup — opens downward */
    .so-tooltip {{
        visibility:hidden; opacity:0;
        position:absolute; z-index:9999;
        left:0; top:calc(100% + 6px);
        width:300px; min-width:200px;
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
    .so-val {{
        font-family:'JetBrains Mono',monospace; font-size:0.70rem;
        color:#666; text-align:right; white-space:nowrap;
        width:80px; overflow:hidden; text-overflow:ellipsis;
    }}
    </style>
    <div style="background:#12121F; border:1px solid #1E1E2E; border-radius:10px; padding:2px 4px;">
    {rows_html}
    </div>
    """
    components.html(overview_html, height=len(signals) * 30 + 20, scrolling=False)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

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
        icon = cat_icons.get(cat, '•')
        st.markdown(f'<div class="category-header">{icon} {cat}</div>', unsafe_allow_html=True)

        cols = st.columns(3)
        for i, s in enumerate(items):
            badge_class   = f"badge-{s['signal'].lower()}"
            card_class    = f"card-{s['signal'].lower()}"
            tooltip_txt   = TOOLTIPS.get(s['name'], s.get('description', ''))
            commentary    = zone_commentary(s)

            zone_html = f"""
            <div class="zone-thresholds">
                <span class="zone-buy">🟢 {s['buy_zone']}</span>
                <span class="zone-sell">🔴 {s['sell_zone']}</span>
            </div>"""

            with cols[i % 3]:
                st.markdown(f"""
                <div class="indicator-card {card_class}" style="position:relative; overflow:visible;">
                    <div class="card-header">
                        <div style="flex:1; min-width:0;">
                            <div class="card-tooltip-wrap">
                                <div class="card-name">{s['name']} <span style="font-size:0.6rem; color:#444; font-weight:400;">ℹ</span></div>
                                <div class="card-tooltip-popup">
                                    <div class="ct-what">{tooltip_txt}</div>
                                    <div class="ct-divider"></div>
                                    <div class="ct-now">{commentary}</div>
                                </div>
                            </div>
                            <div class="card-category">{s['category']}</div>
                        </div>
                        <span class="signal-badge {badge_class}">{s['emoji']} {s['signal']}</span>
                    </div>
                    <div class="card-value" style="color:{s['color']};">{s['value_str']}</div>
                    <div class="card-detail">{s['detail']}</div>
                    {zone_html}
                    <div class="zone-commentary">{commentary}</div>
                </div>
                """, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
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
        phase_signal = "🟢 ACCUMULATE"
        p_badge      = "buy"
    elif cycle_pct < 50:
        phase_name   = "Bull Market Build-Up"
        phase_desc   = "The supply shock begins to take effect. Institutional and retail demand typically increases. Historically, this phase sees strong price appreciation — we are likely in the early-to-mid bull market."
        phase_signal = "🟢 ACCUMULATE / HOLD"
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
        phase_desc   = "Approaching the next halving. Historically the best time to accumulate Bitcoin as prices are near cycle lows and sentiment is at extreme fear. The next supply shock is approaching."
        phase_signal = "🟢 STRONG ACCUMULATE"
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

# ═════════════════════════════════════════════════════════════════════════════
# TAB 4: INDICATOR GUIDE
# ═════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Indicator Reference Guide")
    st.markdown("""
    <div class="info-box">
    This dashboard tracks the key Bitcoin accumulation indicators from the Bitcoin cycle analysis framework.
    Each indicator is assigned a signal based on its historical buy/sell zones. The <b>Overall Verdict</b> is a
    consensus of all signals — when most indicators are in the green, it has historically been an excellent time to accumulate Bitcoin.
    Hover over any indicator name on the Signal Tracker tab for a detailed explanation and live commentary.
    </div>
    """, unsafe_allow_html=True)

    guide_data = [
        {'Indicator': 'Fear & Greed Index',    'Category': 'Sentiment',        'Buy Zone': '< 25',        'Caution': '25–55',       'Sell Zone': '> 75',       'Weight': 'Moderate', 'Why It Matters': 'Contrarian — buy when others fear'},
        {'Indicator': 'MVRV Z-Score',          'Category': 'On-Chain',         'Buy Zone': '< 0',         'Caution': '0–3',         'Sell Zone': '> 5',        'Weight': 'High',     'Why It Matters': 'Best on-chain cycle bottom/top indicator'},
        {'Indicator': 'NUPL',                  'Category': 'On-Chain',         'Buy Zone': '< 25%',       'Caution': '25–50%',      'Sell Zone': '> 75%',      'Weight': 'High',     'Why It Matters': 'Measures holder psychology directly'},
        {'Indicator': 'Puell Multiple',        'Category': 'On-Chain',         'Buy Zone': '< 0.5',       'Caution': '0.5–2.2',     'Sell Zone': '> 2.2',      'Weight': 'Moderate', 'Why It Matters': 'Miner capitulation = buy signal'},
        {'Indicator': 'RHODL Ratio',           'Category': 'On-Chain',         'Buy Zone': '< 5,000',     'Caution': '5k–50k',      'Sell Zone': '> 50,000',   'Weight': 'Moderate', 'Why It Matters': 'LTH dominance = accumulation phase'},
        {'Indicator': 'Reserve Risk',          'Category': 'On-Chain',         'Buy Zone': '< 0.0012',    'Caution': '0.0012–0.005','Sell Zone': '> 0.005',    'Weight': 'Moderate', 'Why It Matters': 'HODLer conviction vs risk'},
        {'Indicator': 'Mayer Multiple',        'Category': 'Price Model',      'Buy Zone': '< 0.8',       'Caution': '0.8–1.5',     'Sell Zone': '> 2.4',      'Weight': 'High',     'Why It Matters': 'Below 0.8 always been great buy'},
        {'Indicator': '200-Week MA',           'Category': 'Price Model',      'Buy Zone': 'Below 200W',  'Caution': '0–100%',      'Sell Zone': '> 100%',     'Weight': 'High',     'Why It Matters': 'Every bear bottom has touched this'},
        {'Indicator': '2-Year MA Multiplier',  'Category': 'Price Model',      'Buy Zone': '< 1.0×',      'Caution': '1–3.5×',      'Sell Zone': '> 3.5×',     'Weight': 'Moderate', 'Why It Matters': 'Below 2yr MA = accumulation zone'},
        {'Indicator': 'Ahr999 Index',          'Category': 'Price Model',      'Buy Zone': '< 0.45',      'Caution': '0.45–1.2',    'Sell Zone': '> 4.0',      'Weight': 'Moderate', 'Why It Matters': 'DCA zone when < 0.45'},
        {'Indicator': 'RSI (14-Day)',          'Category': 'Technical',        'Buy Zone': '< 30',        'Caution': '30–70',       'Sell Zone': '> 70',       'Weight': 'Low-Mod',  'Why It Matters': 'Short-term momentum signal'},
        {'Indicator': 'RSI Weekly',            'Category': 'Technical',        'Buy Zone': '< 35',        'Caution': '35–65',       'Sell Zone': '> 80',       'Weight': 'Moderate', 'Why It Matters': 'Weekly oversold = major signal'},
        {'Indicator': 'Pi Cycle Top',          'Category': 'Technical',        'Buy Zone': 'Not triggered','Caution': 'Approaching', 'Sell Zone': 'Triggered',  'Weight': 'High',     'Why It Matters': 'Called every cycle top within 3 days'},
        {'Indicator': 'BTC Dominance',         'Category': 'Market Structure', 'Buy Zone': '> 60%',       'Caution': '50–60%',      'Sell Zone': '< 45%',      'Weight': 'Moderate', 'Why It Matters': 'High dom = early cycle, safe for BTC'},
        {'Indicator': 'Altcoin Season Index',  'Category': 'Market Structure', 'Buy Zone': '< 25',        'Caution': '25–75',       'Sell Zone': '> 75',       'Weight': 'Moderate', 'Why It Matters': 'Altcoin season = late cycle'},
        {'Indicator': 'CBBI',                  'Category': 'Market Structure', 'Buy Zone': '< 30',        'Caution': '30–65',       'Sell Zone': '> 90',       'Weight': 'High',     'Why It Matters': '9-indicator composite cycle score'},
    ]

    guide_df = pd.DataFrame(guide_data)
    st.dataframe(guide_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("""
    <div class="info-box">
    <b>Disclaimer:</b> This dashboard is for educational and informational purposes only.
    It does not constitute financial advice. Bitcoin is a highly volatile asset.
    Always do your own research and consult a financial advisor before making investment decisions.
    Past indicator performance does not guarantee future results.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-top:40px; padding:20px 0 10px 0; border-top:1px solid #1E1E2E; text-align:center;'>
    <div style='font-size:0.72rem; color:#444; line-height:2;'>
        Data: CoinGecko &middot; alternative.me &middot; CoinGlass &middot; Yahoo Finance &middot; FRED API
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        Auto-refreshes every 5 minutes
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        The Overall Verdict is a weighted consensus of all 18 indicators
    </div>
    <div style='font-size:0.70rem; color:#333; margin-top:6px;'>
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        <a href='mailto:beaumckee@gmail.com' style='color:#F7931A; text-decoration:none;'>beaumckee@gmail.com</a>
        &nbsp;&nbsp;&middot;&nbsp;&nbsp;
        <span style='color:#333;'>Not financial advice.</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Auto-refresh every 5 minutes
components.html("""
<script>
    setTimeout(function() { window.location.reload(); }, 300000);
</script>
""", height=0)

"""
Market Vibe Generator — generates a short AI market commentary paragraph
based on current Bitcoin indicator data.
"""

import os
from openai import OpenAI


def _get_openai_client() -> OpenAI:
    """
    Returns an OpenAI client, reading the API key from:
    1. Streamlit secrets (st.secrets) — used when deployed on Streamlit Cloud
    2. OPENAI_API_KEY environment variable — used locally / in sandbox
    """
    api_key = None
    try:
        import streamlit as st
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return OpenAI(api_key=api_key)
    return OpenAI()  # relies on OPENAI_API_KEY env var set by the platform


def generate_market_vibe(data: dict, signals: list, verdict: str) -> str:
    """
    Generate a 2-3 sentence market vibe summary using GPT.
    Returns a plain string (no markdown).
    """
    try:
        client = _get_openai_client()

        price     = data.get('price', 0)
        price_aud = data.get('price_aud', 0)
        chg_24h   = data.get('chg_24h', 0)
        chg_7d    = data.get('chg_7d', 0)
        fg        = data.get('fear_greed', 50)
        fg_label  = data.get('fear_greed_label', 'Neutral')
        dominance = data.get('btc_dominance', 55)

        buy_n     = sum(1 for s in signals if s['signal'] == 'BUY')
        caution_n = sum(1 for s in signals if s['signal'] == 'CAUTION')
        sell_n    = sum(1 for s in signals if s['signal'] == 'SELL')

        # Find notable signals
        buy_names    = [s['name'] for s in signals if s['signal'] == 'BUY'][:3]
        caution_names= [s['name'] for s in signals if s['signal'] == 'CAUTION'][:2]

        system_msg = (
            "You are BTCpulse, a data-driven Bitcoin market analysis tool. "
            "You write in a calm, analytical, trustworthy tone — like a knowledgeable friend who follows Bitcoin closely. "
            "You describe what the data shows, never what anyone should do. "
            "You are not a financial adviser. No investment advice, no buy/sell recommendations, no hype, no doom."
        )

        prompt = f"""Write a 2-3 sentence daily market vibe summary (max 100 words) for the BTCpulse dashboard.

Current data:
- BTC Price: ${price:,.0f} USD (A${price_aud:,.0f} AUD)
- 24h Change: {chg_24h:+.2f}% · 7d Change: {chg_7d:+.2f}%
- Fear & Greed Index: {fg}/100 ({fg_label})
- BTC Dominance: {dominance:.1f}%
- Indicator Distribution: {buy_n} Value Zone · {caution_n} Neutral · {sell_n} Risk Zone (of {len(signals)} total)
- Overall Signal: {verdict}
- Key Value Zone indicators: {', '.join(buy_names) if buy_names else 'None'}
- Key Neutral indicators: {', '.join(caution_names) if caution_names else 'None'}

Describe what the current data indicates about Bitcoin's market cycle position. Plain factual sentences only. No markdown, no bullet points. This is general information only."""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=180,
            temperature=0.6,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Market vibe error: {e}")
        # Fallback: generate a simple rule-based summary
        return _fallback_vibe(data, signals, verdict)


def _fallback_vibe(data: dict, signals: list, verdict: str) -> str:
    """Rule-based fallback if LLM is unavailable."""
    price   = data.get('price', 0)
    chg_24h = data.get('chg_24h', 0)
    fg      = data.get('fear_greed', 50)
    fg_label= data.get('fear_greed_label', 'Neutral')
    buy_n   = sum(1 for s in signals if s['signal'] == 'BUY')
    total   = len(signals)

    direction = "pulling back" if chg_24h < -2 else ("rallying" if chg_24h > 2 else "consolidating")
    sentiment = "deeply fearful" if fg < 25 else ("greedy" if fg > 65 else "neutral")

    if buy_n >= total * 0.6:
        outlook = "The majority of value indicators are in historically low-risk territory — data consistent with past value accumulation zones."
    elif buy_n >= total * 0.4:
        outlook = "The majority of indicators are in value territory, though some elevated-risk signals remain."
    else:
        outlook = "Mixed signals across indicators — data does not strongly favour either value or risk territory at this time."

    return (f"Bitcoin is {direction} at ${price:,.0f}, with market sentiment currently {sentiment} "
            f"(Fear & Greed: {fg}/100 — {fg_label}). {outlook}")

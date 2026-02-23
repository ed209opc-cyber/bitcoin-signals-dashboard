# ₿ Bitcoin Accumulation Signals Dashboard

A professional dark-mode Streamlit dashboard that answers one question: **Is now a good time to accumulate Bitcoin?**

Tracks 16 on-chain, technical, and sentiment indicators in real time, each showing a colour-coded BUY / CAUTION / SELL signal, with an AI-generated daily market commentary.

---

## Features

- **16 indicators** — Fear & Greed, MVRV Z-Score, NUPL, Puell Multiple, RHODL Ratio, Reserve Risk, Mayer Multiple, 200-Week MA, 2-Year MA Multiplier, Ahr999, RSI (Daily & Weekly), Pi Cycle Top, BTC Dominance, Altcoin Season Index, CBBI
- **Overall Verdict** — weighted consensus signal (STRONG BUY → SELL / REDUCE)
- **AI Market Vibe** — GPT-generated daily commentary, cached once per UTC day
- **AUD pricing** — live BTC/AUD alongside USD
- **Hover tooltips** — every indicator explains itself with live commentary
- **5-year price chart** with halving markers
- **Halving Cycle tab** — countdown, cycle phase, full history
- **Indicator Guide tab** — full reference for all 16 indicators
- Dark mode, Bitcoin orange accent, responsive layout

---

## Quick Start (Local)

```bash
git clone https://github.com/YOUR_USERNAME/bitcoin-signals-dashboard.git
cd bitcoin-signals-dashboard
pip install -r requirements.txt
export OPENAI_API_KEY=sk-your-key-here
streamlit run app.py
```

---

## Deploy to Streamlit Cloud (Free)

1. Push this repo to GitHub (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select your repo → set **Main file path** to `app.py`
4. Under **Advanced settings → Secrets**, add:
   ```toml
   OPENAI_API_KEY = "sk-your-openai-api-key-here"
   ```
5. Click **Deploy** — your dashboard will be live at `https://your-app.streamlit.app`

---

## How the AI Commentary Works

The **Market Vibe** section uses GPT-4.1-mini to write a 2–3 sentence daily analysis. It reads the live indicator data and answers: *is now a good time to accumulate?*

- Generates **once per UTC day** and caches the result to `.daily_vibe_cache.json`
- All subsequent page loads that day serve the cached text (no extra API calls)
- Resets automatically at midnight UTC
- Falls back to a rule-based summary if the API is unavailable
- Cost: ~$0.0004 per day (essentially free)

---

## Data Sources

| Source | Data |
|--------|------|
| [CoinGecko](https://coingecko.com) | Price, market cap, volume, dominance |
| [alternative.me](https://alternative.me/crypto/fear-and-greed-index/) | Fear & Greed Index |
| [CoinGlass](https://coinglass.com) | MVRV, NUPL, Puell, RHODL, Reserve Risk |
| [Yahoo Finance](https://finance.yahoo.com) | Historical OHLCV for price chart |
| [exchangerate-api.com](https://exchangerate-api.com) | AUD/USD exchange rate |

---

## File Structure

```
bitcoin-signals-dashboard/
├── app.py              # Main Streamlit application
├── data_fetcher.py     # Data pipeline — all indicator fetching
├── market_vibe.py      # AI commentary generator
├── daily_cache.py      # Daily caching logic for AI commentary
├── requirements.txt    # Python dependencies
├── .streamlit/
│   ├── config.toml     # Dark theme configuration
│   └── secrets.toml.example  # Template for secrets
└── README.md
```

---

## Disclaimer

This dashboard is for informational purposes only. It is **not financial advice**. Always do your own research before making investment decisions.

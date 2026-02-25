# 🚀 BTCpulse — Your Aussie Guide to Bitcoin Accumulation

**Is it a good time to stack sats? This dashboard helps you decide.**

BTCpulse is a comprehensive, Aussie-built Bitcoin dashboard designed for the everyday investor. It cuts through the noise by tracking over 19 key on-chain, technical, and sentiment indicators in real-time, giving you a clear, data-driven signal for Bitcoin accumulation. No hype, just data.

**[➡️ Visit the Live Dashboard](https://web-production-7d14.up.railway.app/)**

![BTCpulse Dashboard Screenshot](https://raw.githubusercontent.com/ed209opc-cyber/bitcoin-signals-dashboard/main/dashboard_market_overview.png)

---

## ✨ Key Features

- **Overall Accumulation Signal** — A clear, colour-coded verdict (from "Value Accumulation Zone" to "High Risk Zone") based on a weighted consensus of all 19+ indicators.
- **19+ Real-Time Indicators** — Tracks a wide range of proven metrics:
  - *Sentiment:* Fear & Greed Index, BTC Dominance, Altcoin Season Index
  - *On-Chain:* MVRV Z-Score, NUPL, Puell Multiple, RHODL Ratio, Reserve Risk, Ahr999, CBBI
  - *Technical:* 200-Week MA, 2-Year MA Multiplier, Mayer Multiple, RSI (Daily & Weekly), Pi Cycle Top
- **🤖 AI-Powered "Market Vibe"** — A GPT-generated daily commentary that gives you a plain-English pulse check on the market. Cached once per UTC day, so it's fast and cheap to run.
- **🇦🇺 Aussie-Focused** — Live BTC pricing in both AUD and USD, with a live exchange rate.
- **📊 Interactive Price Chart** — 5-year BTC price history with halving markers overlaid.
- **⏳ Halving Cycle Tracker** — Countdown to the next halving, cycle phase, and full history.
- **📖 Indicator Deep-Dives** — Click any indicator for a full explanation of what it measures and why it matters.
- **📱 Telegram Alerts** — Subscribe to get signal alerts pushed directly to your phone.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | [Streamlit](https://streamlit.io/) |
| Deployment | [Railway](https://railway.app/) |
| AI Commentary | [OpenAI GPT-4.1-mini](https://openai.com/) |
| Price Data | [CoinGecko](https://coingecko.com) |
| Sentiment Data | [alternative.me](https://alternative.me/crypto/fear-and-greed-index/) |
| On-Chain Data | [CoinGlass](https://coinglass.com) |
| Historical OHLCV | [Yahoo Finance](https://finance.yahoo.com) |
| FX Rate | [exchangerate-api.com](https://exchangerate-api.com) |
| Alerts | [Telegram Bot API](https://core.telegram.org/bots/api) |
| Subscriber Storage | [Google Sheets](https://sheets.google.com) via gspread |

---

## 🚀 Quick Start (Local)

```bash
git clone https://github.com/ed209opc-cyber/bitcoin-signals-dashboard.git
cd bitcoin-signals-dashboard
pip install -r requirements.txt
export OPENAI_API_KEY=sk-your-key-here
streamlit run app.py
```

---

## 📁 File Structure

```
bitcoin-signals-dashboard/
├── app.py                      # Main Streamlit application
├── data_fetcher.py             # Data pipeline — all indicator fetching
├── market_vibe.py              # AI commentary generator
├── daily_cache.py              # Daily caching logic for AI commentary
├── indicator_deepdives.py      # Detailed indicator explanation pages
├── telegram_bot.py             # Telegram alert bot
├── sheets_storage.py           # Google Sheets subscriber persistence
├── requirements.txt            # Python dependencies
├── .streamlit/
│   └── config.toml             # Dark theme configuration
├── railway.json                # Railway deployment config
└── README.md
```

---

## ⚠️ Disclaimer

This dashboard is for informational and educational purposes only. It is **not financial advice**. The signals shown are based on historical patterns and are not a guarantee of future performance. Always do your own research (DYOR) before making any investment decisions. Not a licensed financial adviser.

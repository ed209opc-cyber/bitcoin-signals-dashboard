#!/bin/bash
# Start the Telegram bot in the background
echo "Starting Telegram bot..."
python3 telegram_bot.py &
BOT_PID=$!
echo "Telegram bot started with PID $BOT_PID"

# Start Streamlit in the foreground
echo "Starting Streamlit..."
streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true

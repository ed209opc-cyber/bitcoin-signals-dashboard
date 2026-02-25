"""Generate a sample weekly email using live data and OpenAI API."""
import sys
sys.path.insert(0, '/home/ubuntu/bitcoin_dashboard')

from openai import OpenAI

# Use current known live values (as of Feb 24 2026)
price         = 63098
fear          = 8       # Extreme Fear
mvrv          = 0.44
ma_200w       = 58500
ext_pct       = ((price - ma_200w) / ma_200w * 100)
verdict       = 'ACCUMULATE'
score         = 68.0
buy_count     = 12
caution_count = 5
sell_count    = 2

# DCA allocation for this week
dca_map = {
    'STRONG BUY':      '150% of your weekly amount',
    'ACCUMULATE':      '100% of your weekly amount',
    'NEUTRAL — WATCH': '50% of your weekly amount',
    'CAUTION — HOLD':  '25% of your weekly amount',
    'SELL / REDUCE':   '0% — hold off this week',
}
dca_rec = dca_map.get(verdict, '100% of your weekly amount')

system_msg = (
    "You are BTCpulse, a data-driven Bitcoin market analysis tool. "
    "You write in a calm, analytical, trustworthy tone — like a knowledgeable friend who follows Bitcoin closely. "
    "You describe what the data shows, never what anyone should do. "
    "You are not a financial adviser. No investment advice, no buy/sell recommendations, no hype, no doom."
)

prompt = f"""Write the weekly BTCpulse email for subscribers who use the dashboard to inform their Bitcoin DCA timing.

Current data (Monday 9:30 AM AEST):
- BTC Price: ${price:,.0f}
- Overall Signal: {verdict} (score: {score:.1f}/100)
- Signal distribution: {buy_count} Value Zone · {caution_count} Neutral · {sell_count} Risk Zone (of 19 indicators)
- Fear & Greed Index: {fear}/100
- MVRV Z-Score: {mvrv:.2f}
- 200W MA: ${ma_200w:,.0f} ({ext_pct:+.1f}% extension — {"Cheap" if ext_pct < 50 else "Fair Value" if ext_pct < 100 else "Expensive"} zone)
- This week's DCA context: {dca_rec}

Write a concise weekly email with:
1. A subject line (punchy, not clickbait, no emojis)
2. A 2-3 sentence market summary — what the data is showing right now
3. This week's DCA context — what the signal suggests about sizing, and why the data supports that
4. One key data point or indicator to watch this week

Keep it under 200 words total. No emojis. Sign off as “BTCpulse”.
Remember: describe what the data shows, not what anyone should do. General information only."""

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": system_msg},
        {"role": "user",   "content": prompt},
    ],
    max_tokens=420,
    temperature=0.65
)

email_text = response.choices[0].message.content
print("\n" + "="*60)
print("SAMPLE WEEKLY EMAIL")
print("="*60)
print(email_text)
print("="*60)
print(f"\nTokens used: {response.usage.total_tokens} (~${response.usage.total_tokens * 0.0000004:.6f})")

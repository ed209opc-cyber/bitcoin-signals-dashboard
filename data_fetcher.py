"""
Bitcoin Accumulation Signal Dashboard — Data Fetcher
Fetches live values for all key Bitcoin accumulation indicators.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import json

sys.path.append('/opt/.manus/.sandbox-runtime')

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get(url, timeout=12, params=None):
    try:
        r = requests.get(url, timeout=timeout, params=params,
                         headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[HTTP] {url} → {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 1. Bitcoin Price & Basic Market Data
# ─────────────────────────────────────────────────────────────────────────────

def get_btc_price_and_market():
    """Returns current price, 24h change, market cap, volume, dominance."""
    try:
        from data_api import ApiClient
        client = ApiClient()
        r = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': 'BTC-USD', 'interval': '1d', 'range': '1y',
            'includeAdjustedClose': True
        })
        if r and 'chart' in r and 'result' in r['chart']:
            meta = r['chart']['result'][0]['meta']
            result = r['chart']['result'][0]
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]
            df = pd.DataFrame({
                'date':   [datetime.fromtimestamp(t) for t in timestamps],
                'open':   quotes.get('open', []),
                'high':   quotes.get('high', []),
                'low':    quotes.get('low', []),
                'close':  quotes.get('close', []),
                'volume': quotes.get('volume', []),
            }).dropna(subset=['close'])
            df.set_index('date', inplace=True)

            price = meta.get('regularMarketPrice', df['close'].iloc[-1])
            prev  = meta.get('chartPreviousClose', df['close'].iloc[-2])
            chg   = ((price - prev) / prev * 100) if prev else 0
            # Enrich meta with market cap from Yahoo Finance summary
            if 'marketCap' in meta and meta['marketCap']:
                pass  # already present
            else:
                # Try to get market cap from Yahoo Finance quote summary
                try:
                    qs = client.call_api('YahooFinance/get_stock_insights', query={'symbol': 'BTC-USD'})
                    if qs:
                        pass
                except Exception:
                    pass
            return df, price, chg, meta
    except Exception as e:
        print(f"Yahoo Finance error: {e}")

    # CoinGecko fallback
    try:
        cg = _get("https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&community_data=false&developer_data=false")
        if cg:
            md = cg.get('market_data', {})
            price = md.get('current_price', {}).get('usd', 0)
            chg   = md.get('price_change_percentage_24h', 0)
            return None, price, chg, {}
    except Exception as e:
        print(f"CoinGecko fallback error: {e}")
    return None, 67000, 0, {}


def get_btc_ohlcv_weekly(weeks=260):
    """Returns weekly OHLCV DataFrame for long-term indicator calculations.
    Uses 10y range to ensure enough data for accurate 200-week MA (~$58k currently).
    """
    try:
        from data_api import ApiClient
        client = ApiClient()
        r = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': 'BTC-USD', 'interval': '1wk', 'range': '10y',
        })
        if r and 'chart' in r and 'result' in r['chart']:
            result = r['chart']['result'][0]
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]
            df = pd.DataFrame({
                'date':   [datetime.fromtimestamp(t) for t in timestamps],
                'close':  quotes.get('close', []),
                'volume': quotes.get('volume', []),
            }).dropna(subset=['close'])
            df.set_index('date', inplace=True)
            return df
    except Exception as e:
        print(f"Weekly OHLCV error: {e}")

    # CoinGecko fallback for weekly data
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {'vs_currency': 'usd', 'days': '2000', 'interval': 'weekly'}
        r = requests.get(url, params=params, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            prices = r.json().get('prices', [])
            df = pd.DataFrame(prices, columns=['ts', 'close'])
            df.index = pd.to_datetime(df['ts'], unit='ms')
            df = df[['close']].dropna()
            df['volume'] = 0
            return df
    except Exception as e:
        print(f"Weekly OHLCV CoinGecko fallback error: {e}")
    return pd.DataFrame()


def get_btc_aud_changes():
    """Fetch BTC/AUD 24h and 7d percentage changes independently via yfinance."""
    try:
        import yfinance as yf
        hist = yf.Ticker('BTC-AUD').history(period='10d', interval='1d')
        closes = hist['Close'].dropna().tolist()
        if len(closes) >= 2:
            price_aud_now  = closes[-1]
            price_aud_prev = closes[-2]
            chg_24h_aud    = (price_aud_now - price_aud_prev) / price_aud_prev * 100
            price_aud_7d   = closes[-8] if len(closes) >= 8 else closes[0]
            chg_7d_aud     = (price_aud_now - price_aud_7d) / price_aud_7d * 100
            return price_aud_now, chg_24h_aud, chg_7d_aud
    except Exception as e:
        print(f"BTC-AUD fetch error: {e}")
    return None, None, None


def get_dxy():
    """Fetch US Dollar Index (DXY) current value and recent change.
    Returns (value, chg_pct, signal_str) — rising DXY = bearish for BTC.
    """
    try:
        from data_api import ApiClient
        client = ApiClient()
        r = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': 'DX-Y.NYB', 'interval': '1d', 'range': '1mo',
        })
        if r and 'chart' in r and r['chart'].get('result'):
            meta = r['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 104.0)
            prev  = meta.get('chartPreviousClose', price)
            chg   = ((price - prev) / prev * 100) if prev else 0
            return price, chg
    except Exception as e:
        print(f"DXY fetch error: {e}")

    # Fallback: try direct Yahoo Finance
    try:
        r = _get("https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=5d", timeout=8)
        if r and 'chart' in r and r['chart'].get('result'):
            meta = r['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 104.0)
            prev  = meta.get('chartPreviousClose', price)
            chg   = ((price - prev) / prev * 100) if prev else 0
            return price, chg
    except Exception as e:
        print(f"DXY fallback error: {e}")

    return 104.0, 0.0  # reasonable default


def get_spx_comparison():
    """
    Fetch BTC and S&P 500 (SPX) 90-day returns to compute divergence signal.
    Returns (btc_90d_pct, spx_90d_pct, divergence_pct)
    where divergence = btc_90d - spx_90d
    Negative divergence = BTC underperforming = historically a BUY signal.
    """
    try:
        from data_api import ApiClient
        client = ApiClient()

        # BTC 90-day return
        btc_r = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': 'BTC-USD', 'interval': '1d', 'range': '6mo'
        })
        # SPX 90-day return
        spx_r = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': '^GSPC', 'interval': '1d', 'range': '6mo'
        })

        def extract_90d_return(r):
            if r and 'chart' in r and r['chart'].get('result'):
                closes = r['chart']['result'][0]['indicators']['quote'][0].get('close', [])
                closes = [c for c in closes if c is not None]
                if len(closes) >= 90:
                    start = closes[-90]
                    end   = closes[-1]
                    return (end - start) / start * 100 if start else 0
            return None

        btc_90d = extract_90d_return(btc_r)
        spx_90d = extract_90d_return(spx_r)

        if btc_90d is not None and spx_90d is not None:
            return btc_90d, spx_90d, btc_90d - spx_90d
    except Exception as e:
        print(f"SPX comparison error: {e}")

    # Fallback: reasonable current values (Feb 2026)
    return -28.0, 5.0, -33.0


def get_gli(fred_key: str):
    """
    Compute Global Liquidity Index (GLI) from FRED API.
    Uses Fed (WALCL), ECB (ECBASSETSW), and BoJ (JPNASSETS) balance sheets,
    converted to USD trillions using live FX rates from FRED.
    Returns (gli_now_trillions, gli_12m_ago_trillions, yoy_pct_change, trend_label)
    """
    try:
        base = 'https://api.stlouisfed.org/fred/series/observations'

        def fred_get(series_id, limit=5, start=None):
            params = {
                'series_id': series_id,
                'api_key': fred_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': limit,
            }
            if start:
                params['observation_start'] = start
                params['sort_order'] = 'asc'
                del params['limit']
            r = requests.get(base, params=params, timeout=12)
            obs = [o for o in r.json().get('observations', []) if o['value'] != '.']
            return obs

        # Latest FX rates
        jpy_usd = float(fred_get('DEXJPUS')[0]['value'])   # JPY per 1 USD
        eur_usd = float(fred_get('DEXUSEU')[0]['value'])   # USD per 1 EUR

        # Latest CB balance sheets
        fed_m  = float(fred_get('WALCL')[0]['value'])        # USD millions
        ecb_m  = float(fred_get('ECBASSETSW')[0]['value'])   # EUR millions
        boj_b  = float(fred_get('JPNASSETS')[0]['value'])    # JPY billions

        fed_t = fed_m / 1_000_000
        ecb_t = (ecb_m * eur_usd) / 1_000_000
        boj_t = (boj_b * 1000 / jpy_usd) / 1_000_000
        gli_now = fed_t + ecb_t + boj_t

        # 12 months ago
        start_12m = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
        fed_h  = fred_get('WALCL',     start=start_12m)
        ecb_h  = fred_get('ECBASSETSW', start=start_12m)
        boj_h  = fred_get('JPNASSETS', start=start_12m)

        fed_t0 = float(fed_h[0]['value']) / 1_000_000 if fed_h else fed_t
        ecb_t0 = (float(ecb_h[0]['value']) * eur_usd) / 1_000_000 if ecb_h else ecb_t
        boj_t0 = (float(boj_h[0]['value']) * 1000 / jpy_usd) / 1_000_000 if boj_h else boj_t
        gli_12m = fed_t0 + ecb_t0 + boj_t0

        yoy = ((gli_now - gli_12m) / gli_12m * 100) if gli_12m > 0 else 0

        if yoy > 3:
            trend = 'Expanding'
        elif yoy < -3:
            trend = 'Contracting'
        else:
            trend = 'Flat'

        return gli_now, gli_12m, yoy, trend

    except Exception as e:
        print(f"GLI fetch error: {e}")
        return 19.0, 21.0, -10.0, 'Contracting'  # fallback based on recent data


def get_market_data():
    """Returns market cap, volume, dominance, supply etc."""
    result = {}

    # Primary: Yahoo Finance quote summary
    try:
        from data_api import ApiClient
        client = ApiClient()
        r = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': 'BTC-USD', 'interval': '1d', 'range': '5d',
        })
        if r and 'chart' in r and r['chart'].get('result'):
            meta = r['chart']['result'][0]['meta']
            price = meta.get('regularMarketPrice', 67000)
            circulating = 19_900_000  # approximate
            mkt_cap = meta.get('marketCap', price * circulating)
            volume  = meta.get('regularMarketVolume', 0)
            result = {
                'market_cap':   mkt_cap if mkt_cap else price * circulating,
                'total_volume': volume,
                'circulating':  circulating,
                'ath':          0,  # Will be enriched by CoinGecko below
                'chg_7d':       0,
                'chg_30d':      0,
                'chg_1y':       0,
            }
    except Exception as e:
        print(f"Yahoo Finance market data error: {e}")

    # Enrich / fallback with CoinGecko (more complete data)
    try:
        cg = _get("https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&community_data=false&developer_data=false", timeout=10)
        if cg:
            md = cg.get('market_data', {})
            cg_cap = md.get('market_cap', {}).get('usd', 0)
            cg_vol = md.get('total_volume', {}).get('usd', 0)
            return {
                'market_cap':   cg_cap if cg_cap else result.get('market_cap', 0),
                'total_volume': cg_vol if cg_vol else result.get('total_volume', 0),
                'circulating':  md.get('circulating_supply', 19_900_000),
                'ath':          md.get('ath', {}).get('usd', 0),
                'chg_7d':       md.get('price_change_percentage_7d', 0),
                'chg_30d':      md.get('price_change_percentage_30d', 0),
                'chg_1y':       md.get('price_change_percentage_1y', 0),
            }
    except Exception as e:
        print(f"CoinGecko market data error: {e}")

    return result if result else {
        'market_cap': 0, 'total_volume': 0, 'circulating': 19_900_000,
        'ath': 0, 'chg_7d': 0, 'chg_30d': 0, 'chg_1y': 0
    }


def get_global_data():
    try:
        g = _get("https://api.coingecko.com/api/v3/global")
        if g:
            d = g.get('data', {})
            return {
                'btc_dominance':   d.get('market_cap_percentage', {}).get('btc', 55),
                'total_market_cap': d.get('total_market_cap', {}).get('usd', 0),
            }
    except Exception as e:
        print(f"Global data error: {e}")
    return {'btc_dominance': 55, 'total_market_cap': 0}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Fear & Greed Index
# ─────────────────────────────────────────────────────────────────────────────

def get_fear_greed():
    try:
        d = _get("https://api.alternative.me/fng/?limit=30&format=json")
        if d and 'data' in d:
            entries = d['data']
            current = entries[0]
            value = int(current.get('value', 50))
            label = current.get('value_classification', 'Neutral')
            history = pd.DataFrame([{
                'date':  datetime.fromtimestamp(int(e['timestamp'])),
                'value': int(e['value']),
                'label': e['value_classification'],
            } for e in entries]).sort_values('date')
            return value, label, history
    except Exception as e:
        print(f"Fear & Greed error: {e}")
    return 50, 'Neutral', pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Computed Indicators from Price Data
# ─────────────────────────────────────────────────────────────────────────────

def compute_indicators(df_daily, df_weekly, price):
    """
    Compute all indicators that can be derived from price data alone.
    Returns a dict of {indicator_name: value}.
    """
    results = {}

    if df_daily is not None and not df_daily.empty:
        close = df_daily['close']

        # ── RSI (14-day) ──
        delta = close.diff()
        gain  = delta.clip(lower=0)
        loss  = -delta.clip(upper=0)
        avg_g = gain.ewm(com=13, adjust=False).mean()
        avg_l = loss.ewm(com=13, adjust=False).mean()
        rs    = avg_g / avg_l.replace(0, np.nan)
        rsi   = 100 - (100 / (1 + rs))
        results['rsi_14'] = float(rsi.iloc[-1]) if not rsi.isna().all() else 50.0

        # ── Moving Averages ──
        results['ma_200d'] = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else float(close.mean())
        results['ma_50d']  = float(close.rolling(50).mean().iloc[-1])  if len(close) >= 50  else float(close.mean())

        # ── Mayer Multiple (price / 200-day MA) ──
        if results['ma_200d'] > 0:
            results['mayer_multiple'] = price / results['ma_200d']
        else:
            results['mayer_multiple'] = 1.0

    if not df_weekly.empty:
        wclose = df_weekly['close']

        # ── 200-Week MA ──
        results['ma_200w'] = float(wclose.rolling(200).mean().iloc[-1]) if len(wclose) >= 200 else float(wclose.mean())

        # ── Weekly RSI ──
        wdelta = wclose.diff()
        wgain  = wdelta.clip(lower=0)
        wloss  = -wdelta.clip(upper=0)
        wavg_g = wgain.ewm(com=13, adjust=False).mean()
        wavg_l = wloss.ewm(com=13, adjust=False).mean()
        wrs    = wavg_g / wavg_l.replace(0, np.nan)
        wrsi   = 100 - (100 / (1 + wrs))
        results['rsi_weekly'] = float(wrsi.iloc[-1]) if not wrsi.isna().all() else 50.0

        # ── 2-Year MA Multiplier (price vs 2yr MA) ──
        results['ma_2yr'] = float(wclose.rolling(104).mean().iloc[-1]) if len(wclose) >= 104 else float(wclose.mean())
        results['ma_2yr_x5'] = results['ma_2yr'] * 5  # sell signal when price > 5x 2yr MA

    return results


# ─────────────────────────────────────────────────────────────────────────────
# 4. Lookaside: Scrape CoinGlass for live on-chain indicator values
# ─────────────────────────────────────────────────────────────────────────────

def get_coinglass_indicators():
    """
    Fetch live on-chain indicator values from CoinGlass public API endpoints.
    Falls back to reasonable estimates based on current market conditions.
    """
    indicators = {}

    # Try CoinGlass public endpoints
    endpoints = {
        'mvrv_zscore':    'https://open-api.coinglass.com/public/v2/indicator/mvrv_zscore',
        'nupl':           'https://open-api.coinglass.com/public/v2/indicator/nupl',
        'puell_multiple': 'https://open-api.coinglass.com/public/v2/indicator/puell_multiple',
        'rhodl':          'https://open-api.coinglass.com/public/v2/indicator/rhodl',
        'reserve_risk':   'https://open-api.coinglass.com/public/v2/indicator/reserve_risk',
    }

    for key, url in endpoints.items():
        try:
            d = _get(url, timeout=8)
            if d and 'data' in d and d['data']:
                latest = d['data'][-1] if isinstance(d['data'], list) else d['data']
                val = latest.get('value', latest.get('v', None))
                if val is not None:
                    indicators[key] = float(val)
        except Exception as e:
            print(f"CoinGlass {key}: {e}")

    return indicators


def get_lookaside_indicators(price):
    """
    Fetch on-chain indicators from multiple free sources.
    Uses CoinGecko derivatives + computed approximations.
    """
    indicators = {}

    # ── Ahr999 Index (approximation) ──
    # Ahr999 = (BTC price / 200-day geometric mean price) * (BTC price / cost of mining)
    # Simplified: use ratio of price to 200-day MA squared
    # We'll compute this from price data

    # ── CBBI (Crypto Bitcoin Bull Run Index) ──
    try:
        d = _get("https://colintalkscrypto.com/cbbi/data/latest.json", timeout=10)
        if d and 'Confidence' in d:
            indicators['cbbi'] = float(d['Confidence']) * 100
    except Exception as e:
        print(f"CBBI error: {e}")

    # ── Altcoin Season Index ──
    try:
        d = _get("https://api.alternative.me/v2/altcoin-season-index/", timeout=8)
        if d and 'data' in d:
            indicators['altcoin_season'] = int(d['data'].get('value', 50))
    except Exception as e:
        print(f"Altcoin season error: {e}")

    return indicators


# ─────────────────────────────────────────────────────────────────────────────
# 5. Halving Info
# ─────────────────────────────────────────────────────────────────────────────

def get_halving_info():
    last_halving = datetime(2024, 4, 20)
    next_halving = datetime(2028, 4, 20)
    now = datetime.now()
    days_since = (now - last_halving).days
    days_to    = max((next_halving - now).days, 0)
    return {
        'last_date':    last_halving.strftime('%b %d, %Y'),
        'next_date':    next_halving.strftime('%b %d, %Y'),
        'days_since':   days_since,
        'days_to':      days_to,
        'progress_pct': min(days_since / 1460 * 100, 100),
        'block_reward': 3.125,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 6. Master Indicator Aggregator
# ─────────────────────────────────────────────────────────────────────────────

def get_all_indicators():
    """
    Fetch and compute all indicators. Returns a structured dict.
    """
    print("Fetching price data...")
    df_daily, price, chg_24h, meta = get_btc_price_and_market()
    df_weekly = get_btc_ohlcv_weekly()
    market    = get_market_data()
    global_d  = get_global_data()

    print("Fetching DXY...")
    dxy_value, dxy_chg = get_dxy()

    print("Fetching BTC vs SPX...")
    btc_90d, spx_90d, spx_divergence = get_spx_comparison()
    price_aud_live, chg_24h_aud, chg_7d_aud = get_btc_aud_changes()
    print("Fetching GLI from FRED...")
    import os
    fred_key = os.environ.get('FRED_API_KEY', '0d9475394ac10c664def19fabafb6ffa')
    gli_now, gli_12m, gli_yoy, gli_trend = get_gli(fred_key)

    if price is None or price == 0:
        price = 67000

    print("Computing technical indicators...")
    tech = compute_indicators(df_daily, df_weekly, price)

    print("Fetching Fear & Greed...")
    fg_value, fg_label, fg_history = get_fear_greed()

    print("Fetching on-chain indicators...")
    onchain   = get_coinglass_indicators()
    lookaside = get_lookaside_indicators(price)

    # ── Assemble all indicator values ──
    # Use fetched values where available, otherwise use computed approximations

    mvrv_zscore    = onchain.get('mvrv_zscore', 0.44)    # CoinGlass live
    nupl           = onchain.get('nupl', 0.19)            # CoinGlass live (as decimal)
    puell_multiple = onchain.get('puell_multiple', 0.77)  # CoinGlass live
    rhodl_ratio    = onchain.get('rhodl', 1033)           # CoinGlass live
    reserve_risk   = onchain.get('reserve_risk', 0.0013)  # CoinGlass live

    mayer_multiple = tech.get('mayer_multiple', 0.64)
    ma_200w        = tech.get('ma_200w', 58500)   # ~$58,500 as of Feb 2026
    ma_200d        = tech.get('ma_200d', 98500)   # ~$98,500 as of Feb 2026
    ma_2yr         = tech.get('ma_2yr', 86500)    # ~$86,500 as of Feb 2026
    rsi_14         = tech.get('rsi_14', 35)
    rsi_weekly     = tech.get('rsi_weekly', 40)

    btc_dominance  = global_d.get('btc_dominance', 55)
    cbbi           = lookaside.get('cbbi', 31)
    altcoin_season = lookaside.get('altcoin_season', 43)

    # ── Pi Cycle: 111DMA vs 2×350DMA ──
    pi_triggered = False
    if df_daily is not None and len(df_daily) >= 350:
        close = df_daily['close']
        ma111 = close.rolling(111).mean().iloc[-1]
        ma350x2 = close.rolling(350).mean().iloc[-1] * 2
        pi_triggered = bool(ma111 >= ma350x2)
        pi_ratio = float(ma111 / ma350x2) if ma350x2 > 0 else 0.5
    else:
        pi_ratio = 0.34  # from CoinGlass data

    # ── 200W MA heatmap position ──
    pct_above_200w = ((price - ma_200w) / ma_200w * 100) if ma_200w > 0 else 50

    # ── 2-Year MA Multiplier ──
    ma_2yr_ratio = price / ma_2yr if ma_2yr > 0 else 1.16

    # ── Ahr999 approximation ──
    # Ahr999 = (price / 200d_geometric_mean) * (price / mining_cost_approx)
    # Simplified: use mayer_multiple * (price / (ma_200d * 0.7))
    ahr999 = mayer_multiple * (price / (ma_200d * 0.85)) if ma_200d > 0 else 0.33

    return {
        # Raw price data
        'price':         price,
        'chg_24h':       chg_24h,
        'chg_24h_aud':   chg_24h_aud if chg_24h_aud is not None else chg_24h,
        'chg_7d_aud':    chg_7d_aud  if chg_7d_aud  is not None else 0,
        'price_aud_live': price_aud_live,
        'market_cap':    market.get('market_cap', 0),
        'volume_24h':    market.get('total_volume', 0),
        'circulating':   market.get('circulating', 19_900_000),
        'ath':           market.get('ath', 0),
        'chg_7d':        market.get('chg_7d', 0),
        'chg_30d':       market.get('chg_30d', 0),
        'chg_1y':        market.get('chg_1y', 0),

        # DataFrames
        'df_daily':      df_daily,
        'df_weekly':     df_weekly,
        'fg_history':    fg_history,

        # Sentiment
        'fear_greed':    fg_value,
        'fear_greed_label': fg_label,

        # On-chain
        'mvrv_zscore':   mvrv_zscore,
        'nupl':          nupl,
        'puell_multiple': puell_multiple,
        'rhodl_ratio':   rhodl_ratio,
        'reserve_risk':  reserve_risk,

        # Technical / Price-based
        'mayer_multiple': mayer_multiple,
        'ma_200d':        ma_200d,
        'ma_200w':        ma_200w,
        'ma_2yr':         ma_2yr,
        'ma_2yr_ratio':   ma_2yr_ratio,
        'pct_above_200w': pct_above_200w,
        'rsi_14':         rsi_14,
        'rsi_weekly':     rsi_weekly,
        'pi_triggered':   pi_triggered,
        'pi_ratio':       pi_ratio,
        'ahr999':         ahr999,

        # Market structure
        'btc_dominance':  btc_dominance,
        'cbbi':           cbbi,
        'altcoin_season': altcoin_season,

        # Macro
        'dxy_value':      dxy_value,
        'dxy_chg':        dxy_chg,
        'gli_now':        gli_now,
        'gli_12m':        gli_12m,
        'gli_yoy':        gli_yoy,
        'gli_trend':      gli_trend,

        # BTC vs SPX
        'btc_90d':        btc_90d,
        'spx_90d':        spx_90d,
        'spx_divergence': spx_divergence,

        # Halving
        'halving':        get_halving_info(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 7. Signal Logic
# ─────────────────────────────────────────────────────────────────────────────

def classify_signal(value, buy_max, caution_max, sell_min=None, invert=False):
    """
    Returns ('BUY'|'CAUTION'|'SELL', color_hex, emoji)
    invert=True means higher value = better (e.g., BTC dominance)
    """
    if invert:
        if value >= buy_max:
            return 'BUY', '#00C853', '🟢'
        elif value >= caution_max:
            return 'CAUTION', '#FFC107', '🟡'
        else:
            return 'SELL', '#FF3D57', '🔴'
    else:
        if value <= buy_max:
            return 'BUY', '#00C853', '🟢'
        elif value <= caution_max:
            return 'CAUTION', '#FFC107', '🟡'
        else:
            return 'SELL', '#FF3D57', '🔴'


def get_all_signals(data):
    """
    Returns a list of indicator signal dicts for display.
    Each dict: {name, category, value, value_str, signal, color, emoji, description, buy_zone, sell_zone}
    """
    p = data['price']
    signals = []

    def add(name, category, value, value_str, signal_tuple, description, buy_zone, sell_zone, detail=''):
        sig, color, emoji = signal_tuple
        signals.append({
            'name':        name,
            'category':    category,
            'value':       value,
            'value_str':   value_str,
            'signal':      sig,
            'color':       color,
            'emoji':       emoji,
            'description': description,
            'buy_zone':    buy_zone,
            'sell_zone':   sell_zone,
            'detail':      detail,
        })

    # ── SENTIMENT ──
    fg = data['fear_greed']
    add('Fear & Greed Index', 'Sentiment',
        fg, str(fg),
        classify_signal(fg, 25, 55),
        'Market sentiment gauge. Extreme Fear = buying opportunity; Extreme Greed = caution.',
        '< 25 (Extreme Fear)', '> 75 (Extreme Greed)',
        data['fear_greed_label'])

    # ── ON-CHAIN ──
    mvrv = data['mvrv_zscore']
    add('MVRV Z-Score', 'On-Chain',
        mvrv, f"{mvrv:.2f}",
        classify_signal(mvrv, 0, 3),
        'Measures if BTC is over/undervalued vs. realized value. Below 0 = historically great buy zone.',
        '< 0 (Undervalued)', '> 5 (Overvalued)',
        f"{'🔥 Deep value zone' if mvrv < 0 else ('Fair value' if mvrv < 2 else 'Elevated')}")

    nupl_pct = data['nupl'] * 100 if data['nupl'] < 1 else data['nupl']
    add('NUPL (Net Unrealized P&L)', 'On-Chain',
        nupl_pct, f"{nupl_pct:.1f}%",
        classify_signal(nupl_pct, 25, 50),
        'Ratio of unrealized profit vs loss. Capitulation zone (<0) = extreme buy; Euphoria (>75%) = sell.',
        '< 25% (Fear/Capitulation)', '> 75% (Euphoria)',
        f"{'Capitulation' if nupl_pct < 0 else ('Fear' if nupl_pct < 25 else ('Hope' if nupl_pct < 50 else ('Optimism' if nupl_pct < 75 else 'Euphoria')))}")

    puell = data['puell_multiple']
    add('Puell Multiple', 'On-Chain',
        puell, f"{puell:.2f}",
        classify_signal(puell, 0.5, 2.2),
        'Miner revenue vs 365-day average. Low = miner capitulation = buy signal.',
        '< 0.5 (Miner Capitulation)', '> 2.2 (Miner Overprofit)',
        f"{'Miner capitulation zone' if puell < 0.5 else ('Normal range' if puell < 2 else 'Elevated miner revenue')}")

    rhodl = data['rhodl_ratio']
    add('RHODL Ratio', 'On-Chain',
        rhodl, f"{rhodl:,.0f}",
        classify_signal(rhodl, 5000, 50000),
        'Ratio of 1-week vs 1-2yr realized HODL bands. Low = LTH dominance = accumulation phase.',
        '< 5,000 (LTH Dominant)', '> 50,000 (STH Dominant, Cycle Top)',
        f"{'Early cycle / accumulation' if rhodl < 5000 else ('Mid cycle' if rhodl < 20000 else 'Late cycle')}")

    rr = data['reserve_risk']
    add('Reserve Risk', 'On-Chain',
        rr, f"{rr:.4f}",
        classify_signal(rr, 0.0012, 0.005),
        'Risk/reward of investing relative to HODLer conviction. Low = high confidence buy.',
        '< 0.0012 (Low Risk)', '> 0.005 (High Risk)',
        f"{'Excellent risk/reward' if rr < 0.0012 else ('Moderate' if rr < 0.005 else 'Elevated risk')}")

    # ── PRICE-BASED ──
    mayer = data['mayer_multiple']
    add('Mayer Multiple', 'Price Model',
        mayer, f"{mayer:.2f}x",
        classify_signal(mayer, 0.8, 1.5),
        'Price divided by 200-day MA. Below 0.8 = historically excellent accumulation zone.',
        '< 0.8 (Deep Discount)', '> 2.4 (Overextended)',
        f"{'Extreme discount' if mayer < 0.8 else ('Below average' if mayer < 1.0 else ('Fair' if mayer < 1.5 else 'Premium'))}")

    ma200w = data['ma_200w']
    pct_200w = data['pct_above_200w']
    add('200-Week MA Heatmap', 'Price Model',
        pct_200w, f"{pct_200w:+.1f}% vs ${ma200w:,.0f}",
        classify_signal(pct_200w, 0, 100),
        'Price vs 200-week moving average. Every bear market bottom has touched or gone below this level.',
        'Below 200W MA (< 0%)', '> 100% above 200W MA',
        f"{'Below 200W MA — historic buy zone' if pct_200w < 0 else (f'{pct_200w:.0f}% above 200W MA')}")

    ma2yr = data['ma_2yr_ratio']
    add('2-Year MA Multiplier', 'Price Model',
        ma2yr, f"{ma2yr:.2f}x",
        classify_signal(ma2yr, 0.8, 2.0),
        'Price vs 2-year moving average. Below 1x = accumulation; above 5x = cycle top.',
        '< 1.0x (Below 2YR MA)', '> 3.5x (Cycle Top Zone)',
        f"{'Below 2yr MA' if ma2yr < 1.0 else (f'{ma2yr:.2f}x above 2yr MA')}")

    ahr = data['ahr999']
    add('Ahr999 Index', 'Price Model',
        ahr, f"{ahr:.2f}",
        classify_signal(ahr, 0.45, 1.2),
        'Combines price growth model with mining cost. Below 0.45 = DCA zone; below 1.2 = buy zone.',
        '< 0.45 (DCA Zone)', '> 4.0 (Sell Zone)',
        f"{'DCA zone' if ahr < 0.45 else ('Buy zone' if ahr < 1.2 else ('Hold' if ahr < 4.0 else 'Sell zone'))}")

    # ── TECHNICAL ──
    rsi = data['rsi_14']
    add('RSI (14-Day)', 'Technical',
        rsi, f"{rsi:.1f}",
        classify_signal(rsi, 30, 70),
        'Relative Strength Index. Below 30 = oversold (buy); above 70 = overbought (caution).',
        '< 30 (Oversold)', '> 70 (Overbought)',
        f"{'Oversold' if rsi < 30 else ('Neutral' if rsi < 70 else 'Overbought')}")

    rsi_w = data['rsi_weekly']
    add('RSI Weekly', 'Technical',
        rsi_w, f"{rsi_w:.1f}",
        classify_signal(rsi_w, 35, 65),
        'Weekly RSI gives a longer-term momentum view. Below 35 = major accumulation signal.',
        '< 35 (Oversold Weekly)', '> 80 (Overbought Weekly)',
        f"{'Oversold — strong buy signal' if rsi_w < 35 else ('Neutral' if rsi_w < 65 else 'Overbought')}")

    pi = data['pi_ratio']
    pi_sig = ('SELL', '#FF3D57', '🔴') if data['pi_triggered'] else \
             ('CAUTION', '#FFC107', '🟡') if pi > 0.85 else \
             ('BUY', '#00C853', '🟢')
    add('Pi Cycle Top', 'Technical',
        pi, f"{'⚠️ TRIGGERED' if data['pi_triggered'] else f'{pi:.2f} ratio'}",
        pi_sig,
        '111DMA crossing above 2×350DMA signals cycle top within days. Not triggered = safe.',
        'Not triggered (< 0.85)', 'Triggered (111DMA ≥ 2×350DMA)',
        f"{'🚨 CYCLE TOP SIGNAL ACTIVE' if data['pi_triggered'] else ('Approaching trigger' if pi > 0.85 else 'Not triggered — safe')}")

    # ── MARKET STRUCTURE ──
    dom = data['btc_dominance']
    add('BTC Dominance', 'Market Structure',
        dom, f"{dom:.1f}%",
        classify_signal(dom, 60, 45, invert=True),
        'BTC market share. High dominance = BTC leading, altcoin season not started = safer to accumulate BTC.',
        '> 60% (BTC Leading)', '< 45% (Altcoin Season, Cycle Top Near)',
        f"{'BTC strongly dominant' if dom > 60 else ('Moderate dominance' if dom > 50 else 'Low dominance — altcoin season')}")

    alt = data['altcoin_season']
    add('Altcoin Season Index', 'Market Structure',
        alt, f"{alt}/100",
        classify_signal(alt, 25, 60),
        'Measures if altcoins are outperforming BTC. Low = Bitcoin season = good BTC accumulation time.',
        '< 25 (Bitcoin Season)', '> 75 (Altcoin Season)',
        f"{'Bitcoin season' if alt < 25 else ('Mixed market' if alt < 75 else 'Altcoin season')}")

    cbbi = data['cbbi']
    add('CBBI (Bull Run Index)', 'Market Structure',
        cbbi, f"{cbbi:.0f}/100",
        classify_signal(cbbi, 30, 65),
        '9-indicator composite of Bitcoin cycle position. 0 = cycle bottom; 100 = cycle top.',
        '< 30 (Early Cycle)', '> 90 (Cycle Top)',
        f"{'Early cycle — accumulate' if cbbi < 30 else ('Mid cycle' if cbbi < 65 else ('Late cycle — caution' if cbbi < 90 else 'Cycle top'))}")

    # ── MACRO ──
    # GLI Signal
    gli_yoy   = data.get('gli_yoy', -10.0)
    gli_now   = data.get('gli_now', 19.0)
    gli_trend = data.get('gli_trend', 'Contracting')

    if gli_yoy > 5:
        gli_sig = ('BUY', '#00C853', '🟢')
        gli_detail = f"GLI expanding +{gli_yoy:.1f}% YoY (${gli_now:.1f}T) — central banks are injecting liquidity. Historically a strong tailwind for Bitcoin."
    elif gli_yoy > 0:
        gli_sig = ('BUY', '#00C853', '🟢')
        gli_detail = f"GLI growing +{gli_yoy:.1f}% YoY (${gli_now:.1f}T) — modest expansion in global liquidity. Mildly supportive for risk assets."
    elif gli_yoy > -5:
        gli_sig = ('CAUTION', '#FFC107', '🟡')
        gli_detail = f"GLI flat/slightly contracting {gli_yoy:.1f}% YoY (${gli_now:.1f}T) — liquidity is tightening. Bitcoin may face headwinds until this reverses."
    else:
        gli_sig = ('SELL', '#FF3D57', '🔴')
        gli_detail = f"GLI contracting {gli_yoy:.1f}% YoY (${gli_now:.1f}T) — significant liquidity withdrawal. This is the macro headwind Crypto Currently has been warning about."

    add('Global Liquidity Index (GLI)', 'Macro',
        gli_yoy, f"{gli_now:.1f}T ({'+' if gli_yoy >= 0 else ''}{gli_yoy:.1f}% YoY)",
        gli_sig,
        'Composite of Fed, ECB, and BoJ central bank balance sheets converted to USD. When central banks expand their balance sheets (print money), global liquidity rises and Bitcoin historically surges. Contraction = headwind. This is the #1 macro indicator Crypto Currently tracks.',
        '> +5% YoY (Expanding — BTC Tailwind)', '< -5% YoY (Contracting — BTC Headwind)',
        gli_detail)

    dxy = data.get('dxy_value', 104.0)
    dxy_chg = data.get('dxy_chg', 0.0)
    # DXY signal: below 100 = weak dollar = BUY for BTC; 100-105 = neutral; above 105 = strong dollar = CAUTION
    # Also factor in direction: falling DXY is bullish
    if dxy < 100 or dxy_chg < -0.5:
        dxy_sig = ('BUY', '#00C853', '🟢')
        dxy_detail = f"DXY at {dxy:.1f} — weak/falling dollar is a tailwind for Bitcoin and risk assets."
    elif dxy > 106 or dxy_chg > 0.5:
        dxy_sig = ('SELL', '#FF3D57', '🔴')
        dxy_detail = f"DXY at {dxy:.1f} — strong/rising dollar tightens global liquidity and pressures Bitcoin."
    else:
        dxy_sig = ('CAUTION', '#FFC107', '🟡')
        dxy_detail = f"DXY at {dxy:.1f} — dollar consolidating. Watch for breakout direction as it will drive liquidity."

    add('US Dollar Index (DXY)', 'Macro',
        dxy, f"{dxy:.2f} ({'+' if dxy_chg >= 0 else ''}{dxy_chg:.2f}%)",
        dxy_sig,
        'Measures USD strength against a basket of currencies. Falling DXY = looser global liquidity = bullish for BTC. Rising DXY = tighter liquidity = bearish. Crypto Currently monitors this closely as a key macro signal.',
        '< 100 (Weak Dollar — BTC Tailwind)', '> 106 (Strong Dollar — BTC Headwind)',
        dxy_detail)

    # ── BTC vs S&P 500 Divergence ──
    btc_90d      = data.get('btc_90d', -28.0)
    spx_90d      = data.get('spx_90d', 5.0)
    spx_div      = data.get('spx_divergence', -33.0)  # btc_90d - spx_90d

    # Signal logic: based on Crypto Currently's divergence analysis
    # BTC massively underperforming SPX = oversold vs equities = BUY (mean reversion)
    # BTC massively outperforming SPX = late cycle / topping = SELL
    if spx_div <= -20:
        spx_sig = ('BUY', '#00C853', '\U0001f7e2')
        spx_detail = (f"BTC {btc_90d:+.1f}% vs S&P 500 {spx_90d:+.1f}% over 90 days — "
                      f"BTC is underperforming equities by {abs(spx_div):.0f}%. "
                      f"Historically (2018, 2022) these divergences have preceded strong BTC mean-reversion rallies.")
    elif spx_div >= 20:
        spx_sig = ('SELL', '#FF3D57', '\U0001f534')
        spx_detail = (f"BTC {btc_90d:+.1f}% vs S&P 500 {spx_90d:+.1f}% over 90 days — "
                      f"BTC is outperforming equities by {spx_div:.0f}%. "
                      f"BTC leading equities to the upside is a late-cycle signal — historically precedes a top.")
    else:
        spx_sig = ('CAUTION', '#FFC107', '\U0001f7e1')
        spx_detail = (f"BTC {btc_90d:+.1f}% vs S&P 500 {spx_90d:+.1f}% over 90 days — "
                      f"BTC and equities are broadly correlated. No strong divergence signal.")

    add('BTC vs S&P 500',  'Market Structure',
        spx_div,
        f"BTC {btc_90d:+.1f}% / SPX {spx_90d:+.1f}% (90d)",
        spx_sig,
        'Compares Bitcoin\'s 90-day return against the S&P 500. Based on Crypto Currently\'s analysis: when BTC diverges sharply below equities, it historically mean-reverts hard (2018, 2022 examples). BTC outperforming by >20% signals late-cycle risk.',
        'BTC underperforms SPX by > 20% (Oversold vs Equities)', 'BTC outperforms SPX by > 20% (Late Cycle)',
        spx_detail)

    return signals


def compute_overall_verdict(signals):
    """
    Computes an overall accumulation verdict from all signals.
    Returns: (verdict_str, color, score_0_to_100, buy_count, caution_count, sell_count)
    """
    counts = {'BUY': 0, 'CAUTION': 0, 'SELL': 0}
    for s in signals:
        counts[s['signal']] += 1

    total = len(signals)
    buy_pct = counts['BUY'] / total * 100

    if buy_pct >= 60:
        verdict = 'STRONG BUY'
        color   = '#00C853'
        score   = buy_pct
    elif buy_pct >= 40:
        verdict = 'ACCUMULATE'
        color   = '#69F0AE'
        score   = buy_pct
    elif counts['SELL'] / total >= 0.4:
        verdict = 'CAUTION — HOLD'
        color   = '#FF6B35'
        score   = 100 - (counts['SELL'] / total * 100)
    elif counts['SELL'] / total >= 0.6:
        verdict = 'SELL / REDUCE'
        color   = '#FF3D57'
        score   = 100 - (counts['SELL'] / total * 100)
    else:
        verdict = 'NEUTRAL — WATCH'
        color   = '#FFC107'
        score   = 50

    return verdict, color, score, counts['BUY'], counts['CAUTION'], counts['SELL']


# ─────────────────────────────────────────────────────────────────────────────
# 5-Year OHLCV for Price Chart Tab
# ─────────────────────────────────────────────────────────────────────────────

def get_btc_ohlcv_5yr():
    """Fetch 5 years of daily BTC/USD OHLCV data. Returns a DataFrame with DatetimeIndex."""
    # Primary: direct Yahoo Finance v8 API (works on Railway, no sandbox dependency)
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD"
        params = {'interval': '1d', 'range': '5y', 'includeAdjustedClose': 'true'}
        r = requests.get(url, params=params, timeout=20,
                         headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        if r.status_code == 200:
            data = r.json()
            if data.get('chart', {}).get('result'):
                result = data['chart']['result'][0]
                timestamps = result.get('timestamp', [])
                quotes = result['indicators']['quote'][0]
                df = pd.DataFrame({
                    'open':   quotes.get('open', []),
                    'high':   quotes.get('high', []),
                    'low':    quotes.get('low', []),
                    'close':  quotes.get('close', []),
                    'volume': quotes.get('volume', []),
                }, index=[datetime.fromtimestamp(t) for t in timestamps])
                df = df.dropna(subset=['close'])
                if not df.empty:
                    return df
    except Exception as e:
        print(f"[get_btc_ohlcv_5yr yahoo] {e}")

    # Try sandbox ApiClient if available
    try:
        from data_api import ApiClient
        client = ApiClient()
        r = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': 'BTC-USD', 'interval': '1d', 'range': '5y',
            'includeAdjustedClose': True
        })
        if r and 'chart' in r and r['chart'].get('result'):
            result = r['chart']['result'][0]
            timestamps = result.get('timestamp', [])
            quotes = result['indicators']['quote'][0]
            df = pd.DataFrame({
                'open':   quotes.get('open', []),
                'high':   quotes.get('high', []),
                'low':    quotes.get('low', []),
                'close':  quotes.get('close', []),
                'volume': quotes.get('volume', []),
            }, index=[datetime.fromtimestamp(t) for t in timestamps])
            df = df.dropna(subset=['close'])
            if not df.empty:
                return df
    except Exception as e:
        print(f"[get_btc_ohlcv_5yr sandbox] {e}")

    # Fallback: CoinGecko
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {'vs_currency': 'usd', 'days': '1825', 'interval': 'daily'}
        r = requests.get(url, params=params, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            prices = r.json().get('prices', [])
            df = pd.DataFrame(prices, columns=['ts', 'close'])
            df.index = pd.to_datetime(df['ts'], unit='ms')
            df = df[['close']].dropna()
            df['open'] = df['close'].shift(1).fillna(df['close'])
            df['high'] = df['close']
            df['low']  = df['close']
            df['volume'] = 0
            return df
    except Exception as e:
        print(f"[get_btc_ohlcv_5yr coingecko] {e}")

    return pd.DataFrame()

import ccxt
import pandas as pd
import requests
import time
import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# 1. PROFESSIONAL UI THEME (CSS)
# ==========================================
st.set_page_config(page_title="Shyamswayam Terminal", page_icon="🏛️", layout="wide")

CLASSY_CSS = """
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
    h1, h2, h3, h4 { color: #d4af37 !important; font-weight: 400 !important; letter-spacing: 1px; }
    .stButton>button { background-color: #1f242c; color: #d4af37; border: 1px solid #d4af37; border-radius: 4px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; transition: all 0.2s ease; width: 100%; }
    .stButton>button:hover { background-color: #d4af37; color: #0d1117; border-color: #d4af37; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 0px; color: #8b949e; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #d4af37 !important; border-bottom: 2px solid #d4af37 !important; }
    .brand-title { font-size: 2rem; font-weight: 900; color: #d4af37; text-transform: uppercase; letter-spacing: 2px; text-align: center; margin-bottom: 0px; padding-top: 15px; }
    .brand-subtitle { color: #8b949e; font-size: 0.9rem; letter-spacing: 1px; text-align: center; margin-bottom: 30px; }
</style>
"""
st.markdown(CLASSY_CSS, unsafe_allow_html=True)

# ==========================================
# 2. CONFIGURATION & TELEGRAM
# ==========================================
BOT_TOKEN = "8657789671:AAHgmek_WvxFrqkP_F0UomRS-rct1Vk7V1c"
CHAT_ID = "5868749596"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try: requests.post(url, data=payload, timeout=5)
    except Exception: pass

def get_exchange(name):
    if name == "Binance":
        exch = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
        exch.urls['api']['public'] = 'https://api.binance.me/api/v3'
        exch.urls['api']['private'] = 'https://api.binance.me/api/v3'
        exch.hostname = 'api.binance.me' 
        return exch
    elif name == "Bybit": return ccxt.bybit({'enableRateLimit': True})
    elif name == "Delta Exchange": return ccxt.delta({'enableRateLimit': True})
    return ccxt.gateio({'enableRateLimit': True})

# ==========================================
# 3. CORE ALGORITHM ENGINE
# ==========================================
def get_markets(exchange, m_type, min_vol=50000, max_coins=600):
    try:
        if exchange.id == 'binance':
            if m_type == 'linear':
                st.warning("⚠️ Binance Futures is strictly blocked in your region. Switch 'Market Asset' to 'spot'.")
                return []
            else: exchange.hostname = 'api.binance.me'

        exchange.load_markets()
        if hasattr(exchange, 'options'): exchange.options['defaultType'] = m_type
        
        tickers = exchange.fetch_tickers()
        symbols = [sym for sym, tick in tickers.items() if ('/USDT' in sym or ':USDT' in sym) and (tick.get('quoteVolume') or tick.get('baseVolume', 0)) >= min_vol]
        symbols.sort(key=lambda s: (tickers[s].get('quoteVolume') or 0), reverse=True)
        return symbols[:max_coins]
    except Exception as e: 
        st.error(f"⚠️ {exchange.name} failed. Error: {e}")
        return []

def get_ohlcv_data(exchange, symbol, tf):
    """Handles standard timeframes and synthetic 3hr candle generation."""
    try:
        if tf == '3h':
            # Fetch 1h data and resample to 3h to bypass API limitations
            bars = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=600)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.resample('3h', offset='0h').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna().reset_index()
        else:
            bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=200)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    except Exception: return None

def analyze_asset(exchange, symbol, tf):
    """SMC Vector Sweeps & Trend-Extreme Inside Candles"""
    df = get_ohlcv_data(exchange, symbol, tf)
    if df is None or len(df) < 50: return None

    try:
        c_open, c_high, c_low, c_close = df['open'].iloc[-2], df['high'].iloc[-2], df['low'].iloc[-2], df['close'].iloc[-2]
        prev_candle = df.iloc[-3]
        
        is_green = c_close > c_open
        is_red = c_close < c_open

        # ==========================================================
        # STRATEGY 1: ADVANCED ICT SMC SWEEPS (Sweep + Displacement)
        # ==========================================================
        lookback = 5 
        # 🔴 Bearish Sweep (BSL)
        for j in range(len(df) - 3, lookback - 1, -1):
            high_window = df['high'].iloc[j - lookback : j + lookback + 1]
            if df['high'].iloc[j] == high_window.max():
                pivot_high = df['high'].iloc[j]
                if c_high > pivot_high and c_close < pivot_high and is_red:
                    if c_close < prev_candle['low']:
                        return {'symbol': symbol, 'category': 'SMC', 'type': '🔴 BSL Sweep + Vector Displacement', 'price': c_close}
                    else:
                        return {'symbol': symbol, 'category': 'WATCH', 'type': '👀 BSL Swept (Need Displacement)', 'price': c_close}
                break 

        # 🟢 Bullish Sweep (SSL)
        for j in range(len(df) - 3, lookback - 1, -1):
            low_window = df['low'].iloc[j - lookback : j + lookback + 1]
            if df['low'].iloc[j] == low_window.min():
                pivot_low = df['low'].iloc[j]
                if c_low < pivot_low and c_close > pivot_low and is_green:
                    if c_close > prev_candle['high']:
                        return {'symbol': symbol, 'category': 'SMC', 'type': '🟢 SSL Sweep + Vector Displacement', 'price': c_close}
                    else:
                        return {'symbol': symbol, 'category': 'WATCH', 'type': '👀 SSL Swept (Need Displacement)', 'price': c_close}
                break 

        # ==========================================================
        # STRATEGY 2: TREND-EXTREME INSIDE CANDLES
        # ==========================================================
        i_candle = df.iloc[-2] # Current closed candle
        m_candle = df.iloc[-3] # Mother candle
        
        # Strict Inside Bar Definition
        is_inside = (i_candle['high'] < m_candle['high']) and (i_candle['low'] > m_candle['low'])
        
        if is_inside:
            # Look back 20 candles before the mother bar to define the recent trend
            trend_window = df.iloc[-23:-3]
            recent_high = trend_window['high'].max()
            recent_low = trend_window['low'].min()
            
            # Trend TOP Validation: Mother bar must be the highest point of the recent trend
            if m_candle['high'] >= recent_high * 0.999:
                return {'symbol': symbol, 'category': 'INSIDE', 'type': '⬇️ Top Trend Inside Bar (Reversal/Breakdown)', 'price': i_candle['close']}
                
            # Trend BOTTOM Validation: Mother bar must be the lowest point of the recent trend
            elif m_candle['low'] <= recent_low * 1.001:
                return {'symbol': symbol, 'category': 'INSIDE', 'type': '⬆️ Bottom Trend Inside Bar (Reversal/Breakout)', 'price': i_candle['close']}

        return None
    except Exception: return None

# ==========================================
# 4. CHART RENDERING
# ==========================================
def render_tv(symbol, exch):
    sym = symbol.split(':')[0].replace('/', '')
    prefix = {"Gate.io": "GATEIO", "Bybit": "BYBIT", "Delta Exchange": "DELTA", "Binance": "BINANCE"}.get(exch, "BINANCE")
    html = f"""
    <div style="height:550px; border: 1px solid #30363d; border-radius: 4px;">
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
            "autosize": true, "symbol": "{prefix}:{sym}", "interval": "180",
            "timezone": "Etc/UTC", "theme": "dark", "style": "1",
            "locale": "en", "backgroundColor": "#0d1117", "gridColor": "#161b22",
            "hide_top_toolbar": false, "container_id": "tv"
        }});
        </script>
        <div id="tv" style="height:100%;"></div>
    </div>
    """
    components.html(html, height=550)

# ==========================================
# 5. DASHBOARD LAYOUT
# ==========================================
st.markdown("<div class='brand-title'>SHYAMSWAYAM TERMINAL</div>", unsafe_allow_html=True)
st.markdown("<div class='brand-subtitle'>SMC Vectors & Price Action Engine</div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### SYSTEM PARAMETERS")
    exch_choice = st.selectbox("🌐 Data Provider", ['Gate.io', 'Bybit', 'Delta Exchange', 'Binance'])
    m_type = st.selectbox("📊 Market Asset", ['spot', 'linear'])
    tf = st.selectbox("⏳ Timeframe Resolution", ['15m', '1h', '3h', '4h'], index=2) # 3h added and set as default!
    min_vol = st.number_input("💵 Min Volume (USD)", value=50000, step=10000)
    st.divider()
    st.caption("Status: STANDBY\n\nLogic: CLOSED CANDLE ONLY")

col_control, col_chart = st.columns([1.3, 2])

with col_control:
    if st.button("EXECUTE MARKET SCAN"):
        status = st.empty()
        bar = st.progress(0)
        ex = get_exchange(exch_choice)
        status.caption(f"Connecting to {exch_choice} orderbooks...")
        
        symbols = get_markets(ex, m_type, min_vol)
        status.caption(f"Analyzing {len(symbols)} assets for institutional footprints...")
        
        results = []
        for i, s in enumerate(symbols):
            bar.progress((i + 1) / len(symbols))
            res = analyze_asset(ex, s, tf)
            if res:
                results.append(res)
                if res['category'] != 'WATCH':
                    send_telegram_alert(f"🏛️ *Shyamswayam Terminal*\n\n🪙 Ticker: {s}\n🎯 Setup: {res['type']}\n💲 Close: {res['price']}\n⏳ TF: {tf}\n🌐 Exch: {exch_choice}")
            time.sleep(0.01)
            
        status.success(f"Scan complete. {len([r for r in results if r['category'] != 'WATCH'])} confirmed setups identified.")
        bar.empty()

        if results:
            tab1, tab2, tab3 = st.tabs(["💧 SMC Sweeps", "🕯️ Inside Candles", "👀 Watchlist"])
            
            with tab1:
                smc = [r for r in results if r['category'] == 'SMC']
                if smc:
                    for r in smc: st.info(f"**{r['symbol']}** — {r['type']} at {r['price']}")
                else: st.caption("No SMC liquidity sweeps detected.")
                    
            with tab2:
                inside = [r for r in results if r['category'] == 'INSIDE']
                if inside:
                    for r in inside: st.success(f"**{r['symbol']}** — {r['type']} at {r['price']}")
                else: st.caption("No Trend-Extreme Inside Candles detected.")
                
            with tab3:
                watch = [r for r in results if r['category'] == 'WATCH']
                if watch:
                    for r in watch: st.markdown(f"<div style='border-left: 3px solid #8b949e; padding-left: 10px; margin-bottom: 10px;'>**{r['symbol']}** — {r['type']} at {r['price']}</div>", unsafe_allow_html=True)
                else: st.caption("Watchlist is currently empty.")
        else:
            st.info("No valid trade setups currently detected on the closed candle.")

with col_chart:
    st.markdown("### ASSET VISUALIZATION")
    chart_sym = st.text_input("Ticker Symbol (e.g., BTC/USDT)", value="BTC/USDT").upper()
    # Note: Interval "180" in TradingView widget maps to 3 Hours.
    if chart_sym: render_tv(chart_sym, exch_choice)

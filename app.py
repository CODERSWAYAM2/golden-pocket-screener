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
    /* Sleek Dark Slate Background */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Clean Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    /* Muted Gold Typography */
    h1, h2, h3, h4 {
        color: #d4af37 !important;
        font-weight: 400 !important;
        letter-spacing: 1px;
    }
    /* Professional Flat Button */
    .stButton>button {
        background-color: #1f242c;
        color: #d4af37;
        border: 1px solid #d4af37;
        border-radius: 4px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #d4af37;
        color: #0d1117;
        border-color: #d4af37;
    }
    /* Tab Styling for clean organization */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 0px;
        color: #8b949e;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #d4af37 !important;
        border-bottom: 2px solid #d4af37 !important;
    }
    /* Branding */
    .brand-title {
        font-size: 2rem;
        font-weight: 900;
        color: #d4af37;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-align: center;
        margin-bottom: 0px;
        padding-top: 15px;
    }
    .brand-subtitle {
        color: #8b949e;
        font-size: 0.9rem;
        letter-spacing: 1px;
        text-align: center;
        margin-bottom: 30px;
    }
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
    """Initializes the selected exchange with heavy-duty India bypass."""
    if name == "Binance":
        exch = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        exch.urls['api']['public'] = 'https://api.binance.me/api/v3'
        exch.urls['api']['private'] = 'https://api.binance.me/api/v3'
        exch.hostname = 'api.binance.me' 
        return exch
        
    elif name == "Bybit": 
        return ccxt.bybit({'enableRateLimit': True})
    elif name == "Delta Exchange": 
        return ccxt.delta({'enableRateLimit': True})
        
    return ccxt.gateio({'enableRateLimit': True})

# ==========================================
# 3. CORE ALGORITHM ENGINE
# ==========================================
def get_markets(exchange, m_type, min_vol=50000, max_coins=600):
    """Scans for active, liquid markets based on user volume thresholds."""
    try:
        if exchange.id == 'binance':
            if m_type == 'linear':
                st.warning("⚠️ Binance Futures is strictly blocked in your region. Switch 'Market Asset' to 'spot'.")
                return []
            else:
                exchange.hostname = 'api.binance.me'

        exchange.load_markets()
        if hasattr(exchange, 'options'): exchange.options['defaultType'] = m_type
        
        tickers = exchange.fetch_tickers()
        symbols = []
        for sym, tick in tickers.items():
            if '/USDT' in sym or ':USDT' in sym:
                vol = tick.get('quoteVolume') or tick.get('baseVolume', 0)
                if vol and vol >= min_vol: symbols.append(sym)
                
        symbols.sort(key=lambda s: (tickers[s].get('quoteVolume') or 0), reverse=True)
        return symbols[:max_coins]
        
    except Exception as e: 
        st.error(f"⚠️ {exchange.name} failed. Error: {e}")
        return []

def analyze_asset(exchange, symbol, tf):
    """
    The Ultimate Shyamswayam Mathematical Engine.
    Includes: SMC Sweeps, Watchlist Radar, Golden Pockets, A1 Sweeps, & Deep Pullbacks.
    Operates STRICTLY on the closed candle.
    """
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=200)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        if len(df) < 150: return None

        # --- THE 'JUST-CLOSED' CANDLE LOGIC ---
        c_open = df['open'].iloc[-2]
        c_high = df['high'].iloc[-2]
        c_low = df['low'].iloc[-2]
        c_close = df['close'].iloc[-2]
        prev_candle = df.iloc[-3]
        
        is_green = c_close > c_open
        is_red = c_close < c_open

        # ==========================================================
        # STRATEGY 1: ADVANCED ICT SMC SWEEPS (Sweep + Displacement)
        # ==========================================================
        lookback = 5 
        for j in range(len(df) - 3, lookback - 1, -1):
            # 🔴 Bearish Sweep (BSL)
            high_window = df['high'].iloc[j - lookback : j + lookback + 1]
            if df['high'].iloc[j] == high_window.max():
                pivot_high = df['high'].iloc[j]
                if c_high > pivot_high and c_close < pivot_high and is_red:
                    # Book Confirmation: Vector Candle Engulfs Previous Low
                    if c_close < prev_candle['low']:
                        return {'symbol': symbol, 'category': 'SMC', 'type': '🔴 BSL Sweep + Vector Displacement', 'price': c_close}
                    else:
                        return {'symbol': symbol, 'category': 'WATCH', 'type': '👀 BSL Swept (Need Displacement)', 'price': c_close}
                break 

        for j in range(len(df) - 3, lookback - 1, -1):
            # 🟢 Bullish Sweep (SSL)
            low_window = df['low'].iloc[j - lookback : j + lookback + 1]
            if df['low'].iloc[j] == low_window.min():
                pivot_low = df['low'].iloc[j]
                if c_low < pivot_low and c_close > pivot_low and is_green:
                    # Book Confirmation: Vector Candle Engulfs Previous High
                    if c_close > prev_candle['high']:
                        return {'symbol': symbol, 'category': 'SMC', 'type': '🟢 SSL Sweep + Vector Displacement', 'price': c_close}
                    else:
                        return {'symbol': symbol, 'category': 'WATCH', 'type': '👀 SSL Swept (Need Displacement)', 'price': c_close}
                break 

        # ==========================================================
        # STRATEGY 2: TREND-ALIGNED FIBONACCI
        # ==========================================================
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        if c_close < df['EMA_50'].iloc[-2]: return None # Abort if against trend

        recent_window = df.iloc[-100:-2].reset_index(drop=True)
        h_idx = recent_window['high'].idxmax()
        swing_h = recent_window['high'].max()
        if h_idx == 0: return None
        
        swing_l = recent_window.loc[:h_idx, 'low'].min()
        swing_rng = swing_h - swing_l
        if swing_rng == 0 or (swing_rng / swing_l) * 100 < 1.5: return None

        fib_5 = swing_h - (swing_rng * 0.5)
        fib_618 = swing_h - (swing_rng * 0.618)
        fib_786 = swing_h - (swing_rng * 0.786)

        # --- A1 Liquidity Sweep ---
        after_high = recent_window.loc[h_idx:]
        if len(after_high) > 3:
            pocket_touches = after_high[(after_high['low'] <= fib_5) & (after_high['low'] >= fib_786)]
            if not pocket_touches.empty:
                pocket_low = pocket_touches['low'].min()
                if is_green and c_low < pocket_low and c_close > pocket_low:
                    return {'symbol': symbol, 'category': 'FIB', 'type': '🔥 A1 Fib Sweep', 'price': c_close}

        # --- 0.5 to 0.618 Golden Pocket ---
        in_pocket = (fib_618 * 0.998) <= c_close <= (fib_5 * 1.005)
        swept_pocket = c_low <= fib_5 and c_low >= (fib_786 * 0.99)
        
        if swept_pocket or in_pocket:
            # 1. THE NEW UPGRADE: Internal BOS / ChoCh Confirmation (Strongest Signal)
            if is_green and c_close > prev_candle['high']:
                return {'symbol': symbol, 'category': 'FIB', 'type': '👑 Golden Pocket + BOS Confirmed', 'price': c_close}
            
            # 2. YOUR RESTORED LOGIC: Strong Momentum Validation 
            if in_pocket and is_green and (c_close - c_open) / swing_rng > 0.05: 
                if not (prev_candle['open'] > fib_5 and prev_candle['close'] < fib_618): 
                    return {'symbol': symbol, 'category': 'FIB', 'type': '🟡 Validated 0.5-0.6 Pocket', 'price': c_close}
            
            # 3. YOUR RESTORED LOGIC: Watchlist Radar (Still setting up)
            if in_pocket:
                return {'symbol': symbol, 'category': 'WATCH', 'type': '👀 Entering 0.5 Zone', 'price': c_close}

        # --- Deep 0.786 Pullback ---
        if (fib_786 * 0.998) <= c_close <= (fib_786 * 1.005) and is_green:
            return {'symbol': symbol, 'category': 'DEEP', 'type': '🔴 0.786 Deep Pullback', 'price': c_close}

        return None
    except Exception: return None

# ==========================================
# 4. CHART RENDERING
# ==========================================
def render_tv(symbol, exch):
    sym = symbol.split(':')[0].replace('/', '')
    prefix = "GATEIO"
    if exch == "Bybit": prefix = "BYBIT"
    elif exch == "Delta Exchange": prefix = "DELTA"
    elif exch == "Binance": prefix = "BINANCE"  
    
    html = f"""
    <div style="height:550px; border: 1px solid #30363d; border-radius: 4px;">
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
            "autosize": true, "symbol": "{prefix}:{sym}", "interval": "60",
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
st.markdown("<div class='brand-subtitle'>Institutional SMC & Fibonacci Analysis Engine</div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### SYSTEM PARAMETERS")
    exch_choice = st.selectbox("🌐 Data Provider", ['Gate.io', 'Bybit', 'Delta Exchange', 'Binance'])
    m_type = st.selectbox("📊 Market Asset", ['spot', 'linear'], help="Linear = Perpetual Futures")
    tf = st.selectbox("⏳ Timeframe Resolution", ['15m', '1h', '4h'], index=1)
    min_vol = st.number_input("💵 Min Volume (USD)", value=50000, step=10000)
    st.divider()
    st.caption("Status: STANDBY\n\nAlerts: ACTIVE\n\nLogic: CLOSED CANDLE ONLY")

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
            tab1, tab2, tab3, tab4 = st.tabs(["💧 SMC Sweeps", "📐 Fibonacci", "📉 Deep Retest", "👀 Watchlist"])
            
            with tab1:
                smc = [r for r in results if r['category'] == 'SMC']
                if smc:
                    for r in smc: st.info(f"**{r['symbol']}** — {r['type']} at {r['price']}")
                else: st.caption("No SMC liquidity sweeps detected on the closed candle.")
                    
            with tab2:
                fib = [r for r in results if r['category'] == 'FIB']
                if fib:
                    for r in fib: st.success(f"**{r['symbol']}** — {r['type']} at {r['price']}")
                else: st.caption("No valid 0.5-0.6 Golden Pocket or A1 Sweep patterns.")
                    
            with tab3:
                deep = [r for r in results if r['category'] == 'DEEP']
                if deep:
                    for r in deep: st.warning(f"**{r['symbol']}** — {r['type']} at {r['price']}")
                else: st.caption("No deep 0.786 pullbacks detected.")
                
            with tab4:
                watch = [r for r in results if r['category'] == 'WATCH']
                if watch:
                    for r in watch: st.markdown(f"<div style='border-left: 3px solid #8b949e; padding-left: 10px; margin-bottom: 10px;'>**{r['symbol']}** — {r['type']} at {r['price']}</div>", unsafe_allow_html=True)
                else: st.caption("No assets are currently entering the 0.5-0.618 radar zone.")
        else:
            st.info("No valid trade setups currently detected on the closed candle.")

with col_chart:
    st.markdown("### ASSET VISUALIZATION")
    chart_sym = st.text_input("Ticker Symbol (e.g., BTC/USDT)", value="BTC/USDT").upper()
    if chart_sym: render_tv(chart_sym, exch_choice)

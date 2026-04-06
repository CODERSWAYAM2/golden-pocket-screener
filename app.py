import ccxt
import pandas as pd
import requests
import time
import streamlit as st
import streamlit.components.v1 as components

# --- PAGE CONFIGURATION & CUSTOM CSS ---
st.set_page_config(page_title="Shyamswayam Trading", page_icon="⚡", layout="wide")

custom_css = """
<style>
    /* Main Background - Deep Blue/Black Gradient */
    .stApp {
        background-color: #0a0e17;
        background-image: radial-gradient(circle at 50% 0%, #161e2d 0%, #0a0e17 80%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0f1522 !important;
        border-right: 1px solid #d4af37;
    }

    /* Golden Action Button with Pulse Animation */
    .stButton>button {
        background: linear-gradient(135deg, #d4af37 0%, #f9e596 50%, #d4af37 100%);
        color: #000000;
        border: none;
        border-radius: 8px;
        font-weight: 900;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4);
        width: 100%;
        animation: pulse 2s infinite;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(212, 175, 55, 0.7);
        color: #000;
    }

    /* Keyframe Animations */
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(212, 175, 55, 0); }
        100% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0); }
    }

    /* Custom Logo Container */
    .brand-logo {
        text-align: center;
        padding: 25px 15px;
        background: linear-gradient(180deg, rgba(212,175,55,0.1) 0%, rgba(10,14,23,0) 100%);
        border: 1px solid rgba(212, 175, 55, 0.3);
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: inset 0 0 20px rgba(212,175,55,0.05);
    }
    .brand-title {
        font-size: 2.2rem;
        font-weight: 900;
        background: -webkit-linear-gradient(#ffdf00, #d4af37);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .brand-subtitle {
        color: #8b9bb4;
        font-size: 0.9rem;
        letter-spacing: 1px;
        margin-top: 5px;
    }

    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        color: #d4af37;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- SHYAMSWAYAM BRANDING HEADER ---
st.markdown("""
<div class="brand-logo">
    <h1 class="brand-title">SHYAMSWAYAM</h1>
    <div class="brand-subtitle">INSTITUTIONAL ALGORITHMIC SCREENER</div>
</div>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
EXCHANGE_NAME = "Gate.io"
BOT_TOKEN = "8657789671:AAHgmek_WvxFrqkP_F0UomRS-rct1Vk7V1c"
CHAT_ID = "5868749596"

exchange = ccxt.gateio({'enableRateLimit': True})

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try: requests.post(url, data=payload, timeout=5)
    except Exception: pass

def get_base_filtered_coins(market_type, min_volume=30000, max_coins=250):
    try:
        exchange.load_markets()
        exchange.options['defaultType'] = market_type
        tickers = exchange.fetch_tickers()
        valid_symbols = []
        for symbol, ticker in tickers.items():
            if '/USDT' in symbol:
                vol = ticker.get('quoteVolume') or ticker.get('baseVolume', 0)
                if vol and vol >= min_volume:
                    valid_symbols.append(symbol)
        valid_symbols.sort(key=lambda s: (tickers[s].get('quoteVolume') or 0), reverse=True)
        return valid_symbols[:max_coins]
    except Exception: return []

def check_all_setups(symbol, timeframe):
    """The Ultimate Mathematical Engine integrating SMC and Fib Strategies."""
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=120)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        if len(df) < 100: return None

        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        current_price = last_candle['close']
        is_green = current_price > last_candle['open']
        is_red = current_price < last_candle['open']

        # ==========================================================
        # STRATEGY 1: SMC LIQUIDITY SWEEPS (Support / Resistance)
        # ==========================================================
        liq_window = df.iloc[-60:-4]
        support_level = liq_window['low'].min()
        resistance_level = liq_window['high'].max()

        if last_candle['low'] < support_level and current_price > support_level and is_green:
            return {'symbol': symbol, 'type': 'SMC Bullish', 'display_name': '🟢 Bullish SMC Sweep (Support)', 'price': current_price}

        if last_candle['high'] > resistance_level and current_price < resistance_level and is_red:
            return {'symbol': symbol, 'type': 'SMC Bearish', 'display_name': '🔴 Bearish SMC Sweep (Resistance)', 'price': current_price}

        # ==========================================================
        # STRATEGY 2: TREND-ALIGNED FIBONACCI SETUPS
        # ==========================================================
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        if current_price < df['EMA_50'].iloc[-1]: return None

        recent_df = df.tail(60).reset_index(drop=True)
        high_idx = recent_df['high'].idxmax()
        swing_high = recent_df['high'].max()
        if high_idx == 0: return None
        
        swing_low = recent_df.loc[:high_idx, 'low'].min()
        swing_range = swing_high - swing_low
        if swing_range == 0: return None

        # Sideways Buffer Filter
        if (swing_range / swing_low) * 100 < 1.5: return None

        fib_0_5 = swing_high - (swing_range * 0.5)
        fib_0_618 = swing_high - (swing_range * 0.618)
        fib_0_786 = swing_high - (swing_range * 0.786)

        pocket_top = fib_0_5 * 1.002
        pocket_bottom = fib_0_618 * 0.998
        
        # --- A1 Liquidity Sweep ---
        candles_after_high = recent_df.loc[high_idx:].reset_index(drop=True)
        if len(candles_after_high) > 5:
            zone_touches = candles_after_high[candles_after_high['low'] <= fib_0_618 * 1.005]
            if not zone_touches.empty:
                first_touch_low = zone_touches['low'].iloc[0]
                first_touch_idx = zone_touches.index[0]
                if len(candles_after_high) > first_touch_idx + 3:
                    if is_green and last_candle['low'] < first_touch_low and current_price > first_touch_low:
                        return {'symbol': symbol, 'type': 'A1 Sweep', 'display_name': '🔥 A1 Fib Liquidity Sweep', 'price': current_price}

        # --- Strict Golden Pocket ---
        if pocket_bottom <= current_price <= pocket_top:
            if is_green and (current_price - last_candle['open']) / swing_range > 0.05:
                if not (prev_candle['open'] > fib_0_5 and prev_candle['close'] < fib_0_618):
                    return {'symbol': symbol, 'type': 'Golden Pocket', 'display_name': '🟡 Validated Golden Pocket', 'price': current_price}

        # --- Deep Pullback ---
        if (fib_0_786 * 0.997) <= current_price <= (fib_0_786 * 1.005) and is_green:
            return {'symbol': symbol, 'type': 'Deep Pullback', 'display_name': '🔴 Deep Pullback (0.786)', 'price': current_price}

        return None
    except Exception: return None

def render_chart(symbol):
    clean_sym = symbol.split(':')[0].replace('/', '')
    tv_symbol = f"GATEIO:{clean_sym}"
    html = f"""
    <div style="height:600px; border: 1px solid #d4af37; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
            "autosize": true, "symbol": "{tv_symbol}", "interval": "60",
            "timezone": "Etc/UTC", "theme": "dark", "style": "1",
            "locale": "en", "backgroundColor": "#0a0e17", "gridColor": "#161e2d",
            "hide_top_toolbar": false, "save_image": false,
            "container_id": "tv_chart"
        }});
        </script>
        <div id="tv_chart" style="height:100%;"></div>
    </div>
    """
    components.html(html, height=600)

# --- UI LAYOUT ---
with st.sidebar:
    st.markdown("<h3 style='color: #d4af37;'>⚙️ ENGINE PARAMS</h3>", unsafe_allow_html=True)
    m_type = st.selectbox("Market Type", ['spot'])
    tf = st.selectbox("⏳ Timeframe", ['15m', '1h', '4h'], index=1)
    vol_threshold = st.number_input("💵 Min Volume ($)", value=30000, step=10000)
    st.divider()
    st.markdown("🟢 **Status:** Active")
    st.markdown("📡 **Telegram:** Connected")

col_scan, col_chart = st.columns([1.2, 1.8])

with col_scan:
    if st.button("INITIALIZE SCAN"):
        status = st.empty()
        p_bar = st.progress(0)
        status.info("Synchronizing with Exchange Data...")
        symbols = get_base_filtered_coins(m_type, min_volume=vol_threshold)
        
        all_results = []
        status.info(f"Analyzing {len(symbols)} assets for Institutional Footprints...")
        
        for i, s in enumerate(symbols):
            p_bar.progress((i + 1) / len(symbols))
            res = check_all_setups(s, tf)
            if res:
                all_results.append(res)
                msg = f"🚨 *Shyamswayam Alert*\n\n🪙 {s}\n🎯 {res['display_name']}\n⏳ TF: {tf}\n💲 Price: {res['price']}"
                send_telegram_alert(msg)
            time.sleep(0.01)
            
        status.success(f"Execution Complete. {len(all_results)} high-probability targets identified.")
        st.divider()

        smc_bull = [s for s in all_results if s['type'] == 'SMC Bullish']
        smc_bear = [s for s in all_results if s['type'] == 'SMC Bearish']
        a1_sweep = [s for s in all_results if s['type'] == 'A1 Sweep']
        golden = [s for s in all_results if s['type'] == 'Golden Pocket']
        deep = [s for s in all_results if s['type'] == 'Deep Pullback']

        st.markdown("<h4 style='color: #d4af37;'>💧 SMC LIQUIDITY SWEEPS</h4>", unsafe_allow_html=True)
        if smc_bull or smc_bear:
            for item in smc_bull: st.success(f"**{item['symbol']}** — Bullish Sweep at {item['price']}")
            for item in smc_bear: st.error(f"**{item['symbol']}** — Bearish Sweep at {item['price']}")
        else: st.caption("No SMC anomalies detected.")

        st.markdown("<h4 style='color: #d4af37;'>🔥 A1 FIB LIQUIDITY SWEEP</h4>", unsafe_allow_html=True)
        if a1_sweep:
            for item in a1_sweep: st.error(f"**{item['symbol']}** — Swept Fib Low at {item['price']}")
        else: st.caption("No A1 patterns active.")

        st.markdown("<h4 style='color: #d4af37;'>🟡 VALIDATED GOLDEN POCKET</h4>", unsafe_allow_html=True)
        if golden:
            for item in golden: st.success(f"**{item['symbol']}** — Zone Held at {item['price']}")
        else: st.caption("No validated pocket entries.")

        st.markdown("<h4 style='color: #d4af37;'>🔴 DEEP PULLBACK (0.786)</h4>", unsafe_allow_html=True)
        if deep:
            for item in deep: st.warning(f"**{item['symbol']}** — Deep Retest at {item['price']}")
        else: st.caption("No deep retests found.")

with col_chart:
    st.markdown("<h3 style='color: #d4af37;'>📈 TACTICAL OVERVIEW</h3>", unsafe_allow_html=True)
    target_sym = st.text_input("Input Ticker (e.g., BTC/USDT)", value="BTC/USDT").upper()
    if target_sym: render_chart(target_sym)

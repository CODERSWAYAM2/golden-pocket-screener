import ccxt
import pandas as pd
import requests
import time
import streamlit as st
import streamlit.components.v1 as components

# --- CONFIGURATION ---
EXCHANGE_NAME = "Bybit"
BOT_TOKEN = "8657789671:AAHgmek_WvxFrqkP_F0UomRS-rct1Vk7V1c"
CHAT_ID = "5868749596"

# Initialize Bybit
exchange = ccxt.bybit({'enableRateLimit': True})

def send_telegram_alert(message):
    """Sends a push notification to your Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception:
        pass

def get_base_filtered_coins(market_type, min_volume=50000, max_coins=250):
    """Fetches high-volume coins directly from the exchange."""
    try:
        exchange.load_markets()
        exchange.options['defaultType'] = market_type
        tickers = exchange.fetch_tickers()
        
        valid_symbols = []
        for symbol, ticker in tickers.items():
            if '/USDT' in symbol or ':USDT' in symbol:
                # Use quoteVolume (USDT volume) or baseVolume as fallback
                vol = ticker.get('quoteVolume') or ticker.get('baseVolume', 0)
                if vol and vol >= min_volume:
                    valid_symbols.append(symbol)
                    
        # Sort by volume (Highest first)
        valid_symbols.sort(key=lambda s: (tickers[s].get('quoteVolume') or 0), reverse=True)
        return valid_symbols[:max_coins]
    except Exception as e:
        st.error(f"Error fetching markets: {e}")
        return []

def check_fibonacci_setup(symbol, timeframe):
    """Mathematical engine to find Trend + Retest setups."""
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        if len(df) < 60: return None

        # 1. TREND: 50 EMA (Native Pandas calculation - very fast)
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        current_price = df['close'].iloc[-1]
        current_ema = df['EMA_50'].iloc[-1]
        
        # Only trade WITH the trend (Price must be above EMA 50)
        if current_price < current_ema:
            return None

        # 2. SWING DETECTION: Find the most recent peak and the floor before it
        recent_df = df.tail(50).reset_index(drop=True)
        high_idx = recent_df['high'].idxmax()
        swing_high = recent_df['high'].max()
        
        if high_idx == 0: return None
        swing_low = recent_df.loc[:high_idx, 'low'].min()
        swing_range = swing_high - swing_low
        
        if swing_range == 0: return None
            
        # 3. FIBONACCI LEVELS
        fib_0_5 = swing_high - (swing_range * 0.5)
        fib_0_618 = swing_high - (swing_range * 0.618)
        fib_0_786 = swing_high - (swing_range * 0.786)
        
        # 4. TARGET ZONES (With small buffer for wicks)
        if (fib_0_618 * 0.997) <= current_price <= (fib_0_5 * 1.003):
            return {'symbol': symbol, 'type': 'Golden Pocket', 'price': current_price}
        elif (fib_0_786 * 0.997) <= current_price <= (fib_0_786 * 1.005):
            return {'symbol': symbol, 'type': 'Deep Pullback', 'price': current_price}
            
        return None
    except Exception:
        return None

def render_chart(symbol):
    """Embeds the TradingView interactive chart."""
    clean_sym = symbol.split(':')[0].replace('/', '')
    tv_symbol = f"BYBIT:{clean_sym}"
    html = f"""
    <div style="height:500px;">
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true, "symbol": "{tv_symbol}", "interval": "60",
        "timezone": "Etc/UTC", "theme": "dark", "style": "1",
        "locale": "en", "enable_publishing": false, "allow_symbol_change": true,
        "container_id": "tv_chart"
      }});
      </script><div id="tv_chart" style="height:100%;"></div>
    </div>
    """
    components.html(html, height=500)

# --- APP INTERFACE ---
st.set_page_config(page_title="Shyamswayam Screener", layout="wide")

st.markdown("<h1 style='text-align: center; color: #00ffcc;'>⚡ Shyamswayam Trading Screener</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Trend-Aligned Fibonacci Engine (Bybit)</p>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Scan Settings")
    market_type = st.selectbox("Market Type", ['linear', 'spot'], help="Linear = Futures, Spot = Coins")
    tf = st.selectbox("Timeframe", ['5m', '15m', '1h', '4h', '1d'], index=2)
    vol_threshold = st.number_input("Min 24h Volume ($)", value=50000, step=10000)
    st.divider()
    st.success("📲 Telegram Connected")
    st.info("Strategy: Price > 50 EMA + Pullback to Fib levels")

col_scan, col_chart = st.columns([1, 1.4])

with col_scan:
    if st.button("🚀 START LIVE SCAN", use_container_width=True, type="primary"):
        status = st.empty()
        p_bar = st.progress(0)
        
        status.info("Searching high-volume markets...")
        symbols = get_base_filtered_coins(market_type, min_volume=vol_threshold)
        
        golden_list = []
        deep_list = []
        
        status.info(f"Scanning {len(symbols)} charts...")
        for i, s in enumerate(symbols):
            p_bar.progress((i + 1) / len(symbols))
            res = check_fibonacci_setup(s, tf)
            if res:
                if res['type'] == 'Golden Pocket':
                    golden_list.append(res)
                else:
                    deep_list.append(res)
                
                # Send Alert
                msg = f"🚨 *Shyamswayam Setup!*\n\n🪙 {s}\n🎯 {res['type']}\n💲 Price: {res['price']}\n⏳ TF: {tf}"
                send_telegram_alert(msg)
            time.sleep(0.02)
            
        status.success(f"Scan complete! Found {len(golden_list) + len(deep_list)} setups.")

        # --- RESULTS SECTIONS ---
        st.divider()
        st.subheader("🟡 Golden Pocket (0.5 - 0.618)")
        if golden_list:
            for item in golden_list:
                st.success(f"**{item['symbol']}** — Price: {item['price']}")
        else:
            st.write("No active golden pocket setups.")

        st.subheader("🔴 Deep Pullback (0.786)")
        if deep_list:
            for item in deep_list:
                st.warning(f"**{item['symbol']}** — Price: {item['price']}")
        else:
            st.write("No active deep pullback setups.")

with col_chart:
    st.subheader("📈 Live Interactive Chart")
    target_sym = st.text_input("Enter Symbol to View", value="BTC/USDT").upper()
    render_chart(target_sym)

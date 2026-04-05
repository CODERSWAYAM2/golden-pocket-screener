import ccxt
import pandas as pd
import requests
import time
import streamlit as st
import streamlit.components.v1 as components

# Initialize Delta Exchange
exchange = ccxt.delta({'enableRateLimit': True})

def send_telegram_alert(message, bot_token, chat_id):
    """Sends a push notification to your Telegram."""
    if not bot_token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        pass

def get_base_filtered_coins(min_volume=500000, max_coins=200):
    """Fetches high-volume coins directly from the exchange to prevent IP blocks."""
    exchange.load_markets()
    tickers = exchange.fetch_tickers()
    
    valid_symbols = []
    for symbol, ticker in tickers.items():
        if 'USDT' in symbol:
            vol = ticker.get('quoteVolume', 0)
            if vol is not None and vol >= min_volume:
                valid_symbols.append(symbol)
                
    # Sort by volume and return top X coins
    valid_symbols.sort(key=lambda s: tickers[s].get('quoteVolume', 0), reverse=True)
    return valid_symbols[:max_coins]

def check_fibonacci_setup(symbol, timeframe):
    """
    Checks for Uptrend + 0.5/0.618 Golden Pocket OR 0.786 Deep Pullback.
    """
    try:
        # Fetch 100 candles (need enough for EMA 50 trend detection)
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        if df.empty or len(df) < 60:
            return None

        # 1. TREND FILTER: Calculate 50 EMA
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        current_price = df['close'].iloc[-1]
        current_ema = df['EMA_50'].iloc[-1]
        
        # If price is below EMA 50, it's not a strong uptrend. Skip to avoid fakeouts.
        if current_price < current_ema:
            return None

        # 2. SWING DETECTION (Last 50 candles)
        recent_df = df.tail(50).reset_index(drop=True)
        
        # Find the peak (Swing High)
        high_idx = recent_df['high'].idxmax()
        swing_high = recent_df['high'].max()
        
        # Find the lowest point BEFORE the peak (Swing Low) - This ensures it's a true upward swing
        if high_idx == 0: 
            return None 
            
        swing_low = recent_df.loc[:high_idx, 'low'].min()
        swing_range = swing_high - swing_low
        
        if swing_range == 0:
            return None
            
        # 3. FIBONACCI CALCULATIONS (Measuring from Top to Bottom)
        fib_0_5 = swing_high - (swing_range * 0.5)
        fib_0_618 = swing_high - (swing_range * 0.618)
        fib_0_786 = swing_high - (swing_range * 0.786)
        
        # 4. ZONE CHECKS (Adding a tiny 0.3% buffer for wicks)
        pocket_top = fib_0_5 * 1.003
        pocket_bottom = fib_0_618 * 0.997
        deep_pullback_zone = fib_0_786 * 0.995
        
        setup_type = None
        
        if pocket_bottom <= current_price <= pocket_top:
            setup_type = "🟡 Golden Pocket (0.5 - 0.618)"
        elif deep_pullback_zone <= current_price <= (fib_0_786 * 1.005):
            setup_type = "🔴 Deep Pullback (0.786)"
            
        if setup_type:
            return {
                'symbol': symbol,
                'type': setup_type,
                'price': current_price
            }
        return None
        
    except Exception:
        return None

def render_tradingview_widget(symbol):
    """Embeds a live TradingView chart for the selected coin."""
    tv_symbol = f"BINANCE:{symbol.replace('/', '').replace(':', '')}"
    
    html_code = f"""
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
      {{
      "autosize": true,
      "symbol": "{tv_symbol}",
      "interval": "60",
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "enable_publishing": false,
      "backgroundColor": "rgba(19, 23, 34, 1)",
      "gridColor": "rgba(42, 46, 57, 0.06)",
      "hide_top_toolbar": false,
      "hide_legend": false,
      "save_image": false,
      "container_id": "tradingview_chart"
    }}
      </script>
    </div>
    """
    components.html(html_code, height=500)

# --- UI DESIGN ---

st.set_page_config(page_title="Shyamswayam Screener", page_icon="⚡", layout="wide")

st.markdown("<h1 style='text-align: center; color: #00ffcc;'>⚡ Shyamswayam Trading Screener</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Pro-Trend Fibonacci Engine | Retests & Deep Pullbacks</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Screener Settings")
    selected_tf = st.selectbox("⏳ Timeframe", ['5m', '15m', '1h', '2h', '4h', '1d', '1w'], index=2)
    min_vol = st.number_input("💵 Min Volume ($)", value=500000, step=100000)
    max_scan = st.slider("🔍 Coins to Scan", 50, 300, 150)
    
    st.divider()
    st.header("📲 Telegram Alerts Active")
    # Credentials hardcoded as requested
    tg_bot = st.text_input("Bot Token", value="8657789671:AAHgmek_WvxFrqkP_F0UomRS-rct1Vk7V1c", type="password")
    tg_chat = st.text_input("Chat ID", value="5868749596", type="password")
    st.caption("Your bot is connected and ready to send alerts.")

# Main Layout
col1, col2 = st.columns([1, 1.5])

with col1:
    if st.button("🚀 Run Live Scan", use_container_width=True, type="primary"):
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        status_text.text("Fetching market data...")
        symbols = get_base_filtered_coins(min_volume=min_vol, max_coins=max_scan)
        
        found_setups = []
        
        status_text.text(f"Scanning {len(symbols)} charts on {selected_tf} timeframe...")
        for i, sym in enumerate(symbols):
            progress_bar.progress((i + 1) / len(symbols))
            
            result = check_fibonacci_setup(sym, timeframe=selected_tf)
            if result:
                found_setups.append(result)
                
                # Trigger Telegram Alert using hardcoded credentials
                if tg_bot and tg_chat:
                    msg = f"🚨 *Shyamswayam Setup Detected!*\n\n🪙 *Coin:* {sym}\n⏳ *TF:* {selected_tf}\n🎯 *Zone:* {result['type']}\n💲 *Price:* {result['price']}"
                    send_telegram_alert(msg, tg_bot, tg_chat)
                    
            time.sleep(0.05) # Rate limit safety
            
        status_text.success(f"Scan Complete! Found {len(found_setups)} trend-aligned setups.")
        
        # Display Results
        if found_setups:
            for setup in found_setups:
                with st.expander(f"{setup['symbol']} - {setup['type']}", expanded=True):
                    st.write(f"**Current Price:** {setup['price']}")
                    st.write("🟢 Trend: Uptrend (Above EMA 50)")
        else:
            st.info("No trend-aligned Fibonacci setups found right now. Wait for a pullback!")

with col2:
    st.markdown("### 📈 Live Chart Viewer")
    st.write("Type a coin symbol below to load its live TradingView chart.")
    chart_symbol = st.text_input("Enter Coin (e.g., BTC/USDT)", value="BTC/USDT")
    
    if chart_symbol:
        render_tradingview_widget(chart_symbol)

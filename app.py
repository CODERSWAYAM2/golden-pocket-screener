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
    /* Institutional Result Card */
    .result-card {
        background-color: #161b22;
        border-left: 4px solid #d4af37;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 12px;
        font-size: 1.1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .symbol-label { font-weight: 800; color: #ffffff; font-size: 1.2rem; }
    .price-label { color: #d4af37; font-family: monospace; font-weight: bold; }
    .setup-label { color: #8b949e; font-size: 0.95rem; margin-top: 5px; }
    
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
    try:
        if exchange.id == 'binance':
            if m_type == 'linear':
                st.warning("⚠️ Binance Futures is strictly blocked. Switch 'Market Asset' to 'spot'.")
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

def analyze_asset(exchange, symbol, tf, target_strategy):
    """
    Advanced Live Market Engine.
    Incorporates Break of Structure (BOS), ICT Traps, and exact Live Pricing.
    """
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=250)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        if len(df) < 200: return None

        # 🚨 STRICT LIVE MARKET DATA (Currently Ticking Candle) 🚨
        live_candle = df.iloc[-1]
        live_price = live_candle['close']
        c_low = live_candle['low']
        c_high = live_candle['high']
        
        setups = []

        # ==========================================================
        # STRATEGY 1: ICT LIQUIDITY SWEEPS (The Trap)
        # ==========================================================
       # ---------------------------------------------------------
        # STRATEGY 1: ADVANCED ICT LIQUIDITY SWEEPS (JUDAS SWING & TRAPS)
        # ---------------------------------------------------------
        # 1. Define Fractal Swing Highs (BSL) and Swing Lows (SSL)
        # A true liquidity pool requires 2 lower highs on the left, and 2 on the right.
        df['swing_high'] = (df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(2)) & \
                           (df['high'] > df['high'].shift(-1)) & (df['high'] > df['high'].shift(-2))
                           
        df['swing_low'] = (df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(2)) & \
                          (df['low'] < df['low'].shift(-1)) & (df['low'] < df['low'].shift(-2))

        # 2. Extract the 5 most recent unmitigated Liquidity Pools
        recent_bsl = df[df['swing_high']]['high'].dropna().iloc[-5:].values
        recent_ssl = df[df['swing_low']]['low'].dropna().iloc[-5:].values
        
        sweep_detected = False

        # 3. BEARISH TRAP EVALUATION (Sweeping Buy-Side Liquidity to short)
        for bsl in recent_bsl:
            # Did the live candle pierce the Liquidity Pool?
            if c_high > bsl:
                # Is the live price currently trapped back BELOW the pool?
                if live_price < bsl:
                    total_candle_size = c_high - c_low
                    rejection_size = c_high - live_price
                    
                    # 🚨 REJECTION BLOCK FILTER: The wick must be significant (>40% of the candle)
                    # This proves institutional displacement away from the sweep.
                    if total_candle_size > 0 and (rejection_size / total_candle_size) >= 0.40:
                        setups.append({
                            'strategy': 'ICT Liquidity Sweeps', 
                            'type': f'🔴 Bearish Judas Swing (Swept BSL @ ${bsl:,.4f}){fvg_text}',
                            'price': live_price
                        })
                        sweep_detected = True
                        break # Stop checking older pools; we have a valid live trap

        # 4. BULLISH TRAP EVALUATION (Sweeping Sell-Side Liquidity to long)
        if not sweep_detected:
            for ssl in recent_ssl:
                # Did the live candle pierce the Liquidity Pool?
                if c_low < ssl:
                    # Is the live price currently trapped back ABOVE the pool?
                    if live_price > ssl:
                        total_candle_size = c_high - c_low
                        rejection_size = live_price - c_low
                        
                        # 🚨 REJECTION BLOCK FILTER: Strong wick rejection required
                        if total_candle_size > 0 and (rejection_size / total_candle_size) >= 0.40:
                            setups.append({
                                'strategy': 'ICT Liquidity Sweeps', 
                                'type': f'🟢 Bullish Judas Swing (Swept SSL @ ${ssl:,.4f}){fvg_text}',
                                'price': live_price
                            })
                            break

        # ==========================================================
        # STRATEGY 2 & 3: BOS + GOLDEN POCKET / A1 SWEEPS
        # ==========================================================
        # 1. Find impulsive Swing High
        impulse_high_idx = df['high'].iloc[-100:-1].idxmax()
        impulse_high = df['high'].iloc[impulse_high_idx]
        
        # 2. Find the Swing Low that started the impulse
        impulse_low_idx = df['low'].iloc[-200:impulse_high_idx].idxmin()
        impulse_low = df['low'].iloc[impulse_low_idx]
        
        # 3. Locate the previous peak before this move started
        prior_peak_window = df['high'].iloc[-250:impulse_low_idx]
        
        if not prior_peak_window.empty:
            prior_peak = prior_peak_window.max()
            
            # 🔥 BOS VALIDATION: The new impulse high MUST be higher than the prior peak
            if impulse_high > prior_peak:
                swing_rng = impulse_high - impulse_low
                
                # Must be a valid move (e.g., > 1% distance)
                if swing_rng > 0 and (swing_rng / impulse_low) * 100 > 1.0:
                    fib_500 = impulse_high - (swing_rng * 0.5)
                    fib_618 = impulse_high - (swing_rng * 0.618)
                    fib_786 = impulse_high - (swing_rng * 0.786)
                    
                    # 🎯 LIVE GOLDEN POCKET: Live ticking price is strictly inside the 0.5 - 0.618 zone
                    if fib_618 <= live_price <= fib_500:
                        setups.append({'symbol': symbol, 'strategy': 'Golden Pocket', 'type': '🟡 Live inside Golden Pocket (BOS Verified)', 'price': live_price})
                    
                    # 🔥 A1 SWEEP: Wicks below the 0.618, but live price recovered inside the pocket
                    if c_low < fib_618 and fib_618 < live_price <= fib_500:
                        setups.append({'symbol': symbol, 'strategy': 'A1 Sweeps', 'type': '🔥 A1 Sweep Active (Hunted 0.618 Stops)', 'price': live_price})
                        
                    # 📉 DEEP PULLBACK
                    if (fib_786 * 0.998) <= live_price <= (fib_786 * 1.002):
                        setups.append({'symbol': symbol, 'strategy': 'Deep Pullbacks', 'type': '🔴 0.786 Deep Pullback', 'price': live_price})

        # --- Filter Logic ---
        if target_strategy == 'ALL STRATEGIES':
            return setups if setups else None
        else:
            filtered = [s for s in setups if s['strategy'] == target_strategy]
            return filtered if filtered else None

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
            "autosize": true, "symbol": "{prefix}:{sym}", "interval": "15",
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
st.markdown("<div class='brand-subtitle'>Institutional SMC & Live Fibonacci Analysis Engine</div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🎯 STRATEGY SELECTOR")
    strategy_choice = st.selectbox("Select Protocol:", [
        'ALL STRATEGIES', 
        'Golden Pocket', 
        'A1 Sweeps', 
        'ICT Liquidity Sweeps',
        'Deep Pullbacks'
    ])
    st.divider()
    
    st.markdown("### ⚙️ SYSTEM PARAMETERS")
    exch_choice = st.selectbox("🌐 Data Provider", ['Binance', 'Gate.io', 'Bybit', 'Delta Exchange'])
    m_type = st.selectbox("📊 Market Asset", ['spot', 'linear'], help="Linear = Perpetual Futures (Use spot for Binance)")
    tf = st.selectbox("⏳ Timeframe Resolution", ['15m', '1h', '4h'], index=0)
    min_vol = st.number_input("💵 Min Volume (USD)", value=50000, step=10000)
    st.divider()
    st.caption("Status: STANDBY\n\nAlerts: ACTIVE\n\nLogic: LIVE MARKET ACTION ONLY")

col_control, col_chart = st.columns([1.3, 2])

with col_control:
    st.markdown(f"### 🔍 SCANNING: `{strategy_choice}`")
    
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
            res_list = analyze_asset(ex, s, tf, strategy_choice)
            
            if res_list:
                for res in res_list:
                    results.append(res)
                    # Telegram Alerts
                    send_telegram_alert(f"🏛️ *Shyamswayam Terminal*\n\n🪙 Ticker: {s}\n🎯 Setup: {res['type']}\n💲 Live Price: {res['price']}\n⏳ TF: {tf}\n🌐 Exch: {exch_choice}")
            time.sleep(0.01)
            
        status.success(f"Scan complete. {len(results)} active setups identified.")
        bar.empty()

        # Display Results in Clean Institutional Cards
        if results:
            for r in results:
                st.markdown(f"""
                <div class="result-card">
                    <span class="symbol-label">{r['symbol']}</span> <br>
                    <span class="setup-label">{r['type']}</span> <br>
                    <span class="price-label">Live Price: ${r['price']:,.5f}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No valid setups found for '{strategy_choice}' at this exact moment.")

with col_chart:
    st.markdown("### ASSET VISUALIZATION")
    chart_sym = st.text_input("Ticker Symbol (e.g., BTC/USDT)", value="BTC/USDT").upper()
    if chart_sym: render_tv(chart_sym, exch_choice)

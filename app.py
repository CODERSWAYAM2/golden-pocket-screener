import ccxt
import pandas as pd
import requests
import time
import streamlit as st


# Initialize KuCoin exchange (Friendly to cloud servers)
exchange = ccxt.kucoin({'enableRateLimit': True})

def get_base_filtered_coins(min_volume=100000, min_mcap_rank=150):
    """Fetches all markets directly from the exchange and filters by volume."""
    exchange.load_markets()
    
    # Fetch 24hr data for every coin on the exchange at once
    tickers = exchange.fetch_tickers()
    
    valid_symbols = []
    for symbol, ticker in tickers.items():
        # Only look at USDT pairs
        if 'USDT' in symbol:
            # quoteVolume is the 24h volume in Dollars (USDT)
            vol = ticker.get('quoteVolume', 0)
            
            if vol is not None and vol >= min_volume:
                valid_symbols.append(symbol)
                
    # Sort the list by highest volume first (this replaces "Market Cap" ranking)
    valid_symbols.sort(key=lambda s: tickers[s].get('quoteVolume', 0), reverse=True)
    
    # Return only the top X coins so the app doesn't take 10 minutes to scan
    return valid_symbols[:min_mcap_rank]
    response = requests.get(url, params=params)
    data = response.json()
    
    valid_symbols = []
    for coin in data:
        if coin['total_volume'] is not None and coin['total_volume'] >= min_volume:
            symbol = f"{coin['symbol'].upper()}/USDT"
            valid_symbols.append(symbol)
            
    return valid_symbols

def check_fibonacci_setup(symbol, timeframe, lookback=40):
    """Checks if price is in the 0.5 - 0.65 (Golden Pocket + Wick Buffer) zone."""
    try:
        # Fetch OHLCV data
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=lookback)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        if df.empty:
            return False

        # Identify recent swings
        swing_high = df['high'].max()
        swing_low = df['low'].min()
        current_price = df['close'].iloc[-1]
        
        swing_range = swing_high - swing_low
        if swing_range == 0:
            return False
            
        # Calculate Fib levels (with 0.65 to catch wicks slightly below 0.618)
        fib_0_5 = swing_high - (swing_range * 0.5)
        fib_0_65 = swing_high - (swing_range * 0.65) 
        
        # Check if current price is inside the pocket
        if fib_0_65 <= current_price <= fib_0_5:
            return True
        return False
        
    except Exception:
        # Pass silently if coin is not on Binance or throws an error
        return False

# --- STREAMLIT WEB APP UI ---

st.set_page_config(page_title="Fibonacci Screener", page_icon="📈", layout="centered")

st.title("📈 Golden Pocket Crypto Screener")
st.markdown("**Strategy:** Scans top crypto assets (>$100k Vol) to find prices currently sitting inside the **0.5 - 0.618 Fibonacci retracement zone** (with a slight buffer for wicks).")

# Sidebar settings
st.sidebar.header("Screener Settings")
mcap_rank = st.sidebar.slider("Top Coins by Market Cap to Scan", 50, 300, 150)
min_vol = st.sidebar.number_input("Minimum Daily Volume ($)", value=100000, step=50000)

if st.button("🚀 Run Screener", use_container_width=True):
    
    # UI Elements for progress
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # 1. Fetching Coins
    status_text.text("Fetching market cap & volume data from CoinGecko...")
    symbols_to_check = get_base_filtered_coins(min_volume=min_vol, min_mcap_rank=mcap_rank)
    
    # 2. Loading Binance Markets
    status_text.text("Connecting to Binance to verify trading pairs...")
    exchange.load_markets()
    available_symbols = [s for s in symbols_to_check if s in exchange.markets]
    
    matched_coins_15m = []
    matched_coins_1h = []
    
    total_symbols = len(available_symbols)
    
    # 3. Scanning Charts
    status_text.text(f"Scanning charts for {total_symbols} valid coins. This takes a minute to respect API limits...")
    
    for index, symbol in enumerate(available_symbols):
        # Update progress bar
        progress = (index + 1) / total_symbols
        progress_bar.progress(progress)
        
        # Check 15m chart
        if check_fibonacci_setup(symbol, timeframe='15m', lookback=40):
            matched_coins_15m.append(symbol)
            
        # Check 1h chart
        if check_fibonacci_setup(symbol, timeframe='1h', lookback=40):
            matched_coins_1h.append(symbol)
            
        time.sleep(0.1) # Prevents Binance from banning your IP
        
    status_text.text("✅ Scan Complete!")
    
    # --- DISPLAY RESULTS ---
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⏱️ 15-Min Chart Setups")
        if matched_coins_15m:
            for coin in matched_coins_15m:
                st.success(coin)
        else:
            st.info("No setups found.")

    with col2:
        st.subheader("⌛ 1-Hour Chart Setups")
        if matched_coins_1h:
            for coin in matched_coins_1h:
                st.success(coin)
        else:
            st.info("No setups found.")
            
    st.divider()
    
    # Find Confluence (Matches on both)
    confluence = set(matched_coins_15m).intersection(set(matched_coins_1h))
    st.subheader("🔥 Strong Confluence (Both 15m & 1h)")
    if confluence:
        for coin in confluence:
            st.warning(f"**{coin}** is in the Golden Pocket on both timeframes!")
    else:
        st.write("No dual-timeframe setups found right now.")

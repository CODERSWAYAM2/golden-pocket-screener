import streamlit as st
import requests
import pandas as pd
import urllib.parse
import time
from datetime import datetime

# =============================================================================
# ⚙️ APP CONFIGURATION & UI SETUP
# =============================================================================
st.set_page_config(page_title="Bulls Thrive | Pro Scanner", page_icon="🐃", layout="wide")

st.title("🐃 Bulls Thrive | Pending Breakout Scanner")
st.markdown("Scans the F&O Universe for live inside candles **AND** past inside candles that are still coiled and waiting to break out.")

# --- SECURE SIDEBAR FOR CREDENTIALS ---
with st.sidebar:
    st.header("🔑 API Credentials")
    st.markdown("Enter your tokens below to run the scan securely.")
    
    UPSTOX_TOKEN = st.text_input("Upstox Access Token", type="password")
    TG_BOT_TOKEN = st.text_input("Telegram Bot Token", type="password")
    TG_CHAT_ID = st.text_input("Telegram Chat ID", type="password")
    
    st.markdown("---")
    st.caption("🔒 Tokens are only stored in your current browser session and are never saved.")

# =============================================================================
# 📊 STOCK UNIVERSE
# =============================================================================
INDICES = ["NIFTY 50", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]

FNO_STOCKS = [
    "AARTIIND", "ABB", "ABBOTINDIA", "ABCAPITAL", "ABFRL", "ACC", "ADANIENSOL", "ADANIENT", 
    "ADANIPORTS", "ALKEM", "AMBUJACEM", "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY", "ASIANPAINT", 
    "ASTRAL", "ATUL", "AUBANK", "AUROPHARMA", "AXISBANK", "BAJAJ-AUTO", "BAJAJFINSV", "BAJFINANCE", 
    "BALRAMCHIN", "BANDHANBNK", "BANKBARODA", "BATAINDIA", "BEL", "BERGEPAINT", "BHARATFORG", 
    "BHARTIARTL", "BHEL", "BIOCON", "BOSCHLTD", "BPCL", "BRITANNIA", "BSOFT", "CANBK", "CANFINHOME", 
    "CHAMBLFERT", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CONCOR", "COROMANDEL", 
    "CROMPTON", "CUB", "CUMMINSIND", "DABUR", "DALBHARAT", "DEEPAKNTR", "DIVISLAB", "DIXON", "DLF", 
    "DRREDDY", "EICHERMOT", "ESCORTS", "EXIDEIND", "FEDERALBNK", "GAIL", "GLENMARK", "GMRINFRA", 
    "GNFC", "GODREJCP", "GODREJPROP", "GRANULES", "GRASIM", "GUJGASLTD", "HAL", "HAVELLS", "HCLTECH", 
    "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDCOPPER", "HINDPETRO", 
    "HINDUNILVR", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDEA", "IDFCFIRSTB", "IEX", "IGL", "INDHOTEL", 
    "INDIACEM", "INDIAMART", "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", "IOC", "IPCALAB", "IRCTC", 
    "ITC", "JINDALSTEL", "JKCEMENT", "JSWSTEEL", "JUBLFOOD", "KOTAKBANK", "LALPATHLAB", "LAURUSLABS", 
    "LICHSGFIN", "LT", "LTIM", "LTTS", "LUPIN", "M&M", "M&MFIN", "MANAPPURAM", "MARICO", "MARUTI", 
    "MCX", "METROPOLIS", "MFSL", "MGL", "MOTHERSON", "MPHASIS", "MRF", "MUTHOOTFIN", "NATIONALUM", 
    "NAUKRI", "NAVINFLUOR", "NESTLEIND", "NMDC", "NTPC", "OBEROIRLTY", "OFSS", "ONGC", "PAGEIND", 
    "PEL", "PERSISTENT", "PETRONET", "PFC", "PIDILITIND", "PIIND", "PNB", "POLYCAB", "POWERGRID", 
    "PVRINOX", "RAMCOCEM", "RBLBANK", "RECLTD", "RELIANCE", "SAIL", "SBICARD", "SBILIFE", "SBIN", 
    "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SRF", "SUNPHARMA", "SUNTV", "SYNGENE", "TATACHEM", 
    "TATACOMM", "TATACONSUM", "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", "TECHM", "TITAN", 
    "TORNTPHARM", "TRENT", "TVSMOTOR", "UBL", "ULTRACEMCO", "UPLLTD", "VEDL", "VOLTAS", "WIPRO", 
    "ZEEL", "ZYDUSLIFE"
]

ALL_SYMBOLS = INDICES + FNO_STOCKS

# =============================================================================
# 📡 DATA FETCHING & MATH LOGIC
# =============================================================================
def get_instrument_key(symbol):
    if symbol == "NIFTY 50": return "NSE_INDEX|Nifty 50"
    if symbol == "BANKNIFTY": return "NSE_INDEX|Nifty Bank"
    if symbol == "FINNIFTY": return "NSE_INDEX|Nifty Fin Service"
    if symbol == "MIDCPNIFTY": return "NSE_INDEX|Nifty Mid Select"
    return f"NSE_EQ|{symbol}"

def fetch_live_candles(symbol):
    raw_key = get_instrument_key(symbol)
    encoded_key = urllib.parse.quote(raw_key)
    url = f"https://api.upstox.com/v2/historical-candle/intraday/{encoded_key}/30minute"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {UPSTOX_TOKEN}'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            candles = []
            for c in reversed(data['data']['candles'][:65]):
                candles.append({"open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4])})
            return candles
        return None
    except:
        return None

def calculate_ema(prices, period):
    ema = []
    k = 2 / (period + 1)
    for i, price in enumerate(prices):
        if i == 0: ema.append(price)
        else: ema.append((price * k) + (ema[-1] * (1 - k)))
    return ema

def detect_trend(candles):
    if not candles or len(candles) < 30: return "neutral"
    closes = [c['close'] for c in candles]
    ema9, ema21 = calculate_ema(closes, 9), calculate_ema(closes, 21)
    last_close, last_ema9, last_ema21 = closes[-1], ema9[-1], ema21[-1]
    
    if last_close > last_ema9 and last_ema9 > last_ema21: return "uptrend"
    if last_close < last_ema9 and last_ema9 < last_ema21: return "downtrend"
    return "neutral"

def scan_symbol(symbol):
    candles = fetch_live_candles(symbol)
    if not candles or len(candles) < 20: return None
    
    n = len(candles)
    
    # 🕵️ THE TIME MACHINE LOOP: Look back up to 15 candles for an inside bar
    for i in range(n - 1, n - 16, -1):
        last = candles[i]
        mother = candles[i-1]
        
        # 1. Check if Wicks are strictly inside
        if not (last['high'] <= mother['high'] and last['low'] >= mother['low']): continue
        
        # 2. Check if Full Body is strictly inside
        inside_body_top = max(last['open'], last['close'])
        inside_body_bottom = min(last['open'], last['close'])
        if not (inside_body_top <= mother['high'] and inside_body_bottom >= mother['low']): continue
            
        range_val = mother['high'] - mother['low']
        if range_val < 0.001: continue
        
        # 3. VERIFY PENDING BREAKOUT: Has it broken out since it formed?
        broke_out = False
        for j in range(i + 1, n):
            # If any candle *after* the inside candle breached the mother's high or low
            if candles[j]['high'] > mother['high'] or candles[j]['low'] < mother['low']:
                broke_out = True
                break
                
        # If it hasn't broken out, we found a coiled setup!
        if not broke_out:
            inside_range = last['high'] - last['low']
            compression = round((1 - inside_range / range_val) * 100, 1)
            
            trend = detect_trend(candles)
            trend_display = "🟢 UPTREND" if trend == "uptrend" else "🔴 DOWNTREND" if trend == "downtrend" else "🟡 NEUTRAL"
            
            # Calculate how many 30m periods it has been stuck inside
            periods_coiled = (n - 1) - i
            
            # Current Market Price is always the absolute latest candle
            cmp_raw = candles[-1]['close'] 
            
            return {
                "Symbol": symbol, 
                "Info Trend": trend_display,
                "Comp (%)": compression, 
                "Coiled (Periods)": periods_coiled,
                "CMP": f"₹{cmp_raw:.2f}", 
                "Breakout Above": f"₹{mother['high']:.2f}", 
                "Breakdown Below": f"₹{mother['low']:.2f}",
                "_raw_trend": trend,
                "_raw_coiled": periods_coiled
            }
            
    return None

# =============================================================================
# 🚀 TELEGRAM ALERTS
# =============================================================================
def send_telegram_alert(alerts):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return 
        
    msg = f"🐃 <b>BULLS THRIVE | PENDING BREAKOUT SCANNER</b>\n"
    msg += f"⏰ {datetime.now().strftime('%I:%M %p')} (30m Timeframe)\n"
    msg += f"📊 <b>{len(alerts)}</b> Coiled Setups Found\n"
    msg += "─" * 28 + "\n\n"
    
    for a in alerts[:20]: 
        trend_icon = "🟢" if a['_raw_trend'] == 'uptrend' else "🔴" if a['_raw_trend'] == 'downtrend' else "🟡"
        
        # Add a fire emoji if it's been coiling for a long time
        coil_str = f"🔥 Coiled for {a['Coiled (Periods)']} candles!" if a['Coiled (Periods)'] > 1 else "New Inside Candle"
        
        msg += f"{trend_icon} <b>{a['Symbol']}</b> ({coil_str})\n"
        msg += f"   CMP: {a['CMP']}\n"
        msg += f"   Watch Breakout: {a['Breakout Above']} | Breakdown: {a['Breakdown Below']}\n\n"
        
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, json=payload)
    except: pass

# =============================================================================
# 🖥️ MAIN EXECUTION
# =============================================================================
if st.button("🚀 Run Live Market Scan", type="primary", use_container_width=True):
    if not UPSTOX_TOKEN:
        st.error("⚠️ Please enter your Upstox Access Token in the sidebar first.")
        st.stop()

    with st.status(f"Scanning {len(ALL_SYMBOLS)} stocks for Master Candles...", expanded=True) as status:
        found_alerts = []
        progress_bar = st.progress(0)
        
        for i, symbol in enumerate(ALL_SYMBOLS):
            result = scan_symbol(symbol)
            if result:
                found_alerts.append(result)
            
            progress_bar.progress((i + 1) / len(ALL_SYMBOLS))
            time.sleep(0.15) 

        status.update(label=f"Scan Complete! Found {len(found_alerts)} pending setups.", state="complete")

    if found_alerts:
        send_telegram_alert(found_alerts)
        
        st.subheader(f"🎯 {len(found_alerts)} Coiled Setups Detected")
        df = pd.DataFrame(found_alerts)
        
        # Sort by longest coiled first, then by highest compression
        display_df = df.sort_values(by=["_raw_coiled", "Comp (%)"], ascending=[False, False]).drop(columns=['_raw_trend', '_raw_coiled']).reset_index(drop=True)
        
        # Streamlit styling for the new column
        st.dataframe(
            display_df, 
            use_container_width=True,
            column_config={
                "Comp (%)": st.column_config.ProgressColumn("Compression", format="%f%%", min_value=0, max_value=100),
                "Coiled (Periods)": st.column_config.NumberColumn("Periods Coiled", help="How many 30m candles this has been stuck inside the mother candle.")
            }
        )
        
        if TG_BOT_TOKEN and TG_CHAT_ID:
            st.success("✅ Telegram Alert successfully fired to your community!")
    else:
        st.info("No inside candles or pending breakouts found in this session.")

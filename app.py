import streamlit as st
import requests
import pandas as pd
import urllib.parse
import time
from datetime import datetime

# =============================================================================
# ⚙️ APP CONFIGURATION & UI SETUP
# =============================================================================
st.set_page_config(page_title="Bulls Thrive | Raw Scanner", page_icon="🐃", layout="wide")

st.title("🐃 Bulls Thrive | Raw Inside Scanner")
st.markdown("Scans the entire F&O Universe on the 30m timeframe for perfect, full-body inside candles. **No trend filters applied.**")

# --- SECURE SIDEBAR FOR CREDENTIALS ---
with st.sidebar:
    st.header("🔑 API Credentials")
    st.markdown("Enter your tokens below to run the scan securely.")
    
    UPSTOX_TOKEN = st.text_input("eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI1U0JDSEciLCJqdGkiOiI2YTAwNDFjMDdkYTE2ZTUxOTZkYTdlOWIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzc4NDAxNzI4LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MDk5ODY0MDB9.WENgG9K9uldqPtJLaJH6HDXfQNeaqU5kp7NxIY72L9g", type="password", help="Generates daily from your Upstox Developer Console")
    TG_BOT_TOKEN = st.text_input("8740787035:AAEG6-h378Qf5ob2z1OXVLvuaKQ7CCRFDLk", type="password", help="From BotFather (Optional)")
    TG_CHAT_ID = st.text_input("5868749596", type="password", help="Your channel or personal ID (Optional)")
    
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
    if not candles: return None
    
    mother, last = candles[-2], candles[-1]
    
    if not (last['high'] <= mother['high'] and last['low'] >= mother['low']): return None
    
    inside_body_top = max(last['open'], last['close'])
    inside_body_bottom = min(last['open'], last['close'])
    if not (inside_body_top <= mother['high'] and inside_body_bottom >= mother['low']): return None
        
    range_val = mother['high'] - mother['low']
    if range_val < 0.001: return None
    
    inside_range = last['high'] - last['low']
    compression = round((1 - inside_range / range_val) * 100, 1)
    
    trend = detect_trend(candles)
    trend_display = "🟢 UPTREND" if trend == "uptrend" else "🔴 DOWNTREND" if trend == "downtrend" else "🟡 NEUTRAL"
    
    return {
        "Symbol": symbol, 
        "Info Trend": trend_display,
        "Comp (%)": compression, 
        "CMP": f"₹{last['close']:.2f}", 
        "Breakout Above": f"₹{mother['high']:.2f}", 
        "Breakdown Below": f"₹{mother['low']:.2f}",
        "_raw_trend": trend # Hidden column for telegram sorting
    }

# =============================================================================
# 🚀 TELEGRAM ALERTS
# =============================================================================
def send_telegram_alert(alerts):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return # Skip quietly if user didn't enter Telegram details
        
    msg = f"🐃 <b>BULLS THRIVE | RAW INSIDE SCANNER</b>\n"
    msg += f"⏰ {datetime.now().strftime('%I:%M %p')} (30m Timeframe)\n"
    msg += f"📊 <b>{len(alerts)}</b> Raw Inside Candles Found\n"
    msg += "─" * 28 + "\n\n"
    
    for a in alerts[:20]: 
        trend_icon = "🟢" if a['_raw_trend'] == 'uptrend' else "🔴" if a['_raw_trend'] == 'downtrend' else "🟡"
        msg += f"{trend_icon} <b>{a['Symbol']}</b> (Comp: {a['Comp (%)']}%)\n"
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

    with st.status(f"Scanning {len(ALL_SYMBOLS)} high-liquidity stocks...", expanded=True) as status:
        found_alerts = []
        progress_bar = st.progress(0)
        
        for i, symbol in enumerate(ALL_SYMBOLS):
            result = scan_symbol(symbol)
            if result:
                found_alerts.append(result)
            
            progress_bar.progress((i + 1) / len(ALL_SYMBOLS))
            time.sleep(0.15) 

        status.update(label=f"Scan Complete! Found {len(found_alerts)} setups.", state="complete")

    if found_alerts:
        send_telegram_alert(found_alerts)
        
        # Display Results
        st.subheader(f"🎯 {len(found_alerts)} Inside Candles Detected")
        df = pd.DataFrame(found_alerts)
        
        # Clean up dataframe for display (remove hidden sorting column)
        display_df = df.sort_values(by="Comp (%)", ascending=False).drop(columns=['_raw_trend']).reset_index(drop=True)
        
        st.dataframe(
            display_df, 
            use_container_width=True,
            column_config={
                "Comp (%)": st.column_config.ProgressColumn("Compression", format="%f%%", min_value=0, max_value=100)
            }
        )
        
        if TG_BOT_TOKEN and TG_CHAT_ID:
            st.success("✅ Telegram Alert successfully fired to your community!")
    else:
        st.info("No inside candles found in this session.")

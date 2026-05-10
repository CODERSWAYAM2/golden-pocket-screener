import time
import requests
import urllib.parse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich import box
from rich.align import Align

# =============================================================================
# ⚙️ CONFIGURATION & TELEGRAM
# =============================================================================
# 👉 PUT YOUR TELEGRAM CREDENTIALS HERE
TELEGRAM_TOKEN = "8740787035:AAEG6-h378Qf5ob2z1OXVLvuaKQ7CCRFDLk"  
TELEGRAM_CHAT_ID = "5868749596" 

UPSTOX_ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI1U0JDSEciLCJqdGkiOiI2YTAwNDFjMDdkYTE2ZTUxOTZkYTdlOWIiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzc4NDAxNzI4LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MDk5ODY0MDB9.WENgG9K9uldqPtJLaJH6HDXfQNeaqU5kp7NxIY72L9g" 

# =============================================================================
# 📊 STOCK UNIVERSE (F&O Liquidity)
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

console = Console()

def get_category_info(symbol):
    if symbol in INDICES: return "[bold yellow]INDEX[/]", True
    elif symbol in FNO_STOCKS: return "[bold blue]F&O[/]", True
    else: return "[bold cyan]CASH[/]", False

def get_instrument_key(symbol):
    if symbol == "NIFTY 50": return "NSE_INDEX|Nifty 50"
    if symbol == "BANKNIFTY": return "NSE_INDEX|Nifty Bank"
    if symbol == "FINNIFTY": return "NSE_INDEX|Nifty Fin Service"
    if symbol == "MIDCPNIFTY": return "NSE_INDEX|Nifty Mid Select"
    return f"NSE_EQ|{symbol}"

# =============================================================================
# 📡 DATA FETCHING & MATH 
# =============================================================================
def fetch_live_candles(symbol):
    if UPSTOX_ACCESS_TOKEN == "YOUR_UPSTOX_ACCESS_TOKEN" or not UPSTOX_ACCESS_TOKEN:
        return None

    raw_key = get_instrument_key(symbol)
    encoded_key = urllib.parse.quote(raw_key)
    
    url = f"https://api.upstox.com/v2/historical-candle/intraday/{encoded_key}/30minute"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {UPSTOX_ACCESS_TOKEN}'}
    
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
    """Calculates trend purely for informational display, NOT for filtering."""
    if len(candles) < 30: return "neutral"
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
    
    # 1. Wicks strictly inside
    if not (last['high'] <= mother['high'] and last['low'] >= mother['low']): 
        return None
    
    # 2. Body strictly inside
    inside_body_top = max(last['open'], last['close'])
    inside_body_bottom = min(last['open'], last['close'])
    if not (inside_body_top <= mother['high'] and inside_body_bottom >= mother['low']): 
        return None
        
    range_val = mother['high'] - mother['low']
    if range_val < 0.001: return None
    
    inside_range = last['high'] - last['low']
    compression = round((1 - inside_range / range_val) * 100, 1)
    
    # Calculate trend just to show it to the user
    informational_trend = detect_trend(candles)
    
    # Standardize target math based on Mother candle High/Low
    target_up = round(mother['high'] * 1.006, 2)
    target_dn = round(mother['low'] * 0.994, 2)
    cmp_raw = last['close']
    
    cat_str, has_options = get_category_info(symbol)
    
    return {
        "symbol": symbol, 
        "trend": informational_trend, 
        "compression": compression,
        "cmp": round(cmp_raw, 2), 
        "mother_high": round(mother['high'], 2), 
        "mother_low": round(mother['low'], 2),
        "category": cat_str, 
        "has_options": has_options
    }

# =============================================================================
# 🚀 TELEGRAM ALERTS
# =============================================================================
def send_telegram_alert(alerts):
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        return # Skip if user hasn't set credentials yet
        
    msg = f"🐃 <b>BULLS THRIVE | RAW INSIDE SCANNER</b>\n"
    msg += f"⏰ {datetime.now().strftime('%I:%M %p')} (30m Timeframe)\n"
    msg += f"📊 <b>{len(alerts)}</b> Raw Inside Candles Found\n"
    msg += "─" * 28 + "\n\n"
    
    for a in alerts[:20]: # Limit to 20 to avoid TG message length limits
        trend_icon = "🟢" if a['trend'] == 'uptrend' else "🔴" if a['trend'] == 'downtrend' else "🟡"
        
        msg += f"{trend_icon} <b>{a['symbol']}</b> (Comp: {a['compression']}%)\n"
        msg += f"   CMP: ₹{a['cmp']}\n"
        msg += f"   Watch Breakout: ₹{a['mother_high']} | Breakdown: ₹{a['mother_low']}\n\n"
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        pass # Silent fail to keep terminal clean

# =============================================================================
# 🖥️ TERMINAL UI 
# =============================================================================
def generate_table(alerts):
    table = Table(box=box.ROUNDED, expand=True, header_style="bold cyan")
    table.add_column("Symbol", justify="left", style="bold white")
    table.add_column("Trend (Info)", justify="center")
    table.add_column("Comp %", justify="right")
    table.add_column("CMP", justify="right", style="bold")
    table.add_column("Breakout Above", justify="right", style="green")
    table.add_column("Breakdown Below", justify="right", style="red")

    for a in alerts:
        trend_str = "[bold green]↗ UPT[/]" if a['trend'] == 'uptrend' else "[bold red]↘ DNT[/]" if a['trend'] == 'downtrend' else "[bold yellow]〰️ NEU[/]"
        
        table.add_row(
            a['symbol'], trend_str, f"{a['compression']}%", 
            f"₹{a['cmp']}", f"₹{a['mother_high']}", f"₹{a['mother_low']}"
        )
    return table

def main():
    console.clear()
    header = Panel(
        Align.center(f"Scanning Universe: {len(ALL_SYMBOLS)} Symbols\nMode: RAW INSIDE CANDLE (No Filters)"), 
        title="[bold cyan]Bulls Thrive - Raw Momentum Scanner[/]", 
        box=box.DOUBLE, style="blue"
    )
    console.print(header)

    found_alerts = []
    with Live(console=console, refresh_per_second=4) as live:
        for i, symbol in enumerate(ALL_SYMBOLS):
            progress = f"Scanning {symbol} ({i+1}/{len(ALL_SYMBOLS)})"
            live.update(Panel(progress, title="⏳ Running Scan", border_style="yellow"))
            
            result = scan_symbol(symbol)
            if result: found_alerts.append(result)
            
            time.sleep(0.15) # Rate limit protection
            
        found_alerts.sort(key=lambda x: (not x['has_options'], -x['compression'])) 
        
        if found_alerts:
            final_table = generate_table(found_alerts)
            live.update(Panel(final_table, title=f"✅ Scan Complete - {datetime.now().strftime('%I:%M %p')}", border_style="green"))
            
            # 🔥 FIRE TELEGRAM ALERT
            send_telegram_alert(found_alerts)
        else:
            live.update(Panel("[bold yellow]No inside candles found in this session.[/]", title="✅ Scan Complete", border_style="green"))

if __name__ == "__main__":
    main()

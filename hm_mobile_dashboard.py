import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz

st.set_page_config(page_title="HM Live F&O Screener", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
st.title("📈 Hilega-Milega Live F&O Screener")
st.caption("Real-time Chartink alternative for Nifty 50, Bank Nifty & NSE F&O Stocks")

WATCHLIST = {
    "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK", "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
    "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS", "INFY": "INFY.NS", "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS", "ITC": "ITC.NS", "LT": "LT.NS",
    "BAJFINANCE": "BAJFINANCE.NS", "AXISBANK": "AXISBANK.NS", "KOTAKBANK": "KOTAKBANK.NS",
    "MARUTI": "MARUTI.NS", "M&M": "M&M.NS", "SUNPHARMA": "SUNPHARMA.NS",
    "TATAMOTORS": "TATAMOTORS.NS", "TATASTEEL": "TATASTEEL.NS", "NTPC": "NTPC.NS",
    "TITAN": "TITAN.NS", "HCLTECH": "HCLTECH.NS", "ULTRACEMCO": "ULTRACEMCO.NS",
    "ADANIENT": "ADANIENT.NS", "ADANIPORTS": "ADANIPORTS.NS", "POWERGRID": "POWERGRID.NS",
    "ONGC": "ONGC.NS", "BAJAJFINSV": "BAJAJFINSV.NS", "COALINDIA": "COALINDIA.NS",
    "WIPRO": "WIPRO.NS", "HAL": "HAL.NS", "BEL": "BEL.NS",
    "TRENT": "TRENT.NS", "ZOMATO": "ZOMATO.NS", "DLF": "DLF.NS",
    "JSWSTEEL": "JSWSTEEL.NS", "HINDALCO": "HINDALCO.NS", "GRASIM": "GRASIM.NS",
    "TECHM": "TECHM.NS", "INDUSINDBK": "INDUSINDBK.NS", "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
    "HINDUNILVR": "HINDUNILVR.NS", "ASIANPAINT": "ASIANPAINT.NS", "CIPLA": "CIPLA.NS",
    "DRREDDY": "DRREDDY.NS", "EICHERMOT": "EICHERMOT.NS", "HEROMOTOCO": "HEROMOTOCO.NS",
    "DIVISLAB": "DIVISLAB.NS", "APOLLOHOSP": "APOLLOHOSP.NS", "BPCL": "BPCL.NS",
    "TATACONSUM": "TATACONSUM.NS", "BRITANNIA": "BRITANNIA.NS", "PFC": "PFC.NS",
    "RECLTD": "RECLTD.NS", "VEDL": "VEDL.NS", "TATAELXSI": "TATAELXSI.NS",
    "TATAPOWER": "TATAPOWER.NS", "SIEMENS": "SIEMENS.NS", "ABB": "ABB.NS",
    "BHEL": "BHEL.NS", "IRCTC": "IRCTC.NS", "POLYCAB": "POLYCAB.NS",
    "CHOLAFIN": "CHOLAFIN.NS", "SHRIRAMFIN": "SHRIRAMFIN.NS", "BANKBARODA": "BANKBARODA.NS",
    "PNB": "PNB.NS", "CANBK": "CANBK.NS", "FEDERALBNK": "FEDERALBNK.NS",
    "IDFCFIRSTB": "IDFCFIRSTB.NS", "AUBANK": "AUBANK.NS", "BANDHANBNK": "BANDHANBNK.NS",
    "RBLBANK": "RBLBANK.NS", "MUTHOOTFIN": "MUTHOOTFIN.NS", "MANAPPURAM": "MANAPPURAM.NS",
    "SBILIFE": "SBILIFE.NS", "HDFCLIFE": "HDFCLIFE.NS", "ICICIPRULI": "ICICIPRULI.NS",
    "LICHSGFIN": "LICHSGFIN.NS", "PERSISTENT": "PERSISTENT.NS", "COFORGE": "COFORGE.NS",
    "LTIM": "LTIM.NS", "MPHASIS": "MPHASIS.NS", "LTTS": "LTTS.NS",
    "NAUKRI": "NAUKRI.NS", "DIXON": "DIXON.NS", "MCX": "MCX.NS",
    "IEX": "IEX.NS", "CDSL": "CDSL.NS", "ANGELONE": "ANGELONE.NS",
    "BSE": "BSE.NS", "VOLTAS": "VOLTAS.NS", "HAVELLS": "HAVELLS.NS",
    "CUMMINSIND": "CUMMINSIND.NS", "ASHOKLEY": "ASHOKLEY.NS", "TVSMOTOR": "TVSMOTOR.NS",
    "ESCORTS": "ESCORTS.NS", "BHARATFORG": "BHARATFORG.NS", "MOTHERSON": "MOTHERSON.NS",
    "BALKRISIND": "BALKRISIND.NS", "MRF": "MRF.NS", "APOLLOTYRE": "APOLLOTYRE.NS",
    "EXIDEIND": "EXIDEIND.NS", "AMBUJACEM": "AMBUJACEM.NS", "ACC": "ACC.NS",
    "SHREECEM": "SHREECEM.NS", "DALBHARAT": "DALBHARAT.NS", "SAIL": "SAIL.NS",
    "NMDC": "NMDC.NS", "JINDALSTEL": "JINDALSTEL.NS", "NATIONALUM": "NATIONALUM.NS",
    "IOC": "IOC.NS", "HINDPETRO": "HINDPETRO.NS", "GAIL": "GAIL.NS",
    "PETRONET": "PETRONET.NS", "IGL": "IGL.NS", "MGL": "MGL.NS",
    "GUJGASLTD": "GUJGASLTD.NS", "AUROPHARMA": "AUROPHARMA.NS", "LUPIN": "LUPIN.NS",
    "BIOCON": "BIOCON.NS", "ALKEM": "ALKEM.NS", "TORNTPHARM": "TORNTPHARM.NS",
    "ZYDUSLIFE": "ZYDUSLIFE.NS", "GLENMARK": "GLENMARK.NS", "LAURUSLABS": "LAURUSLABS.NS",
    "GRANULES": "GRANULES.NS", "SYNGENE": "SYNGENE.NS", "LALPATHLAB": "LALPATHLAB.NS",
    "METROPOLIS": "METROPOLIS.NS", "MAXHEALTH": "MAXHEALTH.NS", "INDHOTEL": "INDHOTEL.NS",
    "JUBLFOOD": "JUBLFOOD.NS", "PAGEIND": "PAGEIND.NS", "ABFRL": "ABFRL.NS",
    "BATAINDIA": "BATAINDIA.NS", "PIDILITIND": "PIDILITIND.NS", "BERGEPAINT": "BERGEPAINT.NS",
    "GODREJCP": "GODREJCP.NS", "DABUR": "DABUR.NS", "MARICO": "MARICO.NS",
    "COLPAL": "COLPAL.NS", "UBL": "UBL.NS", "UNITDSPR": "UNITDSPR.NS",
    "GODREJPROP": "GODREJPROP.NS", "OBEROIRLTY": "OBEROIRLTY.NS", "PRESTIGE": "PRESTIGE.NS",
    "CONCOR": "CONCOR.NS", "INDIGO": "INDIGO.NS", "GMRINFRA": "GMRINFRA.NS",
    "PIIND": "PIIND.NS", "SRF": "SRF.NS", "UPL": "UPL.NS",
    "TATACHEM": "TATACHEM.NS", "DEEPAKNTR": "DEEPAKNTR.NS", "AARTIIND": "AARTIIND.NS",
    "NAVINFLUOR": "NAVINFLUOR.NS", "ATUL": "ATUL.NS", "CHAMBLFERT": "CHAMBLFERT.NS",
    "COROMANDEL": "COROMANDEL.NS", "GNFC": "GNFC.NS"
}

def compute_rsi(series, length=9):
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))

def compute_wma(series, length=21):
    weights = np.arange(1, length + 1, dtype=float)
    weight_sum = weights.sum()
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weight_sum, raw=True)

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    timeframe = st.selectbox("Timeframe", ["15m", "5m", "1h", "1d"], index=0)
with col2:
    filter_mode = st.selectbox(
        "Filter Signals",
        [
            "All Triggered Crossovers Only",
            "Bullish Signals Only (Bottom Buy & Buy >50)",
            "Bearish Signals Only (Top/Exit & Short <50)",
            "Show Full F&O Watchlist Status",
        ],
        index=0,
    )
with col3:
    st.write("")
    scan_btn = st.button("🔄 Run Live Scan Now", use_container_width=True, type="primary")

@st.cache_data(ttl=120)
def fetch_and_scan(tf):
    tickers = list(WATCHLIST.values())
    symbol_map = {v: k for k, v in WATCHLIST.items()}
    period = "5d" if tf in ["5m", "15m"] else ("1mo" if tf == "1h" else "6mo")
    data = yf.download(tickers=tickers, period=period, interval=tf, group_by="ticker", threads=True, progress=False)

    rows = []
    for yf_ticker, name in symbol_map.items():
        try:
            df = data[yf_ticker].dropna() if len(tickers) > 1 else data.dropna()
            if len(df) < 35:
                continue
            close = df["Close"].squeeze()
            high = df["High"].squeeze()
            low = df["Low"].squeeze()

            rsi9 = compute_rsi(close, 9)
            ema3 = rsi9.ewm(span=3, adjust=False).mean()
            wma21 = compute_wma(rsi9, 21)

            r_now, r_prev = float(rsi9.iloc[-1]), float(rsi9.iloc[-2])
            e_now = float(ema3.iloc[-1])
            w_now, w_prev = float(wma21.iloc[-1]), float(wma21.iloc[-2])
            c_now, h_now, l_now = float(close.iloc[-1]), float(high.iloc[-1]), float(low.iloc[-1])
            spread = abs(r_now - w_now)

            if np.isnan([r_now, e_now, w_now]).any():
                continue

            if (r_now > w_now) and (r_prev <= w_prev) and (r_now >= e_now):
                sig, sl = "🟢 BOTTOM BUY", round(l_now, 2)
            elif (r_now > 50.0) and (r_prev <= 50.0) and (r_now > w_now) and (r_now >= e_now):
                sig, sl = "🚀 BUY >50", round(l_now, 2)
            elif (r_now < w_now) and (r_prev >= w_prev) and (r_now <= e_now):
                sig, sl = "🟠 TOP / EXIT", round(h_now, 2)
            elif (r_now < 50.0) and (r_prev >= 50.0) and (r_now < w_now) and (r_now <= e_now):
                sig, sl = "🔴 SHORT <50", round(h_now, 2)
            else:
                zone = "Bullish Hold (>WMA21)" if r_now > w_now else "Bearish Hold (<WMA21)"
                sig, sl = f"⚪ {zone}", round(l_now if r_now > w_now else h_now, 2)

            rows.append({
                "Symbol": name, "Signal": sig, "Close (₹)": round(c_now, 2),
                "Ref Stop-Loss": sl, "RSI (9)": round(r_now, 2), "EMA (3)": round(e_now, 2),
                "WMA (21)": round(w_now, 2), "Spread": round(spread, 2),
            })
        except Exception:
            continue
    return pd.DataFrame(rows)

if scan_btn:
    st.cache_data.clear()

ist_now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d %b %Y, %I:%M:%S %p IST")
with st.spinner(f"Scanning {len(WATCHLIST)} NSE F&O Symbols on {timeframe}..."):
    df_results = fetch_and_scan(timeframe)

if not df_results.empty:
    if filter_mode == "All Triggered Crossovers Only":
        df_view = df_results[~df_results["Signal"].str.startswith("⚪")]
    elif filter_mode == "Bullish Signals Only (Bottom Buy & Buy >50)":
        df_view = df_results[df_results["Signal"].str.contains("BUY")]
    elif filter_mode == "Bearish Signals Only (Top/Exit & Short <50)":
        df_view = df_results[df_results["Signal"].str.contains("TOP|SHORT")]
    else:
        df_view = df_results

    st.subheader(f"Live Results ({len(df_view)} Matches) — Updated {ist_now}")
    st.dataframe(df_view, use_container_width=True, hide_index=True)
else:
    st.info("No data returned. Please click 'Run Live Scan Now'.")

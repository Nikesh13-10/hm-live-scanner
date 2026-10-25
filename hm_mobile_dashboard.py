```python
"""
Hilega-Milega (HM) Mobile Web Screener Dashboard (Chartink Alternative)
Deploy free on Streamlit Community Cloud (https://share.streamlit.io) to open on any mobile browser!
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz
from hm_cloud_scanner import WATCHLIST, compute_rsi, compute_wma

st.set_page_config(
    page_title="HM Live F&O Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📈 Hilega-Milega Live F&O Screener")
st.caption("Real-time Chartink alternative for Nifty 50, Bank Nifty & NSE F&O Stocks")

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
def fetch_and_scan(tf: str):
    tickers = list(WATCHLIST.values())
    symbol_map = {v: k for k, v in WATCHLIST.items()}
    period = "5d" if tf in ["5m", "15m"] else ("1mo" if tf == "1h" else "6mo")

    data = yf.download(
        tickers=tickers,
        period=period,
        interval=tf,
        group_by="ticker",
        threads=True,
        progress=False,
    )

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
            c_now = float(close.iloc[-1])
            h_now = float(high.iloc[-1])
            l_now = float(low.iloc[-1])
            spread = abs(r_now - w_now)

            if np.isnan([r_now, e_now, w_now]).any():
                continue

            if (r_now > w_now) and (r_prev <= w_prev) and (r_now >= e_now):
                sig = "🟢 BOTTOM BUY"
                sl = round(l_now, 2)
            elif (r_now > 50.0) and (r_prev <= 50.0) and (r_now > w_now) and (r_now >= e_now):
                sig = "🚀 BUY >50"
                sl = round(l_now, 2)
            elif (r_now < w_now) and (r_prev >= w_prev) and (r_now <= e_now):
                sig = "🟠 TOP / EXIT"
                sl = round(h_now, 2)
            elif (r_now < 50.0) and (r_prev >= 50.0) and (r_now < w_now) and (r_now <= e_now):
                sig = "🔴 SHORT <50"
                sl = round(h_now, 2)
            else:
                zone = "Bullish Hold (>WMA21)" if r_now > w_now else "Bearish Hold (<WMA21)"
                sig = f"⚪ {zone}"
                sl = round(l_now if r_now > w_now else h_now, 2)

            rows.append(
                {
                    "Symbol": name,
                    "Signal": sig,
                    "Close (₹)": round(c_now, 2),
                    "Ref Stop-Loss": sl,
                    "RSI (9)": round(r_now, 2),
                    "EMA (3)": round(e_now, 2),
                    "WMA (21)": round(w_now, 2),
                    "Spread": round(spread, 2),
                }
            )
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
```

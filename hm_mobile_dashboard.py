import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pytz

st.set_page_config(
    page_title="Long-Term Investment Screener (HM + Multibagger/Compounder)",
    page_icon="💎",
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

# ==============================================================================
# 1. CURATED INVESTMENT UNIVERSE (ETFs + NIFTY 50 + QUALITY COMPOUNDERS/MIDCAPS)
# ==============================================================================
ETFS = {
    "NIFTYBEES": "NIFTYBEES.NS",
    "BANKBEES": "BANKBEES.NS",
    "JUNIORBEES": "JUNIORBEES.NS",
    "MID150BEES": "MID150BEES.NS",
    "GOLDBEES": "GOLDBEES.NS",
    "SILVERBEES": "SILVERBEES.NS",
}

INVESTMENT_STOCKS = {
    "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS", "INFY": "INFY.NS", "SBIN": "SBIN.NS",
    "BHARTIARTL": "BHARTIARTL.NS", "ITC": "ITC.NS", "LT": "LT.NS",
    "BAJFINANCE": "BAJFINANCE.NS", "AXISBANK": "AXISBANK.NS", "KOTAKBANK": "KOTAKBANK.NS",
    "MARUTI": "MARUTI.NS", "M&M": "M&M.NS", "SUNPHARMA": "SUNPHARMA.NS",
    "TITAN": "TITAN.NS", "HCLTECH": "HCLTECH.NS", "ULTRACEMCO": "ULTRACEMCO.NS",
    "NTPC": "NTPC.NS", "POWERGRID": "POWERGRID.NS", "ONGC": "ONGC.NS",
    "COALINDIA": "COALINDIA.NS", "BAJAJFINSV": "BAJAJFINSV.NS", "ASIANPAINT": "ASIANPAINT.NS",
    "HINDUNILVR": "HINDUNILVR.NS", "NESTLEIND": "NESTLEIND.NS", "BRITANNIA": "BRITANNIA.NS",
    "PIDILITIND": "PIDILITIND.NS", "CIPLA": "CIPLA.NS", "DRREDDY": "DRREDDY.NS",
    "DIVISLAB": "DIVISLAB.NS", "APOLLOHOSP": "APOLLOHOSP.NS", "EICHERMOT": "EICHERMOT.NS",
    "BAJAJ-AUTO": "BAJAJ-AUTO.NS", "TVSMOTOR": "TVSMOTOR.NS", "TATACONSUM": "TATACONSUM.NS",
    "HAL": "HAL.NS", "BEL": "BEL.NS", "TRENT": "TRENT.NS", "DIXON": "DIXON.NS",
    "POLYCAB": "POLYCAB.NS", "ABB": "ABB.NS", "SIEMENS": "SIEMENS.NS",
    "CUMMINSIND": "CUMMINSIND.NS", "HAVELLS": "HAVELLS.NS", "PERSISTENT": "PERSISTENT.NS",
    "COFORGE": "COFORGE.NS", "LTIM": "LTIM.NS", "NAUKRI": "NAUKRI.NS",
    "CDSL": "CDSL.NS", "BSE": "BSE.NS", "MCX": "MCX.NS", "CHOLAFIN": "CHOLAFIN.NS",
    "SHRIRAMFIN": "SHRIRAMFIN.NS", "SBILIFE": "SBILIFE.NS", "HDFCLIFE": "HDFCLIFE.NS",
    "INDHOTEL": "INDHOTEL.NS", "MAXHEALTH": "MAXHEALTH.NS", "PIIND": "PIIND.NS",
    "SRF": "SRF.NS", "DEEPAKNTR": "DEEPAKNTR.NS", "PAGEIND": "PAGEIND.NS",
    "VARUNBEV (VBL)": "VBL.NS", "DMART": "DMART.NS", "ZOMATO": "ZOMATO.NS",
    "TATAPOWER": "TATAPOWER.NS", "DLF": "DLF.NS", "INDIGO": "INDIGO.NS",
}

ALL_DEFAULT_SYMBOLS = {**ETFS, **INVESTMENT_STOCKS}

# ==============================================================================
# 2. HILEGA-MILEGA MATH (WEEKLY / MONTHLY)
# ==============================================================================
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
    return series.rolling(length).apply(lambda x: [invalid URL](x, weights) / weight_sum, raw=True)

# ==============================================================================
# 3. FUNDAMENTAL DATA FETCHER (CACHED 6 HOURS FOR SPEED)
# ==============================================================================
def _fetch_single_fundamental(item):
    name, yf_ticker = item
    if name in ETFS:
        return name, {"pe": None, "roe": None, "eps_g": None, "dte": None, "mcap_cr": None}
    try:
        info = yf.Ticker(yf_ticker).info
        pe = info.get("trailingPE") or info.get("forwardPE")
        roe = info.get("returnOnEquity")
        eps_g = info.get("earningsGrowth") or info.get("revenueGrowth")
        dte = info.get("debtToEquity")
        mcap = info.get("marketCap")
        return name, {
            "pe": round(float(pe), 1) if pe is not None else None,
            "roe": round(float(roe) * 100, 1) if roe is not None else None,
            "eps_g": round(float(eps_g) * 100, 1) if eps_g is not None else None,
            "dte": round(float(dte) / 100.0, 2) if dte is not None else None,
            "mcap_cr": round(float(mcap) / 1e7, 0) if mcap is not None else None,
        }
    except Exception:
        return name, {"pe": None, "roe": None, "eps_g": None, "dte": None, "mcap_cr": None}

@st.cache_data(ttl=21600)
def fetch_fundamentals_batch(symbol_dict):
    results = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        for name, data in ex.map(_fetch_single_fundamental, symbol_dict.items()):
            results[name] = data
    return results

def classify_investment_bucket(name, fund, disc_pct):
    if name in ETFS:
        return "🪙 ETF / Index"
    pe = fund.get("pe")
    roe = fund.get("roe")
    eps_g = fund.get("eps_g")

    # 1. Multibagger: Fast Earnings Growth (>=20%) + room for PE re-rating (PE <= 45)
    if eps_g is not None and eps_g >= 20.0 and (pe is None or pe <= 45.0):
        return "🚀 Multibagger"
    # 2. Core Compounder: Strong ROE (>=15%) + positive/steady earnings growth
    if roe is not None and roe >= 15.0 and (eps_g is None or eps_g >= 5.0):
        return "🛡️ Compounder"
    # 3. Value / Dip Candidate: Reasonable PE (<22) + good discount from 52W high
    if pe is not None and 0 < pe <= 22.0 and disc_pct >= 12.0:
        return "💎 Value Dip"
    return "👀 Watchlist"

# ==============================================================================
# 4. MAIN INVESTMENT SCANNER ENGINE
# ==============================================================================
@st.cache_data(ttl=600)
def run_investment_scan(tf, symbol_dict):
    tickers = list(symbol_dict.values())
    symbol_map = {v: k for k, v in symbol_dict.items()}
    period = "2y" if tf == "1wk" else "5y"

    data = [invalid URL](
        tickers=tickers,
        period=period,
        interval=tf,
        group_by="ticker",
        threads=True,
        progress=False,
    )
    fundamentals = fetch_fundamentals_batch(symbol_dict)

    rows = []
    for yf_ticker, name in symbol_map.items():
        try:
            df = data[yf_ticker].dropna() if len(tickers) > 1 else data.dropna()
            if len(df) < 25:
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
            l_now = float(low.iloc[-1])

            if np.isnan([r_now, e_now, w_now, c_now]).any():
                continue

            # 52-Week High & Discount %
            lookback_52w = 52 if tf == "1wk" else 12
            high_52w = float(high.tail(lookback_52w).max())
            disc_pct = round(((high_52w - c_now) / high_52w) * 100.0, 1) if high_52w > 0 else 0.0

            # Long-term Trend Proxy (~200 DMA = 40-Week SMA or 10-Month SMA)
            ma_len = 40 if tf == "1wk" else 10
            ma_val = float(close.rolling(ma_len).mean().iloc[-1]) if len(close) >= ma_len else float(close.mean())
            above_200dma = c_now >= ma_val
            dma_status = "Above 200 DMA" if above_200dma else "Below 200 DMA"

            # Investment-Only Long Signals (Hilega-Milega)
            fresh_bottom = (r_now > w_now) and (r_prev <= w_prev) and (r_now >= e_now)
            if fresh_bottom or ((r_now > w_now) and (r_now >= e_now) and (disc_pct >= 12.0)):
                sig = "🟢 BOTTOM ACCUMULATE (Buy on Dip)"
            elif (r_now > 50.0) and (r_now > w_now) and above_200dma:
                sig = "🚀 CORE UPTREND (SIP / Hold)"
            elif (r_now < w_now) and (r_prev >= w_prev):
                sig = "🟠 TOP WARNING / REBALANCE"
            elif (r_now < 50.0) and (r_now < w_now):
                sig = "🔴 WEAK / WAIT FOR BOTTOM"
            else:
                sig = "⚪ NEUTRAL / WATCH"

            fund = fundamentals.get(name, {})
            bucket = classify_investment_bucket(name, fund, disc_pct)

            rows.append({
                "Symbol": name,
                "Category": bucket,
                "Investment Signal": sig,
                "Price (₹)": round(c_now, 2),
                "52W High Disc %": disc_pct,
                "200 DMA": dma_status,
                "P/E": fund.get("pe"),
                "ROE %": fund.get("roe"),
                "EPS Growth %": fund.get("eps_g"),
                "RSI (9)": round(r_now, 1),
                "WMA (21)": round(w_now, 1),
                "Support (Low ₹)": round(l_now, 2),
            })
        except Exception:
            continue

    df_out = pd.DataFrame(rows)
    if not df_out.empty:
        # Sort: Bottom Accumulate & Core Uptrend on top, then highest discount/ROE
        sig_order = {
            "🟢 BOTTOM ACCUMULATE (Buy on Dip)": 1,
            "🚀 CORE UPTREND (SIP / Hold)": 2,
            "⚪ NEUTRAL / WATCH": 3,
            "🟠 TOP WARNING / REBALANCE": 4,
            "🔴 WEAK / WAIT FOR BOTTOM": 5,
        }
        df_out["_ord"] = df_out["Investment Signal"].map(sig_order).fillna(9)
        df_out = df_out.sort_values(by=["_ord", "52W High Disc %"], ascending=[True, False]).drop(columns=["_ord"]).reset_index(drop=True)
    return df_out

# ==============================================================================
# 5. UI LAYOUT (CLEAN INVESTMENT-ONLY SCREENER)
# ==============================================================================
st.title("💎 Long-Term Investment Screener")
st.caption("Weekly & Monthly Hilega-Milega + **Multibagger vs Compounder** Fundamental Filter (Long-Only)")

# Custom Stock Input (For checking stocks from NK Stocktalk or personal watchlist)
custom_input = st.text_input(
    "🔍 Custom Stocks जोडा (उदा. NK Stocktalk मधील कोणताही स्टॉक — कॉमा देऊन NSE Symbol लिहा):",
    placeholder="उदा. TATAMOTORS, JIOFIN, ZYDUSLIFE, KPITTECH",
)

active_symbols = dict(ALL_DEFAULT_SYMBOLS)
if custom_input.strip():
    for raw in custom_input.split(","):
        sym = raw.strip().upper().replace(".NS", "")
        if sym and sym not in active_symbols:
            active_symbols[sym] = f"{sym}.NS"

c1, c2, c3, c4 = st.columns([0.9, 1.3, 1.3, 0.9])
with c1:
    timeframe = st.selectbox("Timeframe", ["1wk", "1mo"], index=0, help="1wk = Weekly (Best for Swing/Positional Investing), 1mo = Monthly (Core Long-Term Investing)")
with c2:
    cat_filter = st.selectbox(
        "Category (Multibagger / Compounder)",
        [
            "All Categories",
            "🚀 Multibagger Only",
            "🛡️ Compounder Only",
            "💎 Value Dip Only",
            "🪙 ETF / Index Only",
        ],
        index=0,
    )
with c3:
    sig_filter = st.selectbox(
        "Signal Filter",
        [
            "Buy / Accumulate & SIP Only",
            "🟢 Bottom Accumulate (Buy on Dip) Only",
            "🟠 Top Warning / Rebalance Only",
            "Show Full Investment Universe",
        ],
        index=0,
    )
with c4:
    st.write("")
    refresh_btn = st.button("🔄 Refresh Scan", use_container_width=True, type="primary")

if refresh_btn:
    st.cache_data.clear()

ist_now = [invalid URL](pytz.timezone("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST")

with st.spinner(f"Scanning {len(active_symbols)} Investment Stocks & ETFs on {timeframe} chart..."):
    df_res = run_investment_scan(timeframe, active_symbols)

if not df_res.empty:
    df_view = df_res.copy()

    if cat_filter == "🚀 Multibagger Only":
        df_view = df_view[df_view["Category"] == "🚀 Multibagger"]
    elif cat_filter == "🛡️ Compounder Only":
        df_view = df_view[df_view["Category"] == "🛡️ Compounder"]
    elif cat_filter == "💎 Value Dip Only":
        df_view = df_view[df_view["Category"] == "💎 Value Dip"]
    elif cat_filter == "🪙 ETF / Index Only":
        df_view = df_view[df_view["Category"] == "🪙 ETF / Index"]

    if sig_filter == "Buy / Accumulate & SIP Only":
        df_view = df_view[df_view["Investment Signal"].str.contains("BOTTOM|UPTREND")]
    elif sig_filter == "🟢 Bottom Accumulate (Buy on Dip) Only":
        df_view = df_view[df_view["Investment Signal"].str.contains("BOTTOM")]
    elif sig_filter == "🟠 Top Warning / Rebalance Only":
        df_view = df_view[df_view["Investment Signal"].str.contains("TOP")]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🟢 Bottom Accumulate", int(df_res["Investment Signal"].str.contains("BOTTOM").sum()))
    m2.metric("🚀 Multibagger Candidates", int((df_res["Category"] == "🚀 Multibagger").sum()))
    m3.metric("🛡️ Core Compounders", int((df_res["Category"] == "🛡️ Compounder").sum()))
    m4.metric("🟠 Top / Rebalance Alerts", int(df_res["Investment Signal"].str.contains("TOP").sum()))

    st.subheader(f"Results ({len(df_view)} Stocks) — {timeframe.upper()} Chart | {ist_now}")
    st.dataframe(df_view, use_container_width=True, hide_index=True)
else:
    [invalid URL]("डेटा लोड झाला नाही. कृपया 'Refresh Scan' वर क्लिक करा.")

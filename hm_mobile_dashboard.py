import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pytz

st.set_page_config(
    page_title="Long-Term Investment Screener, Analyzer & 5Y Backtester",
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
    "VBL": "VBL.NS", "DMART": "DMART.NS", "ZOMATO": "ZOMATO.NS",
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
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weight_sum, raw=True)


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

    if eps_g is not None and eps_g >= 20.0 and (pe is None or pe <= 45.0):
        return "🚀 Multibagger"
    if roe is not None and roe >= 15.0 and (eps_g is None or eps_g >= 5.0):
        return "🛡️ Compounder"
    if pe is not None and 0 < pe <= 22.0 and disc_pct >= 12.0:
        return "💎 Value Dip"
    return "👀 Watchlist"


def get_hm_signal_for_series(df, tf="1wk"):
    if df is None or len(df) < 25:
        return None
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
        return None

    lookback_52w = 52 if tf == "1wk" else 12
    high_52w = float(high.tail(lookback_52w).max())
    low_52w = float(low.tail(lookback_52w).min())
    disc_pct = round(((high_52w - c_now) / high_52w) * 100.0, 1) if high_52w > 0 else 0.0

    ma_len = 40 if tf == "1wk" else 10
    ma_series = close.rolling(ma_len).mean()
    ma_val = float(ma_series.iloc[-1]) if not np.isnan(ma_series.iloc[-1]) else float(close.mean())
    above_200dma = c_now >= ma_val

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

    return {
        "signal": sig,
        "close": round(c_now, 2),
        "low": round(l_now, 2),
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "disc_pct": disc_pct,
        "ma_val": round(ma_val, 2),
        "above_200dma": above_200dma,
        "rsi9": round(r_now, 1),
        "ema3": round(e_now, 1),
        "wma21": round(w_now, 1),
        "ma_series": ma_series,
        "close_series": close,
    }


# ==============================================================================
# 4. MAIN INVESTMENT SCANNER ENGINE
# ==============================================================================
@st.cache_data(ttl=600)
def run_investment_scan(tf, symbol_dict):
    tickers = list(symbol_dict.values())
    symbol_map = {v: k for k, v in symbol_dict.items()}
    period = "2y" if tf == "1wk" else "5y"

    data = yf.download(
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
            hm = get_hm_signal_for_series(df, tf)
            if hm is None:
                continue

            fund = fundamentals.get(name, {})
            bucket = classify_investment_bucket(name, fund, hm["disc_pct"])

            rows.append({
                "Symbol": name,
                "Category": bucket,
                "Investment Signal": hm["signal"],
                "Price (₹)": hm["close"],
                "52W High Disc %": hm["disc_pct"],
                "200 DMA": "Above 200 DMA" if hm["above_200dma"] else "Below 200 DMA",
                "P/E": fund.get("pe"),
                "ROE %": fund.get("roe"),
                "EPS Growth %": fund.get("eps_g"),
                "RSI (9)": hm["rsi9"],
                "WMA (21)": hm["wma21"],
                "Support (Low ₹)": hm["low"],
            })
        except Exception:
            continue

    df_out = pd.DataFrame(rows)
    if not df_out.empty:
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
# 5. SINGLE STOCK DEEP INVESTMENT ANALYZER (ANY NSE STOCK)
# ==============================================================================
@st.cache_data(ttl=600)
def analyze_single_stock(raw_symbol):
    clean_sym = raw_symbol.strip().upper().replace(".NS", "").replace(".BO", "")
    yf_ticker = f"{clean_sym}.NS"

    df_wk = yf.download(tickers=yf_ticker, period="5y", interval="1wk", progress=False)
    df_mo = yf.download(tickers=yf_ticker, period="5y", interval="1mo", progress=False)

    if df_wk is None or df_wk.empty or len(df_wk) < 25:
        return None

    hm_wk = get_hm_signal_for_series(df_wk.dropna(), "1wk")
    hm_mo = get_hm_signal_for_series(df_mo.dropna(), "1mo") if (df_mo is not None and len(df_mo) >= 25) else None

    if hm_wk is None:
        return None

    info = {}
    try:
        info = yf.Ticker(yf_ticker).info or {}
    except Exception:
        info = {}

    pe = info.get("trailingPE") or info.get("forwardPE")
    roe = info.get("returnOnEquity")
    eps_g = info.get("earningsGrowth") or info.get("revenueGrowth")
    dte = info.get("debtToEquity")
    mcap = info.get("marketCap")
    div_y = info.get("dividendYield")

    fund = {
        "name": info.get("longName") or info.get("shortName") or clean_sym,
        "sector": info.get("sector") or "N/A",
        "industry": info.get("industry") or "N/A",
        "pe": round(float(pe), 1) if pe is not None else None,
        "roe": round(float(roe) * 100, 1) if roe is not None else None,
        "eps_g": round(float(eps_g) * 100, 1) if eps_g is not None else None,
        "dte": round(float(dte) / 100.0, 2) if dte is not None else None,
        "mcap_cr": round(float(mcap) / 1e7, 0) if mcap is not None else None,
        "div_yield": round(float(div_y) * 100, 2) if div_y is not None else None,
    }

    bucket = classify_investment_bucket(clean_sym, fund, hm_wk["disc_pct"])

    # Chart DataFrame (5-Year Weekly Price vs 200 DMA Proxy)
    chart_df = pd.DataFrame({
        "Price (₹)": hm_wk["close_series"],
        "200 DMA Proxy (40W SMA)": hm_wk["ma_series"],
    }).dropna()

    return {
        "symbol": clean_sym,
        "yf_ticker": yf_ticker,
        "bucket": bucket,
        "fund": fund,
        "hm_wk": hm_wk,
        "hm_mo": hm_mo,
        "chart_df": chart_df,
    }


# ==============================================================================
# 6. 3Y–5Y LONG-ONLY INVESTMENT BACKTESTER (HM STRATEGY VS BUY & HOLD)
# ==============================================================================
@st.cache_data(ttl=600)
def run_investment_backtest(yf_ticker, symbol_name, tf="1wk", years=5, initial_capital=500000.0, use_200dma_filter=True):
    fetch_years = years + 2
    df = yf.download(tickers=yf_ticker, period=f"{fetch_years}y", interval=tf, progress=False)
    if df is None or len(df) < 35:
        return None, None, None

    df = df.dropna().copy()
    close = df["Close"].squeeze()

    rsi9 = compute_rsi(close, 9)
    ema3 = rsi9.ewm(span=3, adjust=False).mean()
    wma21 = compute_wma(rsi9, 21)
    ma_len = 40 if tf == "1wk" else 10
    ma_long = close.rolling(ma_len).mean()

    bars_needed = years * (52 if tf == "1wk" else 12)
    start_idx = max(30, len(df) - bars_needed)
    if start_idx >= len(df) - 5:
        start_idx = 30

    capital = initial_capital
    shares = 0.0
    entry_price = 0.0
    entry_date = None
    trades = []
    equity_rows = []

    bh_start_price = float(close.iloc[start_idx])
    bh_shares = initial_capital / bh_start_price if bh_start_price > 0 else 0.0

    for i in range(start_idx, len(df)):
        dt = df.index[i]
        c_i = float(close.iloc[i])
        r_i, r_prev = float(rsi9.iloc[i]), float(rsi9.iloc[i - 1])
        e_i = float(ema3.iloc[i])
        w_i, w_prev = float(wma21.iloc[i]), float(wma21.iloc[i - 1])
        ma_i = float(ma_long.iloc[i]) if not np.isnan(ma_long.iloc[i]) else c_i

        if np.isnan([r_i, e_i, w_i, c_i]).any():
            continue

        dma_ok = (c_i >= ma_i) if use_200dma_filter else True
        buy_signal = ((r_i > w_i and r_prev <= w_prev) or (r_i > 50.0 and r_prev <= 50.0 and r_i > w_i)) and (r_i >= e_i) and dma_ok
        exit_signal = (r_i < w_i) and (r_prev >= w_prev)

        if shares == 0.0 and buy_signal:
            shares = capital / c_i
            entry_price = c_i
            entry_date = dt.strftime("%d-%b-%Y")
            capital = 0.0
        elif shares > 0.0 and exit_signal:
            exit_val = shares * c_i
            pnl = exit_val - (shares * entry_price)
            ret_pct = ((c_i - entry_price) / entry_price) * 100.0
            trades.append({
                "Entry Date": entry_date,
                "Exit Date": dt.strftime("%d-%b-%Y"),
                "Buy Price (₹)": round(entry_price, 2),
                "Sell Price (₹)": round(c_i, 2),
                "Return %": round(ret_pct, 2),
                "Net P&L (₹)": round(pnl, 2),
                "Portfolio Value (₹)": round(exit_val, 2),
            })
            capital = exit_val
            shares = 0.0

        curr_port_val = capital + (shares * c_i)
        bh_val = bh_shares * c_i
        equity_rows.append({
            "Date": dt,
            "HM Strategy (₹)": round(curr_port_val, 2),
            "Buy & Hold (₹)": round(bh_val, 2),
        })

    last_price = float(close.iloc[-1])
    if shares > 0.0:
        curr_val = shares * last_price
        pnl = curr_val - (shares * entry_price)
        ret_pct = ((last_price - entry_price) / entry_price) * 100.0
        trades.append({
            "Entry Date": entry_date,
            "Exit Date": "HOLDING (Open)",
            "Buy Price (₹)": round(entry_price, 2),
            "Sell Price (₹)": round(last_price, 2),
            "Return %": round(ret_pct, 2),
            "Net P&L (₹)": round(pnl, 2),
            "Portfolio Value (₹)": round(curr_val, 2),
        })
        final_val = curr_val
    else:
        final_val = capital

    df_eq = pd.DataFrame(equity_rows)
    df_trades = pd.DataFrame(trades)

    actual_years = max((df.index[-1] - df.index[start_idx]).days / 365.25, 0.5)
    hm_total_ret = ((final_val - initial_capital) / initial_capital) * 100.0
    hm_cagr = (((final_val / initial_capital) ** (1.0 / actual_years)) - 1.0) * 100.0 if final_val > 0 else 0.0

    bh_final = bh_shares * last_price
    bh_total_ret = ((bh_final - initial_capital) / initial_capital) * 100.0
    bh_cagr = (((bh_final / initial_capital) ** (1.0 / actual_years)) - 1.0) * 100.0 if bh_final > 0 else 0.0

    hm_dd = (((df_eq["HM Strategy (₹)"] - df_eq["HM Strategy (₹)"].cummax()) / df_eq["HM Strategy (₹)"].cummax()) * 100.0).min() if not df_eq.empty else 0.0
    bh_dd = (((df_eq["Buy & Hold (₹)"] - df_eq["Buy & Hold (₹)"].cummax()) / df_eq["Buy & Hold (₹)"].cummax()) * 100.0).min() if not df_eq.empty else 0.0

    win_rate = round((len(df_trades[df_trades["Net P&L (₹)"] > 0]) / len(df_trades)) * 100.0, 1) if not df_trades.empty else 0.0

    summary = {
        "final_val": round(final_val, 2),
        "hm_ret": round(hm_total_ret, 1),
        "hm_cagr": round(hm_cagr, 1),
        "hm_dd": round(float(hm_dd), 1),
        "bh_final": round(bh_final, 2),
        "bh_ret": round(bh_total_ret, 1),
        "bh_cagr": round(bh_cagr, 1),
        "bh_dd": round(float(bh_dd), 1),
        "total_trades": len(df_trades),
        "win_rate": win_rate,
    }
    return summary, df_trades, df_eq


# ==============================================================================
# 7. UI LAYOUT (3 TABS: SCREENER + SINGLE STOCK ANALYZER + 3Y–5Y BACKTESTER)
# ==============================================================================
st.title("💎 Long-Term Investment Screener, Stock Analyzer & Backtester")
st.caption("Weekly & Monthly Hilega-Milega + **Multibagger vs Compounder** Fundamental Filter (Long-Only)")

tab_scan, tab_single, tab_bt = st.tabs([
    "🔍 Investment Screener (Multibagger & Compounder)",
    "🔎 Single Stock Analyzer (कोणताही स्टॉक तपासा)",
    "📊 3Y–5Y Investment Backtester (HM vs Buy & Hold)",
])

with tab_scan:
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
        timeframe = st.selectbox("Timeframe", ["1wk", "1mo"], index=0)
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

    ist_now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST")

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
        st.info("डेटा लोड झाला नाही. कृपया 'Refresh Scan' वर क्लिक करा.")

# ==============================================================================
# TAB 2: SINGLE STOCK INVESTMENT ANALYZER
# ==============================================================================
with tab_single:
    st.subheader("🔎 Single Stock Investment Analyzer (कोणताही NSE स्टॉक तपासा)")
    st.caption("कोणत्याही NSE स्टॉकचे Symbol टाका — त्याचा Multibagger/Compounder दर्जा, Fundamentals आणि Weekly + Monthly Hilega-Milega रिपोर्ट एका क्लिकवर पहा.")

    sc1, sc2 = st.columns([2.2, 1.0])
    with sc1:
        query_sym = st.text_input(
            "NSE Stock Symbol टाका (उदा. TRENT, KPITTECH, JIOFIN, NESTLEIND, TATAMOTORS, IRFC):",
            value="TRENT",
            key="single_stock_input",
        )
    with sc2:
        st.write("")
        analyze_btn = st.button("🔎 Analyze Stock", use_container_width=True, type="primary")

    if query_sym.strip():
        with st.spinner(f"Analyzing {query_sym.strip().upper()}..."):
            report = analyze_single_stock(query_sym)

        if report is None:
            st.error(f"'{query_sym.strip().upper()}' साठी डेटा सापडला नाही. कृपया अचूक NSE Symbol टाका (उदा. RELIANCE, TCS, TRENT, JIOFIN).")
        else:
            f = report["fund"]
            wk = report["hm_wk"]
            mo = report["hm_mo"]

            st.markdown(f"### {f['name']} (`{report['symbol']}`) — {report['bucket']}")
            st.caption(f"Sector: **{f['sector']}**  |  Industry: **{f['industry']}**")

            # Top Price & Trend Metrics
            p1, p2, p3, p4, p5 = st.columns(5)
            p1.metric("💰 Current Price", f"₹{wk['close']:,.2f}")
            p2.metric("📉 52W High Discount", f"{wk['disc_pct']}%", f"52W High: ₹{wk['high_52w']:,.0f}")
            p3.metric("🧭 200 DMA Status", "Above 200 DMA" if wk["above_200dma"] else "Below 200 DMA", f"200 DMA: ₹{wk['ma_val']:,.0f}")
            p4.metric("📅 Weekly HM Signal", wk["signal"].split("(")[0].strip(), f"RSI9: {wk['rsi9']} | WMA21: {wk['wma21']}")
            if mo:
                p5.metric("🗓️ Monthly HM Signal", mo["signal"].split("(")[0].strip(), f"RSI9: {mo['rsi9']} | WMA21: {mo['wma21']}")
            else:
                p5.metric("🗓️ Monthly HM Signal", "N/A (<2Y History)")

            # Fundamental Health Metrics
            st.write("**📊 Fundamental Quality Card:**")
            f1, f2, f3, f4, f5 = st.columns(5)
            f1.metric("🏢 Market Cap", f"₹{f['mcap_cr']:,.0f} Cr" if f["mcap_cr"] else "N/A")
            f2.metric("⚖️ P/E Ratio", f"{f['pe']}" if f["pe"] is not None else "N/A")
            f3.metric("🏆 ROE %", f"{f['roe']}%" if f["roe"] is not None else "N/A")
            f4.metric("📈 EPS / Rev Growth", f"{f['eps_g']}%" if f["eps_g"] is not None else "N/A")
            f5.metric("🏦 Debt / Equity", f"{f['dte']}" if f["dte"] is not None else "N/A")

            # Actionable Summary Box
            wk_bull = "BOTTOM" in wk["signal"] or "UPTREND" in wk["signal"]
            mo_bull = (mo is not None) and ("BOTTOM" in mo["signal"] or "UPTREND" in mo["signal"])
            if wk_bull and mo_bull and wk["above_200dma"]:
                st.success(f"✅ **Investment Verdict ({report['symbol']}):** Weekly आणि Monthly दोन्ही चार्टवर मजबूत तेजी (`Above 200 DMA`) आहे. कॅटेगरी: **{report['bucket']}** — लाँग-टर्म SIP / टप्प्याटप्प्याने खरेदीसाठी चांगली स्थिती.")
            elif wk_bull and wk["disc_pct"] >= 12.0:
                st.info(f"🟢 **Buy-on-Dip Zone ({report['symbol']}):** स्टॉक ५२-आठवड्यांच्या उच्चांकापासून **{wk['disc_pct']}% डिस्काउंटवर** असून Weekly HM वर सुधारणा दिसत आहे. फंडामेंटल्स (`ROE`, `EPS Growth`) तपासून २–३ टप्प्यांत खरेदीचा विचार करता येईल.")
            elif "TOP" in wk["signal"] or (mo and "TOP" in mo["signal"]):
                st.warning(f"🟠 **Caution / Rebalance ({report['symbol']}):** HM इंडिकेटरवर Top Warning दिसत आहे. सध्या नवीन एकरकमी खरेदी टाळा.")
            else:
                st.error(f"🔴 **Wait / Avoid New Buy ({report['symbol']}):** स्टॉक सध्या कमजोर झोनमध्ये (`RSI 9 < WMA 21` किंवा `Below 200 DMA`) आहे. बॉटम तयार होण्याची वाट पहा.")

            # 5-Year Price vs 200 DMA Chart
            if not report["chart_df"].empty:
                st.write(f"**📈 {report['symbol']} — 5-Year Weekly Price vs 200 DMA Trend:**")
                st.line_chart(report["chart_df"])

# ==============================================================================
# TAB 3: 3Y–5Y INVESTMENT BACKTESTER
# ==============================================================================
with tab_bt:
    st.subheader("📊 3Y–5Y Investment Backtester (Hilega-Milega vs Buy & Hold)")
    st.caption("Long-Only: Weekly किंवा Monthly चार्टवर HM क्रॉसओव्हरवर खरेदी आणि Top क्रॉसवर (RSI9 < WMA21) बाहेर पडून कॅश सुरक्षित ठेवते.")

    b1, b2, b3, b4, b5 = st.columns([1.4, 0.9, 0.9, 1.0, 1.2])
    with b1:
        bt_sym = st.selectbox("Select Stock / ETF", list(active_symbols.keys()), index=0, key="bt_sym")
    with b2:
        bt_tf = st.selectbox("Timeframe", ["1wk", "1mo"], index=0, key="bt_tf")
    with b3:
        bt_years = st.selectbox("Period (Years)", [3, 5, 7], index=1, key="bt_years")
    with b4:
        bt_cap = st.number_input("Capital (₹)", min_value=50000, value=500000, step=50000, key="bt_cap")
    with b5:
        st.write("")
        bt_dma = st.checkbox("200 DMA Filter वापरा", value=True, help="फक्त 200 DMA च्या वरच खरेदी करा")

    with st.spinner(f"Running {bt_years}-Year Investment Backtest on {bt_sym} ({bt_tf})..."):
        summary, df_bt_trades, df_bt_eq = run_investment_backtest(
            active_symbols[bt_sym], bt_sym, bt_tf, bt_years, float(bt_cap), bt_dma
        )

    if summary is not None:
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("💎 HM Strategy Final Value", f"₹{summary['final_val']:,.0f}", f"{summary['hm_ret']:+.1f}% ({summary['hm_cagr']}% CAGR)")
        k2.metric("🏦 Buy & Hold Final Value", f"₹{summary['bh_final']:,.0f}", f"{summary['bh_ret']:+.1f}% ({summary['bh_cagr']}% CAGR)")
        k3.metric("🛡️ HM Max Drawdown", f"{summary['hm_dd']}%", f"vs B&H: {summary['bh_dd']}%")
        k4.metric("🎯 Win Rate", f"{summary['win_rate']}%", f"{summary['total_trades']} Trades")
        k5.metric("⚡ Strategy Edge", f"{round(summary['hm_ret'] - summary['bh_ret'], 1):+.1f}%", "vs Buy & Hold")

        if df_bt_eq is not None and not df_bt_eq.empty:
            st.write("**📈 Portfolio Growth Curve: HM Strategy vs Buy & Hold (₹):**")
            st.line_chart(df_bt_eq.set_index("Date")[["HM Strategy (₹)", "Buy & Hold (₹)"]])

        if df_bt_trades is not None and not df_bt_trades.empty:
            st.write(f"**📜 Historical Investment Trades ({len(df_bt_trades)} Trades):**")
            st.dataframe(df_bt_trades, use_container_width=True, hide_index=True)
        else:
            st.info("या कालावधीत कोणताही Long-Only क्रॉसओव्हर सिग्नल आला नाही (200 DMA Filter बंद करून तपासून पहा).")
    else:
        st.warning("या स्टॉकसाठी पुरेसा ऐतिहासिक डेटा उपलब्ध नाही.")

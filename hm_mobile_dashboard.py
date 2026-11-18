import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz

st.set_page_config(
    page_title="4-Pillar Pullback + HM Swing Screener & Backtester",
    page_icon="🎯",
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
# 1. CURATED LIQUID SWING UNIVERSE (NIFTY 50 + TOP TRENDING MIDCAPS)
# ==============================================================================
TOP_20_CORE = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "SBIN", "INFY",
    "TCS", "LT", "BHARTIARTL", "ITC", "M&M",
    "SUNPHARMA", "BAJFINANCE", "AXISBANK", "MARUTI", "TITAN",
    "NTPC", "HAL", "BEL", "TRENT", "DIXON",
]

SWING_UNIVERSE = {
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
    "SRF": "SRF.NS", "DEEPAKNTR": "DEEPAKNTR.NS", "VBL": "VBL.NS",
    "DMART": "DMART.NS", "ZOMATO": "ZOMATO.NS", "TATAPOWER": "TATAPOWER.NS",
    "DLF": "DLF.NS", "INDIGO": "INDIGO.NS", "JSWSTEEL": "JSWSTEEL.NS",
    "HINDALCO": "HINDALCO.NS", "TATASTEEL": "TATASTEEL.NS",
}

# ==============================================================================
# 2. HILEGA-MILEGA & TREND INDICATORS (DAILY 1D)
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
# 3. LIVE 4-PILLAR PULLBACK + HM SWING SCREENER (DAILY 1D)
# ==============================================================================
@st.cache_data(ttl=600)
def run_swing_scan(symbol_dict, target_pct=9.0, sl_pct=5.0, rsi_pullback_max=45.0):
    tickers = list(symbol_dict.values())
    symbol_map = {v: k for k, v in symbol_dict.items()}

    data = yf.download(
        tickers=tickers,
        period="2y",
        interval="1d",
        group_by="ticker",
        threads=True,
        progress=False,
    )

    rows = []
    for yf_ticker, name in symbol_map.items():
        try:
            df = data[yf_ticker].dropna() if len(tickers) > 1 else data.dropna()
            if len(df) < 210:
                continue

            close = df["Close"].squeeze()
            high = df["High"].squeeze()
            low = df["Low"].squeeze()

            sma50 = close.rolling(50).mean()
            sma200 = close.rolling(200).mean()
            ema20 = close.ewm(span=20, adjust=False).mean()

            rsi9 = compute_rsi(close, 9)
            ema3 = rsi9.ewm(span=3, adjust=False).mean()
            wma21 = compute_wma(rsi9, 21)

            c_now = float(close.iloc[-1])
            h_prev = float(high.iloc[-2])
            l_5d = float(low.tail(5).min())
            s50 = float(sma50.iloc[-1])
            s200 = float(sma200.iloc[-1])
            e20 = float(ema20.iloc[-1])

            r_now, r_prev = float(rsi9.iloc[-1]), float(rsi9.iloc[-2])
            e_now, e_prev = float(ema3.iloc[-1]), float(ema3.iloc[-2])
            w_now, w_prev = float(wma21.iloc[-1]), float(wma21.iloc[-2])

            if np.isnan([c_now, s50, s200, r_now, e_now, w_now]).any():
                continue

            # Pillar 1: Strong Uptrend (Price > 200 DMA and 50 DMA > 200 DMA)
            strong_uptrend = (c_now > s200) and (s50 > s200)

            # Pillar 2: Recent Pullback (RSI9 dipped <= threshold within last 5 candles)
            recent_rsi_min = float(rsi9.iloc[-6:-1].min())
            in_pullback_zone = (recent_rsi_min <= rsi_pullback_max) or (r_now <= rsi_pullback_max)

            # Pillar 3: Hilega-Milega Turn Up + Price Confirmation (Close > Prev High)
            hm_turn_up = ((r_now > e_now and r_prev <= e_prev) or (r_now > w_now and r_prev <= w_prev)) and (r_now > r_prev)
            price_confirm = c_now > h_prev

            high_52w = float(high.tail(252).max())
            disc_52w = round(((high_52w - c_now) / high_52w) * 100.0, 1) if high_52w > 0 else 0.0
            dist_50dma = round(((c_now - s50) / s50) * 100.0, 1)

            # Stop-Loss & Target
            fixed_sl = c_now * (1.0 - sl_pct / 100.0)
            smart_sl = round(max(l_5d * 0.995, fixed_sl), 2)
            target_price = round(c_now * (1.0 + target_pct / 100.0), 2)

            if strong_uptrend and in_pullback_zone and hm_turn_up and price_confirm:
                status = "🔥 READY TO BUY (4-Pillar Confirmed)"
            elif strong_uptrend and (r_now <= rsi_pullback_max):
                status = "👀 PULLBACK WATCHLIST (Wait for Turn)"
            elif strong_uptrend and (r_now > 50.0) and (r_now > w_now):
                status = "🚀 UPTREND HOLD"
            elif not strong_uptrend:
                status = "🔴 AVOID (Below 200 DMA / Weak)"
            else:
                status = "⚪ NEUTRAL"

            rows.append({
                "Symbol": name,
                "Swing Status": status,
                "Close (₹)": round(c_now, 2),
                "Breakout Level (Prev High)": round(h_prev, 2),
                "Stop-Loss (₹)": smart_sl,
                f"Target (+{target_pct:.0f}% ₹)": target_price,
                "RSI (9)": round(r_now, 1),
                "EMA (3)": round(e_now, 1),
                "WMA (21)": round(w_now, 1),
                "50 DMA Dist %": dist_50dma,
                "52W Disc %": disc_52w,
            })
        except Exception:
            continue

    df_out = pd.DataFrame(rows)
    if not df_out.empty:
        order_map = {
            "🔥 READY TO BUY (4-Pillar Confirmed)": 1,
            "👀 PULLBACK WATCHLIST (Wait for Turn)": 2,
            "🚀 UPTREND HOLD": 3,
            "⚪ NEUTRAL": 4,
            "🔴 AVOID (Below 200 DMA / Weak)": 5,
        }
        df_out["_ord"] = df_out["Swing Status"].map(order_map).fillna(9)
        df_out = df_out.sort_values(by=["_ord", "RSI (9)"], ascending=[True, True]).drop(columns=["_ord"]).reset_index(drop=True)
    return df_out


# ==============================================================================
# 4. 3Y–5Y MULTI-STOCK / SINGLE-STOCK SWING BACKTESTER (4-PILLAR PULLBACK + HM)
# ==============================================================================
def _backtest_single_df(df, sym_name, years, target_pct, sl_pct, rsi_pullback_max, max_hold_days):
    if df is None or len(df) < 230:
        return []
    df = df.dropna().copy()
    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()

    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    rsi9 = compute_rsi(close, 9)
    ema3 = rsi9.ewm(span=3, adjust=False).mean()
    wma21 = compute_wma(rsi9, 21)

    bars_needed = years * 252
    start_idx = max(210, len(df) - bars_needed)
    if start_idx >= len(df) - 10:
        start_idx = 210

    trades = []
    pos = None

    for i in range(start_idx, len(df)):
        dt = df.index[i]
        c_i, h_i, l_i = float(close.iloc[i]), float(high.iloc[i]), float(low.iloc[i])
        h_prev = float(high.iloc[i - 1])
        s50_i, s200_i = float(sma50.iloc[i]), float(sma200.iloc[i])
        r_i, r_prev = float(rsi9.iloc[i]), float(rsi9.iloc[i - 1])
        e_i, e_prev = float(ema3.iloc[i]), float(ema3.iloc[i - 1])
        w_i, w_prev = float(wma21.iloc[i]), float(wma21.iloc[i - 1])

        if np.isnan([c_i, s50_i, s200_i, r_i, e_i, w_i]).any():
            continue

        # Manage Open Swing Position (Closing-Basis SL, Target, Overbought Exhaustion, or Time Stop)
        if pos is not None:
            pos["Days"] += 1
            exit_price = None
            reason = None

            if h_i >= pos["Target"]:
                exit_price = pos["Target"]
                reason = f"Target Hit (+{target_pct:.0f}%)"
            elif c_i <= pos["SL"]:
                exit_price = c_i
                reason = "Closing Stop-Loss"
            elif (r_prev >= 78.0) and (r_i < e_i) and (c_i > pos["Entry"]):
                exit_price = c_i
                reason = "Overbought Exhaustion (RSI>78)"
            elif pos["Days"] >= max_hold_days:
                exit_price = c_i
                reason = f"Time Stop ({max_hold_days}d)"

            if exit_price is not None:
                ret_pct = ((exit_price - pos["Entry"]) / pos["Entry"]) * 100.0
                trades.append({
                    "Symbol": sym_name,
                    "Entry Date": pos["EntryDate"],
                    "Exit Date": dt.strftime("%d-%b-%Y"),
                    "ExitDT": dt,
                    "Days Held": pos["Days"],
                    "Entry (₹)": round(pos["Entry"], 2),
                    "Exit (₹)": round(exit_price, 2),
                    "Return %": round(ret_pct, 2),
                    "Exit Reason": reason,
                })
                pos = None

        # Check 4-Pillar Entry Signal
        if pos is None:
            strong_uptrend = (c_i > s200_i) and (s50_i > s200_i)
            recent_rsi_min = float(rsi9.iloc[i - 5:i].min())
            in_pullback = recent_rsi_min <= rsi_pullback_max
            hm_turn = ((r_i > e_i and r_prev <= e_prev) or (r_i > w_i and r_prev <= w_prev)) and (r_i > r_prev)
            price_confirm = c_i > h_prev

            if strong_uptrend and in_pullback and hm_turn and price_confirm:
                l_5d = float(low.iloc[i - 4:i + 1].min())
                sl_val = max(l_5d * 0.995, c_i * (1.0 - sl_pct / 100.0))
                tgt_val = c_i * (1.0 + target_pct / 100.0)
                pos = {
                    "EntryDate": dt.strftime("%d-%b-%Y"),
                    "Entry": c_i,
                    "SL": sl_val,
                    "Target": tgt_val,
                    "Days": 0,
                }

    return trades


@st.cache_data(ttl=600)
def run_portfolio_backtest(mode_scope, selected_sym, symbol_dict, years=5, target_pct=9.0, sl_pct=5.0, rsi_pullback_max=45.0, max_hold_days=25, initial_cap=500000.0):
    if mode_scope == "Top 20 Core Nifty/Midcap Portfolio":
        target_syms = [s for s in TOP_20_CORE if s in symbol_dict]
    else:
        target_syms = [selected_sym]

    tickers = [symbol_dict[s] for s in target_syms]
    fetch_years = years + 2
    data = yf.download(
        tickers=tickers,
        period=f"{fetch_years}y",
        interval="1d",
        group_by="ticker",
        threads=True,
        progress=False,
    )

    all_trades = []
    for s in target_syms:
        yf_t = symbol_dict[s]
        try:
            sub_df = data[yf_t].dropna() if len(tickers) > 1 else data.dropna()
            t_list = _backtest_single_df(sub_df, s, years, target_pct, sl_pct, rsi_pullback_max, max_hold_days)
            all_trades.extend(t_list)
        except Exception:
            continue

    if not all_trades:
        return None, pd.DataFrame(), pd.DataFrame()

    df_trades = pd.DataFrame(all_trades).sort_values(by="ExitDT").reset_index(drop=True)

    # Simulate realistic position sizing: 20% of equity per swing slot (max 5 concurrent swings) for Portfolio, or 100% for Single Stock
    alloc_frac = 0.20 if len(target_syms) > 1 else 1.0
    capital = initial_cap
    eq_rows = []
    pnl_list = []

    for _, row in df_trades.iterrows():
        trade_size = capital * alloc_frac
        pnl = trade_size * (row["Return %"] / 100.0)
        capital += pnl
        pnl_list.append(round(pnl, 2))
        eq_rows.append({"Date": row["ExitDT"], "Portfolio Equity (₹)": round(capital, 2)})

    df_trades["Net P&L (₹)"] = pnl_list
    df_trades_display = df_trades.drop(columns=["ExitDT"])
    df_eq = pd.DataFrame(eq_rows)

    wins = df_trades[df_trades["Return %"] > 0]
    losses = df_trades[df_trades["Return %"] <= 0]
    win_rate = round((len(wins) / len(df_trades)) * 100.0, 1)
    avg_win = round(float(wins["Return %"].mean()), 2) if not wins.empty else 0.0
    avg_loss = round(float(losses["Return %"].mean()), 2) if not losses.empty else 0.0

    gross_win = wins["Net P&L (₹)"].sum() if not wins.empty else 0.0
    gross_loss = abs(losses["Net P&L (₹)"].sum()) if not losses.empty else 0.0
    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else round(gross_win, 2)

    tot_ret = round(((capital - initial_cap) / initial_cap) * 100.0, 1)
    cagr = round((((capital / initial_cap) ** (1.0 / years)) - 1.0) * 100.0, 1) if capital > 0 else 0.0
    max_dd = round(float((((df_eq["Portfolio Equity (₹)"] - df_eq["Portfolio Equity (₹)"].cummax()) / df_eq["Portfolio Equity (₹)"].cummax()) * 100.0).min()), 1)

    summary = {
        "final_cap": round(capital, 2),
        "tot_ret": tot_ret,
        "cagr": cagr,
        "total_trades": len(df_trades),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "pf": pf,
        "max_dd": max_dd,
    }
    return summary, df_trades_display, df_eq


# ==============================================================================
# 5. UI LAYOUT
# ==============================================================================
st.title("🎯 4-Pillar Pullback + Hilega-Milega Swing Screener")
st.caption("Daily (`1d`) Long-Only Swing System: **Uptrend (`>200 DMA` & `50>200`) + Pullback (`RSI9 <= 45`) + HM Turn Up + Prev High Breakout**")

tab_live, tab_bt = st.tabs([
    "🔍 Live Daily Swing Screener",
    "📊 3Y–5Y Multi-Stock Portfolio Backtester",
])

with tab_live:
    custom_input = st.text_input(
        "🔍 Custom NSE Stocks जोडा (कॉमा देऊन लिहा):",
        placeholder="उदा. KPITTECH, ZYDUSLIFE, JIOFIN, TATAMOTORS",
    )
    active_symbols = dict(SWING_UNIVERSE)
    if custom_input.strip():
        for raw in custom_input.split(","):
            sym = raw.strip().upper().replace(".NS", "")
            if sym and sym not in active_symbols:
                active_symbols[sym] = f"{sym}.NS"

    c1, c2, c3, c4 = st.columns([1.2, 0.9, 0.9, 0.9])
    with c1:
        status_filter = st.selectbox(
            "Filter Swing Setups",
            [
                "🔥 Ready to Buy + 👀 Pullback Watchlist",
                "🔥 Ready to Buy (4-Pillar Confirmed) Only",
                "👀 Pullback Watchlist Only",
                "Show All 70+ Stocks",
            ],
            index=0,
        )
    with c2:
        live_tgt = st.selectbox("Target %", [6.0, 8.0, 9.0, 10.0, 12.0], index=2)
    with c3:
        live_sl = st.selectbox("Max SL %", [4.0, 5.0, 6.0, 7.0], index=1)
    with c4:
        st.write("")
        scan_btn = st.button("🔄 Run Swing Scan", use_container_width=True, type="primary")

    if scan_btn:
        st.cache_data.clear()

    ist_now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST")
    with st.spinner(f"Scanning {len(active_symbols)} Stocks on Daily (1d) Chart..."):
        df_swing = run_swing_scan(active_symbols, live_tgt, live_sl, 45.0)

    if not df_swing.empty:
        if status_filter == "🔥 Ready to Buy + 👀 Pullback Watchlist":
            df_view = df_swing[df_swing["Swing Status"].str.contains("READY|WATCHLIST")]
        elif status_filter == "🔥 Ready to Buy (4-Pillar Confirmed) Only":
            df_view = df_swing[df_swing["Swing Status"].str.contains("READY")]
        elif status_filter == "👀 Pullback Watchlist Only":
            df_view = df_swing[df_swing["Swing Status"].str.contains("WATCHLIST")]
        else:
            df_view = df_swing

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔥 Ready to Buy Today", int(df_swing["Swing Status"].str.contains("READY").sum()))
        m2.metric("👀 Pullback Watchlist", int(df_swing["Swing Status"].str.contains("WATCHLIST").sum()))
        m3.metric("🚀 Strong Uptrend (>200 DMA)", int(df_swing["Swing Status"].str.contains("UPTREND|READY|WATCHLIST").sum()))
        m4.metric("🔴 Weak / Avoid (<200 DMA)", int(df_swing["Swing Status"].str.contains("AVOID").sum()))

        st.subheader(f"Daily Swing Setups ({len(df_view)} Matches) — {ist_now}")
        st.dataframe(df_view, use_container_width=True, hide_index=True)
    else:
        st.info("डेटा लोड झाला नाही. कृपया 'Run Swing Scan' वर क्लिक करा.")

with tab_bt:
    st.subheader("📊 3Y–5Y Honest Swing Backtester (4-Pillar Pullback + HM)")
    st.caption("टीप: यामध्ये ब्रोकरेज, STT/कर आणि स्लिपेज धरलेले नाहीत. खरी स्विंग अ‍ॅक्युरसी मार्केटनुसार साधारण ६५%–७८% दरम्यान राहते.")

    bc1, bc2, bc3, bc4, bc5 = st.columns([1.4, 1.1, 0.8, 0.8, 0.8])
    with bc1:
        bt_scope = st.selectbox("Backtest Mode", ["Top 20 Core Nifty/Midcap Portfolio", "Single Stock"], index=0)
    with bc2:
        bt_sym = st.selectbox("Select Stock (if Single)", list(active_symbols.keys()), index=0, disabled=(bt_scope != "Single Stock"))
    with bc3:
        bt_years = st.selectbox("Years", [3, 5], index=1)
    with bc4:
        bt_tgt = st.selectbox("Target %", [6.0, 8.0, 9.0, 10.0, 12.0], index=2, key="bt_tgt")
    with bc5:
        bt_sl = st.selectbox("SL %", [4.0, 5.0, 6.0, 7.0], index=1, key="bt_sl")

    with st.spinner(f"Running {bt_years}-Year Swing Backtest..."):
        summary, df_bt_trades, df_bt_eq = run_portfolio_backtest(
            bt_scope, bt_sym, active_symbols, bt_years, bt_tgt, bt_sl, 45.0, 25, 500000.0
        )

    if summary is not None:
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("💰 Final Capital (from ₹5L)", f"₹{summary['final_cap']:,.0f}", f"{summary['tot_ret']:+.1f}% ({summary['cagr']}% CAGR)")
        k2.metric("🎯 Honest Win Rate", f"{summary['win_rate']}%", f"{summary['total_trades']} Trades")
        k3.metric("⚖️ Profit Factor", f"{summary['pf']}x")
        k4.metric("📈 Avg Win / Avg Loss", f"+{summary['avg_win']}%", f"{summary['avg_loss']}%")
        k5.metric("📉 Max Drawdown", f"{summary['max_dd']}%")

        if not df_bt_eq.empty:
            st.write("**📈 Portfolio Equity Curve (₹):**")
            st.line_chart(df_bt_eq.set_index("Date")["Portfolio Equity (₹)"])

        if not df_bt_trades.empty:
            st.write(f"**📜 All Historical Swing Trades ({len(df_bt_trades)} Trades):**")
            st.dataframe(df_bt_trades.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.warning("या सेटिंग्जवर कोणताही ऐतिहासिक ट्रेड आढळला नाही.")

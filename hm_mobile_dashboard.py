import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import pytz

st.set_page_config(page_title="NSE F&O Screener + Paper Trader + 90d Backtester", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

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

INITIAL_CAPITAL = 500000.0
PORTFOLIO_FILE = "paper_portfolio_state.json"

def load_portfolio():
    if "paper_portfolio" not in st.session_state:
        if os.path.exists(PORTFOLIO_FILE):
            try:
                with open(PORTFOLIO_FILE, "r") as f:
                    st.session_state.paper_portfolio = json.load(f)
                    return
            except Exception:
                pass
        st.session_state.paper_portfolio = {
            "cash": INITIAL_CAPITAL,
            "realized_pnl": 0.0,
            "positions": [],
            "history": [],
        }

def save_portfolio():
    try:
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump(st.session_state.paper_portfolio, f)
    except Exception:
        pass

load_portfolio()

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

def compute_atr_series(df, length=14):
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    close = df["Close"].squeeze()
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / length, min_periods=length, adjust=False).mean()

def compute_atr(df, length=14):
    atr_s = compute_atr_series(df, length)
    val = float(atr_s.iloc[-1])
    close = df["Close"].squeeze()
    return round(val, 2) if not np.isnan(val) else round(float(close.iloc[-1]) * 0.005, 2)

def compute_intraday_vwap_and_orb(df):
    try:
        idx = df.index
        dates = idx.tz_convert("Asia/Kolkata").date if idx.tz is not None else idx.date
        day_df = df.loc[dates == dates[-1]]

        tp = (day_df["High"].squeeze() + day_df["Low"].squeeze() + day_df["Close"].squeeze()) / 3.0
        vol = day_df["Volume"].squeeze()
        cum_vol = vol.cumsum()
        vwap_val = float((tp * vol).cumsum().iloc[-1] / cum_vol.iloc[-1]) if float(cum_vol.iloc[-1]) > 0 else float(tp.mean())

        orb_high = float(day_df["High"].squeeze().iloc[0])
        orb_low = float(day_df["Low"].squeeze().iloc[0])

        all_vol = df["Volume"].squeeze()
        avg_vol_20 = float(all_vol.iloc[-21:-1].mean()) if len(all_vol) > 21 else float(all_vol.mean())
        curr_vol = float(all_vol.iloc[-1])
        rvol = round(curr_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0
        return round(vwap_val, 2), round(orb_high, 2), round(orb_low, 2), rvol
    except Exception:
        c_last = float(df["Close"].squeeze().iloc[-1])
        h_last = float(df["High"].squeeze().iloc[-1])
        l_last = float(df["Low"].squeeze().iloc[-1])
        return round(c_last, 2), round(h_last, 2), round(l_last, 2), 1.0

@st.cache_data(ttl=45)
def get_live_spot_price(symbol_name):
    yf_ticker = WATCHLIST.get(symbol_name, "RELIANCE.NS")
    try:
        df = yf.download(tickers=yf_ticker, period="5d", interval="5m", progress=False)
        if df is not None and not df.empty:
            close = df["Close"].squeeze()
            high = df["High"].squeeze()
            low = df["Low"].squeeze()
            rsi9 = compute_rsi(close, 9)
            wma21 = compute_wma(rsi9, 21)
            atr14 = compute_atr(df, 14)
            vwap_val, orb_h, orb_l, rvol = compute_intraday_vwap_and_orb(df)
            spot = round(float(close.iloc[-1]), 2)
            l_now = float(low.iloc[-1])
            h_now = float(high.iloc[-1])

            smart_long_sl = round(min(l_now, vwap_val) - (0.25 * atr14), 2)
            smart_short_sl = round(max(h_now, vwap_val) + (0.25 * atr14), 2)

            return {
                "spot": spot,
                "high": round(h_now, 2),
                "low": round(l_now, 2),
                "vwap": vwap_val,
                "atr": atr14,
                "smart_long_sl": smart_long_sl,
                "smart_short_sl": smart_short_sl,
                "rsi9": round(float(rsi9.iloc[-1]), 2),
                "wma21": round(float(wma21.iloc[-1]), 2),
            }
    except Exception:
        pass
    return {
        "spot": 0.0, "high": 0.0, "low": 0.0, "vwap": 0.0, "atr": 1.0,
        "smart_long_sl": 0.0, "smart_short_sl": 0.0, "rsi9": 50.0, "wma21": 50.0
    }

@st.cache_data(ttl=120)
def run_90_day_backtest(symbol_name, tf, strat_name, risk_pct, avoid_midday_chop=True):
    """Simulates 90-day historical trades (or 60d max on 15m) with Smart SL, 1:1.5 Breakeven Trail & 1:3 Target."""
    yf_ticker = WATCHLIST.get(symbol_name, "^NSEI")
    # Yahoo Finance allows max 60d for 15m, and 90d+ for 1h and 1d
    period_str = "60d" if tf == "15m" else "90d"
    df = yf.download(tickers=yf_ticker, period=period_str, interval=tf, progress=False)
    if df is None or len(df) < 40:
        return None, None, None

    df = df.dropna().copy()
    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()
    vol = df["Volume"].squeeze()

    rsi9 = compute_rsi(close, 9)
    ema3 = rsi9.ewm(span=3, adjust=False).mean()
    wma21 = compute_wma(rsi9, 21)
    atr14 = compute_atr_series(df, 14).bfill().fillna(close * 0.005)
    vol_avg20 = vol.rolling(20).mean().bfill()

    idx = df.index
    if idx.tz is not None:
        ist_idx = idx.tz_convert("Asia/Kolkata")
    else:
        ist_idx = idx

    # Compute daily rolling VWAP & Opening Range High/Low
    dates = pd.Series(ist_idx.date, index=df.index)
    tp = (high + low + close) / 3.0
    tp_vol = tp * vol
    cum_tp_vol = tp_vol.groupby(dates).cumsum()
    cum_vol = vol.groupby(dates).cumsum().replace(0, np.nan)
    vwap_s = (cum_tp_vol / cum_vol).fillna(close)
    orb_high_s = high.groupby(dates).transform("first")
    orb_low_s = low.groupby(dates).transform("first")

    is_hybrid = "Hybrid" in strat_name
    is_index = symbol_name in ["NIFTY 50", "BANK NIFTY", "FINNIFTY"]

    capital = INITIAL_CAPITAL
    equity_curve = []
    trades = []
    pos = None

    for i in range(25, len(df)):
        t_stamp = ist_idx[i]
        c_i, h_i, l_i = float(close.iloc[i]), float(high.iloc[i]), float(low.iloc[i])
        c_prev, h_prev, l_prev = float(close.iloc[i - 1]), float(high.iloc[i - 1]), float(low.iloc[i - 1])
        r_i, r_prev = float(rsi9.iloc[i]), float(rsi9.iloc[i - 1])
        e_i = float(ema3.iloc[i])
        w_i, w_prev = float(wma21.iloc[i]), float(wma21.iloc[i - 1])
        atr_i = float(atr14.iloc[i])
        vwap_i = float(vwap_s.iloc[i])
        orb_h_i, orb_l_i = float(orb_high_s.iloc[i]), float(orb_low_s.iloc[i])
        v_i, v_avg = float(vol.iloc[i]), float(vol_avg20.iloc[i])
        rvol_i = (v_i / v_avg) if v_avg > 0 else 1.0

        if np.isnan([r_i, e_i, w_i, c_i]).any():
            continue

        # 1. Manage Open Position if active
        if pos is not None:
            exit_price = None
            exit_reason = None

            if pos["Side"] == "LONG":
                if l_i <= pos["SL"]:
                    exit_price = pos["SL"]
                    exit_reason = "Stop-Loss / Trail SL" if pos["SL"] < pos["Entry"] else "Breakeven Trail SL"
                elif h_i >= pos["T2"]:
                    exit_price = pos["T2"]
                    exit_reason = "Target 2 (1:3) Hit"
                elif (r_i < w_i) and (r_prev >= w_prev):
                    exit_price = c_i
                    exit_reason = "HM Top / Reversal Exit"
                elif h_i >= pos["T1"] and pos["SL"] < pos["Entry"]:
                    pos["SL"] = pos["Entry"]  # Auto-trail SL to Breakeven
            else:
                if h_i >= pos["SL"]:
                    exit_price = pos["SL"]
                    exit_reason = "Stop-Loss / Trail SL" if pos["SL"] > pos["Entry"] else "Breakeven Trail SL"
                elif l_i <= pos["T2"]:
                    exit_price = pos["T2"]
                    exit_reason = "Target 2 (1:3) Hit"
                elif (r_i > w_i) and (r_prev <= w_prev):
                    exit_price = c_i
                    exit_reason = "HM Bottom / Reversal Exit"
                elif l_i <= pos["T1"] and pos["SL"] > pos["Entry"]:
                    pos["SL"] = pos["Entry"]  # Auto-trail SL to Breakeven

            if exit_price is not None:
                pnl = (exit_price - pos["Entry"]) * pos["Qty"] if pos["Side"] == "LONG" else (pos["Entry"] - exit_price) * pos["Qty"]
                capital += pnl
                trades.append({
                    "Entry Time": pos["EntryTime"],
                    "Exit Time": t_stamp.strftime("%d-%b %H:%M"),
                    "Symbol": symbol_name,
                    "Side": pos["Side"],
                    "Qty": pos["Qty"],
                    "Entry (₹)": round(pos["Entry"], 2),
                    "Exit (₹)": round(exit_price, 2),
                    "Exit Reason": exit_reason,
                    "Net P&L (₹)": round(pnl, 2),
                    "Balance (₹)": round(capital, 2),
                })
                pos = None

        # 2. Check for New Entry Signal if flat
        if pos is None:
            if avoid_midday_chop and tf in ["5m", "15m"]:
                hr_min = t_stamp.hour * 60 + t_stamp.minute
                if 690 <= hr_min <= 795:  # 11:30 AM to 1:15 PM IST
                    equity_curve.append({"Time": t_stamp, "Equity (₹)": round(capital, 2)})
                    continue

            buy_trig, short_trig = False, False
            if is_hybrid:
                vol_ok = (rvol_i >= 1.2) or is_index or (tf == "1d")
                if (c_i >= vwap_i) and (r_i > 55.0) and (r_i > w_i) and (r_i >= e_i) and ((c_i > orb_h_i and vol_ok) or (c_i > h_prev)):
                    buy_trig = True
                elif (c_i <= vwap_i) and (r_i < 45.0) and (r_i < w_i) and (r_i <= e_i) and ((c_i < orb_l_i and vol_ok) or (c_i < l_prev)):
                    short_trig = True
            else:
                if ((r_i > w_i and r_prev <= w_prev) or (r_i > 50.0 and r_prev <= 50.0 and r_i > w_i)) and (r_i >= e_i):
                    buy_trig = True
                elif ((r_i < w_i and r_prev >= w_prev) or (r_i < 50.0 and r_prev >= 50.0 and r_i < w_i)) and (r_i <= e_i):
                    short_trig = True

            if buy_trig:
                sl_val = min(l_i, vwap_i if is_hybrid else l_i) - (0.25 * atr_i)
                risk_sh = max(abs(c_i - sl_val), c_i * 0.003)
                max_loss_rs = capital * (risk_pct / 100.0)
                qty = max(1, min(int(max_loss_rs // risk_sh), int(capital // c_i)))
                pos = {
                    "EntryTime": t_stamp.strftime("%d-%b %H:%M"),
                    "Side": "LONG",
                    "Qty": qty,
                    "Entry": c_i,
                    "SL": sl_val,
                    "T1": c_i + (1.5 * risk_sh),
                    "T2": c_i + (3.0 * risk_sh),
                }
            elif short_trig:
                sl_val = max(h_i, vwap_i if is_hybrid else h_i) + (0.25 * atr_i)
                risk_sh = max(abs(sl_val - c_i), c_i * 0.003)
                max_loss_rs = capital * (risk_pct / 100.0)
                qty = max(1, min(int(max_loss_rs // risk_sh), int(capital // c_i)))
                pos = {
                    "EntryTime": t_stamp.strftime("%d-%b %H:%M"),
                    "Side": "SHORT",
                    "Qty": qty,
                    "Entry": c_i,
                    "SL": sl_val,
                    "T1": c_i - (1.5 * risk_sh),
                    "T2": c_i - (3.0 * risk_sh),
                }

        equity_curve.append({"Time": t_stamp, "Equity (₹)": round(capital, 2)})

    df_trades = pd.DataFrame(trades)
    df_eq = pd.DataFrame(equity_curve)
    if df_trades.empty:
        summary = {
            "final_capital": capital, "net_pnl": 0.0, "return_pct": 0.0,
            "total_trades": 0, "win_rate": 0.0, "profit_factor": 0.0, "max_dd_pct": 0.0
        }
        return summary, df_trades, df_eq

    wins = df_trades[df_trades["Net P&L (₹)"] > 0]
    losses = df_trades[df_trades["Net P&L (₹)"] <= 0]
    win_rate = round((len(wins) / len(df_trades)) * 100, 1)
    gross_win = wins["Net P&L (₹)"].sum() if not wins.empty else 0.0
    gross_loss = abs(losses["Net P&L (₹)"].sum()) if not losses.empty else 0.0
    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else round(gross_win, 2)

    eq_series = df_eq["Equity (₹)"]
    roll_max = eq_series.cummax()
    dd_pct = ((eq_series - roll_max) / roll_max) * 100.0
    max_dd = round(float(dd_pct.min()), 2)

    net_pnl = round(capital - INITIAL_CAPITAL, 2)
    summary = {
        "final_capital": round(capital, 2),
        "net_pnl": net_pnl,
        "return_pct": round((net_pnl / INITIAL_CAPITAL) * 100, 2),
        "total_trades": len(df_trades),
        "win_rate": win_rate,
        "profit_factor": pf,
        "max_dd_pct": max_dd,
    }
    return summary, df_trades, df_eq

@st.cache_data(ttl=120)
def fetch_and_scan(tf, strat):
    tickers = list(WATCHLIST.values())
    symbol_map = {v: k for k, v in WATCHLIST.items()}
    period = "5d" if tf in ["5m", "15m"] else ("1mo" if tf == "1h" else "6mo")
    data = yf.download(tickers=tickers, period=period, interval=tf, group_by="ticker", threads=True, progress=False)

    rows = []
    is_hybrid = strat.startswith("🔥")

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
            atr14 = compute_atr(df, 14)

            r_now, r_prev = float(rsi9.iloc[-1]), float(rsi9.iloc[-2])
            e_now = float(ema3.iloc[-1])
            w_now, w_prev = float(wma21.iloc[-1]), float(wma21.iloc[-2])
            c_now, h_now, l_now = float(close.iloc[-1]), float(high.iloc[-1]), float(low.iloc[-1])
            h_prev, l_prev = float(high.iloc[-2]), float(low.iloc[-2])
            spread = abs(r_now - w_now)

            if np.isnan([r_now, e_now, w_now]).any():
                continue

            vwap_val, orb_high, orb_low, rvol = compute_intraday_vwap_and_orb(df)
            is_index = name in ["NIFTY 50", "BANK NIFTY", "FINNIFTY"]
            vol_spike = (rvol >= 1.3) or is_index

            bull_smart_sl = round(min(l_now, vwap_val if is_hybrid else l_now) - (0.25 * atr14), 2)
            bear_smart_sl = round(max(h_now, vwap_val if is_hybrid else h_now) + (0.25 * atr14), 2)

            is_bull_sig = False

            if is_hybrid:
                hm_bull = (r_now > 55.0) and (r_now > w_now) and (r_now >= e_now)
                hm_bear = (r_now < 45.0) and (r_now < w_now) and (r_now <= e_now)
                above_vwap = c_now >= vwap_val
                below_vwap = c_now <= vwap_val

                if above_vwap and hm_bull and (c_now > orb_high) and vol_spike:
                    sig, is_bull_sig = "🔥 HYBRID SUPER BUY (ORB+VWAP+Vol)", True
                elif above_vwap and hm_bull and (c_now > h_prev):
                    sig, is_bull_sig = "🚀 HYBRID VWAP BUY (>55 RSI)", True
                elif below_vwap and hm_bear and (c_now < orb_low) and vol_spike:
                    sig, is_bull_sig = "💥 HYBRID SUPER SHORT (ORB+VWAP+Vol)", False
                elif below_vwap and hm_bear and (c_now < l_prev):
                    sig, is_bull_sig = "🔴 HYBRID VWAP SHORT (<45 RSI)", False
                elif (r_now < w_now) and (r_prev >= w_prev):
                    sig, is_bull_sig = "🟠 TOP / EXIT LONG", False
                else:
                    zone = "Above VWAP & Bullish" if (above_vwap and r_now > w_now) else "Neutral / Chop Zone"
                    sig = f"⚪ {zone}"
                    is_bull_sig = (above_vwap and r_now > w_now)
            else:
                if (r_now > w_now) and (r_prev <= w_prev) and (r_now >= e_now):
                    sig, is_bull_sig = "🟢 BOTTOM BUY", True
                elif (r_now > 50.0) and (r_prev <= 50.0) and (r_now > w_now) and (r_now >= e_now):
                    sig, is_bull_sig = "🚀 BUY >50", True
                elif (r_now < w_now) and (r_prev >= w_prev) and (r_now <= e_now):
                    sig, is_bull_sig = "🟠 TOP / EXIT", False
                elif (r_now < 50.0) and (r_prev >= 50.0) and (r_now < w_now) and (r_now <= e_now):
                    sig, is_bull_sig = "🔴 SHORT <50", False
                else:
                    zone = "Bullish Hold (>WMA21)" if r_now > w_now else "Bearish Hold (<WMA21)"
                    sig = f"⚪ {zone}"
                    is_bull_sig = (r_now > w_now)

            if is_bull_sig:
                sl = bull_smart_sl
                risk = max(abs(c_now - sl), 0.5)
                t1 = round(c_now + (1.5 * risk), 2)
                t2 = round(c_now + (3.0 * risk), 2)
            else:
                sl = bear_smart_sl
                risk = max(abs(sl - c_now), 0.5)
                t1 = round(c_now - (1.5 * risk), 2)
                t2 = round(c_now - (3.0 * risk), 2)

            rows.append({
                "Symbol": name,
                "Signal": sig,
                "Spot (₹)": round(c_now, 2),
                "Smart SL (₹)": sl,
                "Target 1 (1:1.5)": t1,
                "Target 2 (1:3)": t2,
                "VWAP (₹)": vwap_val,
                "Vol Spike": f"{rvol}x",
                "RSI (9)": round(r_now, 2),
                "WMA (21)": round(w_now, 2),
                "Spread": round(spread, 2),
            })
        except Exception:
            continue

    df_out = pd.DataFrame(rows)
    if not df_out.empty:
        df_out = df_out.sort_values(by="Spread", ascending=False).reset_index(drop=True)
    return df_out

st.title("📈 Live NSE F&O Screener, ₹5L Paper Trader & 90d Backtester")

# Live Market Regime Top Banner (Nifty 50 & Bank Nifty Filter)
nifty_spot = get_live_spot_price("NIFTY 50")
bnf_spot = get_live_spot_price("BANK NIFTY")
n_bias = "🟢 BULLISH (>VWAP & RSI>50)" if (nifty_spot["spot"] >= nifty_spot["vwap"] and nifty_spot["rsi9"] >= 50) else ("🔴 BEARISH (<VWAP & RSI<50)" if (nifty_spot["spot"] < nifty_spot["vwap"] and nifty_spot["rsi9"] < 50) else "🟡 SIDEWAYS / MIXED")
b_bias = "🟢 BULLISH (>VWAP & RSI>50)" if (bnf_spot["spot"] >= bnf_spot["vwap"] and bnf_spot["rsi9"] >= 50) else ("🔴 BEARISH (<VWAP & RSI<50)" if (bnf_spot["spot"] < bnf_spot["vwap"] and bnf_spot["rsi9"] < 50) else "🟡 SIDEWAYS / MIXED")
st.caption(
    f"🧭 **Market Regime Filter:**  **NIFTY 50:** ₹{nifty_spot['spot']:,.2f} ({n_bias})   |   "
    f"**BANK NIFTY:** ₹{bnf_spot['spot']:,.2f} ({b_bias})"
)

mode_choice = st.selectbox(
    "Select App Mode / Strategy",
    [
        "🔥 Hybrid Master Screener (VWAP + 15m ORB + Vol + HM)",
        "📈 Hilega-Milega Screener (Classic RSI 9 / EMA 3 / WMA 21)",
        "💼 Paper Trading Terminal + 📊 90-Day Strategy Backtester (₹5,00,000 Limit)",
    ],
    index=0,
)

ist_now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d %b %Y, %I:%M:%S %p IST")

if mode_choice.startswith("💼"):
    tab_paper, tab_bt = st.tabs([
        "💼 Live ₹5,00,000 Paper Trading Terminal",
        "📊 90-Day Historical Strategy Backtester (₹5L Simulation)",
    ])

    # ==========================================================================
    # TAB 1: LIVE ₹5,00,000 PAPER TRADING TERMINAL
    # ==========================================================================
    with tab_paper:
        port = st.session_state.paper_portfolio

        unrealized_pnl = 0.0
        used_margin = 0.0
        remaining_positions = []
        auto_events = []

        for pos in port["positions"]:
            spot_info = get_live_spot_price(pos["Symbol"])
            ltp = spot_info["spot"] if spot_info["spot"] > 0 else pos["EntryPrice"]
            qty = pos["Qty"]
            entry = pos["EntryPrice"]
            sl = pos["StopLoss"]
            t1 = pos.get("Target1", pos.get("Target", entry))
            t2 = pos.get("Target2", pos.get("Target", entry))
            side = pos["Side"]

            if side == "BUY (LONG)":
                pnl = (ltp - entry) * qty
                if ltp <= sl:
                    port["cash"] = round(port["cash"] + pos["Invested"] + pnl, 2)
                    port["realized_pnl"] = round(port["realized_pnl"] + pnl, 2)
                    port["history"].insert(0, {
                        "ExitTime": ist_now, "Symbol": pos["Symbol"], "Side": f"{side} [SL HIT]",
                        "Qty": qty, "Entry (₹)": entry, "Exit Spot (₹)": ltp, "Realized P&L (₹)": round(pnl, 2),
                    })
                    auto_events.append(f"🛑 Stop-Loss Hit on {pos['Symbol']} @ ₹{ltp} (P&L: ₹{pnl:+,.2f})")
                    continue
                elif ltp >= t2:
                    port["cash"] = round(port["cash"] + pos["Invested"] + pnl, 2)
                    port["realized_pnl"] = round(port["realized_pnl"] + pnl, 2)
                    port["history"].insert(0, {
                        "ExitTime": ist_now, "Symbol": pos["Symbol"], "Side": f"{side} [TARGET HIT]",
                        "Qty": qty, "Entry (₹)": entry, "Exit Spot (₹)": ltp, "Realized P&L (₹)": round(pnl, 2),
                    })
                    auto_events.append(f"🎯 Target Hit on {pos['Symbol']} @ ₹{ltp} (P&L: ₹{pnl:+,.2f})")
                    continue
                elif ltp >= t1 and sl < entry:
                    pos["StopLoss"] = entry
                    auto_events.append(f"🛡️ {pos['Symbol']} crossed Target 1! SL auto-trailed to Breakeven (₹{entry}).")
            else:
                pnl = (entry - ltp) * qty
                if ltp >= sl:
                    port["cash"] = round(port["cash"] + pos["Invested"] + pnl, 2)
                    port["realized_pnl"] = round(port["realized_pnl"] + pnl, 2)
                    port["history"].insert(0, {
                        "ExitTime": ist_now, "Symbol": pos["Symbol"], "Side": f"{side} [SL HIT]",
                        "Qty": qty, "Entry (₹)": entry, "Exit Spot (₹)": ltp, "Realized P&L (₹)": round(pnl, 2),
                    })
                    auto_events.append(f"🛑 Stop-Loss Hit on {pos['Symbol']} @ ₹{ltp} (P&L: ₹{pnl:+,.2f})")
                    continue
                elif ltp <= t2:
                    port["cash"] = round(port["cash"] + pos["Invested"] + pnl, 2)
                    port["realized_pnl"] = round(port["realized_pnl"] + pnl, 2)
                    port["history"].insert(0, {
                        "ExitTime": ist_now, "Symbol": pos["Symbol"], "Side": f"{side} [TARGET HIT]",
                        "Qty": qty, "Entry (₹)": entry, "Exit Spot (₹)": ltp, "Realized P&L (₹)": round(pnl, 2),
                    })
                    auto_events.append(f"🎯 Target Hit on {pos['Symbol']} @ ₹{ltp} (P&L: ₹{pnl:+,.2f})")
                    continue
                elif ltp <= t1 and sl > entry:
                    pos["StopLoss"] = entry
                    auto_events.append(f"🛡️ {pos['Symbol']} crossed Target 1! SL auto-trailed to Breakeven (₹{entry}).")

            unrealized_pnl += pnl
            used_margin += pos["Invested"]
            pos_copy = dict(pos)
            pos_copy["Live Spot (₹)"] = round(ltp, 2)
            pos_copy["Live P&L (₹)"] = round(pnl, 2)
            pos_copy["P&L %"] = round((pnl / pos["Invested"]) * 100, 2) if pos["Invested"] > 0 else 0.0
            remaining_positions.append(pos_copy)

        if auto_events:
            port["positions"] = [
                {k: v for k, v in p.items() if k not in ["Live Spot (₹)", "Live P&L (₹)", "P&L %"]}
                for p in remaining_positions
            ]
            save_portfolio()
            for ev in auto_events:
                st.toast(ev)

        total_equity = INITIAL_CAPITAL + port["realized_pnl"] + unrealized_pnl

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💰 Total Portfolio Value", f"₹{total_equity:,.2f}", f"₹{total_equity - INITIAL_CAPITAL:+,.2f}")
        m2.metric("🏦 Available Limit (Cash)", f"₹{port['cash']:,.2f}", f"Used: ₹{used_margin:,.2f}")
        m3.metric("📊 Open Positions P&L", f"₹{unrealized_pnl:+,.2f}")
        m4.metric("✅ Realized Profit / Loss", f"₹{port['realized_pnl']:+,.2f}")

        st.subheader("⚡ Smart Order Ticket (With Auto-SL, Auto-Target & 1% Risk Calculator)")
        c_sym, c_side, c_risk, c_sl, c_t1, c_t2 = st.columns([1.3, 1.0, 1.0, 1.0, 1.0, 1.0])

        with c_sym:
            selected_sym = st.selectbox("Select Stock / Index", list(WATCHLIST.keys()), index=0)

        live_data = get_live_spot_price(selected_sym)
        spot_price = live_data["spot"]

        with c_side:
            order_side = st.selectbox("Order Type", ["BUY (LONG)", "SELL (SHORT)"], index=0)
        with c_risk:
            risk_pct = st.selectbox("Max Risk % of ₹5L", [0.5, 1.0, 1.5, 2.0], index=1)
        with c_sl:
            default_sl = live_data["smart_long_sl"] if order_side == "BUY (LONG)" else live_data["smart_short_sl"]
            stop_loss = st.number_input("Smart Stop-Loss (₹)", value=float(default_sl), step=0.5)

        per_share_risk = max(abs(spot_price - stop_loss), 0.5)
        max_risk_rupees = INITIAL_CAPITAL * (risk_pct / 100.0)
        recommended_qty = max(1, int(max_risk_rupees // per_share_risk))
        max_affordable_qty = max(1, int(port["cash"] // spot_price)) if spot_price > 0 else 1
        safe_default_qty = min(recommended_qty, max_affordable_qty)

        with c_t1:
            def_t1 = round(spot_price + (1.5 * per_share_risk) if order_side == "BUY (LONG)" else spot_price - (1.5 * per_share_risk), 2)
            target_1 = st.number_input("Target 1 (1:1.5 Trail)", value=float(def_t1), step=0.5)
        with c_t2:
            def_t2 = round(spot_price + (3.0 * per_share_risk) if order_side == "BUY (LONG)" else spot_price - (3.0 * per_share_risk), 2)
            target_2 = st.number_input("Target 2 (1:3 Exit)", value=float(def_t2), step=0.5)

        order_qty = st.number_input(
            f"Quantity (Auto-Calculated for {risk_pct}% Risk = ₹{max_risk_rupees:,.0f} Max Loss | Risk/Share: ₹{per_share_risk:.2f})",
            min_value=1,
            value=safe_default_qty,
            step=1,
        )
        order_value = round(spot_price * order_qty, 2)
        actual_max_loss = round(order_qty * per_share_risk, 2)

        st.info(
            f"📌 **{selected_sym} Spot:** **₹{spot_price:,.2f}**  |  **VWAP:** ₹{live_data['vwap']:,.2f}  |  "
            f"**ATR(14):** ₹{live_data['atr']}  |  **RSI(9):** {live_data['rsi9']}  |  "
            f"**Order Value:** **₹{order_value:,.2f}**  |  **Max Loss if SL Hits:** **₹{actual_max_loss:,.2f}**"
        )

        b1, b2, b3 = st.columns([1.3, 1.0, 1.0])
        with b1:
            place_btn = st.button(f"🚀 Place {order_side} ({order_qty} Qty @ ₹{spot_price})", type="primary", use_container_width=True)
        with b2:
            refresh_spot = st.button("🔄 Refresh Spot & Check SL/Targets", use_container_width=True)
        with b3:
            reset_btn = st.button("🗑️ Reset Account to ₹5,00,000", use_container_width=True)

        if refresh_spot:
            st.cache_data.clear()
            st.rerun()

        if reset_btn:
            st.session_state.paper_portfolio = {
                "cash": INITIAL_CAPITAL,
                "realized_pnl": 0.0,
                "positions": [],
                "history": [],
            }
            save_portfolio()
            st.success("Account reset to ₹5,00,000!")
            st.rerun()

        if place_btn:
            if spot_price <= 0:
                st.error("Unable to fetch live spot price right now. Please tap Refresh.")
            elif order_value > port["cash"]:
                st.error(f"Insufficient limit! Order needs ₹{order_value:,.2f}, available cash is ₹{port['cash']:,.2f}.")
            else:
                port["cash"] = round(port["cash"] - order_value, 2)
                port["positions"].append({
                    "Time": ist_now,
                    "Symbol": selected_sym,
                    "Side": order_side,
                    "Qty": int(order_qty),
                    "EntryPrice": spot_price,
                    "StopLoss": stop_loss,
                    "Target1": target_1,
                    "Target2": target_2,
                    "Invested": order_value,
                })
                save_portfolio()
                st.success(f"Placed {order_side}: {order_qty} x {selected_sym} @ ₹{spot_price:,.2f} | Smart SL: ₹{stop_loss} | T1: ₹{target_1} | T2: ₹{target_2}")
                st.rerun()

        st.subheader(f"📂 Open Paper Positions ({len(remaining_positions)})")
        if remaining_positions:
            st.dataframe(pd.DataFrame(remaining_positions), use_container_width=True, hide_index=True)
            st.write("**Manual 1-Click Square-Off at Live Spot Price:**")
            exit_cols = st.columns(min(4, len(remaining_positions)))
            for idx, pos in enumerate(remaining_positions):
                col_slot = exit_cols[idx % len(exit_cols)]
                with col_slot:
                    if st.button(
                        f"❌ Exit {pos['Symbol']} ({pos['Side'][:4]}) | P&L: ₹{pos['Live P&L (₹)']:+,.2f}",
                        key=f"exit_{idx}",
                        use_container_width=True,
                    ):
                        orig = port["positions"].pop(idx)
                        port["cash"] = round(port["cash"] + orig["Invested"] + pos["Live P&L (₹)"], 2)
                        port["realized_pnl"] = round(port["realized_pnl"] + pos["Live P&L (₹)"], 2)
                        port["history"].insert(0, {
                            "ExitTime": ist_now,
                            "Symbol": orig["Symbol"],
                            "Side": f"{orig['Side']} [MANUAL EXIT]",
                            "Qty": orig["Qty"],
                            "Entry (₹)": orig["EntryPrice"],
                            "Exit Spot (₹)": pos["Live Spot (₹)"],
                            "Realized P&L (₹)": pos["Live P&L (₹)"],
                        })
                        save_portfolio()
                        st.rerun()
        else:
            st.caption("No open paper trades yet. Select any stock or index above to place a virtual trade!")

        if port["history"]:
            st.subheader(f"📜 Closed Trade Book ({len(port['history'])} Trades)")
            st.dataframe(pd.DataFrame(port["history"]), use_container_width=True, hide_index=True)

    # ==========================================================================
    # TAB 2: 90-DAY HISTORICAL STRATEGY BACKTESTER (₹5,00,000 SIMULATION)
    # ==========================================================================
    with tab_bt:
        st.subheader("📊 90-Day Strategy Backtester (₹5,00,000 Starting Capital)")
        st.caption("Simulates historical trades with Smart ATR+VWAP Stop-Loss, Auto-Breakeven Trail at Target 1 (1:1.5), and Full Exit at Target 2 (1:3) or HM Reversal.")

        b_c1, b_c2, b_c3, b_c4, b_c5 = st.columns([1.3, 1.5, 0.9, 0.9, 1.1])
        with b_c1:
            bt_sym = st.selectbox("Backtest Symbol", list(WATCHLIST.keys()), index=0, key="bt_sym")
        with b_c2:
            bt_strat = st.selectbox(
                "Strategy to Test",
                ["🔥 Hybrid Master (VWAP+ORB+Vol+HM)", "📈 Classic Hilega-Milega"],
                index=0,
                key="bt_strat",
            )
        with b_c3:
            bt_tf = st.selectbox("Timeframe", ["1h", "1d", "15m"], index=0, key="bt_tf")
        with b_c4:
            bt_risk = st.selectbox("Risk / Trade (%)", [0.5, 1.0, 1.5, 2.0], index=1, key="bt_risk")
        with b_c5:
            st.write("")
            skip_chop = st.checkbox("Skip 11:30–1:15 Chop", value=True)

        if bt_tf == "15m":
            st.caption("ℹ️ *Note: Yahoo Finance provides up to 60 days of 15-minute intraday candles, and full 90 days for `1h` and `1d` candles.*")

        with st.spinner(f"Running 90-Day Backtest on {bt_sym} ({bt_tf})..."):
            summary, df_bt_trades, df_bt_eq = run_90_day_backtest(bt_sym, bt_tf, bt_strat, bt_risk, skip_chop)

        if summary is not None:
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("💰 Final Capital (from ₹5L)", f"₹{summary['final_capital']:,.2f}", f"{summary['return_pct']:+.2f}%")
            k2.metric("📈 Net Profit / Loss", f"₹{summary['net_pnl']:+,.2f}")
            k3.metric("🎯 Win Rate (%)", f"{summary['win_rate']}%", f"{summary['total_trades']} Trades")
            k4.metric("⚖️ Profit Factor", f"{summary['profit_factor']}x")
            k5.metric("📉 Max Drawdown", f"{summary['max_dd_pct']}%")

            if df_bt_eq is not None and not df_bt_eq.empty:
                st.write("**📈 90-Day Portfolio Equity Curve (₹):**")
                st.line_chart(df_bt_eq.set_index("Time")["Equity (₹)"])

            if df_bt_trades is not None and not df_bt_trades.empty:
                st.write(f"**📜 Historical Trade-by-Trade Log ({len(df_bt_trades)} Trades):**")
                st.dataframe(df_bt_trades, use_container_width=True, hide_index=True)
            else:
                st.info("No crossover trades triggered for this symbol/timeframe combination.")
        else:
            st.warning("Could not load historical backtest data for this symbol.")

else:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col1:
        timeframe = st.selectbox("Timeframe", ["15m", "5m", "1h", "1d"], index=0)
    with col2:
        filter_mode = st.selectbox(
            "Filter Signals",
            [
                "All Triggered Signals Only",
                "Bullish Signals Only (Buy)",
                "Bearish Signals Only (Short / Exit)",
                "Show Full F&O Watchlist Status",
            ],
            index=0,
        )
    with col3:
        st.write("")
        scan_btn = st.button("🔄 Run Live Scan Now", use_container_width=True, type="primary")

    if scan_btn:
        st.cache_data.clear()

    with st.spinner(f"Running {mode_choice} on {timeframe}..."):
        df_results = fetch_and_scan(timeframe, mode_choice)

    if not df_results.empty:
        if filter_mode == "All Triggered Signals Only":
            df_view = df_results[~df_results["Signal"].str.startswith("⚪")]
        elif filter_mode == "Bullish Signals Only (Buy)":
            df_view = df_results[df_results["Signal"].str.contains("BUY")]
        elif filter_mode == "Bearish Signals Only (Short / Exit)":
            df_view = df_results[df_results["Signal"].str.contains("TOP|SHORT|EXIT")]
        else:
            df_view = df_results

        st.subheader(f"Live Results ({len(df_view)} Matches, Sorted by Highest Spread) — {ist_now}")
        st.dataframe(df_view, use_container_width=True, hide_index=True)
    else:
        st.info("No data returned. Please click 'Run Live Scan Now'.")

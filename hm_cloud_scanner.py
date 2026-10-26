import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import requests
import numpy as np
import pandas as pd
import yfinance as yf

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

def evaluate_hm_signals(df, symbol_name):
    if df is None or len(df) < 35:
        return None
    close = df["Close"].squeeze()
    high = df["High"].squeeze()
    low = df["Low"].squeeze()

    rsi9 = compute_rsi(close, 9)
    ema3 = rsi9.ewm(span=3, adjust=False).mean()
    wma21 = compute_wma(rsi9, 21)

    curr, prev = -1, -2
    r_now, r_prev = float(rsi9.iloc[curr]), float(rsi9.iloc[prev])
    e_now = float(ema3.iloc[curr])
    w_now, w_prev = float(wma21.iloc[curr]), float(wma21.iloc[prev])
    c_now, h_now, l_now = float(close.iloc[curr]), float(high.iloc[curr]), float(low.iloc[curr])
    spread = abs(r_now - w_now)

    if np.isnan([r_now, e_now, w_now]).any():
        return None

    signal, sl_level = None, None
    if (r_now > w_now) and (r_prev <= w_prev) and (r_now >= e_now):
        signal, sl_level = "BOTTOM BUY (Early Reversal)", f"Candle Low: {l_now:.2f}"
    elif (r_now > 50.0) and (r_prev <= 50.0) and (r_now > w_now) and (r_now >= e_now):
        signal, sl_level = "BUY >50 (Momentum Breakout)", f"Candle Low: {l_now:.2f}"
    elif (r_now < w_now) and (r_prev >= w_prev) and (r_now <= e_now):
        signal, sl_level = "TOP / EXIT (Red Line Out)", f"Candle High: {h_now:.2f}"
    elif (r_now < 50.0) and (r_prev >= 50.0) and (r_now < w_now) and (r_now <= e_now):
        signal, sl_level = "SHORT <50 (Bearish Breakdown)", f"Candle High: {h_now:.2f}"

    if not signal:
        return None

    return {
        "Symbol": symbol_name, "Signal": signal, "Close": round(c_now, 2),
        "StopLoss": sl_level, "RSI9": round(r_now, 2), "EMA3": round(e_now, 2),
        "WMA21": round(w_now, 2), "Spread": round(spread, 2),
    }

def send_telegram_alert(message_text):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not bot_token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message_text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def send_gmail_alert(subject, body_text):
    gmail_user = os.getenv("GMAIL_USER", "").strip()
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    recipient = os.getenv("ALERT_RECIPIENT_EMAIL", gmail_user).strip()
    if not gmail_user or not gmail_app_password:
        return
    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, recipient, msg.as_string())
    except Exception as e:
        print(f"Gmail error: {e}")

def run_scanner(interval="15m"):
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(ist).strftime("%d-%b-%Y %I:%M %p IST")
    tickers = list(WATCHLIST.values())
    symbol_map = {v: k for k, v in WATCHLIST.items()}
    data = yf.download(tickers=tickers, period="5d", interval=interval, group_by="ticker", threads=True, progress=False)

    triggered_alerts = []
    for yf_ticker, clean_name in symbol_map.items():
        try:
            sub_df = data[yf_ticker].dropna() if len(tickers) > 1 else data.dropna()
            res = evaluate_hm_signals(sub_df, clean_name)
            if res:
                triggered_alerts.append(res)
        except Exception:
            continue

    if not triggered_alerts:
        print("No new signals on this candle.")
        return []

    triggered_alerts.sort(key=lambda x: x["Spread"], reverse=True)

    lines = [f"<b>HILEGA-MILEGA ({interval.upper()}) LIVE ALERTS</b>", f"Time: {now_ist}\n"]
    for item in triggered_alerts:
        lines.append(
            f"• <b>{item['Symbol']}</b> — <b>{item['Signal']}</b>\n"
            f"  Close: ₹{item['Close']} | SL ({item['StopLoss']})\n"
            f"  RSI(9): {item['RSI9']} | EMA(3): {item['EMA3']} | WMA(21): {item['WMA21']} | Spread: {item['Spread']}\n"
        )
    full_msg = "\n".join(lines)
    plain_msg = full_msg.replace("<b>", "").replace("</b>", "")
    send_telegram_alert(full_msg)
    send_gmail_alert(f"[HM {interval.upper()} ALERT] {len(triggered_alerts)} Signals Triggered ({now_ist})", plain_msg)
    return triggered_alerts

if __name__ == "__main__":
    run_scanner("15m")

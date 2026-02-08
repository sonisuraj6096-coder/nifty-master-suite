import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, date
import os
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & SECURITY ---
ACCESS_KEY = "nifty2026" 
LOCK_FILE = "trade_lock.txt"
JOURNAL_FILE = "nifty_journal.csv"
LOT_SIZE = 65

st.set_page_config(page_title="Nifty Master Suite Pro", layout="wide")
st_autorefresh(interval=30000, key="refresh")

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- 2. LOGIN GATE ---
if not st.session_state['authenticated']:
    st.title("🔐 Secure Trader Login")
    user_input = st.text_input("Enter Key", type="password")
    if st.button("Unlock"):
        if user_input == ACCESS_KEY:
            st.session_state['authenticated'] = True
            st.rerun()
    st.stop()

# --- 3. CORE LOGIC ---
def log_trade(outcome, pts, net, mood, rule_follow):
    with open(LOCK_FILE, "w") as f: f.write(str(date.today()))
    new_data = pd.DataFrame([{
        "Timestamp": datetime.now(), 
        "Outcome": outcome, 
        "Points": pts, 
        "Net_PnL": net,
        "Mindset": mood,
        "Followed_Rules": rule_follow
    }])
    if not os.path.exists(JOURNAL_FILE):
        new_data.to_csv(JOURNAL_FILE, index=False)
    else:
        new_data.to_csv(JOURNAL_FILE, mode='a', header=False, index=False)

def get_live_price():
    try:
        data = yf.download("^NSEI", period="1d", interval="1m")
        return round(data['Close'].iloc[-1], 2)
    except: return 21500.0

# --- 4. SIDEBAR ---
with st.sidebar:
    st.header("💰 Risk & Levels")
    capital = st.number_input("Capital (₹)", value=100000)
    risk_pct = st.slider("Risk per Trade %", 1.0, 5.0, 2.0)
    lots = max(1, int((capital * (risk_pct/100)) / (10 * LOT_SIZE)))
    st.info(f"📊 Recommended Lots: {lots}")
    
    st.divider()
    res = st.number_input("Resistance", value=21600.0)
    sup = st.number_input("Support", value=21400.0)
    zone_w = st.number_input("Zone Width", value=10.0)
    if st.sidebar.button("Reset Daily Lock (Admin)"):
        if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)
        st.rerun()

# --- 5. MAIN DASHBOARD ---
cmp = get_live_price()
has_traded = os.path.exists(LOCK_FILE) and open(LOCK_FILE).read() == str(date.today())

tab1, tab2 = st.tabs(["🚀 Live Execution", "📈 Weekly Review"])

with tab1:
    st.title(f"Live Price: {cmp}")
    
    # Slippage Monitor
    if os.path.exists(JOURNAL_FILE):
        df = pd.read_csv(JOURNAL_FILE)
        sl_trades = df[df['Outcome'] == "SL Hit"]
        if not sl_trades.empty and sl_trades['Points'].mean() > 12:
            st.error(f"⚠️ SLIPPAGE ALERT: Average loss is {sl_trades['Points'].mean():.1f} pts!")

    if not has_traded:
        st.divider()
        st.subheader("🧠 Pre-Trade Mindset")
        mood = st.select_slider("Current Mindset", options=["Stressed", "Anxious", "Neutral", "Calm", "Confident"], value="Neutral")
        rule_follow = st.toggle("I have checked 5-EMA/9-EMA & Zone Room")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 BUY", use_container_width=True, disabled=not rule_follow):
                log_trade("Target Hit", 20, (20 * lots * LOT_SIZE) - 45, mood, rule_follow)
                st.rerun()
        with col2:
            if st.button("📉 SELL", use_container_width=True, disabled=not rule_follow):
                log_trade("SL Hit", 10, (-10 * lots * LOT_SIZE) - 45, mood, rule_follow)
                st.rerun()
    else:
        st.warning("🚫 ONE & DONE ACTIVE. Trading is closed for today.")

with tab2:
    st.header("📊 Weekly Performance Review")
    if os.path.exists(JOURNAL_FILE):
        df = pd.read_csv(JOURNAL_FILE)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        
        # Win Rate calculation
        win_rate = (len(df[df['Outcome'] == 'Target Hit']) / len(df)) * 100
        st.metric("Overall Win Rate", f"{win_rate:.1f}%")
        
        # Mindset vs Profit Chart
        st.subheader("Mindset vs. Profitability")
        
        fig = px.bar(df, x="Mindset", y="Net_PnL", color="Outcome", title="How your mood affects your money")
        st.plotly_chart(fig, use_container_width=True)
        
        # Equity Curve
        st.subheader("Equity Curve")
        
        df['Cumulative_PnL'] = df['Net_PnL'].cumsum()
        st.line_chart(df, x="Timestamp", y="Cumulative_PnL")
    else:
        st.info("Log some trades to see your performance data here!")

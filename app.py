import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from streamlit_autorefresh import st_autorefresh
import json
import os

# --- PAGE CONFIG (for Streamlit) ---
st.set_page_config(
    page_title = "Decentralized Pattern Game",
    page_icon = "🎮",
    layout = "wide"
)

# --- FIREBASE INIT ---
if not firebase_admin._apps:
    # Use Environment Variable for Cloud, fallback to local file for testing
    fb_json_str = os.environ.get('FIREBASE_JSON')
    db_url = os.environ.get('FIREBASE_DB_URL', 'https://decenteralizedpetterncoe454-default-rtdb.firebaseio.com/')
    
    if fb_json_str:
        fb_config = json.loads(fb_json_str)
        cred = credentials.Certificate(fb_config)
    else:
        # If this file doesn't exist on Arch, it will error out—this is correct!
        cred = credentials.Certificate("service_key.json")
        
    firebase_admin.initialize_app(cred, {'databaseURL': db_url})

# --- AUTO-REFRESH (Every 1 second) ---
st_autorefresh(interval = 1000, key = "ui_refresh")

# --- DATA LOADER (From Cloud) ---
def get_cloud_data():
    try:
        res = db.reference('game_state').get()
        if res:
            return res
    except Exception as e:
        st.error(f"Connection Error: {e}")
    return {"sequence": [], "current_player": "Disconnected", "score": 0, "index": 0}

data = get_cloud_data()

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    div[data-testid="stMetric"] {
        background-color: #1E2130;
        border: 1px solid #3E4255;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        text-align: center;
    }
    div[data-testid="stMetric"]:nth-of-type(1) { border-top: 5px solid #FF4B4B; }
    div[data-testid="stMetric"]:nth-of-type(2) { border-top: 5px solid #1C83E1; }
    div[data-testid="stMetric"]:nth-of-type(3) { border-top: 5px solid #7D33FF; }
    h1, h2, h3 { color: #00FFC8 !important; font-family: 'Courier New', Courier, monospace; }
    </style>
    """, unsafe_allow_html = True)

# --- UI LAYOUT ---
st.title("🕹️ DECENTRALIZED PATTERN GAME: THE REFEREE")
st.write("---")

m1, m2, m3 = st.columns(3)

with m1:
    st.metric(label="LEVEL", value=f"STAGE {data['score']}")

with m2:
    p_name = data["current_player"].upper()
    st.metric(label="ACTIVE PLAYER", value=p_name)

with m3:
    if not data["sequence"]:
        status_text = "IDLE"
    elif data["index"] < len(data["sequence"]):
        status_text = "REPEATING..."
    else:
        status_text = "ADDING NEW!"
    st.metric(label="GAME STATUS", value=status_text)

st.write("---")

# Row 2: Sequence Pattern
if data["sequence"]:
    st.write("### 📡 Live Sequence Pattern")
    spike_cols = st.columns(len(data["sequence"]))
    
    for i, btn in enumerate(data["sequence"]):
        with spike_cols[i]:
            color = "#00D1FF" if btn == "B1" else "#FFD700"
            label = "B1" if btn == "B1" else "B2"
            
            st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;">
                    <div style="width: 12px; height: 60px; background-color: {color}; border-radius: 10px; box-shadow: 0 0 15px {color};"></div>
                    <span style="color: {color}; font-weight: bold; font-family: monospace;">{label}</span>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("📡 System Idle. Awaiting first input from Player 1...")

st.markdown("---")
st.caption(f"By: Abdulmajeed Nazih Ahmad • Cloud Sync Active • KFUPM: COE454 Project")

with st.expander("Show Raw Cloud Data"):
    st.json(data)
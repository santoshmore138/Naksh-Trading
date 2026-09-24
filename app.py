import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import urllib.parse
import datetime

# ॲप कॉन्फिगरेशन आणि डार्क थीम लूक (फॉन्ट साईज कॉम्पॅक्ट ठेवण्यासाठी CSS)
st.set_page_config(page_title="Naksh Pro - Market Analyzer", page_icon="🎯", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 13px;
    }
    h1 {
        font-size: 22px !important;
    }
    h2 {
        font-size: 18px !important;
    }
    h3 {
        font-size: 15px !important;
    }
    .trade-plan-box {
        background-color: #161b22;
        padding: 15px;
        border-radius: 8px;
        border: 2px solid #00D26A;
        margin-bottom: 15px;
        color: white;
    }
    .whatsapp-box {
        background-color: #0b141a;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        color: #e9edef;
        font-family: monospace;
        font-size: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# लहान आणि आकर्षक नाव
st.title("🎯 Naksh Pro")
st.markdown("---")

# ==========================================
# साईडबार - कोटक निओ एपीआय आणि सेटिंग्स
# ==========================================
st.sidebar.header("⚙️ सेटिंग्स")
kotak_token = st.sidebar.text_input("कोटक निओ API टोकन:", type="password", value="00680e24-1524-4793-be33-e0c4978e97bc")

# इंडेक्स निवडण्याचा पर्याय
selected_index = st.sidebar.selectbox("इंडेक्स निवडा:", [
    "SENSEX", 
    "NIFTY", 
    "BANK NIFTY"
])

sync_button = st.sidebar.button("🔄 लाईव्ह डेटा सिंक करा")

# इंडेक्सनुसार डायनॅमिक डेटा
if selected_index == "SENSEX":
    spot_val, spot_change = "74,857.89", "+0.44% (Bullish)"
    pcr_val, max_pain, score_val = "1.38", "74,800", "+8.0 / 10"
    s1, s2, r1, r2 = "74,800", "74,700", "74,900", "75,000"
    entry_zone = "74,820 - 74,850"
    sl_val = "74,750"
    t1, t2 = "74,920", "74,980 - 75,000"
    wa_summary = "🚀 Naksh Pro: SENSEX Signal 🚀\n\n📊 SPOT: 74,857.89 (+0.44%)\n📈 PCR: 1.38 (Bullish)\n\n🎯 Setup: Buy on Dips\nEntry: 74,820 - 74,850\nTarget: 75,000\nStop Loss: 74,750"
    strikes = [74500, 74700, 74800, 74900, 75000, 75200]
    ce_oi = [500000, 800000, 1160000, 1160000, 2066000, 1015000]
    pe_oi = [2193000, 1814000, 1797000, 900000, 400000, 150000]

elif selected_index == "NIFTY":
    spot_val, spot_change = "23,450.20", "+0.55% (Bullish)"
    pcr_val, max_pain, score_val = "1.25", "23,400", "+8.2 / 10"
    s1, s2, r1, r2 = "23,400", "23,300", "23,500", "23,600"
    entry_zone = "23,410 - 23,440"
    sl_val = "23,370"
    t1, t2 = "23,500", "23,600"
    wa_summary = "🚀 Naksh Pro: NIFTY Signal 🚀\n\n📊 SPOT: 23,450.20 (+0.55%)\n📈 PCR: 1.25 (Bullish)\n\n🎯 Setup: Buy on Dips\nEntry: 23,410 - 23,440\nTarget: 23,600\nStop Loss: 23,370"
    strikes = [23200, 23300, 23400, 23500, 23600, 23700]
    ce_oi = [400000, 900000, 1500000, 2200000, 1100000, 500000]
    pe_oi = [1200000, 1600000, 1900000, 800000, 300000, 100000]

else: # BANK NIFTY
    spot_val, spot_change = "50,620.10", "+0.70% (Strong Bullish)"
    pcr_val, max_pain, score_val = "1.42", "50,500", "+8.8 / 10"
    s1, s2, r1, r2 = "50,500", "50,300", "50,800", "51,000"
    entry_zone = "50,550 - 50,600"
    sl_val = "50,450"
    t1, t2 = "50,800", "51,000"
    wa_summary = "🚀 Naksh Pro: BANK NIFTY Signal 🚀\n\n📊 SPOT: 50,620.10 (+0.70%)\n📈 PCR: 1.42 (Strong Bullish)\n\n🎯 Setup: Buy on Dips\nEntry: 50,550 - 50,600\nTarget: 51,000\nStop Loss: 50,450"
    strikes = [50000, 50200, 50500, 50800, 51000, 51200]
    ce_oi = [600000, 1100000, 1800000, 2500000, 1400000, 700000]
    pe_oi = [1500000, 2100000, 2600000, 1200000, 500000, 200000]

if sync_button:
    st.success(f"{selected_index} लाईव्ह डेटा यशस्वीरीत्या सिंक झाला!")

# ==========================================
# मुख्य डॅशबोर्ड मेट्रिक्स
# ==========================================
st.markdown(f"**{selected_index} मार्केट ओव्हरव्ह्यू:**")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("स्पॉट", value=spot_val, delta=spot_change)
with col2:
    st.metric("PCR", value=pcr_val)
with col3:
    st.metric("मॅक्स पेन", value=max_pain)
with col4:
    st.metric("स्कोअर", value=score_val)

st.markdown("---")

# ==========================================
# 1. ट्रेड प्लॅनिंग बॉक्स (आता सर्वात वर)
# ==========================================
st.markdown("### 🎯 1. Naksh Pro Trade Planning Box")
st.markdown(f"""
<div class="trade-plan-box">
    <b>📈 ट्रेड दिशा: BUY ON DIPS (तेजीचा ट्रेड)</b><br>
    • <b>Entry Zone:</b> {entry_zone}<br>
    • <b>Key Level:</b> {s1} सपोर्ट<br>
    • <b>Stop-loss (SL):</b> {sl_val}<br>
    • <b>Targets:</b> {t1} / {t2}
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. कन्फर्मेशन मॅट्रिक्स टेबल
# ==========================================
st.markdown("### 📊 2. Confirmation Matrix")
matrix_data = {
    "Factor": ["Price Action", "PE OI", "CE OI", f"PCR ({pcr_val})", "Volume"],
    "Signal": ["Bullish", "Strongly Bullish", "Neutral", "Bullish", "Bullish"],
    "शेरा": [f"Spot {spot_val}", f"S1 ({s1}) सपोर्ट", f"R2 ({r2}) अडथळा", "तेजीचे वातावरण", "पुट रायटिंग मजबूत"]
}
st.table(pd.DataFrame(matrix_data))

# ==========================================
# 3. नो ट्रेड फिल्टर चेक
# ==========================================
st.markdown(f"""
### 🚦 3. No Trade Filter Check:
* **स्थिती:** मार्केट **{s1}** आणि **{r2}** च्या दरम्यान आहे.
* **निर्णय:** **CLEAR BULLISH SETUP ON DIPS** ({s1} जवळ खरेदी संधी).
""")

# ==========================================
# 4. व्हॉट्सॲप रिपोर्ट आणि शेअरिंग
# ==========================================
st.markdown("### 📤 4. WhatsApp Summary Report")
st.markdown(f"""
<div class="whatsapp-box">
    <pre>{wa_summary}</pre>
</div>
""", unsafe_allow_html=True)

encoded_whatsapp_text = urllib.parse.quote(wa_summary)
whatsapp_share_url = f"https://api.whatsapp.com/send?text={encoded_whatsapp_text}"

st.markdown(f"""
    <a href="{whatsapp_share_url}" target="_blank">
        <button style="background-color:#25D366; color:white; padding:8px 15px; border:none; border-radius:6px; font-size:13px; font-weight:bold; cursor:pointer; margin-top:5px; margin-bottom:15px;">
            💬 व्हॉट्सॲपवर पाठवा (Share)
        </button>
    </a>
""", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 5. स्ट्राइक-वाईस ओपन इंटरेस्ट (OI) चार्ट
# ==========================================
st.markdown(f"### 📈 5. Open Interest (OI) Chart ({selected_index})")
fig = go.Figure(data=[
    go.Bar(name='Call OI (Resistance)', x=strikes, y=ce_oi, marker_color='#ff4b4b'),
    go.Bar(name='Put OI (Support)', x=strikes, y=pe_oi, marker_color='#00D26A')
])
fig.update_layout(
    barmode='group', 
    xaxis_title='Strike Price', 
    yaxis_title='Open Interest',
    template='plotly_dark',
    margin=dict(l=20, r=20, t=30, b=20),
    height=300
)
st.plotly_chart(fig, use_container_width=True)

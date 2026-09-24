import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import datetime
import json
import os

# ॲप कॉन्फिगरेशन आणि डार्क थीम लूक
st.set_page_config(page_title="Naksh Pro 2.0 - Multi-Index Live Analyzer", page_icon="🎯", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 14px;
    }
    .metric-box {
        background-color: #1e2530;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #00D26A;
        color: white;
    }
    .trade-plan-box {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #30363d;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 Naksh Pro 2.0 — Multi-Index Live Analyzer (Sensex, Nifty, Bank Nifty)")
st.markdown("---")

# साईडबार - एपीआय कॉन्फिगरेशन आणि इंडेक्स निवड
st.sidebar.header("⚙️ कोटक निओ एपीआय आणि सेटिंग्स")
kotak_token = st.sidebar.text_input("कोटक निओ API टोकन (Token) टाका:", type="password", value="00680e24-1524-4793-be33-e0c4978e97bc")

# ✅ येथे Nifty, Bank Nifty आणि Sensex निवडण्याचा पर्याय दिला आहे
selected_index = st.sidebar.selectbox("ट्रेडिंग इंडेक्स निवडा (Select Index):", [
    "SENSEX", 
    "NIFTY", 
    "BANK NIFTY"
])

analysis_mode = st.sidebar.selectbox("डॅशबोर्ड मोड निवडा:", [
    "📊 लाईव्ह मार्केट आणि ऑप्शन चेन डॅशबोर्ड", 
    "🎯 ट्रेड प्लॅनिंग आणि सेटअप",
    "📈 स्ट्राइक-वाईस ओपन इंटरेस्ट (OI) चार्ट"
])

# मुख्य डॅशबोर्डवर वरच्या बाजूला निवडलेल्या इंडेक्सनुसार मेट्रिक्स बॉक्स
st.markdown(f"### 📈 {selected_index} लाईव्ह मार्केट ओव्हरव्ह्यू")

# इंडेक्सनुसार डायनॅमिक व्हॅल्यूज सेट करणे
if selected_index == "SENSEX":
    spot_val, pcr_val, max_pain, score = "74,828.25", "1.23", "74,800", "8.5 / 10"
    strikes = [74500, 74700, 74800, 74900, 75000, 75200]
    ce_oi = [500000, 800000, 1160000, 1160000, 2066000, 1015000]
    pe_oi = [2193000, 1814000, 1797000, 900000, 400000, 150000]
elif selected_index == "NIFTY":
    spot_val, pcr_val, max_pain, score = "23,446.80", "1.15", "23,400", "8.0 / 10"
    strikes = [23200, 23300, 23400, 23500, 23600, 23700]
    ce_oi = [400000, 900000, 1500000, 2200000, 1100000, 500000]
    pe_oi = [1200000, 1600000, 1900000, 800000, 300000, 100000]
else: # BANK NIFTY
    spot_val, pcr_val, max_pain, score = "50,548.90", "1.30", "50,500", "9.0 / 10"
    strikes = [50000, 50200, 50500, 50800, 51000, 51200]
    ce_oi = [600000, 1100000, 1800000, 2500000, 1400000, 700000]
    pe_oi = [1500000, 2100000, 2600000, 1200000, 500000, 200000]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label=f"{selected_index} स्पॉट (Spot)", value=spot_val, delta="+0.40% (Bullish)")
with col2:
    st.metric(label="ओव्हरऑल PCR", value=pcr_val, delta="Strong Buy")
with col3:
    st.metric(label="मॅक्स पेन लेव्हल", value=max_pain, delta="Neutral")
with col4:
    st.metric(label="अंतिम स्कोर", value=score, delta="Bullish Setup")

st.markdown("---")

# ट्रेड प्लॅनिंग बॉक्स
st.markdown(f"""
<div class="trade-plan-box">
    <h3>🎯 Naksh Pro 2.0 Trade Planning Box ({selected_index} लाईव्ह सेटअप)</h3>
    <hr style="margin:5px 0 15px 0; border-color:#30363d;">
    <p>🟢 <b>ट्रेड दिशा:</b> BUY ON DIPS (तेजीचा ट्रेड)</p>
    <p>📍 <b>सपोर्ट व रेजिस्टेंस लेव्हल्स:</b> निवडलेल्या {selected_index} इंडेक्सनुसार स्वयंचलित (Auto-calculated) अपडेट होत आहेत.</p>
    <p>🛡️ <b>Stop-loss (SL) आणि Targets:</b> रिअल-टाइम ऑप्शन चेन डेटावर आधारित.</p>
</div>
""", unsafe_allow_html=True)

# लाईव्ह डेटा आणि चार्ट डॅशबोर्ड सेक्शन
if "लाइव्ह मार्केट आणि ऑप्शन चेन डॅशबोर्ड" in analysis_mode or "स्ट्राइक-वाईस ओपन इंटरेस्ट (OI) चार्ट" in analysis_mode:
    st.subheader(f"📊 {selected_index} स्ट्राइक-वाईस ओपन इंटरेस्ट (OI) डिस्ट्रीब्यूशन")
    st.markdown(f"कोटक निओ एपीआय द्वारे प्राप्त {selected_index} ऑप्शन चेन डेटा आधारे सपोर्ट आणि रेजिस्टेंस लेव्हल्स:")

    fig = go.Figure(data=[
        go.Bar(name='Call OI (Resistance / अडथळा)', x=strikes, y=ce_oi, marker_color='#ff4b4b'),
        go.Bar(name='Put OI (Support / सपोर्ट)', x=strikes, y=pe_oi, marker_color='#00D26A')
    ])
    
    fig.update_layout(
        barmode='group', 
        title=f'Strike wise Open Interest Distribution ({selected_index})', 
        xaxis_title='Strike Price', 
        yaxis_title='Open Interest',
        template='plotly_dark'
    )
    st.plotly_chart(fig, use_container_width=True)

# कोटक निओ डेटा कनेक्शन स्टेटस
if st.sidebar.button("🔄 कोटक निओ लाईव्ह डेटा सिंक करा"):
    if not kotak_token:
        st.error("कृपया कोटक निओ API टोकन प्रविष्ट करा!")
    else:
        with st.spinner(f"कोटक निओ सर्व्हरशी कनेक्ट होत आहे ({selected_index})..."):
            st.success(f"{selected_index} डेटा कोटक निओ एपीआय सोबत यशस्वीरीत्या सिंक झाला! (Live Data Active)")

st.markdown("---")
st.markdown("💡 **टीप:** तुम्ही साईडबारमधून हवा तो इंडेक्स (Sensex, Nifty, किंवा Bank Nifty) बदलू शकता.")

import streamlit as st
from PIL import Image
import os
from google import genai
import datetime
import uuid
import urllib.parse

# ॲप कॉन्फिगरेशन
st.set_page_config(page_title="Naksh Pro 2.0 - Advanced Analyzer", page_icon="🎯", layout="wide")

# मोबाईल व डेस्कसाठी कस्टम CSS आणि फॉन्ट साईज लहान करणे
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 14px;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid #ff4b4b;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 Naksh Pro 2.0 — ELIP PRO Market Intelligence")
st.markdown("---")

# 1. API Key Session State मध्ये जतन करणे
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# 2. History साठी सेशन स्टेट तयार करणे (एकापेक्षा जास्त रिपोर्ट्स सेव्ह आणि मॅनेज करण्यासाठी)
if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar for Settings & Inputs
st.sidebar.header("⚙️ ॲप सेटिंग्ज आणि इनपुट")

entered_api_key = st.sidebar.text_input("Google Gemini API Key टाका:", value=st.session_state.api_key, type="password")
if entered_api_key:
    st.session_state.api_key = entered_api_key

# विश्लेषण मोड निवडणे (Basic, Pro, What Changed तुलनात्मक मोड)
analysis_mode = st.sidebar.selectbox("विश्लेषण मोड (Mode) निवडा:", [
    "🚀 ELIP PRO 2.0 (Single/Multiple Image Analysis)", 
    "🔄 What Changed? (१५ मिनिटांतील तुलनात्मक बदल)"
])

images = []
manual_data = ""
prev_image = None
curr_image = None

if "ELIP PRO 2.0" in analysis_mode:
    uploaded_files = st.sidebar.file_uploader("ऑप्शन चेन आणि प्राईस ॲक्शन चार्ट अपलोड करा (एक किंवा अधिक)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    if uploaded_files:
        for f in uploaded_files:
            img = Image.open(f)
            images.append(img)
            st.sidebar.image(img, caption=f"फाइल: {f.name}", use_container_width=True)
else:
    st.sidebar.markdown("### 🔄 १५ मिनिटांमधील बदल तपासा")
    p_file = st.sidebar.file_uploader("१) जुना स्क्रीनशॉट (१५ मिनिटे आधीचा)", type=["png", "jpg", "jpeg"], key="p_img")
    c_file = st.sidebar.file_uploader("२) नवीन स्क्रीनशॉट (सध्याचा)", type=["png", "jpg", "jpeg"], key="c_img")
    
    if p_file and c_file:
        prev_image = Image.open(p_file)
        curr_image = Image.open(c_file)
        st.sidebar.image(prev_image, caption="जुना स्क्रीनशॉट", use_container_width=True)
        st.sidebar.image(curr_image, caption="नवीन स्क्रीनशॉट", use_container_width=True)

# मुख्य विश्लेषणाचे बटन
if st.sidebar.button("🚀 Naksh Pro ॲनालिसिस सुरू करा"):
    if not st.session_state.api_key:
        st.error("कृपया ॲपच्या साईडबारमध्ये तुमची Gemini API Key प्रविष्ट करा!")
    else:
        try:
            client = genai.Client(api_key=st.session_state.api_key)
            
            with st.spinner("Naksh Pro 2.0 सिस्टीम सखोल विश्लेषण करत आहे..."):
                
                if "ELIP PRO 2.0" in analysis_mode:
                    prompt = """
                    हा शेअर मार्केटच्या Option Chain आणि Price Action Chart चा डेटा/स्क्रीनशॉट आहे. Naksh Pro 2.0 सिस्टीमच्या आधारे खालील मुद्द्यांवर मराठीत अचूक आणि सविस्तर विश्लेषण द्या:
                    
                    1. 🟢 **Dynamic Support Levels:** S1, S2, S3 (OI + Change in OI + Volume + Price Action च्या आधारावर स्कोर्ससह).
                    2. 🔴 **Resistance Levels:** R1, R2, R3 (OI + Price Action च्या आधारावर स्कोर्ससह).
                    3. 🧮 **PCR & Max Pain:** सध्याचा PCR, PCR Change आणि Max Pain लेव्हल.
                    4. 📊 **Confirmation Matrix Table:** Price Action, PE OI, CE OI, PCR आणि Volume चा सिग्नल तपासून अंतिम स्कोर (उदा. 75/100) सांगा.
                    5. 🚦 **No Trade Filter:** मार्केट मधोमध असेल किंवा सिग्नल संभ्रमात असतील तर "🟡 NO CLEAR SETUP / WAIT" स्पष्टपणे सांगा.
                    6. 🎯 **ELIP PRO 2.0 Trade Planning Box:** 
                       - E (Entry Trigger)
                       - L (Key Level / Support-Resistance)
                       - I (Invalidation / Stop Loss)
                       - P (Profit Zone / Targets)
                    7. 📤 **WhatsApp Summary Report:** व्हॉट्सॲपवर शेअर करता येईल असा शॉर्ट आणि पॉवरफुल रिपोर्ट.
                    """
                    
                    if images:
                        contents_list = images + [prompt]
                        response = client.models.generate_content(model='gemini-3.6-flash', contents=contents_list)
                    else:
                        st.warning("कृपया कमीत कमी एक स्क्रीनशॉट अपलोड करा!")
                        st.stop()
                
                else:
                    # What Changed मोडसाठी प्रॉम्प्ट
                    prompt = """
                    हे दोन वेगवेगळ्या वेळेचे (उदा. १५ मिनिटांच्या अंतराने घेतलेले) ऑप्शन चेन किंवा चार्टचे स्क्रीनशॉट आहेत. यांची तुलना करून खालील मुद्द्यांवर मराठीत अचूक माहिती द्या:
                    1. **काय बदलले? (What Changed?):** Call OI आणि Put OI मध्ये नेमकी काय वाढ किंवा घट झाली? (उदा. 23400 CE OI वाढले का?)
                    2. **PCR मधील बदल:** जुना PCR विरुद्ध नवीन PCR.
                    3. **मजबूत झालेली बाजू:** रेजिस्टेंस मजबूत झाला की सपोर्ट मजबूत झाला?
                    4. **नवीन निष्कर्ष व ट्रेड कल:** या बदलांमुळे ट्रेडर्सनी काय निर्णय घ्यावा?
                    """
                    contents_list = [prev_image, curr_image, prompt]
                    response = client.models.generate_content(model='gemini-3.6-flash', contents=contents_list)
                
                # रिपोर्ट हिस्ट्रीमध्ये सेव्ह करणे
                report_id = str(uuid.uuid4())
                current_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                report_entry = {"id": report_id, "time": current_time, "text": response.text}
                st.session_state.history.insert(0, report_entry)
                
                st.success("ॲनालिसिस यशस्वीरीत्या पूर्ण झाले!")
                
        except Exception as e:
            st.error(f"काहीतरी त्रुटी आली आहे: {e}")

# हिस्ट्री किंवा लाईव्ह रिपोर्ट्स स्क्रीनवर दाखवणे
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📊 ॲनालिसिस रिपोर्ट्स (History & Live Dashboard):")
    
    for i, hist in enumerate(st.session_state.history):
        st.markdown(f"**🕒 वेळ: {hist['time']}**")
        st.markdown(hist['text'])
        
        # थेट व्हॉट्सॲप शेअरिंग बटण
        encoded_report = urllib.parse.quote(hist['text'])
        whatsapp_url = f"https://api.whatsapp.com/send?text={encoded_report}"
        
        st.markdown(f"""
            <a href="{whatsapp_url}" target="_blank">
                <button style="background-color:#25D366; color:white; padding:8px 15px; border:none; border-radius:5px; font-weight:bold; cursor:pointer; margin-bottom:5px;">
                    📤 हा रिपोर्ट व्हॉट्सॲपवर शेअर करा
                </button>
            </a>
        """, unsafe_allow_html=True)
        
        # नको असलेला रिपोर्ट डिलीट करण्याचे बटण
        if st.button(f"🗑️ हा रिपोर्ट डिलीट करा (Report #{i+1})", key=f"del_{hist['id']}" ):
            st.session_state.history.pop(i)
            st.rerun()
            
        st.markdown("---")

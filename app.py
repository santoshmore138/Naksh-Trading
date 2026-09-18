import streamlit as st
from PIL import Image
import os
from google import genai
import datetime

# ॲप कॉन्फिगरेशन
st.set_page_config(page_title="ELIP PRO Option Chain Analyzer", page_icon="🎯", layout="wide")

# फॉन्ट साईज लहान करण्यासाठी आणि मोबाईल डिझाईन सुधारण्यासाठी कस्टम CSS
st.markdown("""
    <style>
    /* संपूर्ण ॲपमधील फॉन्ट साईज लहान करणे */
    html, body, [class*="css"] {
        font-size: 14px;
    }
    /* रिपोर्ट बॉक्सची साईज */
    .report-box {
        padding: 10px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 ELIP PRO — Option Chain & AI Market Analyzer")
st.markdown("---")

# 1. API Key Session State मध्ये जतन करणे
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# 3. History साठी सेशन स्टेट तयार करणे
if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar for Settings & Inputs
st.sidebar.header("⚙️ ॲप सेटिंग्ज आणि इनपुट")

# युजरने टाकलेली API Key सेशनमध्ये स्टोअर राहिल
entered_api_key = st.sidebar.text_input("Google Gemini API Key टाका:", value=st.session_state.api_key, type="password")
if entered_api_key:
    st.session_state.api_key = entered_api_key

input_mode = st.sidebar.radio("डेटा इनपुट पद्धत निवडा:", ["📷 Option Chain Image Upload", "⌨️ Manual Data Entry"])

image = None
manual_data = ""

if "Image" in input_mode:
    uploaded_file = st.sidebar.file_uploader("ऑप्शन चेनचा स्क्रीनशॉट अपलोड करा", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="अपलोड केलेली ऑप्शन चेन इमेज", use_container_width=True)
else:
    manual_data = st.sidebar.text_area("येथे ऑप्शन चेनचा डेटा किंवा आकडे मॅन्युअली पेस्ट करा:")

# मुख्य विश्लेषणाचे बटन
if st.sidebar.button("🚀 ELIP PRO ॲनालिसिस सुरू करा"):
    if not st.session_state.api_key:
        st.error("कृपया ॲपच्या साईडबारमध्ये तुमची Gemini API Key प्रविष्ट करा!")
    else:
        try:
            client = genai.Client(api_key=st.session_state.api_key)
            
            with st.spinner("ELIP PRO AI डेटाचे सखोल विश्लेषण करत आहे..."):
                prompt = """
                हा एक शेअर मार्केटच्या Option Chain चा डेटा किंवा स्क्रीनशॉट आहे. ELIP PRO सिस्टीमच्या आधारे खालील मुद्द्यांवर मराठीत अचूक आणि सविस्तर विश्लेषण द्या:
                
                1. 🟢 **Support Levels:** S1, S2, S3 (Put OI च्या आधारावर).
                2. 🔴 **Resistance Levels:** R1, R2, R3 (Call OI च्या आधारावर).
                3. 🧮 **PCR & Max Pain:** सध्याचा PCR आणि Max Pain लेव्हल काय सांगते.
                4. 📊 **CE/PE OI Analysis:** कॉल आणि पुट ओआयमधील बदल (Long/Short buildup).
                5. 📈 **Market Trend:** Bullish / Bearish / Sideways पैकी नक्की कल काय आहे?
                6. 📜 **Previous vs Current Comparison:** डेटा मधील संभाव्य हालचालींची तुलना.
                7. 🟢/🟡/🔴 **Trade Status:** Setup / Wait / No Clear Setup यापैकी सध्याची योग्य स्थिती कोणती?
                8. 📤 **Summary Report:** व्हॉट्सॲपवर शेअर करता येईल असा शॉर्ट आणि पॉवरफुल रिपोर्ट.
                """
                
                if image:
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[image, prompt]
                    )
                else:
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[manual_data, prompt]
                    )
                
                # 3. हिस्ट्रीमध्ये नवीन रिपोर्ट जतन करणे (वेळेसह)
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                report_entry = {"time": current_time, "text": response.text}
                st.session_state.history.insert(0, report_entry)
                
                st.success("विश्लेषण यशस्वीरीत्या पूर्ण झाले!")
                
        except Exception as e:
            st.error(f"काहीतरी त्रुटी आली आहे: {e}")

# जर हिस्ट्रीमध्ये रिपोर्ट्स असतील तर ते दाखवणे आणि थेट व्हॉट्सॲप शेअर बटण देणे
if st.session_state.history:
    st.markdown("---")
    st.markdown("### 📊 ताज ॲनालिसिस रिपोर्ट:")
    latest_report = st.session_state.history[0]
    st.markdown(latest_report['text'])
    
    # 2. थेट व्हॉट्सॲप शेअरिंग बटण (One-Click WhatsApp Share Link)
    import urllib.parse
    encoded_report = urllib.parse.quote(latest_report['text'])
    whatsapp_url = f"https://api.whatsapp.com/send?text={encoded_report}"
    
    st.markdown(f"""
        <a href="{whatsapp_url}" target="_blank">
            <button style="background-color:#25D366; color:white; padding:10px 20px; border:none; border-radius:5px; font-weight:bold; cursor:pointer; width:100%;">
                📤 थेट व्हॉट्सॲपवर शेअर करा (Share to WhatsApp)
            </button>
        </a>
    """, unsafe_allow_html=True)
    
    # मागील इतिहासाची (History) यादी दाखवणे
    if len(st.session_state.history) > 1:
        with st.expander("📜 मागील ॲनालिसिस हिस्ट्री पहा (Previous History)"):
            for i, hist in enumerate(st.session_state.history[1:], 1):
                st.markdown(f"**वेळ: {hist['time']}**")
                st.markdown(hist['text'])
                st.markdown("---")

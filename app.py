import streamlit as st
from PIL import Image
import os
from google import genai

st.set_page_config(page_title="ELIP PRO Option Chain Analyzer", page_icon="🎯", layout="wide")

st.title("🎯 ELIP PRO — Option Chain & AI Market Analyzer")
st.markdown("---")

# Sidebar for Settings & Inputs
st.sidebar.header("⚙️ ॲप सेटिंग्ज आणि इनपुट")
api_key = st.sidebar.text_input("Google Gemini API Key टाका:", type="password")

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
    if not api_key:
        st.error("कृपया ॲपच्या साईडबारमध्ये तुमची Gemini API Key प्रविष्ट करा!")
    else:
        try:
            client = genai.Client(api_key=api_key)
            
            with st.spinner("ELIP PRO AI डेटाचे सखोल विश्लेषण करत आहे..."):
                # सर्व प्रॉम्प्ट्स एकत्र करून प्रो लेव्हल विश्लेषण मागवणे
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
                        model='gemini-2.5-flash',
                        contents=[image, prompt]
                    )
                else:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[manual_data, prompt]
                    )
                
                st.success("विश्लेषण यशस्वीरीत्या पूर्ण झाले!")
                st.markdown("### 📊 ELIP PRO ॲनालिसिस रिपोर्ट:")
                st.markdown(response.text)
                
                # WhatsApp Share Mockup Button
                st.info("💡 टीप: वरील रिपोर्ट कॉपी करून तुम्ही थेट व्हॉट्सॲप ग्रुपवर शेअर करू शकता!")
                
        except Exception as e:
            st.error(f"काहीतरी त्रुटी आली आहे: {e}")

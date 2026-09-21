import streamlit as st
from PIL import Image
from google import genai
import urllib.parse
import time

# =========================================================
# NAKSH PRO 3.0
# =========================================================

st.set_page_config(
    page_title="Naksh Pro 3.0",
    page_icon="🎯",
    layout="wide"
)

# -------------------------
# BASIC UI
# -------------------------

st.title("🎯 Naksh Pro 3.0")
st.caption("ELIP PRO • Dynamic Scoring • Confirmation Matrix • What Changed")

st.markdown("---")

# -------------------------
# SESSION STATE
# -------------------------

if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if "history" not in st.session_state:
    st.session_state.history = []

# -------------------------
# SIDEBAR
# -------------------------

st.sidebar.header("⚙️ Naksh Pro Settings")

api_key = st.sidebar.text_input(
    "Gemini API Key",
    value=st.session_state.api_key,
    type="password"
)

if api_key:
    st.session_state.api_key = api_key

mode = st.sidebar.radio(
    "Analysis Mode",
    [
        "🚀 ELIP PRO Analysis",
        "🔄 What Changed?"
    ]
)

# -------------------------
# IMAGE UPLOAD
# -------------------------

images = []

if mode == "🚀 ELIP PRO Analysis":

    files = st.sidebar.file_uploader(
        "Price Action / Option Chain Screenshots",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    if files:
        for file in files:
            img = Image.open(file)
            images.append(img)

            st.sidebar.image(
                img,
                caption=file.name,
                use_container_width=True
            )

else:

    old_file = st.sidebar.file_uploader(
        "1️⃣ जुना Screenshot",
        type=["png", "jpg", "jpeg"]
    )

    new_file = st.sidebar.file_uploader(
        "2️⃣ नवीन Screenshot",
        type=["png", "jpg", "jpeg"]
    )

    if old_file and new_file:

        old_img = Image.open(old_file)
        new_img = Image.open(new_file)

        images = [old_img, new_img]

        st.sidebar.image(
            old_img,
            caption="जुना Screenshot",
            use_container_width=True
        )

        st.sidebar.image(
            new_img,
            caption="नवीन Screenshot",
            use_container_width=True
        )

# -------------------------
# PROMPTS
# -------------------------

ELIP_PROMPT = """
तुम्ही Naksh Pro 3.0 Market Intelligence Analyzer आहात.

दिलेल्या Price Action Chart आणि Option Chain screenshot चे
structured analysis करा.

महत्त्वाचे:
- screenshot मध्ये दिसणाऱ्या डेटावरच analysis करा.
- डेटा स्पष्ट दिसत नसल्यास "डेटा उपलब्ध नाही" असे सांगा.
- अंदाजाला निश्चित भविष्यवाणी म्हणून मांडू नका.
- Risk management स्पष्ट ठेवा.

=============================
1. MARKET STRUCTURE
=============================

• Current Market Level
• Trend: Bullish / Bearish / Sideways
• Price Action Structure
• Breakout / Breakdown / Range

=============================
2. DYNAMIC SUPPORT
=============================

S1:
S2:
S3:

प्रत्येकासाठी:
• OI
• Change in OI
• Volume
• Price Action
• Strength Score /10

=============================
3. RESISTANCE
=============================

R1:
R2:
R3:

प्रत्येकासाठी:
• OI
• Change in OI
• Volume
• Price Action
• Strength Score /10

=============================
4. OPTION CHAIN
=============================

• PCR
• PCR Change
• Max Pain
• Strongest PE support
• Strongest CE resistance
• Important OI concentration

=============================
5. CONFIRMATION MATRIX
=============================

Create this table:

| Factor | Signal | Score |
|---|---|---|
| Price Action | | /10 |
| PE OI | | /10 |
| CE OI | | /10 |
| PCR | | /10 |
| Volume | | /10 |

TOTAL SCORE: /50

Interpretation:

40-50 = Strong confirmation
30-39 = Moderate confirmation
20-29 = Weak / Wait
Below 20 = No clear setup

=============================
6. NO TRADE FILTER
=============================

जर signals conflicting असतील किंवा market range च्या मध्यभागी
असेल तर:

🟡 NO CLEAR SETUP — WAIT

स्पष्ट confirmation नसताना setup force करू नका.

=============================
7. ELIP PRO SETUP
=============================

संभाव्य setup असल्यास:

Direction:
Entry Zone:
Confirmation:
Invalidation / SL:
Target 1:
Target 2:
Trail SL:

जर setup स्पष्ट नसेल तर:
"NO TRADE"

=============================
8. WHAT CAN CHANGE THE VIEW
=============================

• कोणता level break झाला तर bullish view बदलू शकतो?
• कोणता level break झाला तर bearish view बदलू शकतो?
• कोणत्या OI change कडे लक्ष द्यावे?

=============================
9. SHORT WHATSAPP REPORT
=============================

Naksh Pro 3.0

Market:
Trend:
Key Support:
Key Resistance:
PCR:
Max Pain:
Score:
Setup:
Entry:
SL:
T1:
T2:
Status:

हा भाग short आणि WhatsApp-friendly ठेवा.
"""

CHANGE_PROMPT = """
तुम्हाला दोन screenshots दिले आहेत.

पहिला = जुना
दुसरा = नवीन

Naksh Pro 3.0 What Changed Analysis करा.

फक्त दिसणाऱ्या डेटावर आधारित comparison करा.

=============================
1. PRICE ACTION CHANGE
=============================

जुन्या screenshot मधील level:
नवीन screenshot मधील level:

Trend मध्ये काय बदलला?

=============================
2. CALL OI CHANGE
=============================

CE OI:
जुना →
नवीन →

Change:

=============================
3. PUT OI CHANGE
=============================

PE OI:
जुना →
नवीन →

Change:

=============================
4. PCR CHANGE
=============================

Old PCR:
New PCR:
Change:

=============================
5. SUPPORT / RESISTANCE
=============================

Support:
• मजबूत / कमकुवत / नवीन

Resistance:
• मजबूत / कमकुवत / नवीन

=============================
6. VOLUME / PRICE ACTION
=============================

काही significant change असल्यास सांगा.

=============================
7. CONFIRMATION
=============================

Bullish confirmations:
Bearish confirmations:
Conflicting signals:

=============================
8. CURRENT STATUS
=============================

🟢 Bullish Confirmation
🔴 Bearish Confirmation
🟡 No Clear Setup

यापैकी योग्य status निवडा.

=============================
9. WHAT TO WATCH NEXT
=============================

महत्त्वाचे levels आणि OI changes सांगा.

=============================
10. SHORT WHATSAPP SUMMARY
=============================

Old → New:

CE OI:
PE OI:
PCR:
Support:
Resistance:
Trend:
Status:
"""

# -------------------------
# ANALYSIS FUNCTION
# -------------------------

def run_analysis(client, images, prompt):

    contents = images + [prompt]

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=contents
            )

            return response.text

        except Exception as error:

            if "503" in str(error) and attempt < 2:
                time.sleep(3)
            else:
                raise error

# -------------------------
# ANALYSIS BUTTON
# -------------------------

if st.sidebar.button(
    "🚀 Naksh Pro Analysis सुरू करा",
    use_container_width=True
):

    if not st.session_state.api_key:

        st.error("कृपया Gemini API Key टाका.")

    elif not images:

        st.warning("कृपया आवश्यक screenshot upload करा.")

    else:

        try:

            client = genai.Client(
                api_key=st.session_state.api_key
            )

            with st.spinner(
                "🎯 Naksh Pro 3.0 analysis करत आहे..."
            ):

                if mode == "🚀 ELIP PRO Analysis":
                    report = run_analysis(
                        client,
                        images,
                        ELIP_PROMPT
                    )
                else:
                    report = run_analysis(
                        client,
                        images,
                        CHANGE_PROMPT
                    )

            st.session_state.history.insert(
                0,
                {
                    "time": time.strftime(
                        "%d-%m-%Y %H:%M:%S"
                    ),
                    "text": report
                }
            )

            st.success(
                "✅ Naksh Pro Analysis पूर्ण झाले!"
            )

        except Exception as error:

            st.error(
                "Analysis failed. API Key, internet connection "
                "किंवा Gemini model availability तपासा."
            )

# -------------------------
# CURRENT REPORT
# -------------------------

if st.session_state.history:

    st.markdown("---")

    st.subheader("📊 Naksh Pro Reports")

    for index, report in enumerate(
        st.session_state.history
    ):

        with st.expander(
            f"🕒 {report['time']}",
            expanded=(index == 0)
        ):

            st.markdown(report["text"])

            # WhatsApp
            whatsapp_text = urllib.parse.quote(
                report["text"]
            )

            whatsapp_url = (
                "https://api.whatsapp.com/send?text="
                + whatsapp_text
            )

            st.markdown(
                f"""
                <a href="{whatsapp_url}" target="_blank">
                    <button style="
                        background:#25D366;
                        color:white;
                        border:none;
                        padding:10px 18px;
                        border-radius:7px;
                        font-weight:bold;
                    ">
                    📤 WhatsApp वर Share करा
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                f"🗑️ Report Delete #{index + 1}",
                key=f"delete_{index}"
            ):

                st.session_state.history.pop(index)
                st.rerun()

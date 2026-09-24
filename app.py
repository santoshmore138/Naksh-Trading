import streamlit as st
import pandas as pd
import json
import os
import uuid
from datetime import datetime

# =========================================================
# SCREENSHOT ANALYSIS PRO
# NIFTY 50 | BANK NIFTY | SENSEX
# API-FREE STARTER VERSION
# =========================================================

st.set_page_config(
    page_title="Screenshot Analysis PRO",
    page_icon="📊",
    layout="wide"
)

HISTORY_FILE = "analysis_history.json"


# ---------------- HISTORY ----------------

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


if "history" not in st.session_state:
    st.session_state.history = load_history()


# ---------------- SCORE ENGINE ----------------

def calculate_score(
    trend,
    vwap,
    volume,
    price_action,
    option_chain
):
    score = 50
    confirmations = []
    warnings = []

    # TREND
    if trend == "Bullish":
        score += 10
        confirmations.append("Bullish Trend")

    elif trend == "Bearish":
        score += 10
        confirmations.append("Bearish Trend")

    else:
        warnings.append("Trend Neutral")

    # VWAP
    if vwap == "Above VWAP":
        score += 8
        confirmations.append("Price Above VWAP")

    elif vwap == "Below VWAP":
        score += 8
        confirmations.append("Price Below VWAP")

    else:
        warnings.append("VWAP Confirmation नाही")

    # VOLUME
    if volume == "Strong":
        score += 8
        confirmations.append("Strong Volume")

    elif volume == "Weak":
        score -= 5
        warnings.append("Weak Volume")

    # PRICE ACTION
    if price_action == "Bullish Breakout":
        score += 8
        confirmations.append("Bullish Breakout")

    elif price_action == "Bearish Breakdown":
        score += 8
        confirmations.append("Bearish Breakdown")

    elif price_action == "Possible Fake Breakout":
        score -= 12
        warnings.append("Possible Fake Breakout")

    # OPTION CHAIN
    if option_chain == "PE Support":
        score += 8
        confirmations.append("PE OI Support")

    elif option_chain == "CE Resistance":
        score += 8
        confirmations.append("CE OI Resistance")

    elif option_chain == "Conflicting":
        score -= 10
        warnings.append("Option Chain Conflicting")

    else:
        warnings.append("Option Chain Data नाही")

    score = max(0, min(score, 100))

    # FINAL SETUP
    if score < 55 or len(warnings) >= 2:
        setup = "WAIT"

    elif trend == "Bullish" and score >= 70:
        setup = "BUY CE"

    elif trend == "Bearish" and score >= 70:
        setup = "BUY PE"

    else:
        setup = "WATCH"

    return score, setup, confirmations, warnings


# ---------------- HEADER ----------------

st.title("📊 Screenshot Analysis PRO")

st.caption(
    "Option Chain + Price Action + Confirmation Matrix + Saved History"
)


# ---------------- SIDEBAR ----------------

st.sidebar.header("⚙️ PRO SETTINGS")

index = st.sidebar.selectbox(
    "Select Index",
    [
        "NIFTY 50",
        "BANK NIFTY",
        "SENSEX"
    ]
)

timeframe = st.sidebar.selectbox(
    "Chart Timeframe",
    [
        "5 Minute",
        "15 Minute"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info(
    "Clear screenshot वापरा. "
    "Blurred किंवा cropped data मुळे analysis quality कमी होऊ शकते."
)


# =========================================================
# SCREENSHOT UPLOAD
# =========================================================

st.subheader("📸 Screenshot Upload")

col1, col2 = st.columns(2)


with col1:

    st.markdown("### 📊 Option Chain Screenshot")

    option_file = st.file_uploader(
        "Option Chain Upload करा",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp"
        ],
        key="option_chain"
    )

    if option_file:
        st.image(
            option_file,
            caption="Option Chain",
            use_container_width=True
        )


with col2:

    st.markdown("### 📈 Price Action Chart")

    chart_file = st.file_uploader(
        "Price Action Chart Upload करा",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp"
        ],
        key="price_chart"
    )

    if chart_file:
        st.image(
            chart_file,
            caption="Price Action",
            use_container_width=True
        )


st.divider()


# =========================================================
# VERIFIED INPUTS
# =========================================================

st.subheader("🧠 Analysis Verification")

st.warning(
    "Screenshot मध्ये स्पष्ट दिसणारी माहितीच निवडा. "
    "दिसत नसलेली माहिती अंदाजाने भरू नका."
)


c1, c2, c3 = st.columns(3)


with c1:

    trend = st.selectbox(
        "Market Trend",
        [
            "Bullish",
            "Bearish",
            "Neutral"
        ]
    )

    vwap = st.selectbox(
        "VWAP",
        [
            "Above VWAP",
            "Below VWAP",
            "Near / Unknown"
        ]
    )


with c2:

    volume = st.selectbox(
        "Volume",
        [
            "Strong",
            "Normal",
            "Weak"
        ]
    )

    price_action = st.selectbox(
        "Price Action",
        [
            "No Clear Breakout",
            "Bullish Breakout",
            "Bearish Breakdown",
            "Possible Fake Breakout"
        ]
    )


with c3:

    option_chain = st.selectbox(
        "Option Chain Confirmation",
        [
            "PE Support",
            "CE Resistance",
            "Conflicting",
            "Unavailable"
        ]
    )

    spot_price = st.text_input(
        "Spot Price"
    )


# =========================================================
# LEVELS
# =========================================================

st.subheader("🎯 Trade Levels")

l1, l2, l3, l4 = st.columns(4)


with l1:
    entry = st.text_input("Entry")


with l2:
    stop_loss = st.text_input("Stop Loss")


with l3:
    target1 = st.text_input("Target 1")


with l4:
    target2 = st.text_input("Target 2")


st.divider()


# =========================================================
# ANALYSIS
# =========================================================

if st.button(
    "🧠 ANALYZE PRO",
    type="primary",
    use_container_width=True
):

    if not option_file and not chart_file:

        st.error(
            "किमान एक screenshot upload करा."
        )

    else:

        score, setup, confirmations, warnings = calculate_score(
            trend,
            vwap,
            volume,
            price_action,
            option_chain
        )

        st.subheader(
            f"{index} — PRO ANALYSIS"
        )

        r1, r2, r3 = st.columns(3)

        r1.metric(
            "Setup Score",
            f"{score}/100"
        )

        r2.metric(
            "Trend",
            trend
        )

        r3.metric(
            "Setup",
            setup
        )


        # ---------------- SIGNAL ----------------

        if setup == "BUY CE":

            st.success(
                "🟢 BUY CE SETUP"
            )

        elif setup == "BUY PE":

            st.error(
                "🔴 BUY PE SETUP"
            )

        elif setup == "WAIT":

            st.warning(
                "🟡 WAIT — Clear Confirmation नाही"
            )

        else:

            st.info(
                "🟡 WATCH — आणखी Confirmation आवश्यक"
            )


        # ---------------- CONFIRMATION ----------------

        a, b = st.columns(2)


        with a:

            st.markdown(
                "### ✅ Confirmations"
            )

            if confirmations:

                for item in confirmations:
                    st.write(
                        "✓",
                        item
                    )

            else:

                st.write(
                    "Strong confirmation नाही."
                )


        with b:

            st.markdown(
                "### ⚠️ Warnings"
            )

            if warnings:

                for item in warnings:
                    st.write(
                        "⚠️",
                        item
                    )

            else:

                st.write(
                    "Major warning नाही."
                )


        # ---------------- LEVELS ----------------

        st.markdown(
            "### 🎯 Trade Levels"
        )

        t1, t2, t3, t4 = st.columns(4)

        t1.metric(
            "Entry",
            entry or "—"
        )

        t2.metric(
            "SL",
            stop_loss or "—"
        )

        t3.metric(
            "Target 1",
            target1 or "—"
        )

        t4.metric(
            "Target 2",
            target2 or "—"
        )


        # =================================================
        # SAVE
        # =================================================

        record = {

            "id":
                str(uuid.uuid4())[:8],

            "date_time":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "index":
                index,

            "timeframe":
                timeframe,

            "spot_price":
                spot_price,

            "trend":
                trend,

            "score":
                score,

            "setup":
                setup,

            "vwap":
                vwap,

            "volume":
                volume,

            "price_action":
                price_action,

            "option_chain":
                option_chain,

            "entry":
                entry,

            "stop_loss":
                stop_loss,

            "target1":
                target1,

            "target2":
                target2,

            "confirmations":
                confirmations,

            "warnings":
                warnings,

            "option_screenshot":
                option_file.name
                if option_file
                else "",

            "chart_screenshot":
                chart_file.name
                if chart_file
                else ""
        }


        st.session_state.history.insert(
            0,
            record
        )

        # Keep latest 200
        st.session_state.history = \
            st.session_state.history[:200]

        save_history(
            st.session_state.history
        )


        st.success(
            "💾 Analysis History मध्ये Save झाले."
        )


# =========================================================
# HISTORY
# =========================================================

st.divider()

st.subheader(
    "📚 Saved Analysis History"
)


if st.session_state.history:

    df = pd.DataFrame(
        st.session_state.history
    )


    display_columns = [
        "date_time",
        "index",
        "timeframe",
        "trend",
        "score",
        "setup",
        "spot_price",
        "entry",
        "stop_loss",
        "target1",
        "target2"
    ]


    display_columns = [
        x for x in display_columns
        if x in df.columns
    ]


    st.dataframe(
        df[display_columns],
        use_container_width=True,
        hide_index=True
    )


    csv_data = df.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )


    st.download_button(
        "⬇️ Download History CSV",
        csv_data,
        "option_analysis_history.csv",
        "text/csv",
        use_container_width=True
    )


    if st.button(
        "🗑️ Clear All History"
    ):

        st.session_state.history = []

        save_history([])

        st.rerun()


else:

    st.info(
        "अजून कोणतेही analysis save केलेले नाही."
    )


# =========================================================
# WHAT CHANGED
# =========================================================

st.divider()

st.subheader(
    "🧠 What Changed?"
)


if len(st.session_state.history) >= 2:

    latest = \
        st.session_state.history[0]

    previous = \
        st.session_state.history[1]


    q1, q2, q3 = st.columns(3)


    score_difference = (
        latest["score"]
        -
        previous["score"]
    )


    q1.metric(
        "Score Change",
        f"{score_difference:+d}",
        f'{previous["score"]} → {latest["score"]}'
    )


    q2.metric(
        "Current Setup",
        latest["setup"],
        f'Previous: {previous["setup"]}'
    )


    q3.metric(
        "Current Trend",
        latest["trend"],
        f'Previous: {previous["trend"]}'
    )


    changed_items = []


    for field in [
        "vwap",
        "volume",
        "price_action",
        "option_chain"
    ]:

        old_value = previous.get(
            field
        )

        new_value = latest.get(
            field
        )


        if old_value != new_value:

            changed_items.append(
                f"{field}: "
                f"{old_value} → {new_value}"
            )


    if changed_items:

        for item in changed_items:

            st.write(
                "•",
                item
            )

    else:

        st.write(
            "मुख्य confirmation मध्ये बदल नाही."
        )


else:

    st.info(
        "What Changed पाहण्यासाठी "
        "किमान 2 analysis save करा."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Educational analysis tool. "
    "Score हा setup-strength indicator आहे; "
    "तो win probability किंवा profit guarantee नाही. "
    "Screenshot interpretation मध्ये चुका होऊ शकतात."
)

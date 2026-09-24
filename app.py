import base64
import io
import json
import re
import urllib.parse
from datetime import datetime

import anthropic
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

# ---------------------------------------------------------------
# अँप कॉन्फिगरेशन आणि डार्क थीम लूक
# ---------------------------------------------------------------
st.set_page_config(page_title="Naksh Pro 2.0", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
    html, body, [class*="css"] { font-size: 14px; }
    .trade-plan-box {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #30363d;
        margin-bottom: 20px;
        color: white;
    }
    .sig-ce { border-color: #2ea043; }
    .sig-pe { border-color: #f85149; }
    .sig-wait { border-color: #d29922; }
    .sig-title { font-size: 22px; font-weight: 700; margin-bottom: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

COLS = ["strike", "ce_oi", "ce_oi_chg", "pe_oi", "pe_oi_chg"]
DEFAULT_MODEL = "claude-sonnet-5"

EXTRACT_PROMPT = """You are given screenshot(s) of an Indian index chart and/or an option chain.
Extract ONLY what is clearly visible. If a value is not visible or you are unsure, use null.
NEVER guess or invent numbers. Copy numbers exactly as displayed (no commas, do not convert units).

Return ONLY one JSON object, no other text, with this schema:
{
  "index": string|null,
  "spot": number|null,
  "timeframe": string|null,
  "trend": "up"|"down"|"sideways"|null,
  "vwap": number|null,
  "price_support_levels": [numbers visible on chart as support/swing lows],
  "price_resistance_levels": [numbers visible on chart as resistance/swing highs],
  "total_ce_oi": number|null,
  "total_pe_oi": number|null,
  "chain": [
    {"strike": number, "ce_oi": number|null, "ce_oi_chg": number|null,
     "pe_oi": number|null, "pe_oi_chg": number|null}
  ],
  "notes": string
}
"trend" must be judged from the visible candles only."""

REPORT_SYSTEM = (
    "तू 'ELIP PRO' नावाचा Nifty option चे विश्लेषण करणारा सहाय्यक आहेस. फक्त मराठीत लिही. "
    "दिलेल्या JSON मधील आकडेच वापर; स्वतःचे नवीन आकडे, स्तर किंवा अंदाज शोधू नकोस. "
    "जिथे मूल्य null आहे तिथे 'डेटा उपलब्ध नाही' लिही. 'signal' चे मूल्य बदलू नकोस, फक्त त्याचे कारण समजाव. "
    "नफ्याची हमी देऊ नकोस. उत्तर संक्षिप्त ठेव."
)


# ---------------------------------------------------------------
# मदतीचे फंक्शन्स
# ---------------------------------------------------------------
def get_secret_key():
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except Exception:
        return ""


def nz(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def prep_image(f):
    img = Image.open(f).convert("RGB")
    img.thumbnail((2400, 2400))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    data = base64.b64encode(buf.getvalue()).decode()
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/jpeg", "data": data},
    }


def ask_claude(client, model, content, system, max_tokens):
    r = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")


def parse_json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("JSON सापडला नाही")
    return json.loads(text[start : end + 1])


# ---------------------------------------------------------------
# आकडेमोड (कोडमध्ये - AI कडून नाही)
# ---------------------------------------------------------------
def analyze(spot, trend, vwap, tot_ce, tot_pe, chain_df, chart_sup, chart_res):
    df = chain_df.copy()
    for c in COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["strike"]).sort_values("strike").reset_index(drop=True)

    ce = df["ce_oi"].fillna(0)
    pe = df["pe_oi"].fillna(0)

    if tot_ce and tot_pe:
        pcr, pcr_src = round(tot_pe / tot_ce, 2), "Total OI"
    elif ce.sum() > 0:
        pcr, pcr_src = round(pe.sum() / ce.sum(), 2), "दिसणारे स्ट्राइक्स"
    else:
        pcr, pcr_src = None, "डेटा नाही"

    max_pain = None
    if len(df) >= 5 and (ce.sum() + pe.sum()) > 0:
        k = df["strike"].values
        pain = [
            (ce.values * np.clip(s - k, 0, None)).sum()
            + (pe.values * np.clip(k - s, 0, None)).sum()
            for s in k
        ]
        max_pain = float(k[int(np.argmin(pain))])

    supports = df.dropna(subset=["pe_oi"]).nlargest(3, "pe_oi")["strike"].tolist()
    resists = df.dropna(subset=["ce_oi"]).nlargest(3, "ce_oi")["strike"].tolist()
    below = [s for s in supports if s < spot]
    above = [r for r in resists if r > spot]
    nsup = max(below) if below else None
    nres = min(above) if above else None

    has_chg = df["ce_oi_chg"].notna().any() and df["pe_oi_chg"].notna().any()
    ce_chg = float(df["ce_oi_chg"].sum()) if has_chg else None
    pe_chg = float(df["pe_oi_chg"].sum()) if has_chg else None

    bull, bear = [], []
    # 1) ट्रेंड
    if trend == "up":
        bull.append("चार्ट ट्रेंड वर")
    if trend == "down":
        bear.append("चार्ट ट्रेंड खाली")
    # 2) VWAP
    if vwap:
        if spot > vwap:
            bull.append("किंमत VWAP च्या वर")
        elif spot < vwap:
            bear.append("किंमत VWAP च्या खाली")
    # 3) PCR
    if pcr is not None:
        if pcr >= 1.1:
            bull.append(f"PCR {pcr} (बुलिश)")
        elif pcr <= 0.9:
            bear.append(f"PCR {pcr} (बेअरिश)")
    # 4) OI बदल
    if has_chg:
        if pe_chg > ce_chg:
            bull.append("Put OI वाढ > Call OI वाढ")
        elif ce_chg > pe_chg:
            bear.append("Call OI वाढ > Put OI वाढ")
    # 5) मार्गात wall नाही (किमान 0.25% जागा)
    if spot > 0:
        if nres is None or (nres - spot) / spot * 100 >= 0.25:
            bull.append("वर रेझिस्टन्स wall जवळ नाही")
        if nsup is None or (spot - nsup) / spot * 100 >= 0.25:
            bear.append("खाली सपोर्ट wall जवळ नाही")

    signal, note, rr = "WAIT", "किमान 4/5 अटी जुळल्या नाहीत.", None
    if len(bull) >= 4 and len(bull) > len(bear):
        signal = "BUY CE"
    elif len(bear) >= 4 and len(bear) > len(bull):
        signal = "BUY PE"

    if signal != "WAIT" and nsup and nres:
        risk = (spot - nsup) if signal == "BUY CE" else (nres - spot)
        reward = (nres - spot) if signal == "BUY CE" else (spot - nsup)
        if risk > 0:
            rr = round(reward / risk, 2)
            if rr < 1.5:
                signal, note = "WAIT", f"Risk:Reward कमी ({rr}) - ट्रेड टाळा."
    if signal != "WAIT":
        note = "अटी जुळल्या; SL आणि पोझिशन साइज पाळा."

    return {
        "time": datetime.now().strftime("%d-%b %H:%M"),
        "spot": spot,
        "trend": trend,
        "vwap": vwap or None,
        "pcr": pcr,
        "pcr_source": pcr_src,
        "max_pain": max_pain,
        "oi_support_strikes": supports,
        "oi_resistance_strikes": resists,
        "chart_supports": chart_sup,
        "chart_resistances": chart_res,
        "nearest_support": nsup,
        "nearest_resistance": nres,
        "ce_oi_change_total": ce_chg,
        "pe_oi_change_total": pe_chg,
        "bull_score": len(bull),
        "bear_score": len(bear),
        "bull_reasons": bull,
        "bear_reasons": bear,
        "risk_reward": rr,
        "signal": signal,
        "signal_note": note,
        "_df": df,
    }


def whatsapp_text(r):
    def fmt(v):
        return ", ".join(str(int(x)) for x in v) if v else "-"

    icon = {"BUY CE": "🟢", "BUY PE": "🔴", "WAIT": "🟡"}[r["signal"]]
    return (
        f"📊 *NIFTY QUICK UPDATE* 📊\n"
        f"🗓 {r['time']} | Spot: {r['spot']:.0f}\n\n"
        f"🟢 *Support:* {fmt(r['oi_support_strikes'])}\n"
        f"🔴 *Resistance:* {fmt(r['oi_resistance_strikes'])}\n"
        f"📉 PCR: {r['pcr'] if r['pcr'] is not None else '-'} | "
        f"Max Pain: {int(r['max_pain']) if r['max_pain'] else '-'}\n"
        f"📈 Trend: {r['trend'] or '-'}\n"
        f"{icon} *Status:* {r['signal']}\n"
        f"💡 {r['signal_note']}\n\n"
        f"⚠️ शैक्षणिक विश्लेषण, गुंतवणूक सल्ला नाही."
    )


def render_result(r):
    css = {"BUY CE": "sig-ce", "BUY PE": "sig-pe", "WAIT": "sig-wait"}[r["signal"]]
    icon = {"BUY CE": "🟢", "BUY PE": "🔴", "WAIT": "🟡"}[r["signal"]]
    reasons = r["bull_reasons"] if r["bull_score"] >= r["bear_score"] else r["bear_reasons"]
    lvl = ""
    if r["nearest_support"] or r["nearest_resistance"]:
        lvl = (
            f"<br>जवळचा सपोर्ट: <b>{r['nearest_support'] or '-'}</b> | "
            f"जवळचा रेझिस्टन्स: <b>{r['nearest_resistance'] or '-'}</b>"
        )
    st.markdown(
        f"""<div class="trade-plan-box {css}">
        <div class="sig-title">{icon} STATUS: {r['signal']}</div>
        {r['signal_note']}<br>
        स्कोअर - Bull: <b>{r['bull_score']}/5</b> | Bear: <b>{r['bear_score']}/5</b>
        {lvl}<br>
        <small>{' • '.join(reasons) if reasons else ''}</small>
        </div>""",
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Spot", f"{r['spot']:.0f}")
    m2.metric("PCR", r["pcr"] if r["pcr"] is not None else "-", help=f"स्रोत: {r['pcr_source']}")
    m3.metric("Max Pain", int(r["max_pain"]) if r["max_pain"] else "-")

    s1, s2 = st.columns(2)
    s1.success("🟢 OI Support (Put OI): " + (", ".join(str(int(x)) for x in r["oi_support_strikes"]) or "-"))
    s2.error("🔴 OI Resistance (Call OI): " + (", ".join(str(int(x)) for x in r["oi_resistance_strikes"]) or "-"))

    df = r["_df"]
    if len(df) > 0:
        fig = go.Figure()
        fig.add_bar(x=df["strike"], y=df["pe_oi"], name="Put OI", marker_color="#2ea043")
        fig.add_bar(x=df["strike"], y=df["ce_oi"], name="Call OI", marker_color="#f85149")
        fig.update_layout(
            barmode="group",
            template="plotly_dark",
            height=340,
            margin=dict(l=10, r=10, t=30, b=10),
            title="Strike-wise OI",
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------
# सत्र स्थिती
# ---------------------------------------------------------------
for k, v in {"ext": None, "ext_id": 0, "result": None, "report": None, "history": []}.items():
    st.session_state.setdefault(k, v)

# ---------------------------------------------------------------
# साइडबार
# ---------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ सेटिंग्ज")
    secret_key = get_secret_key()
    if secret_key:
        st.success("API Key: Secrets मधून मिळाली ✅")
        api_key = secret_key
    else:
        api_key = st.text_input("Anthropic API Key", type="password", help="sk-ant-...")
    model = st.text_input("Model", value=DEFAULT_MODEL)
    st.caption("Key GitHub वर कोडमध्ये कधीही टाकू नका. Streamlit Secrets वापरा.")

# ---------------------------------------------------------------
# मुख्य स्क्रीन
# ---------------------------------------------------------------
st.title("📈 Naksh Pro 2.0")
st.caption("Nifty Option Chain विश्लेषण | आकडेमोड कोडमध्ये, स्पष्टीकरण Claude कडून")

files = st.file_uploader(
    "चार्ट / Option Chain स्क्रीनशॉट अपलोड करा (एक किंवा अनेक)",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
)

b1, b2 = st.columns(2)
if b1.button("📥 स्क्रीनशॉटमधून डेटा वाचा", type="primary", use_container_width=True):
    if not files:
        st.warning("आधी स्क्रीनशॉट अपलोड करा.")
    elif not api_key:
        st.warning("साइडबारमध्ये API Key टाका.")
    else:
        with st.spinner("Claude स्क्रीनशॉट वाचत आहे..."):
            try:
                client = anthropic.Anthropic(api_key=api_key)
                content = [prep_image(f) for f in files] + [{"type": "text", "text": EXTRACT_PROMPT}]
                txt = ask_claude(
                    client, model, content,
                    "You are a precise data extraction tool. Output JSON only.", 3000,
                )
                st.session_state.ext = parse_json(txt)
                st.session_state.ext_id += 1
                st.session_state.result = None
                st.session_state.report = None
            except Exception as e:
                st.error(f"डेटा वाचता आला नाही: {e}")

if b2.button("✍️ मॅन्युअल एंट्री", use_container_width=True):
    st.session_state.ext = {}
    st.session_state.ext_id += 1
    st.session_state.result = None
    st.session_state.report = None

ex = st.session_state.ext
if ex is not None:
    eid = st.session_state.ext_id
    st.subheader("✏️ डेटा तपासा / दुरुस्त करा")
    st.caption("AI कडून वाचताना आकडे चुकू शकतात. विश्लेषणापूर्वी खालील आकडे स्क्रीनशॉटशी जुळवा.")

    a, b, c, d = st.columns(4)
    spot = a.number_input("Spot", value=nz(ex.get("spot")), step=1.0, key=f"spot{eid}")
    trend_opts = ["up", "down", "sideways", "unknown"]
    tr0 = ex.get("trend") if ex.get("trend") in trend_opts else "unknown"
    trend = b.selectbox("Trend", trend_opts, index=trend_opts.index(tr0), key=f"tr{eid}")
    vwap = c.number_input("VWAP (0 = माहीत नाही)", value=nz(ex.get("vwap")), step=1.0, key=f"vw{eid}")
    d.caption(f"Timeframe: {ex.get('timeframe') or '-'}")

    e, f = st.columns(2)
    tot_ce = e.number_input("Total CE OI (0 = माहीत नाही)", value=nz(ex.get("total_ce_oi")), key=f"tce{eid}")
    tot_pe = f.number_input("Total PE OI (0 = माहीत नाही)", value=nz(ex.get("total_pe_oi")), key=f"tpe{eid}")

    rows = ex.get("chain") or []
    df0 = pd.DataFrame(rows).reindex(columns=COLS) if rows else pd.DataFrame(columns=COLS)
    for col in COLS:
        df0[col] = pd.to_numeric(df0[col], errors="coerce")
    chain_df = st.data_editor(df0, num_rows="dynamic", use_container_width=True, key=f"chain{eid}")

    if ex.get("price_support_levels") or ex.get("price_resistance_levels"):
        st.caption(
            f"चार्टवरील सपोर्ट: {ex.get('price_support_levels')} | "
            f"रेझिस्टन्स: {ex.get('price_resistance_levels')}"
        )
    if ex.get("notes"):
        st.caption(f"Claude ची नोंद: {ex.get('notes')}")

    if st.button("📊 विश्लेषण करा", type="primary", use_container_width=True):
        if spot <= 0:
            st.warning("Spot किंमत टाका.")
        else:
            res = analyze(
                spot, trend, vwap or None, tot_ce or None, tot_pe or None, chain_df,
                ex.get("price_support_levels") or [], ex.get("price_resistance_levels") or [],
            )
            prev = st.session_state.history[-1] if st.session_state.history else None
            st.session_state.result = res
            st.session_state.report = None
            clean = {k: v for k, v in res.items() if k != "_df"}
            st.session_state.history.append(clean)
            st.session_state.history = st.session_state.history[-5:]

            if api_key:
                with st.spinner("Claude विश्लेषण लिहित आहे..."):
                    try:
                        client = anthropic.Anthropic(api_key=api_key)
                        prompt = (
                            "खालील गणिती निकालांच्या आधारे मराठीत या विभागांत लिही:\n"
                            "### OI विश्लेषण (CE/PE)\n### मार्केट ट्रेंड\n"
                            "### आधीची vs सध्याची तुलना (previous null असेल तर 'तुलनेसाठी आधीचा डेटा नाही' लिही)\n"
                            "### ट्रेड कधी करावा (CE खरेदी / PE खरेदी अटी, फक्त दिलेले स्तर वापरून)\n"
                            "### जोखीम\nप्रत्येक विभाग 3-4 ओळींत.\n\n"
                            f"current = {json.dumps(clean, ensure_ascii=False)}\n"
                            f"previous = {json.dumps(prev, ensure_ascii=False)}"
                        )
                        st.session_state.report = ask_claude(
                            client, model, [{"type": "text", "text": prompt}], REPORT_SYSTEM, 2500
                        )
                    except Exception as e:
                        st.error(f"स्पष्टीकरण मिळाले नाही: {e}")

res = st.session_state.result
if res:
    st.divider()
    render_result(res)
    if st.session_state.report:
        st.markdown("### 🧠 Claude चे स्पष्टीकरण")
        st.markdown(st.session_state.report)

    st.markdown("### 📤 WhatsApp Summary")
    wa = whatsapp_text(res)
    st.code(wa, language="text")
    st.link_button("WhatsApp वर पाठवा", "https://wa.me/?text=" + urllib.parse.quote(wa))

st.divider()
st.caption(
    "⚠️ हे शैक्षणिक विश्लेषण आहे, गुंतवणूक सल्ला नाही. Option trading मध्ये मोठा तोटा होऊ शकतो. "
    "नेहमी Stop-loss वापरा आणि जोखीम मर्यादित ठेवा."
)

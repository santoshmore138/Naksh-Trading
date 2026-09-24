import base64
import datetime
import sqlite3
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

app = FastAPI(title="Screenshot Analysis PRO")

# --- 1. DATABASE SETUP (History & Saving) ---
DB_FILE = "trading_analysis.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            index_name TEXT,
            market_bias TEXT,
            dynamic_score INTEGER,
            pcr REAL,
            max_pain REAL,
            result_json TEXT,
            whatsapp_summary TEXT,
            option_chain_img TEXT,
            chart_img TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()


# --- 2. LOGIC & CALCULATIONS ---
def calculate_pcr_and_max_pain(ocr_data: dict):
  """Option Chain मधील डेटा वरून PCR आणि Max Pain कॅल्क्युलेट करणे"""
  total_pe_oi = ocr_data.get("total_pe_oi", 1000000)
  total_ce_oi = ocr_data.get("total_ce_oi", 900000)

  # PCR Formula = Total PE OI / Total CE OI
  pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.0

  # Simplified Max Pain estimation logic (Pro level वर स्ट्राइक प्राईसचे OI बघून ठरवले जाते)
  max_pain = ocr_data.get("atm_strike", 24500)

  return pcr, max_pain


def generate_whatsapp_summary(data: dict) -> str:
  """WhatsApp वर शेअर करण्यासाठी रेडीमेड समरी बनवणे"""
  summary = (
      f"🚨 *SCREENSHOT ANALYSIS PRO REPORT* 🚨\n"
      f"📅 Date/Time: {data['timestamp']}\n"
      f"📊 Index: {data['index_name']}\n\n"
      f"🎯 *Market Bias:* {data['market_bias']} (Score: {data['dynamic_score']}/100)\n"
      f"📉 *PCR:* {data['pcr']} | ⚙️ *Max Pain:* {data['max_pain']}\n\n"
      f"📌 *Setup:* {data['setup_type']}\n"
      f"🟢 *Entry:* {data['entry']}\n"
      f"🔴 *Stop Loss:* {data['stop_loss']}\n"
      f"🎯 *Targets:* T1: {data['target_1']} | T2: {data['target_2']} | T3:"
      f" {data['target_3']}\n"
      f"⚖️ *Risk/Reward:* {data['risk_reward']}\n\n"
      f"_Disclaimer: Educational Purpose Only._"
  )
  return summary


# --- 3. API ENDPOINT FOR ANALYSIS ---
@app.post("/analyze/")
async def analyze_screenshots(
    index_name: str = Form(
        ..., description="NIFTY 50 / BANK NIFTY / SENSEX"
    ),
    option_chain: UploadFile = File(None),
    price_action: UploadFile = File(None),
):
  timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  # Images save करणे (Base64 किंवा Local Storage मध्ये)
  oc_bytes = (
      await option_chain.read() if option_chain else b""
  )
  pa_bytes = await price_action.read() if price_action else b""

  oc_b64 = base64.b64encode(oc_bytes).decode("utf-8") if oc_bytes else ""
  pa_b64 = base64.b64encode(pa_bytes).decode("utf-8") if pa_bytes else ""

  # [Mock OCR & AI Engine Output - प्रत्यक्ष ॲपमध्ये इथे OpenAI Vision / Custom OCR वापरला जाईल]
  mock_ocr_data = {
      "total_pe_oi": 12500000,
      "total_ce_oi": 10200000,
      "atm_strike": 24500,
  }

  pcr, max_pain = calculate_pcr_and_max_pain(mock_ocr_data)

  # Dynamic Score & Confirmation Matrix Logic
  dynamic_score = 78
  market_bias = "Bullish" if pcr > 1.0 else "Bearish"

  analysis_result = {
      "timestamp": timestamp,
      "index_name": index_name,
      "market_bias": market_bias,
      "dynamic_score": dynamic_score,
      "pcr": pcr,
      "max_pain": max_pain,
      "setup_type": "CE Buy on Dip",
      "entry": 24520,
      "stop_loss": 24470,
      "target_1": 24600,
      "target_2": 24680,
      "target_3": 24750,
      "risk_reward": "1:2.5",
  }

  whatsapp_text = generate_whatsapp_summary(analysis_result)
  analysis_result["whatsapp_summary"] = whatsapp_text

  # --- 4. DATABASE SAVE (History) ---
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO analyses (timestamp, index_name, market_bias, dynamic_score, pcr, max_pain, result_json, whatsapp_summary, option_chain_img, chart_img)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
      (
          timestamp,
          index_name,
          market_bias,
          dynamic_score,
          pcr,
          max_pain,
          str(analysis_result),
          whatsapp_text,
          oc_b64[:100],  # साठवणुकीसाठी छोटं रूप (किंवा फाईल पाथ)
          pa_b64[:100],
      ),
  )
  conn.commit()
  conn.close()

  return {
      "status": "Success",
      "message": "Analysis completed and saved successfully!",
      "data": analysis_result,
  }


# --- 5. HISTORY ENDPOINT ---
@app.get("/history/")
def get_history():
  conn = sqlite3.connect(DB_FILE)
  conn.row_factory = sqlite3.Row
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, timestamp, index_name, market_bias, dynamic_score, pcr,"
      " whatsapp_summary FROM analyses ORDER BY id DESC LIMIT 20"
  )
  rows = cursor.fetchall()
  conn.close()
  return [dict(row) for row in rows]

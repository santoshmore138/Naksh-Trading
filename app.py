import datetime
import json
import sqlite3
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from google import genai
from google.genai import types

app = FastAPI(title="Naksh Pro 2.0 Market Intelligence")

# ----------------- DATABASE SETUP (History) -----------------
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
            whatsapp_summary TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()

# ----------------- GEMINI API CONFIGURATION -----------------
client = genai.Client()


@app.post("/analyze-pro/")
async def analyze_pro(
    index_name: str = Form(
        ..., description="NIFTY 50 / BANK NIFTY / SENSEX"
    ),
    option_chain: UploadFile = File(None),
    price_action: UploadFile = File(None),
):
  timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  contents = [
      f"You are an expert Indian Stock Market Options Trading Analyst. Analyze these screenshots together for {index_name}. "
      "Perform a Combined Analysis (Option Chain + Price Action Chart) and return ONLY a valid JSON object with the following exact keys: "
      '{"ocr_verified": true/false, "market_bias": "Bullish/Bearish/Neutral", "dynamic_score": 0-100, '
      '"pcr": 1.15, "max_pain": 24500, "demand_supply_zone": "string", "support_levels": ["S1", "S2", "S3"], '
      '"resistance_levels": ["R1", "R2", "R3"], "setup_type": "CE Buy/PE Buy/No Trade", '
      '"entry": 0.0, "stop_loss": 0.0, "target_1": 0.0, "target_2": 0.0, "target_3": 0.0, '
      '"risk_reward": "1:2", "no_trade_reason": "null or reason", "whatsapp_summary": "Clean WhatsApp text report with emojis"}'
  ]

  # इमेजेस जोडणे
  if option_chain:
    oc_bytes = await option_chain.read()
    contents.append(
        types.Part.from_bytes(data=oc_bytes, mime_type=option_chain.content_type)
    )

  if price_action:
    pa_bytes = await price_action.read()
    contents.append(
        types.Part.from_bytes(data=pa_bytes, mime_type=price_action.content_type)
    )

  try:
    # येथे लेटेस्ट आणि अपडेटेड मॉडेल वापरले आहे (एरर येणार नाही)
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    analysis_data = json.loads(response.text)

    # ----------------- DATABASE SAVE -----------------
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO analyses (timestamp, index_name, market_bias, dynamic_score, pcr, max_pain, result_json, whatsapp_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            index_name,
            analysis_data.get("market_bias", "Neutral"),
            analysis_data.get("dynamic_score", 50),
            analysis_data.get("pcr", 1.0),
            analysis_data.get("max_pain", 0),
            json.dumps(analysis_data),
            analysis_data.get("whatsapp_summary", ""),
        ),
    )
    conn.commit()
    conn.close()

    return {
        "status": "Success",
        "timestamp": timestamp,
        "data": analysis_data,
    }

  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"तांत्रिक त्रुटी आली आहे: {str(e)}"
    )


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

import base64
import json
import os
from fastapi import FastAPI, File, Form, UploadFile
import openai  # OpenAI API (GPT-4o Vision साठी)

app = FastAPI(title="Screenshot Analysis PRO - Combined Engine")

# OpenAI API Key सेट करा
openai.api_key = "YOUR_OPENAI_API_KEY"


def encode_image(image_bytes):
  return base64.b64encode(image_bytes).decode("utf-8")


@app.post("/combined-analysis/")
async def combined_analysis(
    index_name: str = Form(...),  # NIFTY 50 / BANK NIFTY / SENSEX
    option_chain: UploadFile = File(...),
    price_action: UploadFile = File(...),
):

  # फाइल्स बाईट्समध्ये वाचणे
  oc_bytes = await option_chain.read()
  pa_bytes = await price_action.read()

  oc_base64 = encode_image(oc_bytes)
  pa_base64 = encode_image(pa_bytes)

  # AI साठी अत्यंत डोकं लावणारा Prompt (System Prompt)
  prompt_text = f"""
    You are an expert Indian Stock Market Options Trading Analyst. 
    Analyze these two screenshots together for {index_name}:
    1. Option Chain Screenshot (for OI, Change in OI, PCR, Max Pain, Support/Resistance from OI).
    2. Price Action Chart Screenshot (for Trend, Demand/Supply zones, Candlestick pattern, S1/S2/S3, R1/R2/R3).

    Perform a Combined Analysis and return ONLY a valid JSON object with the following exact keys:
    - "ocr_verified": true/false (if numbers are blurry or mismatch, set false and explain)
    - "market_bias": "Bullish" or "Bearish" or "Neutral"
    - "dynamic_score": integer between 0 to 100
    - "pcr": calculated Put-Call Ratio (float)
    - "max_pain": estimated Max Pain strike (integer)
    - "demand_supply_zone": "string describing zone"
    - "support_levels": ["S1", "S2", "S3"]
    - "resistance_levels": ["R1", "R2", "R3"]
    - "setup_type": "CE Buy / PE Buy / No Trade"
    - "entry": integer/float
    - "stop_loss": integer/float
    - "target_1": integer/float
    - "target_2": integer/float
    - "target_3": integer/float
    - "risk_reward": "1:2.5"
    - "no_trade_reason": "null if trade exists, otherwise reason why to avoid"
    - "confirmation_matrix": "Score breakdown or short summary"
    - "whatsapp_summary": "Ready to send clean WhatsApp text report with emojis"
    """

  try:
    # OpenAI Vision API कॉल
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{oc_base64}"
                    },
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{pa_base64}"
                    },
                },
            ],
        }],
        max_tokens=1500,
    )

    ai_response_content = response.choices[0].message.content
    # JSON पार्स करणे
    analysis_data = json.loads(
        ai_response_content.replace("```json", "").replace("```", "").strip()
    )

    return {
        "status": "Success",
        "index": index_name,
        "result": analysis_data,
    }

  except Exception as e:
    return {
        "status": "Error",
        "message": (
            "Analysis failed. Please check screenshots or API key. Error:"
            f" {str(e)}"
        ),
    }

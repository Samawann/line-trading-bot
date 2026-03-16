from flask import Flask, request
import requests
import os

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

# LINE credentials
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

API_BASE = "https://btc-algorithms.onrender.com"

# ===== BTC API =====
def get_btc_prediction():

    url = "https://btc-algorithms.onrender.com/predict"

    try:
        r = requests.get(url)
        data = r.json()

        last_price = data["last_close"]
        predicted_price = data["predicted_close"]
        change = data["predicted_change_pct"]

        if change > 1:
            signal = "BUY"
        elif change < -1:
            signal = "SELL"
        else:
            signal = "HOLD"

        msg = f"""
📊 BTC Dashboard

💰 Current Price
${last_price:,.2f}

🔮 Predicted Price
${predicted_price:,.2f}

📉 Change
{change:.2f} %

📢 Signal
{signal}
"""

        return msg

    except Exception as e:
        print("API error:", e)
        return "Error getting BTC prediction"


# ===== LINE WEBHOOK =====
@app.route("/callback", methods=['POST'])
def callback():

    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    except Exception as e:
        print("Webhook error:", e)

    return 'OK'


# ===== MESSAGE HANDLER =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.lower()

    # ===== DASHBOARD =====
    if text == "btc":
        reply = get_btc_prediction()

    elif text == "price":
        reply = get_btc_prediction()

    elif text == "predict":
        reply = get_btc_prediction()

    else:
        reply = """
Commands

btc → BTC dashboard
price → current + prediction
predict → BTC forecast
"""

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


# ===== RUN SERVER =====
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
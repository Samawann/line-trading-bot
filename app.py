from flask import Flask, request, abort
import requests
import os

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "YOUR_CHANNEL_ACCESS_TOKEN"
CHANNEL_SECRET = "YOUR_CHANNEL_SECRET"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

API_BASE = "https://btc-algorithms.onrender.com"


# ===== GET BTC PREDICTION =====
def get_prediction():

    try:
        r = requests.get(f"{API_BASE}/predict")
        data = r.json()

        price = data.get("last_close")
        prediction = data.get("predicted_close")
        change = data.get("predicted_change_pct")

        return price, prediction, change

    except:
        return None, None, None


# ===== GET SIGNAL =====
def get_signal():

    try:
        r = requests.get(f"{API_BASE}/signal")
        data = r.json()

        return data.get("signal")

    except:
        return None


# ===== WEBHOOK =====
@app.route("/callback", methods=['POST'])
def callback():

    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ===== LINE BOT =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.lower()

    # ===== DASHBOARD =====
    if text == "btc":

        price, prediction, change = get_prediction()
        signal = get_signal()

        if price:
            price = f"${price:,.2f}"

        if prediction:
            prediction = f"${prediction:,.2f}"

        if change:
            change = f"{change:.2f}%"

        flex = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [

                    {
                        "type": "text",
                        "text": "BTC Trading Dashboard",
                        "weight": "bold",
                        "size": "xl"
                    },

                    {
                        "type": "text",
                        "text": f"Price: {price}",
                        "size": "lg"
                    },

                    {
                        "type": "text",
                        "text": f"Prediction: {prediction}",
                        "size": "md"
                    },

                    {
                        "type": "text",
                        "text": f"Predicted Change: {change}",
                        "size": "md"
                    },

                    {
                        "type": "text",
                        "text": f"Signal: {signal}",
                        "size": "lg",
                        "weight": "bold",
                        "color": "#00AA00"
                    },

                    {
                        "type": "text",
                        "text": f"Volatility: {volatility}",
                        "size": "lg"
                    }

                ]
            }
        }

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(
                alt_text="BTC Dashboard",
                contents=flex
            )
        )


    elif text == "predict":

        price, prediction, change = get_prediction()

        msg = f"""
BTC Prediction

Current Price: {price}
Predicted Price: {prediction}
Change: {change}
"""

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )


    elif text == "signal":

        signal = get_signal()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"Trading Signal: {signal}")
        )

        return


    elif text == "predict":

        price, prediction = get_prediction()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"Current Price: {price}\nPrediction: {prediction}"
            )
        )


    else:

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="พิมพ์ btc เพื่อดู BTC Dashboard"
            )
        )


# ===== RUN SERVER =====
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
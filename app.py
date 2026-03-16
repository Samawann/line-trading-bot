from flask import Flask, request, abort
import requests
import os

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

# ===== LINE TOKEN =====
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


# ===== HOME =====
@app.route("/")
def home():
    return "BTC AI Trading Bot Running"


# ===== WEBHOOK =====
@app.route("/callback", methods=['POST'])
def callback():

    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ===== MESSAGE EVENT =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.lower().strip()


    # ===== DASHBOARD =====
    if text == "btc":

        try:

            predict_api = requests.get(
                "https://btc-algorithms.onrender.com/predict-price",
                timeout=10
            ).json()

            signal_api = requests.get(
                "https://btc-algorithms.onrender.com/trading-signal",
                timeout=10
            ).json()

            volatility_api = requests.get(
                "https://btc-algorithms.onrender.com/volatility",
                timeout=10
            ).json()

            price = predict_api.get("current_price", "N/A")
            prediction = predict_api.get("predicted_price", "N/A")
            signal = signal_api.get("signal", "N/A")
            volatility = volatility_api.get("volatility", "N/A")

        except Exception as e:

            print(e)

            price = "N/A"
            prediction = "N/A"
            signal = "N/A"
            volatility = "N/A"


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
                        "type": "separator"
                    },

                    {
                        "type": "text",
                        "text": f"Price: ${price}",
                        "size": "lg"
                    },

                    {
                        "type": "text",
                        "text": f"Prediction: ${prediction}",
                        "size": "lg"
                    },

                    {
                        "type": "text",
                        "text": f"Signal: {signal}",
                        "size": "lg",
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

        return


    # ===== PREDICT =====
    if text == "predict":

        try:

            data = requests.get(
                "https://btc-algorithms.onrender.com/predict-price"
            ).json()

            price = data.get("predicted_price")

            reply = f"Predicted BTC Price\n${price}"

        except:

            reply = "Prediction API error"


        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )

        return


    # ===== SIGNAL =====
    if text == "signal":

        try:

            data = requests.get(
                "https://btc-algorithms.onrender.com/trading-signal"
            ).json()

            signal = data.get("signal")

            reply = f"Trading Signal: {signal}"

        except:

            reply = "Signal API error"


        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )

        return


    # ===== VOLATILITY =====
    if text == "volatility":

        try:

            data = requests.get(
                "https://btc-algorithms.onrender.com/volatility"
            ).json()

            vol = data.get("volatility")

            reply = f"BTC Volatility: {vol}"

        except:

            reply = "Volatility API error"


        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )

        return


    # ===== HELP =====
    help_text = """
BTC AI Trading Bot

Commands
btc → dashboard
predict → price prediction
signal → trading signal
volatility → volatility
"""

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=help_text)
    )


# ===== RUN SERVER =====
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
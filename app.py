from flask import Flask, request, abort
import requests
import os

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, FlexSendMessage
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
    return "LINE BTC AI Bot Running"


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


# ===== MESSAGE EVENT =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.lower().strip()

    # ===== BTC DASHBOARD =====
    if text == "btc":   

        try:

            price = requests.get(
                "https://btc-algorithms.onrender.com/btc"
            ).json()["price"]

            prediction = requests.get(
                "https://btc-algorithms.onrender.com/predict"
            ).json()["prediction"]

            signal = requests.get(
                "https://btc-algorithms.onrender.com/signal"
            ).json()["signal"]

        except:

            price = "N/A"
            prediction = "N/A"
            signal = "N/A"

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


    # ===== PREDICTION =====
    if text == "predict":

        try:

            data = requests.get(
                "https://btc-algorithms.onrender.com/predict"
            ).json()

            prediction = data["prediction"]

            reply = f"Predicted BTC Price\n${prediction}"

        except:

            reply = "Prediction API error"

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(
                alt_text="Prediction",
                contents={
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "BTC Prediction",
                                "weight": "bold",
                                "size": "xl"
                            },
                            {
                                "type": "text",
                                "text": f"${prediction}",
                                "size": "lg"
                            }
                        ]
                    }
                }
            )
        )

        return


    # ===== SIGNAL =====
    if text == "signal":

        try:

            data = requests.get(
                "https://btc-algorithms.onrender.com/signal"
            ).json()

            signal = data["signal"]

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"Trading Signal: {signal}"
                )
            )

        except:

            signal = "API Error"

        flex = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [

                    {
                        "type": "text",
                        "text": "Trading Signal",
                        "weight": "bold",
                        "size": "xl"
                    },

                    {
                        "type": "text",
                        "text": signal,
                        "size": "xxl",
                        "color": "#FF0000"
                    }

                ]
            }
        }

        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(
                alt_text="Trading Signal",
                contents=flex
            )
        )

        return


    # ===== HELP =====
    help_text = """
BTC AI Trading Bot

Commands
btc → Trading dashboard
predict → price prediction
signal → buy/sell signal
"""

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(
            alt_text="Help",
            contents={
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Bot Commands",
                            "weight": "bold",
                            "size": "xl"
                        },
                        {
                            "type": "text",
                            "text": help_text
                        }
                    ]
                }
            }
        )
    )


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )
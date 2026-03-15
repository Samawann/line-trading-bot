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
    return "LINE Trading Bot Running"


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

    # ===== BTC PRICE =====
    if text == "btc":

        try:

            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            data = requests.get(url).json()

            price = data["bitcoin"]["usd"]

            flex_message = {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "BTC PRICE",
                            "weight": "bold",
                            "size": "xl"
                        },
                        {
                            "type": "text",
                            "text": f"${price}",
                            "size": "lg",
                            "color": "#00AA00"
                        },
                        {
                            "type": "text",
                            "text": "Real-time Bitcoin price",
                            "size": "sm",
                            "color": "#999999"
                        }
                    ]
                }
            }

            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(
                    alt_text="BTC Price",
                    contents=flex_message
                )
            )

        except Exception as e:

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Error getting BTC price")
            )


    # ===== HELP MENU =====
    else:

        reply = """
BTC Trading Bot

Commands
btc → BTC price
predict → prediction
signal → trading signal
"""

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )


# ===== RUN SERVER =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
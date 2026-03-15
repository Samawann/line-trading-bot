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

    return 'OK'


# ===== MESSAGE EVENT =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.lower()

    # ===== BTC PRICE =====
    if text == "btc":

        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            data = response.json()

            price = data["bitcoin"]["usd"]

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"BTC Price: ${price}")
            )

        except Exception as e:

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Error getting BTC price")
            )

        return


    # ===== PREDICT =====
    if text == "predict":

        try:

            response = requests.get(
                "https://btc-algorithms.onrender.com/predict",
                timeout=10
            )

            data = response.json()
            prediction = data["prediction"]

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"BTC Predicted Price\n${prediction}"
                )
            )

        except:

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Prediction API error")
            )

        return


    # ===== SIGNAL =====
    if text == "signal":

        try:

            response = requests.get(
                "https://btc-algorithms.onrender.com/signal",
                timeout=10
            )

            data = response.json()
            signal = data["signal"]

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"Trading Signal: {signal}"
                )
            )

        except:

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Signal API error")
            )

        return


    # ===== DEFAULT =====
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text="Commands:\nbtc\npredict\nsignal"
        )
    )


# ===== RUN SERVER =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
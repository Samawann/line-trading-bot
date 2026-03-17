from flask import Flask, request, abort
import requests
import os
from datetime import datetime

from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    FlexSendMessage,
    ImageSendMessage
)
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ===== API =====
def get_btc():

    url = "https://btc-algorithms.onrender.com/predict"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()

        price = data["last_close"]
        predict = data["predicted_close"]
        change = data["predicted_change_pct"]

        signal = "HOLD"

        if change > 1:
            signal = "BUY"
        elif change < -1:
            signal = "SELL"

        return price, predict, change, signal

    except Exception as e:
        print("API ERROR:", e)
        return None, None, None, None


# ===== BTC DASHBOARD (เดิม) =====
def handle_btc(event):

    price, predict, change, signal = get_btc()
    now = datetime.now().strftime("%d %b %Y | %H:%M")

    bubble = {
      "type": "bubble",
      "size": "mega",
      "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [

          {
            "type": "text",
            "text": "BTC Trading Dashboard",
            "weight": "bold",
            "size": "xl",
            "color": "#F7931A"
          },
          {
            "type": "text",
            "text": f"Updated: {now}",
            "size": "sm",
            "color": "#999999"
          },
          {
            "type": "separator",
            "margin": "md"
          },
          {
            "type": "text",
            "text": f"💰 Price: ${price}",
            "size": "lg"
          },
          {
            "type": "text",
            "text": f"🔮 Prediction: ${predict}",
            "size": "md"
          },
          {
            "type": "text",
            "text": f"📉 Change: {change} %",
            "size": "md"
          },
          {
            "type": "text",
            "text": f"📊 Signal: {signal}",
            "size": "lg",
            "weight": "bold"
          }

        ]
      }
    }

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(
            alt_text="BTC Dashboard",
            contents=bubble
        )
    )


# ===== SIGNAL (เดิม) =====
def handle_signal(event):

    price, predict, change, signal = get_btc()

    msg = f"""
BTC Signal

Price: ${price}
Prediction: ${predict}

Change: {change} %

Signal: {signal}

BUY → แนวโน้มขึ้น
SELL → แนวโน้มลง
HOLD → รอดูสถานการณ์
"""

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


# ===== CHART (เดิม) =====
def handle_chart(event):

    chart_url = "https://quickchart.io/chart?c={type:'line',data:{labels:['1','2','3','4','5','6'],datasets:[{label:'BTC',data:[65000,66000,65500,67000,69000,71000]}]}}"

    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(
            original_content_url=chart_url,
            preview_image_url=chart_url
        )
    )


# ===== BITCOIN INFO (เดิม) =====
def handle_bitcoin(event):

    msg = """
Bitcoin คือ Cryptocurrency

ใช้ Blockchain
ไม่มีธนาคารกลาง
มีจำนวนจำกัด 21 ล้านเหรียญ
"""

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


# ===== 🆕 แยกคำสั่ง =====
def handle_price(event):
    price, _, _, _ = get_btc()
    msg = f"💰 BTC Price: ${price}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


def handle_predict(event):
    _, predict, _, _ = get_btc()
    msg = f"🔮 BTC Prediction: ${predict}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


def handle_change(event):
    _, _, change, _ = get_btc()
    msg = f"📉 BTC Change: {change} %"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


def handle_signal_only(event):
    _, _, _, signal = get_btc()

    msg = f"""📊 BTC Signal: {signal}

BUY → ขึ้น
SELL → ลง
HOLD → รอดู
"""

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


# ===== HELP (อัปเดต) =====
def handle_help(event):

    msg = """
BTC AI Bot

Commands

btc → dashboard
signal → full signal
price → ราคา BTC
predict → ราคาคาดการณ์
change → % เปลี่ยน
signalonly → BUY/SELL
chart → กราฟ
bitcoin → about bitcoin
"""

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


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


# ===== ROUTER (อัปเดต) =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.lower()

    if text == "btc":
        handle_btc(event)

    elif text == "signal":
        handle_signal(event)

    elif text == "chart":
        handle_chart(event)

    elif text == "bitcoin":
        handle_bitcoin(event)

    elif text == "price":
        handle_price(event)

    elif text == "predict":
        handle_predict(event)

    elif text == "change":
        handle_change(event)

    elif text == "signalonly":
        handle_signal_only(event)

    else:
        handle_help(event)


# ===== RUN =====
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
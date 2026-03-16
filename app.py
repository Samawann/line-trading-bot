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

# LINE credentials
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


# ===== HOME =====
@app.route("/")
def home():
    return "LINE Trading Bot Running"


# ===== BTC API =====
def get_btc_data():

    try:

        url = "https://btc-algorithms.onrender.com/predict"

        r = requests.get(url,timeout=10)
        data = r.json()

        price = data.get("last_close","N/A")
        predict = data.get("predicted_close","N/A")
        change = data.get("predicted_change_pct","N/A")

        signal = "HOLD"

        if isinstance(change,(int,float)):
            if change > 1:
                signal = "BUY"
            elif change < -1:
                signal = "SELL"

        return price,predict,change,signal

    except Exception as e:

        print("API ERROR",e)

        return "N/A","N/A","N/A","HOLD"


# ===== FLEX DASHBOARD =====
def btc_dashboard(price,predict,change,signal):

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
            "color": "#888888"
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

    return FlexSendMessage(
        alt_text="BTC Dashboard",
        contents=bubble
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

    except Exception as e:
        print("Webhook error:", e)

    return "OK"


# ===== MESSAGE EVENT =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.lower()

    price,predict,change,signal = get_btc_data()


    # ===== DASHBOARD =====
    if text == "btc":

        flex = btc_dashboard(price,predict,change,signal)

        line_bot_api.reply_message(
            event.reply_token,
            flex
        )

        return


    # ===== SIGNAL =====
    if text == "signal":

        msg = f"""
BTC Trading Signal

Price: ${price}
Prediction: ${predict}

Change: {change} %

Signal: {signal}

Guide
BUY → แนวโน้มขึ้น
SELL → แนวโน้มลง
HOLD → รอดูสถานการณ์
"""

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )

        return


    # ===== BTC CHART =====
    if text == "chart":

        chart_url = "https://quickchart.io/chart?c={type:'line',data:{labels:['1','2','3','4','5','6'],datasets:[{label:'BTC',data:[65000,66000,65500,67000,69000,71000]}]}}"

        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url=chart_url,
                preview_image_url=chart_url
            )
        )

        return


    # ===== Q&A BITCOIN =====
    if "bitcoin" in text:

        reply = """
Bitcoin คือ Cryptocurrency

ใช้เทคโนโลยี Blockchain
ไม่มีธนาคารกลาง
มีจำนวนจำกัด 21 ล้านเหรียญ

ถูกใช้เป็นสินทรัพย์ลงทุน
"""

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply)
        )

        return


    # ===== HELP =====
    reply = """
BTC AI Bot

Commands

btc → dashboard
signal → trading signal
chart → btc chart
bitcoin → about bitcoin
"""

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


# ===== RUN SERVER =====
if __name__ == "__main__":

    port = int(os.environ.get("PORT",5000))

    app.run(host="0.0.0.0",port=port)
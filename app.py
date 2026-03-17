from flask import Flask, request, abort
import requests
import os
from datetime import datetime
import time
import threading

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

# ================= API =================
def get_btc():

    url = "https://btc-algorithms.onrender.com/predict"

    for _ in range(3):
        try:
            r = requests.get(url, timeout=15)
            data = r.json()

            price = data.get("last_close")
            predict = data.get("predicted_close")
            change = data.get("predicted_change_pct")

            if None in (price, predict, change):
                raise ValueError("Missing data")

            signal = "HOLD"
            if change > 0.5:
                signal = "BUY"
            elif change < -0.5:
                signal = "SELL"

            return price, predict, change, signal

        except:
            time.sleep(2)

    return None, None, None, None


# ================= CACHE =================
btc_cache = {"data": None, "timestamp": None}

def get_btc_smart():
    now = datetime.now()

    if btc_cache["data"] and (now - btc_cache["timestamp"]).seconds < 60:
        return btc_cache["data"]

    data = get_btc()

    if data[0] is None and btc_cache["data"]:
        return btc_cache["data"]

    btc_cache["data"] = data
    btc_cache["timestamp"] = now

    return data


# ================= DASHBOARD =================
def handle_btc(event):

    price, predict, change, signal = get_btc_smart()

    if price is None:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⚠️ API ล่ม")
        )
        return

    now = datetime.now().strftime("%d %b %Y | %H:%M")

    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "BTC Dashboard", "weight": "bold", "size": "xl"},
                {"type": "text", "text": now, "size": "sm"},
                {"type": "separator"},
                {"type": "text", "text": f"💰 ${price:,.2f}"},
                {"type": "text", "text": f"🔮 ${predict:,.2f}"},
                {"type": "text", "text": f"📉 {change:.2f}%"},
                {"type": "text", "text": f"📊 {signal}", "weight": "bold"}
            ]
        }
    }

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage("BTC", bubble)
    )


# ================= SIGNAL =================
def handle_signal(event):
    price, predict, change, signal = get_btc_smart()

    if price is None:
        reply = "⚠️ API ล่ม"
    else:
        reply = f"""
BTC Signal

Price: ${price:,.2f}
Prediction: ${predict:,.2f}

Change: {change:.2f} %
Signal: {signal}
"""

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


# ================= ANALYZE =================
def handle_analyze(event):
    price, predict, change, signal = get_btc_smart()

    if price is None:
        reply = "⚠️ วิเคราะห์ไม่ได้"
    else:
        trend = "Sideway"
        if change > 0.5:
            trend = "Uptrend"
        elif change < -0.5:
            trend = "Downtrend"

        reply = f"""
📊 BTC Analysis

Price: ${price:,.2f}
Prediction: ${predict:,.2f}

Trend: {trend}
Change: {change:.2f} %
Signal: {signal}
"""

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


# ================= ADV =================
def handle_adv(event):
    price, predict, change, signal = get_btc_smart()

    if price is None:
        reply = "⚠️ API ล่ม"
    else:
        risk = "LOW"
        if abs(change) > 1:
            risk = "HIGH"
        elif abs(change) > 0.5:
            risk = "MEDIUM"

        reply = f"""
Advanced Signal

Price: ${price:,.2f}
Prediction: ${predict:,.2f}

Change: {change:.2f} %
Signal: {signal}
Risk: {risk}
"""

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


# ================= COMPARE =================
def handle_compare(event):
    try:
        r = requests.get("https://btc-algorithms.onrender.com/compare", timeout=10)
        d = r.json()

        reply = f"""
Model Compare

ARIMA: {d.get('arima')}
LSTM: {d.get('lstm')}
GARCH: {d.get('garch')}

Best: {d.get('best_model')}
"""
    except:
        reply = "⚠️ เปรียบเทียบไม่ได้"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


# ================= HEALTH =================
def handle_health(event):
    try:
        r = requests.get("https://btc-algorithms.onrender.com/health", timeout=5)
        status = "🟢 OK" if r.status_code == 200 else "🔴 ERROR"
    except:
        status = "🔴 DOWN"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=status))


# ================= CHAT =================
def handle_chat_api(event, text):
    try:
        r = requests.post(
            "https://btc-algorithms.onrender.com/chat",
            json={"message": text},
            timeout=10
        )
        reply = r.json().get("response", "ตอบไม่ได้")
    except:
        reply = "⚠️ AI ไม่ตอบ"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))


# ================= CHART =================
def handle_chart(event):
    chart_url = "https://quickchart.io/chart?c={type:'line',data:{labels:['1','2'],datasets:[{label:'BTC',data:[65000,70000]}]}}"

    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(chart_url, chart_url)
    )


def handle_chart_real(event):
    price, predict, _, _ = get_btc_smart()

    if price is None:
        reply = "⚠️ โหลดกราฟไม่ได้"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    url = f"https://quickchart.io/chart?c={{type:'line',data:{{labels:['Now','Next'],datasets:[{{label:'BTC',data:[{price},{predict}]}}]}}}}"

    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(url, url)
    )


# ================= AUTO ALERT =================
last_signal = None

def check_signal():
    global last_signal

    price, predict, change, signal = get_btc_smart()

    if price is None:
        return

    if signal != last_signal:
        USER_ID = "YOUR_USER_ID"

        msg = f"🚨 {signal}\n${price:,.2f} → ${predict:,.2f}"

        try:
            line_bot_api.push_message(USER_ID, TextSendMessage(text=msg))
        except:
            pass

        last_signal = signal


def scheduler():
    while True:
        check_signal()
        time.sleep(60)


threading.Thread(target=scheduler, daemon=True).start()


# ================= WEBHOOK =================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ================= ROUTER =================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.lower()

    if text == "btc":
        handle_btc(event)

    elif text == "signal":
        handle_signal(event)

    elif text == "analyze":
        handle_analyze(event)

    elif text == "adv":
        handle_adv(event)

    elif text == "compare":
        handle_compare(event)

    elif text == "health":
        handle_health(event)

    elif text == "chart":
        handle_chart(event)

    elif text == "chart2":
        handle_chart_real(event)

    elif text.startswith("chat"):
        handle_chat_api(event, text)

    else:
        handle_chat_api(event, text)


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
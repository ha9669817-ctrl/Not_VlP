import telebot
from telebot import types
import requests
import json
import base64
from datetime import datetime, timedelta

# --- [ بياناتك الرسمية ] ---
BOT_TOKEN = "8478170976:AAHYHY1VrFtyqteJUOezyPVuyN7Fdae6mDI"
ADMIN_ID = 5031612259
GITHUB_TOKEN = "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"
GITHUB_REPO = "ha9669817-ctrl/Not_VIP"
DATABASE_FILE = "database.json"

bot = telebot.TeleBot(BOT_TOKEN)

def sync_github(data=None, get_sha=False):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATABASE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 1. جلب الملف أو إنشاؤه
    r = requests.get(url, headers=headers)
    sha = r.json().get('sha') if r.status_code == 200 else None
    
    if not data: # لو نبغى بس نقرأ
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode()
            return json.loads(content), sha
        return {"keys": {}}, None

    # 2. رفع الملف وتحديثه
    payload = {
        "message": "Update Keys",
        "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(),
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code in [200, 201]

@bot.message_handler(commands=['start'])
def welcome(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("➕ إنشاء مفتاح", callback_data="add"),
                   types.InlineKeyboardButton("📋 المفاتيح النشطة", callback_data="list"),
                   types.InlineKeyboardButton("🔗 رابط الأداة", callback_data="link"))
        bot.send_message(message.chat.id, "💎 **لوحة تحكم التاجر حمد**\nكل شيء مربوط بجيت هوب أوتوماتيك!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "add":
        msg = bot.send_message(call.message.chat.id, "📝 أرسل: `الاسم الايام` (مثلاً: VIP 30)")
        bot.register_next_step_handler(msg, process_add)
    elif call.data == "list":
        data, _ = sync_github()
        keys = data.get("keys", {})
        txt = "📋 **الأكواد الحالية:**\n" + "\n".join([f"🔑 `{k}` | ⏳ `{v['expiry']}`" for k, v in keys.items()]) if keys else "❌ لا يوجد"
        bot.send_message(call.message.chat.id, txt)
    elif call.data == "link":
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{DATABASE_FILE}"
        bot.send_message(call.message.chat.id, f"🚀 **هذا الرابط اللي تحطه في أداتك:**\n\n`{raw_url}`")

def process_add(message):
    try:
        name, days = message.text.split()[0], int(message.text.split()[1])
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        bot.send_message(message.chat.id, "⏳ جاري الرفع والربط...")
        
        data, _ = sync_github()
        data["keys"][name] = {"expiry": expiry}
        
        if sync_github(data):
            bot.send_message(message.chat.id, f"✅ **تم!**\nالمفتاح `{name}` جاهز في جيت هوب.")
        else:
            bot.send_message(message.chat.id, "❌ فشل الرفع، شيك على التوكن.")
    except:
        bot.send_message(message.chat.id, "⚠️ خطأ في الصيغة!")

bot.polling()

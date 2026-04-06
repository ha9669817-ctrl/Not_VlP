import telebot
from telebot import types
import requests
import json
import base64
from datetime import datetime, timedelta

# --- بيانات حمد المحدثة ---
BOT_TOKEN = "8689755411:AAFUVGg8c2adyi2ExCZ3wHOvikxbjTkkVZk"
OWNER_ID = 5031612259
GITHUB_TOKEN = "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"
GITHUB_REPO = "ha9669817-ctrl/Not_VIP" # تم التعديل حسب صورتك
GITHUB_BRANCH = "main"
DATABASE_FILE = "database.json"

bot = telebot.TeleBot(BOT_TOKEN)

def get_github_content(path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content']).decode()
        return json.loads(content), r.json()['sha']
    # إذا الملف غير موجود، ننشئ واحد جديد
    return {"keys": {}}, None

def save_to_github(path, data, sha=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {
        "message": "Update keys via Bot",
        "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(),
        "branch": GITHUB_BRANCH
    }
    if sha: payload["sha"] = sha
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code in [200, 201]

@bot.message_handler(commands=['start'])
def welcome(message):
    if message.from_user.id == OWNER_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("➕ إنشاء مفتاح", callback_data="gen_key"),
                   types.InlineKeyboardButton("📊 عرض الأكواد", callback_data="list_keys"))
        bot.send_message(message.chat.id, "💎 **لوحة تحكم حمد جاهزة**\nالمستودع المرتبط: `Not_VIP`", 
                         parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "gen_key":
        msg = bot.send_message(call.message.chat.id, "📝 أرسل: `الاسم الايام` (مثال: HAMAD_PRO 30)")
        bot.register_next_step_handler(msg, process_gen)
    elif call.data == "list_keys":
        data, _ = get_github_content(DATABASE_FILE)
        keys = data.get("keys", {})
        if not keys:
            bot.send_message(call.message.chat.id, "❌ لا توجد أكواد حالياً.")
            return
        txt = "📋 **الأكواد الحالية في GitHub:**\n"
        for k, v in keys.items():
            txt += f"🔑 `{k}` | ⏳ `{v['expiry']}`\n"
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")

def process_gen(message):
    try:
        parts = message.text.split()
        name, days = parts[0], int(parts[1])
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        data, sha = get_github_content(DATABASE_FILE)
        data["keys"][name] = {"expiry": expiry}
        
        if save_to_github(DATABASE_FILE, data, sha):
            bot.send_message(message.chat.id, f"✅ تم إنشاء المفتاح `{name}` بنجاح ورفعه لمشروعك Not_VIP.")
        else:
            bot.send_message(message.chat.id, "❌ فشل الرفع لـ GitHub، تأكد من التوكن.")
    except:
        bot.send_message(message.chat.id, "⚠️ صيغة خاطئة! أرسل (الاسم الايام)")

bot.polling()

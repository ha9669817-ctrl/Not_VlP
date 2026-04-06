import telebot
from telebot import types
import requests
import json
import base64
from datetime import datetime, timedelta

# --- بيانات حمد الشخصية (التوكن الجديد) ---
BOT_TOKEN = "8689755411:AAFUVGg8c2adyi2ExCZ3wHOvikxbjTkkVZk"
OWNER_ID = 5031612259
GITHUB_TOKEN = "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"
GITHUB_REPO = "ha9669817-ctrl/Not_VIP"
GITHUB_BRANCH = "main"
DATABASE_FILE = "database.json"

bot = telebot.TeleBot(BOT_TOKEN)

# دالة ذكية لجلب البيانات والـ SHA معاً
def get_github_data():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATABASE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            res = r.json()
            content = base64.b64decode(res['content']).decode()
            return json.loads(content), res['sha']
    except:
        pass
    return {"keys": {}}, None

# دالة الحفظ القوية (تضمن التحديث الإجباري)
def save_to_github(data, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATABASE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # التأكد من جلب آخر SHA لتجنب الرفض
    _, latest_sha = get_github_data()
    
    payload = {
        "message": f"Update keys: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(),
        "branch": GITHUB_BRANCH,
        "sha": latest_sha if latest_sha else sha
    }
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code in [200, 201]

@bot.message_handler(commands=['start'])
def welcome(message):
    if message.from_user.id == OWNER_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("➕ إنشاء مفتاح", callback_data="gen_key"),
                   types.InlineKeyboardButton("📊 عرض الأكواد", callback_data="list_keys"))
        bot.send_message(message.chat.id, "💎 **تم تحديث التوكن بنجاح يا حمد!**\nاللوحة الآن متصلة بـ GitHub وجاهزة للعمل.", 
                         parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "gen_key":
        msg = bot.send_message(call.message.chat.id, "📝 أرسل: `الاسم الايام` (مثال: HAMAD_VIP 30)")
        bot.register_next_step_handler(msg, process_gen)
    elif call.data == "list_keys":
        data, _ = get_github_data()
        keys = data.get("keys", {})
        if not keys:
            bot.send_message(call.message.chat.id, "❌ الملف فارغ حالياً.")
            return
        txt = "📋 **الأكواد النشطة في السيرفر:**\n"
        for k, v in keys.items():
            txt += f"🔑 `{k}` | ⏳ `{v['expiry']}`\n"
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")

def process_gen(message):
    try:
        parts = message.text.split()
        if len(parts) < 2: raise Exception()
        
        name, days = parts[0], int(parts[1])
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        bot.send_message(message.chat.id, "⏳ جاري الرفع إلى GitHub...")
        
        data, sha = get_github_data()
        data["keys"][name] = {"expiry": expiry}
        
        if save_to_github(data, sha):
            bot.send_message(message.chat.id, f"✅ **نجح الحفظ!**\nالمفتاح: `{name}`\nالانتهاء: `{expiry}`")
        else:
            bot.send_message(message.chat.id, "❌ فشل الرفع. تأكد من صلاحيات التوكن الجديد.")
    except:
        bot.send_message(message.chat.id, "⚠️ خطأ! أرسل (الاسم مسافة الرقم).")

print("Bot is LIVE...")
bot.infinity_polling()

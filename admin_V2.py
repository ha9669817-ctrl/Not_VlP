import telebot
from telebot import types
import requests
import json
import base64
from datetime import datetime, timedelta

# --- إعداداتك الخاصة ---
BOT_TOKEN = "8689755411:AAFUVGg8c2adyi2ExCZ3wHOvikxbjTkkVZk"
OWNER_ID = 5031612259
GITHUB_TOKEN = "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"
GITHUB_REPO = "ha9669817-ctrl/Not_VIP"
GITHUB_BRANCH = "main"
DATABASE_FILE = "database.json"

bot = telebot.TeleBot(BOT_TOKEN)

def get_or_create_github_file():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATABASE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        res = r.json()
        content = base64.b64decode(res['content']).decode()
        return json.loads(content), res['sha']
    elif r.status_code == 404:
        # إذا الملف غير موجود، نرجعه كقاموس فارغ وبدون SHA
        return {"keys": {}}, None
    return None, None

def save_to_github(data, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATABASE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    payload = {
        "message": f"Auto Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(),
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha

    res = requests.put(url, headers=headers, json=payload)
    return res.status_code in [200, 201]

@bot.message_handler(commands=['start'])
def welcome(message):
    if message.from_user.id == OWNER_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("➕ إنشاء مفتاح", callback_data="gen_key"),
                   types.InlineKeyboardButton("📊 عرض الأكواد", callback_data="list_keys"))
        bot.send_message(message.chat.id, "✅ **البوت جاهز ويعمل بنظام الإنشاء التلقائي!**\nسيتم حفظ كل شيء في GitHub مباشرة.", 
                         parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "gen_key":
        msg = bot.send_message(call.message.chat.id, "📝 أرسل: `الاسم الايام` (مثال: VIP_KEY 30)")
        bot.register_next_step_handler(msg, process_gen)
    elif call.data == "list_keys":
        data, _ = get_or_create_github_file()
        keys = data.get("keys", {}) if data else {}
        txt = "📋 **الأكواد الحالية:**\n" + "\n".join([f"🔑 `{k}` | ⏳ `{v['expiry']}`" for k, v in keys.items()]) if keys else "❌ لا توجد أكواد."
        bot.send_message(call.message.chat.id, txt, parse_mode="Markdown")

def process_gen(message):
    try:
        parts = message.text.split()
        name, days = parts[0], int(parts[1])
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        bot.send_message(message.chat.id, "⏳ جاري المعالجة والرفع لـ GitHub...")
        
        data, sha = get_or_create_github_file()
        if data is None:
            bot.send_message(message.chat.id, "❌ خطأ في الاتصال بـ GitHub!")
            return

        data["keys"][name] = {"expiry": expiry}
        
        if save_to_github(data, sha):
            bot.send_message(message.chat.id, f"✅ **تم بنجاح!**\nالمفتاح: `{name}` انضاف للملف تلقائياً.")
        else:
            bot.send_message(message.chat.id, "❌ فشل التحديث. تأكد من صلاحيات التوكن الجديد.")
    except:
        bot.send_message(message.chat.id, "⚠️ صيغة خاطئة! (الاسم مسافة الرقم)")

bot.polling()

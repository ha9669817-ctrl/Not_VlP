import telebot
from telebot import types
import requests
import json
import base64
import time
from datetime import datetime, timedelta

# --- إعدادات حمد ---
API_TOKEN = "8689755411:AAFUVGg8c2adyi2ExCZ3wHOvikxbjTkkVZk"
ADMIN_ID = 5031612259
GITHUB_TOKEN = "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"
GITHUB_REPO = "ha9669817-ctrl/Not_VIP"
GITHUB_BRANCH = "main"
DATABASE_FILE = "database.json"

bot = telebot.TeleBot(API_TOKEN)

def get_or_create_github_file():
    """هذه الدالة تبحث عن الملف، وإذا لم تجده تقوم بإنشائه فوراً"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATABASE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            # الملف موجود، نقوم بتحميله
            res = r.json()
            content = base64.b64decode(res['content']).decode()
            return json.loads(content), res['sha']
        
        elif r.status_code == 404:
            # الملف غير موجود! البوت سينشئه الآن
            print("الملف غير موجود، جاري إنشاء database.json...")
            initial_data = {"keys": {}}
            initial_content = base64.b64encode(json.dumps(initial_data, indent=4).encode()).decode()
            
            payload = {
                "message": "Initial creation of database.json",
                "content": initial_content,
                "branch": GITHUB_BRANCH
            }
            create_res = requests.put(url, headers=headers, json=payload)
            if create_res.status_code in [200, 201]:
                return initial_data, create_res.json()['content']['sha']
    except Exception as e:
        print(f"حدث خطأ في الاتصال: {e}")
    
    return None, None

def save_to_github(data, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{DATABASE_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    payload = {
        "message": f"Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": base64.b64encode(json.dumps(data, indent=4).encode()).decode(),
        "branch": GITHUB_BRANCH,
        "sha": sha
    }
    
    res = requests.put(url, headers=headers, json=payload)
    return res.status_code in [200, 201]

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ إنشاء مفتاح", callback_data="add"))
        bot.send_message(message.chat.id, "✅ **نظام حمد للإنشاء التلقائي شغال!**\nإذا الملف مو موجود في GitHub، أنا راح أنشئه لك.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add":
        msg = bot.send_message(call.message.chat.id, "📝 أرسل: `الاسم الايام`")
        bot.register_next_step_handler(msg, process_add_key)

def process_add_key(message):
    try:
        name, days = message.text.split()[0], int(message.text.split()[1])
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        bot.send_message(message.chat.id, "⏳ جاري فحص الملف ورفعه لـ GitHub...")
        
        # هنا البوت يتأكد من وجود الملف أو ينشئه قبل الحفظ
        data, sha = get_or_create_github_file()
        
        if data is not None:
            data["keys"][name] = {"expiry": expiry}
            if save_to_github(data, sha):
                bot.send_message(message.chat.id, f"✅ تم بنجاح!\nالمفتاح: `{name}`\nينتهي: `{expiry}`")
            else:
                bot.send_message(message.chat.id, "❌ فشل تحديث الملف.")
        else:
            bot.send_message(message.chat.id, "❌ تعذر الوصول لـ GitHub.")
    except:
        bot.send_message(message.chat.id, "⚠️ خطأ! أرسل (الاسم مسافة الرقم)")

bot.infinity_polling()

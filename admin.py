import telebot
from telebot import types
from datetime import datetime, timedelta

# --- إعدادات حمد ---
API_TOKEN = "8689755411:AAFUVGg8c2adyi2ExCZ3wHOvikxbjTkkVZk"
ADMIN_ID = 5031612259

bot = telebot.TeleBot(API_TOKEN)

# --- [ واجهة القائمة الرئيسية ] ---
def main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_gen = types.InlineKeyboardButton("➕ إنشاء مفتاح جديد", callback_data="gen_code")
    btn_del = types.InlineKeyboardButton("🗑️ حذف مفتاح", callback_data="del_code")
    btn_req = types.InlineKeyboardButton("🛡️ طلبات التفعيل", callback_data="requests")
    btn_info = types.InlineKeyboardButton("📊 حالة السيرفر", callback_data="status")
    markup.add(btn_gen, btn_del)
    markup.add(btn_req)
    markup.add(btn_info)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id, 
            f"💎 **أهلاً بك يا شيخ المبرمجين حمد**\n\nإليك لوحة التحكم الأسطورية الخاصة بك.\nتحكم بملفات GitHub والهاك بكل سهولة:",
            parse_mode="Markdown", 
            reply_markup=main_markup()
        )

# --- [ معالج الأزرار ] ---
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    # 1. إنشاء كود
    if call.data == "gen_code":
        msg = bot.send_message(call.message.chat.id, "📝 أرسل الاسم والمدة هكذا: `HAMAD 30`")
        bot.register_next_step_handler(msg, process_gen)
    
    # 2. حذف كود (يعطيك النص اللي تحذفه)
    elif call.data == "del_code":
        msg = bot.send_message(call.message.chat.id, "🗑️ أرسل اسم المفتاح اللي تبي تحذفه:")
        bot.register_next_step_handler(msg, process_del)

    # 3. نظام الموافقة والرفض (تجريبي للتنظيم)
    elif call.data == "requests":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ موافقة", callback_data="approve"),
                   types.InlineKeyboardButton("❌ رفض", callback_data="reject"))
        bot.send_message(call.message.chat.id, "⏳ هل تريد الموافقة على طلب التفعيل الأخير؟", reply_markup=markup)

    elif call.data == "status":
        bot.answer_callback_query(call.id, "🚀 السيرفر يعمل بأقصى كفاءة يا بطل!")

    elif call.data == "approve":
        bot.edit_message_text("✅ **تمت الموافقة بنجاح!**\nقم بنسخ الكود الآن لـ GitHub.", call.message.chat.id, call.message.message_id)
        
    elif call.data == "reject":
        bot.edit_message_text("❌ **تم رفض الطلب وإلغاء العملية.**", call.message.chat.id, call.message.message_id)

# --- [ وظائف المعالجة ] ---

def process_gen(message):
    try:
        name, days = message.text.split()[0], int(message.text.split()[1])
        expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        json_code = f'"{name}": {{"expiry": "{expiry}"}}'
        
        res = (
            f"✨ **تم إنشاء المفتاح بنجاح** ✨\n\n"
            f"👤 الاسم: `{name}`\n"
            f"⏳ المدة: `{days}` يوم\n"
            f"📅 ينتهي: `{expiry}`\n\n"
            f"🔹 **انسخ وضعه في GitHub:**\n"
            f"<code>{json_code}</code>"
        )
        bot.send_message(message.chat.id, res, parse_mode="HTML", reply_markup=main_markup())
    except:
        bot.send_message(message.chat.id, "⚠️ خطأ! أرسل (الاسم مسافة الرقم)")

def process_del(message):
    name = message.text
    res = (
        f"🗑️ **طلب حذف مفتاح**\n\n"
        f"ابحث عن هذا السطر في ملفك بـ GitHub وامسحه:\n"
        f"<code>\"{name}\": {{ ... }}</code>\n\n"
        f"⚠️ تأكد من مسح الفاصلة `,` الزائدة بعد الحذف."
    )
    bot.send_message(message.chat.id, res, parse_mode="HTML", reply_markup=main_markup())

bot.infinity_polling()

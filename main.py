import sqlite3
import telebot
from telebot import types

# === O'ZGARUVCHILAR ===
TOKEN = "8978184615:AAHFzyN0AozBNpVUJbViHVDNxo7x2-2g68I"  # BotFather'dan olingan tokeningizni yozing
ADMIN_ID = 8642809489                    # Sizning Telegram ID'ingiz
REQUIRED_CHANNEL = "@tafakkuroff"       # Majburiy obuna kanalingiz

bot = telebot.TeleBot(TOKEN)

# Bazani ulash va jadvallar
conn = sqlite3.connect('aloferiya_bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    invited_count INTEGER DEFAULT 0,
    invited_by INTEGER,
    distance REAL DEFAULT 0.0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS audios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    file_id TEXT
)
''')
conn.commit()

# Kanalga obuna bo'lganini tekshirish funksiyasi
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except:
        return True 

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    # 1. Majburiy obunani tekshirish
    if REQUIRED_CHANNEL and not check_subscription(user_id):
        markup = types.InlineKeyboardMarkup()
        btn_channel = types.InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{REQUIRED_CHANNEL.replace('@', '')}")
        btn_check = types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")
        markup.add(btn_channel)
        markup.add(btn_check)
        
        bot.send_message(
            message.chat.id,
            f"Assalomu alaykum, {first_name}!\n\n"
            f"Botdan foydalanish uchun avval kanalimizga obuna bo‘ling:\n{REQUIRED_CHANNEL}\n\n"
            f"Obuna bo‘lgach, **'Obunani tekshirish'** tugmasini bosing.",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    # Referral va boshqa qism
    args = message.text.split()
    inviter_id = None
    if len(args) > 1:
        try:
            inviter_id = int(args[1])
        except ValueError:
            pass

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, invited_by) VALUES (?, ?, ?, ?)",
            (user_id, message.from_user.username, first_name, inviter_id)
        )
        conn.commit()

        if inviter_id and inviter_id != user_id:
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (inviter_id,))
            if cursor.fetchone():
                cursor.execute("UPDATE users SET invited_count = invited_count + 1 WHERE user_id = ?", (inviter_id,))
                conn.commit()
                try:
                    bot.send_message(inviter_id, "🎉 Tabriklaymiz! Yangi do‘stingiz botga qo‘shildi.")
                except:
                    pass

    cursor.execute("SELECT invited_count FROM users WHERE user_id = ?", (user_id,))
    invited_count = cursor.fetchone()[0]

    if invited_count < 4:
        ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        text = (
            f"🧠 **@Aloferiyabot** platformasiga xush kelibsiz.\n\n"
            f"Botni to‘liq ishlatish uchun **4 ta do‘stingizni** taklif qilishingiz kerak.\n\n"
            f"👥 Siz taklif qilgan do‘stlar: **{invited_count} / 4**\n\n"
            f"Sizning shaxsiy havolangiz:\n`{ref_link}`"
        )
        bot.send_message(message.chat.id, text, parse_mode="Markdown")
    else:
        show_main_menu(message.chat.id, first_name, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_sub(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "Rahmat, obuna tasdiqlandi! ✅")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        start_message(call.message)
    else:
        bot.answer_callback_query(call.id, "Siz hali kanalga obuna bo'lmadingiz! ❌", show_alert=True)

def show_main_menu(chat_id, name, user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_audio = types.KeyboardButton("🎧 Audio kitoblar")
    btn_distance = types.KeyboardButton("🚶 Masofa kiritish")
    btn_rating = types.KeyboardButton("🏆 Reyting")
    btn_link = types.KeyboardButton("🔗 Mening havolam")
    markup.add(btn_audio, btn_distance, btn_rating, btn_link)
    
    # Agar admin bo'lsa Admin panel chiqadi
    if user_id == ADMIN_ID:
        btn_admin = types.KeyboardButton("⚙️ Admin panel")
        markup.add(btn_admin)

    bot.send_message(chat_id, f"Xush kelibsiz, {name}!", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text

    # Admin panel
    if user_id == ADMIN_ID and text == "⚙️ Admin panel":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("➕ Audio qo'shish"), types.KeyboardButton("📊 Statistika"))
        markup.add(types.KeyboardButton("⬅️ Asosiy menyu"))
        bot.send_message(message.chat.id, "⚙️ Admin paneliga xush kelibsiz:", reply_markup=markup)
        return

    if user_id == ADMIN_ID and text == "⬅️ Asosiy menyu":
        show_main_menu(message.chat.id, message.from_user.first_name, user_id)
        return

    if user_id == ADMIN_ID and text == "📊 Statistika":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM audios")
        total_audios = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f"📊 **Bot statistikasi:**\n\n👥 Foydalanuvchilar: {total_users} ta\n🎧 Audio kitoblar: {total_audios} ta", parse_mode="Markdown")
        return

    if user_id == ADMIN_ID and text == "➕ Audio qo'shish":
        msg = bot.send_message(message.chat.id, "Audio nomini kiriting (masalan: *O'tkan kunlar - 1-bob*):")
        bot.register_next_step_handler(msg, get_audio_title)
        return

    # Oddiy foydalanuvchi shartini tekshiramiz
    cursor.execute("SELECT invited_count FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    
    if not res or res[0] < 4:
        start_message(message)
        return

    if text == "🎧 Audio kitoblar":
        cursor.execute("SELECT title, file_id FROM audios")
        audios = cursor.fetchall()
        if not audios:
            bot.send_message(message.chat.id, "Hozircha audio kitoblar qo'shilmagan. Tez orada qo'shiladi.")
        else:
            bot.send_message(message.chat.id, "🎧 **Mavjud audio kitoblar:**")
            for title, file_id in audios:
                bot.send_audio(message.chat.id, file_id, caption=f"📚 {title}")

    elif text == "🚶 Masofa kiritish":
        msg = bot.send_message(message.chat.id, "Bugun qancha masofa yurdingiz? (Kilometrda, masalan: `3.5`):")
        bot.register_next_step_handler(msg, save_distance)

    elif text == "🏆 Reyting":
        cursor.execute("SELECT first_name, distance FROM users ORDER BY distance DESC LIMIT 5")
        top_users = cursor.fetchall()
        rating_text = "🏆 **Eng faol kitobxon-sayohatchilar reytingi:**\n\n"
        for i, (fname, dist) in enumerate(top_users, 1):
            rating_text += f"{i}. {fname} — {dist} km\n"
        bot.send_message(message.chat.id, rating_text, parse_mode="Markdown")

    elif text == "🔗 Mening havolam":
        ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        cursor.execute("SELECT invited_count FROM users WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f"👥 Siz taklif qilgan do‘stlar: **{count} / 4**\n\nHavolangiz:\n`{ref_link}`", parse_mode="Markdown")

def get_audio_title(message):
    title = message.text
    msg = bot.send_message(message.chat.id, f"Endi **{title}** uchun **audio faylni** (mp3 yoki voice) yuboring:")
    bot.register_next_step_handler(msg, save_audio_file, title)

def save_audio_file(message, title):
    if message.audio:
        file_id = message.audio.file_id
    elif message.voice:
        file_id = message.voice.file_id
    else:
        bot.send_message(message.chat.id, "⚠️ Bu audio fayl emas! Iltimos, audio yoki voice yuboring.")
        return

    cursor.execute("INSERT INTO audios (title, file_id) VALUES (?, ?)", (title, file_id))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ Muvaffaqiyatli saqlandi! '{title}' audiosi bazaga qo'shildi.")

def save_distance(message):
    try:
        dist = float(message.text.replace(',', '.'))
        user_id = message.from_user.id
        cursor.execute("UPDATE users SET distance = distance + ? WHERE user_id = ?", (dist, user_id))
        conn.commit()
        bot.send_message(message.chat.id, f"✅ {dist} km masofangiz reytingga qo'shildi!")
    except ValueError:
        bot.send_message(message.chat.id, "⚠️ Xato format! Faqat raqam kiriting (masalan: `2` yoki `1.5`).")

if __name__ == '__main__':
    print("Aloferiyabot to'liq funksionalda ishga tushdi...")
    bot.infinity_polling()

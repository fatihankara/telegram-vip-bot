from flask import Flask
import threading
import time
import json
import os
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --------- FLASK (Botu Canlı Tutma) ---------
web = Flask(__name__)
@web.route('/')
def home(): return "Bot Aktif"

def run(): web.run(host="0.0.0.0", port=10000)
def keep_alive():
    t = threading.Thread(target=run)
    t.start()

keep_alive()

# --------- AYARLAR ---------
TOKEN = "8782987338:AAF4QQsH9pwk5_d1F0sLBzHyPrJBXOQsfGw"
ADMIN_ID = 7950288597

VIP_CHANNEL = -1003784644347
PREMIUM_CHANNEL = -1003883042358
ELITE_CHANNEL = -1001234567890 # <-- ELITE kanal ID'sini buraya yaz!

DATA_FILE = "uyeler.json"
SURE = 30 * 24 * 60 * 60

# --------- VERİ YÖNETİMİ ---------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

# --------- ANA MENÜ (START) ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ VIP (80 TL) - 30 GÜN", url="https://www.shopier.com/beybinurvip/45692063")],
        [InlineKeyboardButton("🌟 PREMIUM (120 TL) - 30 GÜN", url="https://www.shopier.com/beybinurvip/45692092")],
        [InlineKeyboardButton("👑 ELITE (150 TL) - 30 GÜN", url="https://www.shopier.com/beybinurvip/45692110")],
        [InlineKeyboardButton("✅ ÖDEME YAPTIM", callback_data="odeme")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        "<b>👑 BEYBİNUR PRIVÉ – HOŞ GELDİNİZ</b>\n\n"
        "Size en uygun <b>Aylık Üyelik</b> paketini seçebilirsiniz:\n\n"
        "📍 <b>30 GÜNLÜK PAKET SEÇENEKLERİ:</b>\n"
        "• <b>VIP:</b> Günlük 1 Foto — <b>80 TL</b>\n"
        "• <b>PREMIUM:</b> Günlük 3 Foto — <b>120 TL</b>\n"
        "• <b>ELITE:</b> Günlük 5 Foto + 1 Video — <b>150 TL</b>\n\n"
        "⚠️ <i>Not: Üyelikler 30 gün geçerlidir. Süre sonunda sistem otomatik olarak gruptan çıkarır.</i>"
    )
    await update.message.reply_text(text=welcome_text, reply_markup=reply_markup, parse_mode="HTML")

# --------- BUTON (BİLDİRİM) ---------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    admin_msg = (
        f"💰 <b>YENİ ÖDEME BİLDİRİMİ!</b>\n\n👤: @{user.username}\n🆔: <code>{user.id}</code>\n\n"
        f"<b>ONAY:</b>\n<code>/onayvip {user.id}</code>\n<code>/onaypremium {user.id}</code>\n<code>/onayelite {user.id}</code>\n\n"
        f"<b>RED:</b>\n<code>/red {user.id}</code>"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="HTML")
    await query.edit_message_text("✅ Bildiriminiz iletildi. Kontrol sonrası linkiniz buraya gönderilecek.")

# --------- ONAY VE RED ---------
async def onay_genel(update, context, kanal_id, paket):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user_id = int(context.args[0])
        invite = await context.bot.create_chat_invite_link(chat_id=kanal_id, member_limit=1)
        await context.bot.send_message(chat_id=user_id, text=f"🎉 <b>{paket.upper()} Üyeliğiniz Onaylandı!</b>\n\nLink: {invite.invite_link}", parse_mode="HTML")
        data = load_data()
        data[str(user_id)] = {"bitis": int(time.time()) + SURE, "kanal": paket}
        save_data(data)
        await update.message.reply_text(f"✅ {user_id} onaylandı.")
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")

async def onayvip(u, c): await onay_genel(u, c, VIP_CHANNEL, "vip")
async def onaypremium(u, c): await onay_genel(u, c, PREMIUM_CHANNEL, "premium")
async def onayelite(u, c): await onay_genel(u, c, ELITE_CHANNEL, "elite")

async def red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user_id = int(context.args[0])
        await context.bot.send_message(chat_id=user_id, text="❌ <b>Ödemeniz Onaylanmadı.</b> Lütfen işlemi kontrol edip tekrar deneyin.", parse_mode="HTML")
        await update.message.reply_text(f"🚫 {user_id} reddedildi.")
    except:
        await update.message.reply_text("Kullanıcıya ulaşılamadı.")

# --------- SÜRE KONTROL ---------
async def kontrol(application):
    while True:
        data = load_data()
        simdi = int(time.time())
        degisti = False
        for user_id in list(data.keys()):
            if simdi > data[user_id]["bitis"]:
                k_id = VIP_CHANNEL if data[user_id]["kanal"] == "vip" else (PREMIUM_CHANNEL if data[user_id]["kanal"] == "premium" else ELITE_CHANNEL)
                try:
                    await application.bot.ban_chat_member(k_id, int(user_id))
                    await application.bot.unban_chat_member(k_id, int(user_id))
                    await application.bot.send_message(chat_id=int(user_id), text="❌ Üyeliğinizin süresi doldu.")
                except: pass
                del data[user_id]
                degisti = True
        if degisti: save_data(data)
        await asyncio.sleep(3600)

# --------- ANA ÇALIŞTIRICI ---------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    loop = asyncio.get_event_loop()
    loop.create_task(kontrol(app))
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("onayvip", onayvip))
    app.add_handler(CommandHandler("onaypremium", onaypremium))
    app.add_handler(CommandHandler("onayelite", onayelite))
    app.add_handler(CommandHandler("red", red))
    app.add_handler(CallbackQueryHandler(button))
    
    print("Bot başlatılıyor...")
    app.run_polling()

if __name__ == '__main__':
    main()

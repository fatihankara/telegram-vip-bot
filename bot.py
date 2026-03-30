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
def home(): return "Bot aktif ve satışa hazır!"

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
ELITE_CHANNEL = -1001234567890 # <-- ELITE KANAL ID'SİNİ BURAYA YAZIN

DATA_FILE = "uyeler.json"
SURE = 30 * 24 * 60 * 60 # 30 Günlük Süre

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
        [InlineKeyboardButton("⭐ VIP (80 TL) - 1 Foto", url="https://www.shopier.com/beybinurvip/45692063")],
        [InlineKeyboardButton("🌟 PREMIUM (120 TL) - 3 Foto", url="https://www.shopier.com/beybinurvip/45692092")],
        [InlineKeyboardButton("👑 ELITE (150 TL) - 5 Foto + 1 Video", url="https://www.shopier.com/beybinurvip/45692110")],
        [InlineKeyboardButton("✅ ÖDEME YAPTIM", callback_data="odeme")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "<b>👑 BEYBİNUR PRIVÉ – HOŞ GELDİNİZ</b>\n\n"
        "📍 <b>GÜNCEL PAKETLER:</b>\n"
        "• <b>VIP:</b> Günlük 1 Foto — <b>80 TL</b>\n"
        "• <b>PREMIUM:</b> Günlük 3 Foto — <b>120 TL</b>\n"
        "• <b>ELITE:</b> Günlük 5 Foto + 1 Video — <b>150 TL</b>\n\n"
        "🚀 <i>Ödemeyi yapın ve 'Ödeme Yaptım' butonuna basın.</i>"
    )

    await update.message.reply_text(text=welcome_text, reply_markup=reply_markup, parse_mode="HTML")

# --------- BUTON (BİLDİRİM) ---------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    admin_msg = (
        f"💰 <b>YENİ ÖDEME BİLDİRİMİ!</b>\n\n"
        f"👤 Kullanıcı: @{user.username}\n"
        f"🆔 ID: <code>{user.id}</code>\n\n"
        f"<b>✅ ONAY:</b>\n"
        f"<code>/onayvip {user.id}</code>\n"
        f"<code>/onaypremium {user.id}</code>\n"
        f"<code>/onayelite {user.id}</code>\n\n"
        f"<b>❌ REDDET:</b>\n"
        f"<code>/red {user.id}</code>"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="HTML")
    await query.edit_message_text("✅ Bildiriminiz admin panelimize iletildi.")

# --------- ONAY SİSTEMİ ---------
async def onay_genel(update, context, kanal_id, paket):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user_id = int(context.args[0])
        invite = await context.bot.create_chat_invite_link(chat_id=kanal_id, member_limit=1)
        
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 <b>Tebrikler! {paket.upper()} üyeliğiniz aktif edildi.</b>\n\nLink:\n{invite.invite_link}",
            parse_mode="HTML"
        )
        
        data = load_data()
        data[str(user_id)] = {"bitis": int(time.time()) + SURE, "kanal": paket}
        save_data(data)
        await update.message.reply_text(f"✅ {user_id} için {paket} onaylandı.")
    except Exception as e:
        await update.message.reply_text(f"HATA: Kullanıcı botu engellemiş olabilir.\nDetay: {e}")

async def onayvip(u, c): await onay_genel(u, c, VIP_CHANNEL, "vip")
async def onaypremium(u, c): await onay_genel(u, c, PREMIUM_CHANNEL, "premium")
async def onayelite(u, c): await onay_genel(u, c, ELITE_CHANNEL, "elite")

# --------- REDDETME SİSTEMİ ---------
async def red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user_id = int(context.args[0])
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ <b>Ödemeniz Onaylanmadı</b>\n\nSistemde geçerli bir ödeme kaydı bulunamadı. Lütfen işlemi kontrol edip tekrar deneyin.",
            parse_mode="HTML"
        )
        await update.message.reply_text(f"🚫 {user_id} ID'li kullanıcıya ret mesajı gönderildi.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Hata: Kullanıcıya ulaşılamadı. (Botu engellemiş olabilir)")

# --------- SÜRE KONTROL (OTOMATİK ATMA) ---------
async def kontrol(application):
    while True:
        data = load_data()
        simdi = int(time.time())
        degisti = False
        for user_id in list(data.keys()):
            if simdi > data[user_id]["bitis"]:
                kanal_tipi = data[user_id]["kanal"]
                k_id = VIP_CHANNEL if kanal_tipi == "vip" else (PREMIUM_CHANNEL if kanal_tipi == "premium" else ELITE_CHANNEL)
                try:
                    await application.bot.ban_chat_member(k_id, int(user_id))
                    await application.bot.unban_chat_member(k_id, int(user_id))
                    await application.bot.send_message(chat_id=int(user_id), text="❌ Üyeliğinizin süresi doldu. Yenilemek için /start yazabilirsiniz.")
                except: pass
                del data[user_id]
                degisti = True
        if degisti: save_data(data)
        await asyncio.sleep(3600) # Her saat başı kontrol eder

# --------- BOT BAŞLAT ---------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Süre kontrolünü arka planda başlat
    loop = asyncio.get_event_loop()
    loop.create_task(kontrol(app))
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("onayvip", onayvip))
    app.add_handler(CommandHandler("onaypremium", onaypremium))
    app.add_handler(CommandHandler("onayelite", onayelite))
    app.add_handler(CommandHandler("red", red))
    app.add_handler(CallbackQueryHandler(button))
    
    print("Bot tüm fonksiyonlarıyla yayında!")
    app.run_polling()

if __name__ == '__main__':
    main()

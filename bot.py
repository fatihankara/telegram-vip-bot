from flask import Flask
import threading
import time
import json
import os
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# --------- FLASK (502 HATASINI ÖNLEMEK İÇİN GÜNCELLENDİ) ---------
web = Flask(__name__)

@web.route('/')
def home(): 
    return "OK", 200 # En hızlı ve kısa cevabı veriyoruz

def run():
    port = int(os.environ.get("PORT", 10000))
    # Threaded=True yaparak web isteklerini daha hızlı karşılamasını sağlıyoruz
    web.run(host="0.0.0.0", port=port, debug=False, threaded=True)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# --------- AYARLAR ---------
TOKEN = "8782987338:AAEe7o2XclMkzD-AVa-nCG9Xawg7ouX2aCw"
ADMIN_ID = 7950288597

VIP_CHANNEL = -1003784644347
PREMIUM_CHANNEL = -1003883042358
ELITE_CHANNEL = -1001234567890 

FREE_GROUP_ID = -1003365017619  
FREE_GROUP_LINK = "https://t.me/+MJzQ_ypSthEyYjA8" 

DATA_FILE = "uyeler.json"
COUNTER_FILE = "mesaj_sayaci.json" 
SURE = 30 * 24 * 60 * 60 

# --------- VERİ YÖNETİMİ ---------
def load_data(file=DATA_FILE):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data, file=DATA_FILE):
    with open(file, "w") as f: json.dump(data, f)

# --------- ANA MENÜ ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private": return
    keyboard = [
        [InlineKeyboardButton("💎 VIP (80 TL)", url="https://www.shopier.com/beybinurvip/45692063")],
        [InlineKeyboardButton("🌟 PREMIUM (120 TL)", url="https://www.shopier.com/beybinurvip/45692092")],
        [InlineKeyboardButton("👑 ELITE (150 TL)", url="https://www.shopier.com/beybinurvip/45692110")],
        [InlineKeyboardButton("📢 BİLGİLENDİRME GRUBU", callback_data="ucretsiz_bilgi")],
        [InlineKeyboardButton("✅ ÖDEME YAPTIM", callback_data="odeme")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = "<b>👑 BEYBİNUR PRIVÉ – HOŞ GELDİNİZ</b>\n\nPaket seçiniz:\n💎 VIP | 🌟 PREMIUM | 👑 ELITE"
    await update.message.reply_text(text=welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "ucretsiz_bilgi":
        await query.message.reply_text(f"<b>📢 Bilgilendirme Grubu</b>\n\nHakkınız: 5 Mesaj\n🔗 <a href='{FREE_GROUP_LINK}'>KATIL</a>", parse_mode="HTML")
    elif query.data == "odeme":
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"💰 Ödeme Bildirimi: @{query.from_user.username} (ID: {query.from_user.id})")
        await query.edit_message_text("✅ Bildirim iletildi.")

# --------- MESAJ SINIRLAMA ---------
async def mesaj_kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or update.message.text.startswith('/'): return 
    chat_id, user_id = update.effective_chat.id, str(update.effective_user.id)
    if chat_id != FREE_GROUP_ID or int(user_id) == ADMIN_ID: return 
    if user_id in load_data(): return
    sayaclar = load_data(COUNTER_FILE)
    current_count = sayaclar.get(user_id, 0)
    if current_count < 5:
        sayaclar[user_id] = current_count + 1
        save_data(sayaclar, COUNTER_FILE)
    else:
        try:
            await context.bot.restrict_chat_member(chat_id=FREE_GROUP_ID, user_id=int(user_id), permissions=ChatPermissions(can_send_messages=False))
            await update.message.reply_text("⚠️ Mesaj hakkınız doldu!")
        except: pass

# --------- ONAY VE KONTROL ---------
async def onay_genel(update, context, kanal_id, paket):
    if update.effective_user.id != ADMIN_ID or not context.args: return
    try:
        u_id = str(context.args[0])
        data = load_data()
        yeni_bitis = int(time.time()) + SURE
        invite = await context.bot.create_chat_invite_link(chat_id=kanal_id, member_limit=1)
        data[u_id] = {"bitis": yeni_bitis, "kanal": paket}
        save_data(data)
        await context.bot.send_message(chat_id=int(u_id), text=f"🎉 Onaylandı! Link: {invite.invite_link}")
    except: pass

async def kontrol(application):
    while True:
        data, simdi, degisti = load_data(), int(time.time()), False
        for u_id in list(data.keys()):
            if data[u_id]["bitis"] <= simdi:
                k_id = VIP_CHANNEL if data[u_id]["kanal"] == "vip" else (PREMIUM_CHANNEL if data[u_id]["kanal"] == "premium" else ELITE_CHANNEL)
                try: await application.bot.ban_chat_member(k_id, int(u_id)); await application.bot.unban_chat_member(k_id, int(u_id))
                except: pass
                del data[u_id]; degisti = True
        if degisti: save_data(data)
        await asyncio.sleep(3600)

async def post_init(application): asyncio.create_task(kontrol(application))

def main():
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("onayvip", lambda u,c: onay_genel(u,c,VIP_CHANNEL,"vip")))
    app.add_handler(CommandHandler("onaypremium", lambda u,c: onay_genel(u,c,PREMIUM_CHANNEL,"premium")))
    app.add_handler(CommandHandler("onayelite", lambda u,c: onay_genel(u,c,ELITE_CHANNEL,"elite")))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj_kontrol))
    app.run_polling()

if __name__ == '__main__': main()

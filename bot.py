from flask import Flask
import threading
import time
import json
import os
import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Loglama ayarları (Hataları Render Logs'ta daha net görmek için)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --------- FLASK (UptimeRobot İçin - Ultra Stabil) ---------
web = Flask(__name__)

@web.route('/')
def home(): 
    return "Bot Aktif ve Izleniyor", 200

def run():
    # Render'ın portunu otomatik al, yoksa 10000 kullan
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# --------- AYARLAR ---------
TOKEN = "8782987338:AAEe7o2XclMkzD-AVa-nCG9Xawg7ouX2aCw"
ADMIN_ID = 7950288597

VIP_CHANNEL = -1003784644347
PREMIUM_CHANNEL = -1003883042358
ELITE_CHANNEL = -1003705186491 # Elite ID düzeltildi

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
    if not update.effective_chat or update.effective_chat.type != "private": return
    
    keyboard = [
        [InlineKeyboardButton("⭐ VIP (80 TL) - 30 GÜN", url="https://www.shopier.com/beybinurvip/45692063")],
        [InlineKeyboardButton("🌟 PREMIUM (120 TL) - 30 GÜN", url="https://www.shopier.com/beybinurvip/45692092")],
        [InlineKeyboardButton("👑 ELITE (150 TL) - 30 GÜN", url="https://www.shopier.com/beybinurvip/45692110")],
        [InlineKeyboardButton("📢 BİLGİLENDİRME GRUBU", callback_data="ucretsiz_bilgi")],
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
        "⚠️ <i>Not: Üyelikler 30 gün geçerlidir.</i>"
    )
    await update.message.reply_text(text=welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "ucretsiz_bilgi":
        info_text = (
            "<b>📢 Beybi Nur Bilgilendirme Grubu</b>\n\n"
            "Soru sormak için grubumuza katılabilirsiniz.\n"
            "⚠️ <b>NOT:</b> Grupta toplam <b>5 adet mesaj</b> hakkınız vardır.\n\n"
            f"🔗 <a href='{FREE_GROUP_LINK}'>GRUBA GİRİŞ İÇİN TIKLAYIN</a>"
        )
        await query.message.reply_text(text=info_text, parse_mode="HTML")

    elif query.data == "odeme":
        admin_msg = (
            f"💰 <b>YENİ ÖDEME BİLDİRİMİ!</b>\n\n👤: @{user.username}\n🆔: <code>{user.id}</code>\n\n"
            f"<b>ONAY:</b>\n<code>/onayvip {user.id}</code>\n<code>/onaypremium {user.id}</code>\n<code>/onayelite {user.id}</code>\n\n"
            f"<b>RED:</b>\n<code>/red {user.id}</code>"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="HTML")
        await query.edit_message_text("✅ <b>Ödemeniz gönderildi, kontrol ediliyor.</b>\nLütfen bekleyiniz...", parse_mode="HTML")

# --------- MESAJ SINIRLAMA (5 MESAJ) ---------
async def mesaj_kontrol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    if update.message.text.startswith('/'): return 
    
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)

    if chat_id != FREE_GROUP_ID or int(user_id) == ADMIN_ID: return

    # Eğer ücretli üyeyse sınırı kaldır
    aktif_uyeler = load_data()
    if user_id in aktif_uyeler: return

    sayaclar = load_data(COUNTER_FILE)
    current_count = sayaclar.get(user_id, 0)

    if current_count < 5:
        current_count += 1
        sayaclar[user_id] = current_count
        save_data(sayaclar, COUNTER_FILE)
    else:
        try:
            await context.bot.restrict_chat_member(
                chat_id=FREE_GROUP_ID,
                user_id=int(user_id),
                permissions=ChatPermissions(can_send_messages=False)
            )
            await update.message.reply_text(f"⚠️ @{update.effective_user.username} Mesaj hakkınız doldu!")
        except: pass

# --------- ONAY SİSTEMİ ---------
async def onay_genel(update, context, kanal_id, paket):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return
    try:
        user_id = str(context.args[0])
        data = load_data()
        simdi = int(time.time())
        
        eski_bitis = data.get(user_id, {}).get("bitis", simdi)
        yeni_bitis = max(eski_bitis, simdi) + SURE
        
        invite = await context.bot.create_chat_invite_link(chat_id=kanal_id, member_limit=1)
        
        data[user_id] = {"bitis": yeni_bitis, "kanal": paket, "hatirlatildi": False}
        save_data(data)
        
        await context.bot.send_message(
            chat_id=int(user_id), 
            text=f"🎉 <b>{paket.upper()} Üyeliğiniz Onaylandı!</b>\n\n📅 Yeni Bitiş: {time.ctime(yeni_bitis)}\n🔗 Giriş Linki: {invite.invite_link}",
            parse_mode="HTML"
        )
        await update.message.reply_text(f"✅ {user_id} için {paket} onaylandı.")
    except Exception as e: 
        await update.message.reply_text(f"❌ Hata: {e}")

async def red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return
    try:
        user_id = int(context.args[0])
        await context.bot.send_message(chat_id=user_id, text="❌ <b>Ödemeniz Onaylanmadı.</b> Lütfen tekrar deneyin.", parse_mode="HTML")
        await update.message.reply_text(f"🚫 {user_id} reddedildi.")
    except:
        await update.message.reply_text("❌ Kullanıcıya ulaşılamadı.")

# --------- OTOMATİK KONTROL ---------
async def kontrol(application):
    while True:
        data = load_data()
        simdi = int(time.time())
        degisti = False
        for user_id in list(data.keys()):
            kullanici = data[user_id]
            if kullanici["bitis"] <= simdi:
                k_id = VIP_CHANNEL if kullanici["kanal"] == "vip" else (PREMIUM_CHANNEL if kullanici["kanal"] == "premium" else ELITE_CHANNEL)
                try:
                    await application.bot.ban_chat_member(k_id, int(user_id))
                    await application.bot.unban_chat_member(k_id, int(user_id))
                    await application.bot.send_message(chat_id=int(user_id), text="❌ Üyeliğiniz doldu.")
                except: pass
                del data[user_id]
                degisti = True
        if degisti: save_data(data)
        await asyncio.sleep(3600)

async def post_init(application):
    asyncio.create_task(kontrol(application))

def main():
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("onayvip", lambda u,c: onay_genel(u,c,VIP_CHANNEL,"vip")))
    app.add_handler(CommandHandler("onaypremium", lambda u,c: onay_genel(u,c,PREMIUM_CHANNEL,"premium")))
    app.add_handler(CommandHandler("onayelite", lambda u,c: onay_genel(u,c,ELITE_CHANNEL,"elite")))
    app.add_handler(CommandHandler("red", red))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mesaj_kontrol))
    
    app.run_polling(drop_pending_updates=True) # Bot açılırken birikmiş mesajları temizler

if __name__ == '__main__':
    main()

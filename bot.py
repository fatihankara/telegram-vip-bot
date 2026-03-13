from flask import Flask
import threading
import time
import json
import os
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --------- FLASK (Render için botu canlı tutar) ---------

web = Flask(__name__)

@web.route('/')
def home():
    return "Bot çalışıyor"

def run():
    web.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

keep_alive()


# --------- TELEGRAM AYAR ---------

TOKEN = "8782987338:AAF4QQsH9pwk5_d1F0sLBzHyPrJBXOQsfGw"

VIP_CHANNEL = -1003784644347
PREMIUM_CHANNEL = -1003883042358

ADMIN_ID = 7950288597

DATA_FILE = "uyeler.json"

SURE = 30 * 24 * 60 * 60


# --------- VERİ ---------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# --------- START ---------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

        keyboard = [
        [InlineKeyboardButton("💎 VIP Üyelik (500 TL)", url="https://www.shopier.com/beybinurvip/44857425")],
        [InlineKeyboardButton("👑 PREMIUM Üyelik (2000 TL)", url="https://www.shopier.com/beybinurvip/44890199")],
        [InlineKeyboardButton("✅ Ödeme Yaptım", callback_data="odeme")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "👑 *BEYBİNUR PRIVÉ – HOŞ GELDİNİZ*\n\n"
        "Beybinur’un en özel içeriklerine ve dev arşivine erişmek için doğru yerdesiniz.\n\n"
        "📍 *ADIM ADIM ERİŞİM REHBERİ:*\n"
        "1️⃣ *PAKETİNİ SEÇ:* Aşağıdaki VIP veya PREMIUM seçeneklerinden birini belirle.\n"
        "2️⃣ *GÜVENLİ ÖDEME (Shopier):* 'Satın Al' butonuna tıkla, ödemeni güvenle tamamla.\n"
        "3️⃣ *OTOMATİK ONAY:* Ödemeden sonra bu bota dönüp *'Ödeme Yaptım'* butonuna bas!\n\n"
        "🚀 *SONUÇ:*\n"
        "Sistemimiz ödemeni saniyeler içinde onaylar ve giriş linkiniz otomatik gönderilir.\n\n"
        "⚠️ *DİKKAT:* Shopier kaydı olmadan butonu suistimal edenler sistemden yasaklanır."
    )

    await update.message.reply_text(
        text=welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )



# --------- BUTON ---------

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"💰 Yeni ödeme bildirimi!\n\nKullanıcı: @{user.username}\nID: {user.id}"
    )

    await query.edit_message_text("Ödemeniz kontrol ediliyor...")


# --------- VIP ONAY ---------

async def onayvip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])

    invite = await context.bot.create_chat_invite_link(
        chat_id=VIP_CHANNEL,
        member_limit=1
    )

    await context.bot.send_message(
        chat_id=user_id,
        text=f"💎 VIP erişiminiz açıldı!\n\nLink:\n{invite.invite_link}"
    )

    data = load_data()

    data[str(user_id)] = {
        "bitis": int(time.time()) + SURE,
        "kanal": "vip"
    }

    save_data(data)

    await update.message.reply_text("VIP kullanıcı eklendi.")


# --------- PREMIUM ONAY ---------

async def onaypremium(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])

    invite = await context.bot.create_chat_invite_link(
        chat_id=PREMIUM_CHANNEL,
        member_limit=1
    )

    await context.bot.send_message(
        chat_id=user_id,
        text=f"👑 PREMIUM erişiminiz açıldı!\n\nLink:\n{invite.invite_link}"
    )

    data = load_data()

    data[str(user_id)] = {
        "bitis": int(time.time()) + SURE,
        "kanal": "premium"
    }

    save_data(data)

    await update.message.reply_text("PREMIUM kullanıcı eklendi.")

# --------- REDDETME İŞLEMLERİ ---------

async def redvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ *Ödemeniz Onaylanmadı*\n\nSistemde geçerli bir ödeme kaydı bulunamadı. Lütfen işlemi tamamladığınızdan emin olun."
        )
        await update.message.reply_text(f"🚫 {user_id} ID'li kullanıcının VIP talebi reddedildi.")
    except (IndexError, ValueError):
        await update.message.reply_text("Kullanım: /redvip [user_id]")

async def redpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ *Ödemeniz Onaylanmadı*\n\nPremium üyelik bildiriminiz reddedildi. Lütfen bilgilerinizi kontrol edin."
        )
        await update.message.reply_text(f"🚫 {user_id} ID'li kullanıcının Premium talebi reddedildi.")
    except (IndexError, ValueError):
        await update.message.reply_text("Kullanım: /redpremium [user_id]")
# --------- SÜRE KONTROL ---------

async def kontrol(application):

    while True:

        data = load_data()
        simdi = int(time.time())
        degisti = False

        for user_id in list(data.keys()):

            if simdi > data[user_id]["bitis"]:

                kanal = data[user_id]["kanal"]

                try:

                    if kanal == "vip":
                        await application.bot.ban_chat_member(VIP_CHANNEL, int(user_id))
                        await application.bot.unban_chat_member(VIP_CHANNEL, int(user_id))

                    if kanal == "premium":
                        await application.bot.ban_chat_member(PREMIUM_CHANNEL, int(user_id))
                        await application.bot.unban_chat_member(PREMIUM_CHANNEL, int(user_id))

                    keyboard = [
                        [InlineKeyboardButton("💎 VIP Yenile", url="VIP_LINK")],
                        [InlineKeyboardButton("👑 PREMIUM Yenile", url="PREMIUM_LINK")]
                    ]

                    reply_markup = InlineKeyboardMarkup(keyboard)

                    await application.bot.send_message(
                        chat_id=int(user_id),
                        text="❌ Üyeliğinizin süresi doldu.\n\nYenilemek için ödeme yapabilirsiniz.",
                        reply_markup=reply_markup
                    )

                except:
                    pass

                del data[user_id]
                degisti = True

        if degisti:
            save_data(data)

        await asyncio.sleep(3600)


# --------- BOT BAŞLAT ---------

def main():
    # Uygulamayı oluştur
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları ekle
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("onayvip", onayvip))
    app.add_handler(CommandHandler("onaypremium", onaypremium))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("redvip", redvip))
    app.add_handler(CommandHandler("redpremium", redpremium))
    # Botu başlat (Polling modunda en güvenli yol budur)
    print("Bot başarıyla başlatıldı...")
    app.run_polling()

main()

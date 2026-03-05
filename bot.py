from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import time
import json
import os

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

    await update.message.reply_text(
        "Üyelik satın almak için aşağıdaki butonları kullanın 👇",
        reply_markup=reply_markup
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

async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):

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

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):

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


# --------- SÜRE KONTROL ---------

async def kontrol(context: ContextTypes.DEFAULT_TYPE):

    data = load_data()

    simdi = int(time.time())

    degisti = False

    for user_id in list(data.keys()):

        if simdi > data[user_id]["bitis"]:

            kanal = data[user_id]["kanal"]

            try:

                if kanal == "vip":
                    await context.bot.ban_chat_member(VIP_CHANNEL, int(user_id))
                    await context.bot.unban_chat_member(VIP_CHANNEL, int(user_id))

                if kanal == "premium":
                    await context.bot.ban_chat_member(PREMIUM_CHANNEL, int(user_id))
                    await context.bot.unban_chat_member(PREMIUM_CHANNEL, int(user_id))

                keyboard = [

                    [InlineKeyboardButton("💎 VIP Yenile", url="VIP_LINK")],

                    [InlineKeyboardButton("👑 PREMIUM Yenile", url="PREMIUM_LINK")]

                ]

                reply_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_message(
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

# ----------------- BOT -----------------

async def onay(update, context):
    await update.message.reply_text("Kullanıcı onaylandı.")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("onay", onay))
app.add_handler(CallbackQueryHandler(button))

job_queue = app.job_queue
if job_queue:
    job_queue.run_repeating(kontrol, interval=3600, first=10)

if __name__ == "__main__":
    app.run_polling()

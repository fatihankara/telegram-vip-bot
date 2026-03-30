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
ELITE_CHANNEL = -1001234567890  # <-- BURAYA ELITE KANAL ID'SİNİ YAZIN!

DATA_FILE = "uyeler.json"
SURE = 30 * 24 * 60 * 60  # 30 Günlük Süre (Saniye cinsinden)

# --------- VERİ YÖNETİMİ ---------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

# --------- ANA MENÜ (START) ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # GÜNCEL PAKETLER VE SHOPIER LİNKLERİ
    keyboard = [
        [InlineKeyboardButton("⭐ VIP (80 TL) - 30 GÜN", url="https://www.shopier.com/beybinurvip/45692063")],
        [InlineKeyboardButton("🌟 PREMIUM (120 TL) - 30 GÜN", url="https://www.shopier.com/beybinurvip/45692092")],
        [InlineKeyboardButton("👑 ELITE (150 TL) - 30 GÜN", url="https://www.shopier.com/beybinurvip/45692110")],
        [InlineKeyboardButton("✅ ÖDEME YAPTIM", callback_data="odeme")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "<b>👑 BEYBİNUR PRIVÉ – HOŞ GELDİNİZ</b>\n\n"
        "Beybinur'un en özel içeriklerine erişmek için size en uygun <b>Aylık Üyelik</b> paketini seçebilirsiniz:\n\n"
        "📍 <b>30 GÜNLÜK PAKET SEÇENEKLERİ:</b>\n"
        "• <b>VIP Paket:</b> Günlük 1 Foto — <b>80 TL / Ay</b>\n"
        "• <b>PREMIUM Paket:</b> Günlük 3 Foto — <b>120 TL / Ay</b>\n"
        "• <b>ELITE Paket:</b> Günlük 5 Foto + 1 Video — <b>150 TL / Ay</b>\n\n"
        "⚠️ <i>Not: Üyelikler 30 gün geçerlidir. Süre sonunda sistem otomatik olarak gruptan çıkarır.</i>\n\n"
        "🚀 <i>Ödemenizi yapın ve ardından 'Ödeme Yaptım' butonuna basın.</i>"
    )

    await update.message.reply_text(text=welcome_text, reply_markup=reply_markup, parse_mode="HTML")

# --------- BUTON (ÖDEME BİLDİRİMİ) ---------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    admin_msg = (
        f"💰 <b>YENİ ÖDEME BİLDİRİMİ!</b>\n\n"
        f"👤 Kullanıcı: @{user.username}\n"
        f"🆔 ID: <code>{user.id}</code>\n\n"
        f"<b>✅ ONAY KOMUTLARI:</b>\n"
        f"<code>/onayvip {user.id}</code>\n"
        f"<code>/onaypremium {user.id}</code>\n"
        f"<code>/onayelite {user.id}</code>\n\n"
        f"<b>❌ REDDETME:</b>\n"
        f"<code>/red {user.id}</code>"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="HTML")
    await query.edit_message_text("✅ Bildiriminiz iletildi. Kontrol edildikten sonra linkiniz buraya otomatik olarak gönderilecektir.")

# --------- ONAY MEKANİZMASI ---------
async def onay_genel(update, context, kanal_id, paket):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user_id = int(context.args[0])
        invite = await context.bot.create_chat_invite_link(chat_id=kanal_id, member_limit=1)
        
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 <b>Tebrikler! 30 Günlük {paket.upper()} Üyeliğiniz Onaylandı.</b>\n\nKatılım Linki:\n{invite.invite_link}",
            parse_mode="HTML"
        )
        
        data = load_data()
        data[str(user_id)] = {"bitis": int(time.time()) + SURE, "kanal": paket}
        save_data(data)
        await update.message.reply_text(f"✅ {user_id} için {paket} onayı verildi ve link gönderildi.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Hata: Kullanıcı botu engellemiş olabilir veya ID hatalı.\nDetay: {e}")

async def onayvip(u, c): await onay_genel(u, c, VIP_CHANNEL, "vip")
async def onaypremium(u, c): await onay_genel(u, c, PREMIUM_CHANNEL, "premium")
async def onayelite(u, c): await onay_genel(u, c, ELITE_CHANNEL, "elite")

# --------- REDDETME ---------
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
        await update.message.reply_text(f"⚠️ Hata: Kullanıcıya mesaj gitmedi. (Botu engellemiş olabilir)")

# --------- SÜRE KONTROL (OTOMATİK ÇIKARMA) ---------
async def kontrol(application):
    while True:
        data = load_data()
        simdi = int(time.time())
        degisti = False
        for user_id in list(

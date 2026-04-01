from flask import Flask
import threading
import time
import json
import os
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# --------- FLASK (UptimeRobot İçin) ---------
web = Flask(__name__)

@web.route('/')
def home(): 
    return "Bot Aktif ve İzleniyor"

def run():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

# --------- AYARLAR (BURALARI DÜZENLE) ---------
TOKEN = "8782987338:AAEe7o2XclMkzD-AVa-nCG9Xawg7ouX2aCw"
ADMIN_ID = 7950288597

VIP_CHANNEL = -1003784644347
PREMIUM_CHANNEL = -1003883042358
ELITE_CHANNEL = -1001234567890 

# ÜCRETSİZ GRUP AYARLARI
FREE_GROUP_ID = -1001234567890 # <--- BURAYA DUYURU GRUBUNUN ID'SİNİ YAZIN
FREE_GROUP_LINK = "https://t.me/GRUP_LINKINIZ" # <--- BURAYA DUYURU GRUBU LINKINI YAZIN

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
    # Sadece botun özel chat'inde çalışsın, grupta start komutu menü açmasın
    if update.effective_chat.type != "private": return

    keyboard = [
        [InlineKeyboardButton("💎 VIP (80 TL)", url="https://www.shopier.com/beybinurvip/45692063")],
        [InlineKeyboardButton("🌟 PREMIUM (120 TL)", url="https://www.shopier.com/beybinurvip/45692092")],
        [InlineKeyboardButton("👑 ELITE (150 TL)", url="https://www.shopier.com/beybinurvip/45692110")],
        [InlineKeyboardButton("📢 ÜCRETSİZ DUYURU GRUBU", callback_data="ucretsiz_bilgi")],
        [InlineKeyboardButton("✅ ÖDEME YAPTIM", callback_data="odeme")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "<b>👑 BEYBİNUR PRIVÉ – HOŞ GELDİNİZ</b>\n\n"
        "Size en uygun paketi seçebilirsiniz:\n\n"
        "💎 <b>VIP:</b> Günlük 1 Foto — <b>80 TL</b>\n"
        "🌟 <b>PREMIUM:</b> Günlük 3 Foto — <b>120 TL</b>\n"
        "👑 <b>ELITE:</b> Günlük 5 Foto + 1 Video — <b>150 TL</b>\n\n"
        "⚠️ <i>Tüm abonelikler 30 gün geçerlidir.</i>"
    )
    await update.message.reply_text(text=welcome_text, reply_markup=reply_markup, parse_mode="HTML")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "ucretsiz_bilgi":
        info_text = (
            "<b>📢 Beybi Nur Duyuru Grubu</b>\n\n"
            "<i>'Ücretli gruplarımıza katılmadan önce aklınızdaki soru işaretlerini gidermek ve güncel paket detaylarını öğrenmek için doğru yerdesiniz.'</i>\n\n"
            "📋 <b>Neden Bizim Gruplarımızı Seçmelisiniz?</b>\n"
            "• <b>Dev Arşiv:</b> Binlerce güncel içerik.\n"
            "• <b>Günlük Güncelleme:</b> Her gün yeni içerikler.\n"
            "• <b>Güvenli Ödeme:</b> Shopier altyapısıyla.\n\n"
            "⚠️ <b>GRUP KURALI:</b> Duyuru grubunda toplam <b>5 adet mesaj hakkınız</b> vardır. Hakkınız dolduğunda sistem sizi otomatik susturacaktır.\n\n"
            f"🔗 <a href='{FREE_GROUP_LINK}'>GRUBA KATILMAK İÇİN

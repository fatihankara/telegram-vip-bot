from flask import Flask
import threading
import time
import json
import os
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

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

# --------- AYARLAR ---------
TOKEN = "8782987338:AAEe7o2XclMkzD-AVa-nCG9Xawg7ouX2aCw"
ADMIN_ID = 7950288597

VIP_CHANNEL = -1003784644347
PREMIUM_CHANNEL = -1003883042358
ELITE_CHANNEL = -1001234567890 

DATA_FILE = "uyeler.json"
SURE = 30 * 24 * 60 * 60 # 30 Günlük saniye

# --------- VERİ YÖNETİMİ ---------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

# --------- ANA MENÜ ---------
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
    await query.edit_message_text("✅ Bildiriminiz iletildi. Kontrol sonrası işleminiz tamamlanacaktır.")

# --------- ONAY VE SÜRE UZATMA ---------
async def onay_genel(update, context, kanal_id, paket):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return
    try:
        user_id = str(context.args[0])
        data = load_data()
        simdi = int(time.time())

        # SÜRE HESABI: Üye zaten varsa bitişin üzerine ekle, yoksa şimdiden başlat
        eski_bitis = data.get(user_id, {}).get("bitis", simdi)
        yeni_bitis = max(eski_bitis, simdi) + SURE

        # Üyeye özel link oluştur
        invite = await context.bot.create_chat_invite_link(chat_id=kanal_id, member_limit=1)
        
        # Veriyi kaydet
        data[user_id] = {"bitis": yeni_bitis, "kanal": paket, "hatirlatildi": False}
        save_data(data)

        # Kullanıcıya mesaj gönder
        await context.bot.send_message(
            chat_id=int(user_id), 
            text=f"🎉 <b>{paket.upper()} Üyeliğiniz Onaylandı!</b>\n\n"
                 f"📅 Yeni Bitiş Tarihi: {time.ctime(yeni_bitis)}\n"
                 f"🔗 Giriş Linki: {invite.invite_link}\n\n"
                 f"<i>(Eğer gruptaysanız linke tıklamanıza gerek yoktur, süreniz otomatik uzatılmıştır.)</i>",
            parse_mode="HTML"
        )
        await update.message.reply_text(f"✅ {user_id} için süre {paket} olarak uzatıldı/başlatıldı.")
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")

async def onayvip(u, c): await onay_genel(u, c, VIP_CHANNEL, "vip")
async def onaypremium(u, c): await onay_genel(u, c, PREMIUM_CHANNEL, "premium")
async def onayelite(u, c): await onay_genel(u, c, ELITE_CHANNEL, "elite")

async def red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return
    try:
        user_id = int(context.args[0])
        await context.bot.send_message(chat_id=user_id, text="❌ <b>Ödemeniz Onaylanmadı.</b> Lütfen işlemi kontrol edip tekrar deneyin.", parse_mode="HTML")
        await update.message.reply_text(f"🚫 {user_id} reddedildi.")
    except:
        await update.message.reply_text("Kullanıcıya ulaşılamadı.")

# --------- SÜRE VE HATIRLATMA KONTROLÜ ---------
async def kontrol(application):
    while True:
        data = load_data()
        simdi = int(time.time())
        degisti = False
        bir_gun = 24 * 60 * 60 # 24 saat
        
        for user_id in list(data.keys()):
            kullanici = data[user_id]
            kalan_saniye = kullanici["bitis"] - simdi

            # 24 Saat Kala Hatırlatma Mesajı
            if 0 < kalan_saniye <= bir_gun and not kullanici.get("hatirlatildi", False):
                try:
                    await application.bot.send_message(
                        chat_id=int(user_id),
                        text="⚠️ <b>Abonelik Uyarısı!</b>\n\nÜyeliğinizin bitmesine 24 saatten az kaldı. Kesinti yaşamamak için ana menüden paket yenileyebilirsiniz.",
                        parse_mode="HTML"
                    )
                    kullanici["hatirlatildi"] = True
                    degisti = True
                except: pass

            # Süre Tam Dolunca Çıkarma
            elif kalan_saniye <= 0:
                k_id = VIP_CHANNEL if kullanici["kanal"] == "vip" else (PREMIUM_CHANNEL if kullanici["kanal"] == "premium" else ELITE_CHANNEL)
                try:
                    await application.bot.ban_chat_member(k_id, int(user_id))
                    await application.bot.unban_chat_member(k_id, int(user_id))
                    await application.bot.send_message(chat_id=int(user_id), text="❌ Üyeliğiniz doldu ve gruptan çıkarıldınız. Tekrar katılmak için /start")
                except: pass
                del data[user_id]
                degisti = True

        if degisti: save_data(data)
        await asyncio.sleep(3600)

# --------- BAŞLATICI ---------
async def post_init(application):
    asyncio.create_task(kontrol(application))

def main():
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("onayvip", onayvip))
    app.add_handler(CommandHandler("onaypremium", onaypremium))
    app.add_handler(CommandHandler("onayelite", onayelite))
    app.add_handler(CommandHandler("red", red))
    app.add_handler(CallbackQueryHandler(button))
    
    print("Sistem Aktif ve Hatırlatıcı Devrede...")
    app.run_polling()

if __name__ == '__main__':
    main()

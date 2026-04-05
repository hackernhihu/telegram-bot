from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import sqlite3

API_ID = 32597791
API_HASH = "011dc530b6232ccee97a45bb2db196bb"
BOT_TOKEN = "8701935704:AAHo1S_ccPEAzZU2DxyKdL-uy7sgtlhQ9EY"
ADMIN_ID = 8574753078

app = Client("rs_music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

db = sqlite3.connect("database.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    premium INTEGER DEFAULT 0
)
""")

# START
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

    await message.reply_text(
        "🎧 RS MUSIC BOT\n\nSend song name to download",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Top 10 Songs", callback_data="top10")],
            [InlineKeyboardButton("💰 Buy Premium", callback_data="buy")],
            [InlineKeyboardButton("💬 Support", url="https://t.me/RSCODERHUB")]
        ])
    )

# TOP SONGS
TOP_SONGS = ["Kesariya", "Heeriye", "Shape of You", "Perfect", "Apna Bana Le"]

@app.on_callback_query(filters.regex("top10"))
async def top10(client, query):
    text = "🔥 Top Songs:\n\n"
    for i, song in enumerate(TOP_SONGS, 1):
        text += f"{i}. {song}\n"
    await query.message.edit_text(text)

# BUY
@app.on_callback_query(filters.regex("buy"))
async def buy(client, query):
    await query.message.edit_text(
        "💰 Send ₹99 to UPI: theghost@ptyes\n\nThen send UTR number like:\n/utr 123456789"
    )

# UTR SUBMIT
@app.on_message(filters.command("utr"))
async def utr(client, message):
    utr = message.text.split(" ", 1)[1]
    await app.send_message(
        ADMIN_ID,
        f"💰 New Payment\nUser: {message.from_user.id}\nUTR: {utr}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{message.from_user.id}")],
            [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{message.from_user.id}")]
        ])
    )
    await message.reply_text("✅ Payment submitted. Wait for approval.")

# APPROVE
@app.on_callback_query(filters.regex("approve_"))
async def approve(client, query):
    user_id = int(query.data.split("_")[1])
    cursor.execute("UPDATE users SET premium=1 WHERE user_id=?", (user_id,))
    db.commit()

    await app.send_message(user_id, "🎉 Premium Activated!")
    await query.answer("Approved")

# REJECT
@app.on_callback_query(filters.regex("reject_"))
async def reject(client, query):
    user_id = int(query.data.split("_")[1])
    await app.send_message(user_id, "❌ Payment Rejected")
    await query.answer("Rejected")

# DOWNLOAD SONG
@app.on_message(filters.text & ~filters.command(["start", "utr"]))
async def song(client, message):
    user_id = message.from_user.id

    cursor.execute("SELECT premium FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if user[0] == 0:
        return await message.reply_text("⚠️ Premium required")

    await message.reply_text("🔍 Searching...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'song.%(ext)s',
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{message.text}", download=True)['entries'][0]
            filename = ydl.prepare_filename(info)

        await message.reply_audio(
            audio=filename,
            title=info.get("title"),
            performer=info.get("uploader")
        )

    except:
        await message.reply_text("❌ Error")

app.run()

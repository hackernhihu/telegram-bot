import os
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.getenv("32597791"))
API_HASH = os.getenv("011dc530b6232ccee97a45bb2db196bb")
BOT_TOKEN = os.getenv("8701935704:AAHo1S_ccPEAzZU2DxyKdL-uy7sgtlhQ9EY")

app = Client("RsMusicHubBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ===== START =====
@app.on_message(filters.command("start"))
async def start(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Trending Songs", callback_data="trending")],
        [InlineKeyboardButton("🔍 Search Song", callback_data="search")],
        [InlineKeyboardButton("💰 Buy Premium", callback_data="buy")],
        [InlineKeyboardButton("💬 Support", url="https://t.me/RSCODERHUB")]
    ])

    await message.reply_text(
        "🎧 RS MUSIC BOT\n\n"
        "⚡ Fast • Modern • Smart Music Bot\n\n"
        "👉 Send any song name to get instant audio",
        reply_markup=buttons
    )

# ===== CALLBACK =====
@app.on_callback_query()
async def callbacks(client, query):
    data = query.data

    if data == "trending":
        msg = await query.message.reply_text("🔥 Fetching Trending Songs...")

        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                results = ydl.extract_info("ytsearch10:trending songs india 2026", download=False)

            text = "🔥 Trending Songs Right Now\n\n"
            for i, song in enumerate(results['entries'], start=1):
                text += f"{i}. {song['title']}\n"

            await msg.edit(text)

        except:
            await msg.edit("❌ Failed to fetch songs")

    elif data == "buy":
        await query.message.reply_text(
            "💰 Premium Plans\n\n"
            "₹99/week\n₹199/month\n₹599/year\n\n"
            "💳 UPI: theghost@ptyes\n\n"
            "📩 Send UTR after payment"
        )

    elif data == "search":
        await query.message.reply_text("🔍 Send song name to search")

# ===== SONG HANDLER =====
@app.on_message(filters.text & ~filters.command(["start"]))
async def music(client, message):
    query = message.text

    msg = await message.reply_text("🔍 Searching song...")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)['entries'][0]

        title = info['title']
        url = info['url']
        duration = info.get("duration", 0)

        caption = f"🎧 {title}\n⏱ Duration: {duration}s\n\n⚡ Powered by RS MUSIC BOT"

        await message.reply_audio(
            audio=url,
            caption=caption,
            title=title
        )

        await msg.delete()

    except Exception as e:
        await msg.edit("❌ Song not found / error")

# ===== RUN =====
app.run()

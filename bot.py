# bot.py
import asyncio
import os
import sys
from datetime import datetime
from typing import Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import yt_dlp
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait

# ==================== CONFIGURATION ====================
API_ID = int(os.getenv("API_ID", 32597791))
API_HASH = os.getenv("API_HASH", "011dc530b6232ccee97a45bb2db196bb")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8701935704:AAHo1S_ccPEAzZU2DxyKdL-uy7sgtlhQ9EY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 8574753078))

# Premium pricing
PREMIUM_PLANS = {
    "weekly": {"price": "₹99", "duration": "7 days", "id": "week"},
    "monthly": {"price": "₹199", "duration": "30 days", "id": "month"},
    "yearly": {"price": "₹599", "duration": "365 days", "id": "year"}
}

UPI_ID = "musicbot@upi"

# yt-dlp configuration
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'geo_bypass': True,
    'nocheckcertificate': True,
    'prefer_ffmpeg': True,
}

# ==================== HELPER FUNCTIONS ====================

def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "Unknown"
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"

def get_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 Trending Songs", callback_data="trending"),
            InlineKeyboardButton("🔍 Search Song", switch_inline_query_current_chat="")
        ],
        [
            InlineKeyboardButton("💰 Buy Premium", callback_data="premium"),
            InlineKeyboardButton("💬 Support", url="https://t.me/music_bot_support")
        ]
    ])

async def search_youtube(query: str, max_results: int = 1) -> list:
    try:
        search_query = f"ytsearch{max_results}:{query}"
        
        def extract_info():
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                return ydl.extract_info(search_query, download=False)
        
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, extract_info)
        
        if not info or 'entries' not in info:
            return []
        
        results = []
        for entry in info['entries'][:max_results]:
            if entry:
                audio_url = None
                if 'url' in entry:
                    audio_url = entry['url']
                elif 'formats' in entry:
                    audio_formats = [f for f in entry['formats'] if f.get('acodec') != 'none']
                    if audio_formats:
                        best_audio = max(audio_formats, key=lambda f: f.get('abr', 0))
                        audio_url = best_audio.get('url')
                
                if audio_url:
                    results.append({
                        'title': entry.get('title', 'Unknown Title'),
                        'duration': entry.get('duration'),
                        'uploader': entry.get('uploader', 'Unknown'),
                        'url': audio_url,
                        'webpage_url': entry.get('webpage_url', ''),
                        'thumbnail': entry.get('thumbnail', '')
                    })
        
        return results
    except Exception as e:
        logger.error(f"YouTube search error: {e}")
        return []

async def get_trending_songs() -> list:
    return await search_youtube("trending songs india 2024", max_results=10)

# ==================== BOT INITIALIZATION ====================

# Create bot instance
app = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="./bot_data"
)

# ==================== COMMAND HANDLERS ====================

@app.on_message(filters.command(["start", "help"]))
async def start_command(client: Client, message: Message):
    welcome_text = (
        "🎵 **Welcome to Music Bot!**\n\n"
        "Send me any song name and I'll instantly stream high-quality audio for you.\n\n"
        "**How to use:**\n"
        "• Type any song name\n"
        "• Or use inline search\n"
        "• Tap buttons below to explore\n\n"
        "✨ **Premium Features:**\n"
        "• Higher quality audio\n"
        "• No ads\n"
        "• Priority processing\n\n"
        "Enjoy your music! 🎧"
    )
    
    try:
        await message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard()
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.text & ~filters.command(["start", "help"]))
async def handle_song_request(client: Client, message: Message):
    query = message.text.strip()
    
    if not query or len(query) < 2:
        await message.reply_text(
            "❌ **Please enter a valid song name!**\n\n"
            "Example: `Shape of You` or `Alan Walker Faded`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    processing_msg = await message.reply_text(
        f"🔍 **Searching...**\n`{query}`",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        songs = await search_youtube(query, max_results=1)
        
        if not songs:
            await processing_msg.edit_text(
                "❌ **No results found!**\n\nTry different keywords.",
                reply_markup=get_main_keyboard()
            )
            return
        
        song = songs[0]
        duration = format_duration(song['duration'])
        caption = (
            f"🎵 **{song['title']}**\n\n"
            f"⏱️ **Duration:** `{duration}`\n"
            f"👤 **Uploader:** `{song['uploader']}`\n\n"
            f"🎧 **Enjoy your music!**"
        )
        
        await processing_msg.delete()
        
        await message.reply_audio(
            audio=song['url'],
            caption=caption,
            title=song['title'],
            performer=song['uploader'],
            duration=song['duration'],
            thumb=song['thumbnail'] if song['thumbnail'] else None,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎵 YouTube Link", url=song['webpage_url']),
                    InlineKeyboardButton("🔄 New Song", callback_data="refresh")
                ]
            ])
        )
        
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await processing_msg.edit_text("⚠️ Rate limited! Please wait.", reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing_msg.edit_text("❌ Error! Please try again.", reply_markup=get_main_keyboard())

@app.on_message(filters.command("utr"))
async def handle_utr(client: Client, message: Message):
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.reply_text(
            "❌ **Invalid format!**\nUse: `/utr YOUR_UTR_NUMBER`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    utr_number = parts[1].strip()
    user = message.from_user
    
    admin_msg = (
        f"💰 **New Premium Purchase Request**\n\n"
        f"👤 **User:** {user.mention}\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"👤 **Username:** @{user.username if user.username else 'N/A'}\n"
        f"📝 **UTR Number:** `{utr_number}`\n"
        f"⏰ **Time:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
    )
    
    try:
        await client.send_message(ADMIN_ID, admin_msg, parse_mode=ParseMode.MARKDOWN)
        await message.reply_text(
            "✅ **UTR Received!**\n\nThank you! Our team will verify and activate your premium within 24 hours.",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error sending UTR: {e}")
        await message.reply_text("❌ Error submitting UTR! Please contact support.")

# ==================== CALLBACK HANDLERS ====================

@app.on_callback_query()
async def handle_callbacks(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    
    try:
        if data == "trending":
            await callback_query.answer("Fetching trending songs...")
            trending_songs = await get_trending_songs()
            
            if not trending_songs:
                await callback_query.message.reply_text("❌ No trending songs found!", reply_markup=get_main_keyboard())
                return
            
            text = "🔥 **Top Trending Songs Today**\n\n"
            for idx, song in enumerate(trending_songs[:10], 1):
                duration = format_duration(song['duration'])
                text += f"{idx}. **{song['title'][:50]}**\n   ⏱️ `{duration}`\n\n"
            
            text += "\n📝 *Send any song name to play it instantly!*"
            
            buttons = [[InlineKeyboardButton(f"🎵 Play #{i+1}", callback_data=f"play_{i}")] for i in range(min(5, len(trending_songs)))]
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")])
            
            # Store songs temporarily
            callback_query.message._trending_songs = trending_songs
            
            await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
        
        elif data.startswith("play_"):
            song_index = int(data.split("_")[1])
            trending_songs = getattr(callback_query.message, '_trending_songs', [])
            
            if not trending_songs or song_index >= len(trending_songs):
                await callback_query.answer("Song not found!", show_alert=True)
                return
            
            song = trending_songs[song_index]
            await callback_query.answer(f"Playing: {song['title'][:30]}...")
            
            duration = format_duration(song['duration'])
            caption = f"🎵 **{song['title']}**\n\n⏱️ **Duration:** `{duration}`\n🔥 *Trending Song*"
            
            await callback_query.message.reply_audio(
                audio=song['url'],
                caption=caption,
                title=song['title'],
                duration=song['duration'],
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "premium":
            text = "💰 **Premium Subscription**\n\n✨ **Benefits:**\n• Highest quality audio\n• Priority processing\n• No ads\n\n**Plans:**\n"
            buttons = []
            for plan_id, plan in PREMIUM_PLANS.items():
                text += f"• *{plan['price']}* - {plan['duration']}\n"
                buttons.append([InlineKeyboardButton(f"{plan['price']} - {plan['duration']}", callback_data=f"premium_{plan_id}")])
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")])
            
            await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
            await callback_query.answer()
        
        elif data.startswith("premium_"):
            plan_id = data.replace("premium_", "")
            plan = PREMIUM_PLANS.get(plan_id)
            if plan:
                text = (
                    f"💎 **Plan:** {plan['price']}\n\n"
                    f"**Payment:**\nSend *{plan['price']}* to:\n`{UPI_ID}`\n\n"
                    f"After payment, send UTR: `/utr YOUR_UTR_NUMBER`"
                )
                await callback_query.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="premium")]]))
                await callback_query.answer()
        
        elif data == "refresh":
            await callback_query.message.delete()
            await callback_query.answer("Send me a song name!")
        
        elif data == "back_to_menu":
            await callback_query.message.edit_text(
                "🎵 **Main Menu**\n\nSend me any song name!",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_keyboard()
            )
            await callback_query.answer()
        
        else:
            await callback_query.answer("Invalid option!", show_alert=True)
            
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await callback_query.answer("Please wait...", show_alert=True)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

# ==================== MAIN ====================

if __name__ == "__main__":
    logger.info("🤖 Starting Music Bot...")
    try:
        app.run()
    except FloodWait as e:
        logger.error(f"FloodWait: Need to wait {e.value} seconds before restarting")
        time.sleep(e.value)
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

# bot.py
import asyncio
import re
from datetime import datetime
from typing import Optional, Tuple

import yt_dlp
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ==================== CONFIGURATION ====================
API_ID = 32597791
API_HASH = "011dc530b6232ccee97a45bb2db196bb"
BOT_TOKEN = "8701935704:AAHo1S_ccPEAzZU2DxyKdL-uy7sgtlhQ9EY"
ADMIN_ID = 8574753078

# Premium pricing
PREMIUM_PLANS = {
    "weekly": {"price": "₹99", "duration": "7 days", "id": "week"},
    "monthly": {"price": "₹199", "duration": "30 days", "id": "month"},
    "yearly": {"price": "₹599", "duration": "365 days", "id": "year"}
}

UPI_ID = "musicbot@upi"  # Replace with your actual UPI ID

# yt-dlp configuration for optimal performance
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'geo_bypass': True,
    'nocheckcertificate': True,
    'prefer_ffmpeg': True,
    'extract_audio': True,
    'audio_format': 'mp3',
    'audio_quality': '320',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',
    }],
}

# Initialize bot
app = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==================== HELPER FUNCTIONS ====================

def format_duration(seconds: Optional[int]) -> str:
    """Convert seconds to readable duration format"""
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
    """Create main menu inline keyboard"""
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
    """Search YouTube and return audio stream URL with metadata"""
    try:
        search_query = f"ytsearch{max_results}:{query}"
        ydl_opts = {
            **YDL_OPTS,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info without downloading
            info = await asyncio.to_thread(ydl.extract_info, search_query, download=False)
            
            if not info or 'entries' not in info:
                return []
            
            results = []
            for entry in info['entries'][:max_results]:
                if entry:
                    # Get best audio format URL
                    audio_url = None
                    if 'url' in entry:
                        audio_url = entry['url']
                    elif 'formats' in entry:
                        # Find best audio format
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
        print(f"YouTube search error: {e}")
        return []

async def get_trending_songs() -> list:
    """Fetch trending songs from YouTube"""
    return await search_youtube("trending songs india 2024", max_results=10)

# ==================== COMMAND HANDLERS ====================

@app.on_message(filters.command(["start", "help"]))
async def start_command(client: Client, message: Message):
    """Handle /start and /help commands"""
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
    
    await message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

@app.on_message(filters.text & ~filters.command(["start", "help"]))
async def handle_song_request(client: Client, message: Message):
    """Handle song search requests"""
    query = message.text.strip()
    
    if not query or len(query) < 2:
        await message.reply_text(
            "❌ **Please enter a valid song name!**\n\n"
            "Example: `Shape of You` or `Alan Walker Faded`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Send processing message
    processing_msg = await message.reply_text(
        "🔍 **Searching...**\n"
        f"`{query}`",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Search for the song
        songs = await search_youtube(query, max_results=1)
        
        if not songs:
            await processing_msg.edit_text(
                "❌ **No results found!**\n\n"
                "Try:\n"
                "• Using different keywords\n"
                "• Checking spelling\n"
                "• Using the search button below",
                reply_markup=get_main_keyboard()
            )
            return
        
        song = songs[0]
        
        # Format caption
        duration = format_duration(song['duration'])
        caption = (
            f"🎵 **{song['title']}**\n\n"
            f"⏱️ **Duration:** `{duration}`\n"
            f"👤 **Uploader:** `{song['uploader']}`\n\n"
            f"🎧 **Enjoy your music!**"
        )
        
        # Delete processing message
        await processing_msg.delete()
        
        # Send audio to user
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
        
    except Exception as e:
        print(f"Error in handle_song_request: {e}")
        await processing_msg.edit_text(
            "❌ **Something went wrong!**\n\n"
            "Please try again later or contact support.",
            reply_markup=get_main_keyboard()
        )

# ==================== CALLBACK QUERY HANDLERS ====================

@app.on_callback_query()
async def handle_callbacks(client: Client, callback_query: CallbackQuery):
    """Handle all callback queries"""
    data = callback_query.data
    
    if data == "trending":
        await show_trending_songs(callback_query)
    
    elif data == "premium":
        await show_premium_plans(callback_query)
    
    elif data == "refresh":
        await callback_query.message.delete()
        await callback_query.answer("Send me a song name to get started!", show_alert=True)
    
    elif data.startswith("premium_"):
        plan_id = data.replace("premium_", "")
        plan = PREMIUM_PLANS.get(plan_id)
        if plan:
            await handle_premium_purchase(callback_query, plan)
    
    else:
        await callback_query.answer("Invalid option!", show_alert=True)

async def show_trending_songs(callback_query: CallbackQuery):
    """Show trending songs to user"""
    await callback_query.answer("Fetching trending songs...")
    
    trending_msg = await callback_query.message.reply_text(
        "🔥 **Fetching Trending Songs...**\nPlease wait ⏳",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        trending_songs = await get_trending_songs()
        
        if not trending_songs:
            await trending_msg.edit_text(
                "❌ **Unable to fetch trending songs right now.**\n\nPlease try again later.",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Format trending songs list
        text = "🔥 **Top Trending Songs Today**\n\n"
        for idx, song in enumerate(trending_songs, 1):
            duration = format_duration(song['duration'])
            text += f"{idx}. **{song['title'][:50]}**\n   ⏱️ `{duration}`\n\n"
        
        text += "\n📝 *Send any song name to play it instantly!*"
        
        # Create buttons for top 5 songs
        buttons = []
        for idx, song in enumerate(trending_songs[:5], 1):
            buttons.append([
                InlineKeyboardButton(f"🎵 {idx}. Play", callback_data=f"play_{idx}")
            ])
        
        buttons.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
        
        # Store trending songs in memory for quick access
        callback_query.message._trending_songs = trending_songs
        
        await trending_msg.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        print(f"Error in show_trending_songs: {e}")
        await trending_msg.edit_text(
            "❌ **Error fetching trending songs!**\n\nPlease try again.",
            reply_markup=get_main_keyboard()
        )

@app.on_callback_query(lambda c: c.data.startswith("play_"))
async def play_trending_song(client: Client, callback_query: CallbackQuery):
    """Play selected trending song"""
    song_index = int(callback_query.data.split("_")[1]) - 1
    
    trending_songs = getattr(callback_query.message, '_trending_songs', None)
    
    if not trending_songs or song_index >= len(trending_songs):
        await callback_query.answer("Song not found! Please refresh.", show_alert=True)
        return
    
    song = trending_songs[song_index]
    
    await callback_query.answer(f"Playing: {song['title'][:30]}...")
    
    # Send audio
    duration = format_duration(song['duration'])
    caption = (
        f"🎵 **{song['title']}**\n\n"
        f"⏱️ **Duration:** `{duration}`\n"
        f"👤 **Uploader:** `{song['uploader']}`\n\n"
        f"🔥 *Trending Song*"
    )
    
    await callback_query.message.reply_audio(
        audio=song['url'],
        caption=caption,
        title=song['title'],
        performer=song['uploader'],
        duration=song['duration'],
        thumb=song['thumbnail'] if song['thumbnail'] else None,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎵 YouTube Link", url=song['webpage_url'])]
        ])
    )

@app.on_callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(client: Client, callback_query: CallbackQuery):
    """Return to main menu"""
    await callback_query.message.edit_text(
        "🎵 **Main Menu**\n\n"
        "Send me any song name or use the buttons below!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )
    await callback_query.answer()

async def show_premium_plans(callback_query: CallbackQuery):
    """Show premium subscription plans"""
    text = (
        "💰 **Premium Subscription**\n\n"
        "✨ **Benefits:**\n"
        "• 🎵 Highest quality audio (320kbps)\n"
        "• 🚀 Priority processing\n"
        "• 📥 Unlimited downloads\n"
        "• 🎯 No ads\n"
        "• 💬 Priority support\n\n"
        "**Choose your plan:**\n\n"
    )
    
    buttons = []
    for plan_id, plan in PREMIUM_PLANS.items():
        text += f"• *{plan['price']}* - {plan['duration']}\n"
        buttons.append([InlineKeyboardButton(
            f"{plan['price']} - {plan['duration']}", 
            callback_data=f"premium_{plan_id}"
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")])
    
    await callback_query.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await callback_query.answer()

async def handle_premium_purchase(callback_query: CallbackQuery, plan: dict):
    """Handle premium purchase process"""
    text = (
        f"💎 **Premium Plan Selected:** {plan['price']}\n\n"
        f"**Payment Instructions:**\n\n"
        f"1️⃣ Send *{plan['price']}* to this UPI ID:\n"
        f"`{UPI_ID}`\n\n"
        f"2️⃣ After payment, send the UTR/Transaction ID here\n\n"
        f"3️⃣ Our team will activate your premium within 24 hours\n\n"
        f"📝 *Send UTR number in this format:*\n"
        f"`/utr YOUR_UTR_NUMBER`"
    )
    
    buttons = [[InlineKeyboardButton("🔙 Back to Plans", callback_data="premium")]]
    
    await callback_query.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await callback_query.answer()

@app.on_message(filters.command("utr"))
async def handle_utr(client: Client, message: Message):
    """Handle UTR submission"""
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.reply_text(
            "❌ **Invalid format!**\n\n"
            "Use: `/utr YOUR_UTR_NUMBER`\n\n"
            "Example: `/utr HDFC123456789`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    utr_number = parts[1].strip()
    user = message.from_user
    
    # Format message for admin
    admin_msg = (
        f"💰 **New Premium Purchase Request**\n\n"
        f"👤 **User:** {user.mention}\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"👤 **Username:** @{user.username if user.username else 'N/A'}\n"
        f"📝 **UTR Number:** `{utr_number}`\n"
        f"⏰ **Time:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
        f"📌 *Please verify and activate premium manually*"
    )
    
    try:
        # Forward to admin
        await client.send_message(
            ADMIN_ID,
            admin_msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Activate Premium", callback_data=f"activate_{user.id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
                ],
                [InlineKeyboardButton("📩 Reply to User", callback_data=f"reply_{user.id}")]
            ])
        )
        
        # Acknowledge user
        await message.reply_text(
            "✅ **UTR Received!**\n\n"
            "Thank you for your purchase! Our team will verify and activate your premium within 24 hours.\n\n"
            "You'll receive a confirmation message once activated.\n\n"
            "For any queries, contact support.",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        print(f"Error sending UTR to admin: {e}")
        await message.reply_text(
            "❌ **Error submitting UTR!**\n\n"
            "Please contact support directly.",
            parse_mode=ParseMode.MARKDOWN
        )

# Admin callback handlers
@app.on_callback_query(lambda c: c.data.startswith("activate_"))
async def activate_premium(client: Client, callback_query: CallbackQuery):
    """Admin activates premium for user"""
    user_id = int(callback_query.data.split("_")[1])
    
    try:
        await client.send_message(
            user_id,
            "🎉 **Congratulations!** 🎉\n\n"
            "Your premium has been **activated** successfully!\n\n"
            "✨ **Enjoy your benefits:**\n"
            "• Highest quality audio\n"
            "• Priority processing\n"
            "• Unlimited access\n\n"
            "Thank you for choosing us! 🎵"
        )
        
        await callback_query.message.edit_text(
            callback_query.message.text + "\n\n✅ **Premium Activated Successfully!**"
        )
        await callback_query.answer("Premium activated!")
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)

@app.on_callback_query(lambda c: c.data.startswith("reject_"))
async def reject_premium(client: Client, callback_query: CallbackQuery):
    """Admin rejects premium request"""
    user_id = int(callback_query.data.split("_")[1])
    
    try:
        await client.send_message(
            user_id,
            "❌ **Premium Request Rejected**\n\n"
            "We couldn't verify your payment. Please check:\n"
            "• Correct UTR number\n"
            "• Successful payment\n"
            "• Contact support for assistance",
            parse_mode=ParseMode.MARKDOWN
        )
        
        await callback_query.message.edit_text(
            callback_query.message.text + "\n\n❌ **Request Rejected**"
        )
        await callback_query.answer("Request rejected!")
        
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)

@app.on_callback_query(lambda c: c.data.startswith("reply_"))
async def reply_to_user(client: Client, callback_query: CallbackQuery):
    """Admin can reply to user"""
    user_id = int(callback_query.data.split("_")[1])
    
    await callback_query.message.reply_text(
        "📝 **Reply to user:**\n\n"
        "Send your message here and it will be forwarded to the user.\n"
        "Reply to this message with your response."
    )
    
    # Store user_id in a temporary variable (simplified)
    callback_query.message._reply_to_user = user_id
    await callback_query.answer()

# ==================== ERROR HANDLERS ====================

@app.on_message(filters.incoming & ~filters.me)
async def error_handler(_, message: Message):
    """Global error handler for all messages"""
    # This is a placeholder - actual errors are handled in individual functions
    pass

# ==================== MAIN ====================

if __name__ == "__main__":
    print("🤖 Music Bot Started!")
    print("✅ Bot is running...")
    app.run()

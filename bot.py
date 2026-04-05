# bot.py - Using HTTP API (No API ID/Hash required)
import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Only Bot Token needed!
BOT_TOKEN = "8701935704:AAHo1S_ccPEAzZU2DxyKdL-uy7sgtlhQ9EY"
ADMIN_ID = 8574753078

# yt-dlp configuration
YDL_OPTS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
}

async def search_youtube(query: str):
    """Search YouTube and get audio URL"""
    try:
        search_query = f"ytsearch1:{query}"
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(search_query, download=False)
            if info and 'entries' in info and info['entries']:
                entry = info['entries'][0]
                # Get audio URL
                if 'url' in entry:
                    audio_url = entry['url']
                elif 'formats' in entry:
                    audio_formats = [f for f in entry['formats'] if f.get('acodec') != 'none']
                    if audio_formats:
                        audio_url = max(audio_formats, key=lambda f: f.get('abr', 0)).get('url')
                    else:
                        audio_url = entry['formats'][0]['url']
                else:
                    return None
                
                return {
                    'title': entry.get('title', 'Unknown'),
                    'duration': entry.get('duration', 0),
                    'url': audio_url,
                    'webpage': entry.get('webpage_url', '')
                }
    except Exception as e:
        print(f"Error: {e}")
        return None

async def start(update: Update, context):
    """Handle /start command"""
    keyboard = [
        [
            InlineKeyboardButton("🔥 Trending", callback_data='trending'),
            InlineKeyboardButton("💰 Premium", callback_data='premium')
        ],
        [InlineKeyboardButton("💬 Support", url='https://t.me/music_bot_support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎵 **Welcome to Music Bot!**\n\n"
        "Send me any song name and I'll play it for you!\n\n"
        "✨ Just type a song name to get started.",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def handle_song(update: Update, context):
    """Handle song requests"""
    query = update.message.text
    msg = await update.message.reply_text(f"🔍 Searching for: {query}...")
    
    song = await search_youtube(query)
    
    if not song:
        await msg.edit_text("❌ Song not found! Try different keywords.")
        return
    
    await msg.delete()
    
    # Send audio
    await update.message.reply_audio(
        audio=song['url'],
        title=song['title'],
        duration=song['duration'],
        caption=f"🎵 **{song['title']}**\n\nEnjoy! 🎧",
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'trending':
        trending_songs = [
            "Blinding Lights - The Weeknd",
            "Shape of You - Ed Sheeran", 
            "Dance Monkey - Tones and I",
            "Someone You Loved - Lewis Capaldi",
            "Bad Guy - Billie Eilish"
        ]
        
        text = "🔥 **Trending Songs**\n\n"
        for i, song in enumerate(trending_songs, 1):
            text += f"{i}. {song}\n"
        text += "\nSend any song name to play!"
        
        await query.edit_message_text(text, parse_mode='Markdown')
    
    elif query.data == 'premium':
        text = (
            "💰 **Premium Plans**\n\n"
            "✨ **Benefits:**\n"
            "• Higher quality audio\n"
            "• Priority processing\n"
            "• No ads\n\n"
            "**Plans:**\n"
            "• ₹99/week\n"
            "• ₹199/month\n"
            "• ₹599/year\n\n"
            f"Pay to: `music@upi`\n"
            "Send UTR to admin after payment."
        )
        await query.edit_message_text(text, parse_mode='Markdown')

async def utr_handler(update: Update, context):
    """Handle UTR submissions"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    if text.startswith('/utr'):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await update.message.reply_text("❌ Send UTR: `/utr YOUR_UTR`", parse_mode='Markdown')
            return
        
        utr = parts[1]
        user = update.message.from_user
        
        # Forward to admin (in a real bot, you'd save to database)
        await context.bot.send_message(
            ADMIN_ID,
            f"💰 New Payment!\nUser: {user.first_name}\nID: {user.id}\nUTR: {utr}"
        )
        
        await update.message.reply_text("✅ UTR Received! We'll activate premium within 24 hours.")

def main():
    """Start the bot"""
    # Create application - only needs Bot Token!
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("utr", utr_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start bot
    print("🤖 Bot started! (Using HTTP API - No API ID/Hash needed)")
    application.run_polling()

if __name__ == "__main__":
    main()

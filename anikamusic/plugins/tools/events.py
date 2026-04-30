import asyncio
from datetime import date, timedelta
import holidays
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from groq import AsyncGroq

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

from anikamusic import app
from anikamusic.misc import SUDOERS
from anikamusic.utils.database import get_served_chats, get_served_users

# ==========================================
#              CONFIGURATION
# ==========================================
# Yaha apni Groq API key daalo
GROQ_API_KEY = "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"
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

# India holidays setup
ind_holidays = holidays.India(years=date.today().year)

# Aesthetic smallcaps text
def smallcaps(text):
    chars = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ', 
        'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 
        'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ', 
        'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ', 
        'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 
        'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ', 
        'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ'
    }
    return ''.join(chars.get(c, c) for c in str(text))

# ==========================================
#              GROQ AI GENERATOR
# ==========================================
async def generate_ai_wish(event_name):
    """Groq API se festival ke liye fast aur aesthetic wish generate karwata hai"""
    try:
        # LLaMA 3 8B is extremely fast and great for short texts
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {
                    "role": "system", 
                    "content": "You are a creative Telegram bot assistant. Write a short, beautiful, and aesthetic community wish message for a festival. Include nice emojis. Keep it warm and engaging. Do not use hashtags. Write it in a mix of Hindi and English (Hinglish)."
                },
                {
                    "role": "user", 
                    "content": f"Generate a wish for: {event_name}"
                }
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq AI Wish Error: {e}")
        return f"🎉 Wishing everyone a very Happy {event_name}! Have a great day ahead! ✨"

# ==========================================
#              AUTO BROADCASTER
# ==========================================
async def auto_wish_broadcast():
    """Daily check karta hai aur event hone pe sab groups/users ko bhejta hai (NO ASSISTANTS)"""
    today = date.today()
    event_today = ind_holidays.get(today)
    
    if not event_today:
        return # Aaj koi event nahi hai
        
    print(f"[AutoWish] Today is {event_today}! Generating Groq AI wish...")
    
    wish_text = await generate_ai_wish(event_today)
    final_message = f"🎊 **{smallcaps('Special Event Today')}** 🎊\n\n**{event_today}**\n\n{wish_text}"
    
    # 1. BROADCAST TO GROUPS
    sent_chats = 0
    chats = []
    schats = await get_served_chats()
    for chat in schats:
        chats.append(int(chat["chat_id"]))
        
    for i in chats:
        try:
            await app.send_message(i, text=final_message)
            sent_chats += 1
            await asyncio.sleep(0.2)
        except FloodWait as fw:
            flood_time = int(fw.value)
            if flood_time > 200:
                continue
            await asyncio.sleep(flood_time)
        except:
            continue

    # 2. BROADCAST TO USERS
    sent_users = 0
    served_users = []
    susers = await get_served_users()
    for user in susers:
        served_users.append(int(user["user_id"]))
        
    for i in served_users:
        try:
            await app.send_message(i, text=final_message)
            sent_users += 1
            await asyncio.sleep(0.2)
        except FloodWait as fw:
            flood_time = int(fw.value)
            if flood_time > 200:
                continue
            await asyncio.sleep(flood_time)
        except:
            pass

    print(f"[AutoWish] Successfully broadcasted to {sent_chats} groups and {sent_users} users.")

# ==========================================
#              COMMAND: /events
# ==========================================
@app.on_message(filters.command("events"))
async def upcoming_events(client, message: Message):
    today = date.today()
    upcoming = []
    
    # Check next 60 days
    for i in range(1, 60):
        check_date = today + timedelta(days=i)
        event = ind_holidays.get(check_date)
        if event:
            date_str = check_date.strftime("%d %b %Y")
            upcoming.append(f"📅 **{date_str}** - {event}")
            
    if not upcoming:
        await message.reply_text(f"✨ **{smallcaps('Upcoming Events')}**\n\nAgley 2 mahine tak koi bada event nahi hai.")
        return

    text = f"✨ **{smallcaps('Upcoming Events')}** ✨\n\n"
    for ev in upcoming[:5]:
        text += f"{ev}\n"
        
    await message.reply_text(text)


# ==========================================
#              SCHEDULER SETUP
# ==========================================
scheduler = AsyncIOScheduler()
# Har roz subah 8:00 AM par check aur broadcast karega
scheduler.add_job(auto_wish_broadcast, "cron", hour=8, minute=0)
scheduler.start()
          

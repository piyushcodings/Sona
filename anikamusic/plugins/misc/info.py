import asyncio
import aiohttp
from pyrogram import filters, enums
from pyrogram.types import Message

import config
from anikamusic import app

# --- STATIC SAFE IMAGE (Anti-Abuse) ---
SAFE_PFP = "https://i.ibb.co/cSphm5Sz/1d356388-a993-478a-b358-69c96fb57597.jpg"

# --- PREMIUM INJECTION FUNCTION ---
async def inject_premium_markup(chat_id, message_id, markup):
    try:
        token = getattr(config, "BOT_TOKEN", getattr(app, "bot_token", None))
        url = f"https://api.telegram.org/bot{token}/editMessageReplyMarkup"
        payload = {"chat_id": chat_id, "message_id": message_id, "reply_markup": {"inline_keyboard": markup}}
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=payload)
    except Exception as e:
        print(f"❌ Markup Injection Error: {e}")

# --- PREMIUM INFO TEXT TEMPLATE ---
INFO_TEXT = """**
<emoji id='6334696528145286813'>⚡</emoji> 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 <emoji id='6334696528145286813'>⚡</emoji>

<emoji id='6334333036473091884'>📌</emoji> ᴜsᴇʀ ɪᴅ ‣ **`{}`
**<emoji id='6334471179801200139'>🎉</emoji> ғɪʀsᴛ ɴᴀᴍᴇ ‣ **{}
**<emoji id='6334471179801200139'>🎉</emoji> ʟᴀsᴛ ɴᴀᴍᴇ ‣ **{}
**<emoji id='6334672948774831861'>🔐</emoji> ᴜsᴇʀɴᴀᴍᴇ ‣ **{}
**<emoji id='6334381440754517833'>👤</emoji> ᴍᴇɴᴛɪᴏɴ ‣ **{}
**<emoji id='6334789677396002338'>⏱</emoji> ʟᴀsᴛ sᴇᴇɴ ‣ **{}
**<emoji id='6334648089504122382'>🍂</emoji> ᴅᴄ ɪᴅ ‣ **{}
**<emoji id='5375434433195164090'>✨</emoji> ᴘʀᴇᴍɪᴜᴍ ‣ **{}
**<emoji id='5375418387197350395'>💬</emoji> ʙɪᴏ ‣ **`{}`

**•─────────────────•**
"""

# --- STATUS FUNCTION ---
async def userstatus(user_id):
    try:
        user = await app.get_users(user_id)
        x = user.status
        if x == enums.UserStatus.RECENTLY:
            return "Recently"
        elif x == enums.UserStatus.LAST_WEEK:
            return "Last week"
        elif x == enums.UserStatus.LONG_AGO:
            return "Long time ago"
        elif x == enums.UserStatus.OFFLINE:
            return "Offline"
        elif x == enums.UserStatus.ONLINE:
            return "Online"
    except:
        return "Unknown"

# --- AUTO DELETE TASK ---
async def auto_delete_msg(message: Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass

# --- COMMAND HANDLER ---
@app.on_message(filters.command(["info", "userinfo"]) & filters.group)
async def userinfo(_, message: Message):
    chat_id = message.chat.id
    target_user_id = message.from_user.id
    
    # Clean and optimize target extraction
    if message.reply_to_message:
        target_user_id = message.reply_to_message.from_user.id
    elif len(message.command) == 2:
        try:
            target_user_id = message.text.split(None, 1)[1]
        except:
            pass
            
    # --- LOADING ANIMATION ---
    load_msg = await message.reply_text("<emoji id='6334789677396002338'>⏱</emoji> <b>ғᴇᴛᴄʜɪɴɢ ᴅᴀᴛᴀ.</b>")
    await asyncio.sleep(0.2)
    await load_msg.edit_text("<emoji id='6334789677396002338'>⏱</emoji> <b>ғᴇᴛᴄʜɪɴɢ ᴅᴀᴛᴀ..</b>")
    await asyncio.sleep(0.2)
    await load_msg.edit_text("<emoji id='6334789677396002338'>⏱</emoji> <b>ғᴇᴛᴄʜɪɴɢ ᴅᴀᴛᴀ...</b>")
    
    try:
        user_info = await app.get_chat(target_user_id)
        user = await app.get_users(target_user_id)
        status = await userstatus(user.id)
        
        uid = user_info.id
        dc_id = user.dc_id if user.dc_id else "Unknown"
        first_name = user_info.first_name 
        last_name = user_info.last_name if user_info.last_name else "---"
        username = f"@{user_info.username}" if user_info.username else "---"
        mention = user.mention
        bio = user_info.bio if user_info.bio else "No bio set"
        is_premium = "Yes ✅" if user.is_premium else "No ❌"
        
        final_text = INFO_TEXT.format(
            uid, first_name, last_name, username, mention, status, dc_id, is_premium, bio
        )
        
        # --- BUTTONS (Green and Red Hack) ---
        buttons = [
            [
                {"text": "CLOSE", "callback_data": "close", "style": "danger", "icon_custom_emoji_id": "6334598469746952256"}
            ]
        ]
        
        # Send permanent safe image with spoiler effect
        run = await app.send_photo(
            chat_id, 
            photo=SAFE_PFP, 
            caption=final_text, 
            reply_to_message_id=message.id,
            has_spoiler=True # Yahan spoiler effect add kiya gaya hai
        )
        
        # Inject Premium Buttons
        await inject_premium_markup(chat_id, run.id, buttons)
        
        # Delete loading message
        await load_msg.delete()
        
        # --- AUTO DELETE AFTER 2 MINUTES (120 secs) ---
        asyncio.create_task(auto_delete_msg(run, 120))
        asyncio.create_task(auto_delete_msg(message, 120)) # Delete user's command too for a clean chat
            
    except Exception as e:
        await load_msg.edit_text(f"❌ Error: `{str(e)}`")
        asyncio.create_task(auto_delete_msg(load_msg, 10))
        

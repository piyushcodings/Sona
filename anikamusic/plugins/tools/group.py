import aiohttp
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from anikamusic import app
from config import OWNER_ID

# ==========================================
#         🔥 VC NOTIFICATIONS 🔥
# ==========================================

# vc on
@app.on_message(filters.video_chat_started)
async def brah(client, msg: Message):
    text = "<blockquote><emoji id='6334789677396002338'>✨</emoji> **ᴛʜᴇ ᴘᴀʀᴛʏ ʙᴇɢɪɴꜱ! ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ɪꜱ ɴᴏᴡ ʟɪᴠᴇ.**\n\n<emoji id='6334598469746952256'>🫶</emoji> ᴊᴏɪɴ ɪɴ ᴇᴠᴇʀʏᴏɴᴇ, ʟᴇᴛ'ꜱ ʜᴀᴠᴇ ꜰᴜɴ!</blockquote>"
    await msg.reply(text)

# vc off
@app.on_message(filters.video_chat_ended)
async def brah2(client, msg: Message):
    text = "<blockquote><emoji id='6334648089504122382'>❌</emoji> **ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴇɴᴅᴇᴅ!**\n\n<emoji id='6334333036473091884'>⚠️</emoji> ᴛʜᴇ ᴘᴀʀᴛʏ ɪꜱ ᴏᴠᴇʀ. ꜱᴇᴇ ʏᴏᴜ ᴀɢᴀɪɴ!</blockquote>"
    await msg.reply(text)

# invite members on vc
@app.on_message(filters.video_chat_members_invited)
async def brah3(client, message: Message):
    text = f"<blockquote><emoji id='6334696528145286813'>⏳</emoji> **{message.from_user.mention} ɪɴᴠɪᴛᴇᴅ ʏᴏᴜ ᴛᴏ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ!**\n\n<emoji id='6334381440754517833'>✨</emoji> **ɪɴᴠɪᴛᴇᴅ ᴍᴇᴍʙᴇʀꜱ:**\n"
    
    x = 0
    for user in message.video_chat_members_invited.users:
        try:
            text += f"<emoji id='6334598469746952256'>🔸</emoji> [{user.first_name}](tg://user?id={user.id})\n"
            x += 1
        except Exception:
            pass
            
    text += "</blockquote>"
    try:
        await message.reply(text)
    except:
        pass


# ==========================================
#           🔥 MATH COMMAND 🔥
# ==========================================
@app.on_message(filters.command(["math"], prefixes=["/", "!", "."]))
async def calculate_math(client, message: Message):   
    if len(message.command) < 2:
        return await message.reply("<blockquote><emoji id='6334333036473091884'>⚠️</emoji> ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ Qᴜᴇꜱᴛɪᴏɴ! ᴇx: `/math 2+2`</blockquote>")
        
    expression = message.text.split(None, 1)[1]
    try:        
        result = eval(expression)
        response = f"<blockquote><emoji id='6334789677396002338'>✨</emoji> **ᴍᴀᴛʜ ꜱᴏʟᴠᴇᴅ:**\n\n<emoji id='6334672948774831861'>📈</emoji> Qᴜᴇꜱᴛɪᴏɴ: `{expression}`\n<emoji id='6334598469746952256'>💡</emoji> ᴀɴꜱᴡᴇʀ: **{result}**</blockquote>"
    except Exception:
        response = "<blockquote><emoji id='6334648089504122382'>❌</emoji> ɪɴᴠᴀʟɪᴅ ᴇxᴘʀᴇꜱꜱɪᴏɴ! ᴘʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ᴏɴᴇ.</blockquote>"
    await message.reply(response)


# ==========================================
#        🔥 LEAVE GROUP COMMAND 🔥
# ==========================================
@app.on_message(filters.command(["leavegroup"], prefixes=["/", "!", "."]) & filters.user(OWNER_ID))
async def bot_leave(client, message: Message):
    chat_id = message.chat.id
    text = "<blockquote><emoji id='6334471179801200139'>⚠️</emoji> ʙʏᴇ ʙʏᴇ ɢᴜʏꜱ! ɪ ᴀᴍ ʟᴇᴀᴠɪɴɢ...\n\n<emoji id='6334648089504122382'>❌</emoji> **ʟᴇꜰᴛ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.**</blockquote>"
    await message.reply_text(text)
    await app.leave_chat(chat_id=chat_id, delete=True)


# ==========================================
#         🔥 GOOGLE SEARCH (SPG) 🔥
# ==========================================
@app.on_message(filters.command(["spg"], ["/", "!", "."]))
async def search(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("<blockquote><emoji id='6334333036473091884'>⚠️</emoji> ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ Qᴜᴇʀʏ ᴛᴏ ꜱᴇᴀʀᴄʜ!</blockquote>")

    query = message.text.split(None, 1)[1]
    msg = await message.reply("<blockquote><emoji id='6334696528145286813'>⏳</emoji> ꜱᴇᴀʀᴄʜɪɴɢ...</blockquote>")
    
    async with aiohttp.ClientSession() as session:
        start = 1
        # Make sure your API key here is valid!
        url = f"https://content-customsearch.googleapis.com/customsearch/v1?cx=ec8db9e1f9e41e65e&q={query}&key=AIzaSyAa8yy0GdcGPHdtD083HiGGx_S0vMPScDM&start={start}"
        async with session.get(url, headers={"x-referer": "https://explorer.apis.google.com"}) as r:
            response = await r.json()
            
            if not response.get("items"):
                return await msg.edit("<blockquote><emoji id='6334648089504122382'>❌</emoji> ɴᴏ ʀᴇꜱᴜʟᴛꜱ ꜰᴏᴜɴᴅ ꜰᴏʀ ᴛʜɪꜱ Qᴜᴇʀʏ!</blockquote>")
                
            result = f"<blockquote><emoji id='6334789677396002338'>✨</emoji> **ɢᴏᴏɢʟᴇ ꜱᴇᴀʀᴄʜ ʀᴇꜱᴜʟᴛꜱ:**\n\n"
            
            # Show top 5 results to keep the message clean
            for item in response["items"][:5]:
                title = item["title"]
                link = item["link"]
                if "/s" in link:
                    link = link.replace("/s", "")
                elif re.search(r'\/\d', link):
                    link = re.sub(r'\/\d', "", link)
                if "?" in link:
                    link = link.split("?")[0]
                    
                result += f"<emoji id='6334598469746952256'>🔸</emoji> [{title}]({link})\n"
                
            result += "</blockquote>"
            
            await msg.edit(result, disable_web_page_preview=True)
               

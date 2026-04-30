from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from anikamusic import app
from config import BOT_USERNAME
from anikamusic.utils.errors import capture_err
import httpx 
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

start_txt = """
❥ ωєℓ¢σмє тσ  ˹ 𝄞 𖦹 ˹ 𝚂𝛐𝛈𝛂  ♪˼ 🥀 

❥ ʀᴇᴘᴏ ᴄʜᴀᴀʜɪʏe ᴛᴏ ʙᴏᴛ ᴋᴏ 

❥ 3 ɢᴄ ᴍᴀɪ ᴀᴅᴅ ᴋᴀʀ ᴋᴇ 

❥ ᴀᴅᴍɪɴ ʙᴀɴᴏ ᴀᴜʀ sᴄʀᴇᴇɴsʜᴏᴛ 
     
❥ ᴏᴡɴᴇʀ @Hindustani_ladka00 ᴋᴏ ᴅᴏ ғɪʀ ʀᴇᴘᴏ ᴍɪʟ sᴀᴋᴛɪ ʜᴀɪ 

"""




@app.on_message(filters.command("repo"))
async def start(_, msg):
    buttons = [
        [ 
          InlineKeyboardButton("♡ α∂∂ иσω ♡", url=f"https://t.me/imsona_bot?startgroup=true")
        ],
        [
          InlineKeyboardButton("ѕυρρσɾƚ", url="https://t.me/+ZVRFmlrgRWw2YTBl"),
          InlineKeyboardButton("⏤͟͞ 尸讠丫ㄩ丂卄 🇮🇳", url="https://t.me/Hindustani_Ladka00"),
          ],
               [
                InlineKeyboardButton("ᴏᴛʜᴇʀ ʙᴏᴛs", url=f"https://t.me/itzpiyush007"),
],
[
InlineKeyboardButton("ᴄʜᴇᴄᴋ", url=f"https://t.me/Anikamusicbot"),

        ]]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await msg.reply_photo(
        photo="https://graph.org/file/90ef1bc444de679d65209-335d94a31975f4eda6.jpg",
        caption=start_txt,
        reply_markup=reply_markup
    )

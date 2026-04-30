import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import RPCError
from pyrogram.enums import ParseMode

import config
from config import LOGGER_ID as LOG_GROUP_ID
from anikamusic import app 

photo = [
    "https://telegra.ph/file/1949480f01355b4e87d26.jpg",
    "https://telegra.ph/file/3ef2cc0ad2bc548bafb30.jpg",
    "https://telegra.ph/file/a7d663cd2de689b811729.jpg",
    "https://telegra.ph/file/6f19dc23847f5b005e922.jpg",
    "https://telegra.ph/file/2973150dd62fd27a3a6ba.jpg",
]

@app.on_message(filters.new_chat_members, group=2)
async def join_watcher(_, message: Message):    
    chat = message.chat
    
    # Check if the bot itself joined
    for member in message.new_chat_members:
        if member.id == app.id:
            count = await app.get_chat_members_count(chat.id)
            
            # Safe Invite Link Extraction
            try:
                link = await app.export_chat_invite_link(chat.id)
            except RPCError:
                link = "No Permission to fetch link"
                
            username = f"@{chat.username}" if chat.username else "Private Group"
            added_by = message.from_user.mention if message.from_user else "Unknown Admin"

            # 🔥 Premium & Modern 'Added to Group' Message
            msg = (
                f"<emoji id='6334471179801200139'>🎉</emoji> **𝐍ᴇᴡ 𝐆ʀᴏᴜᴘ 𝐀ᴅᴅɪᴛɪᴏɴ** <emoji id='6334471179801200139'>🎉</emoji>\n\n"
                f"<blockquote><emoji id='6334333036473091884'>📌</emoji> **𝐂ʜᴀᴛ 𝐍ᴀᴍᴇ:** {chat.title}\n"
                f"<emoji id='6334648089504122382'>🍂</emoji> **𝐂ʜᴀᴛ 𝐈ᴅ:** `{chat.id}`\n"
                f"<emoji id='6334672948774831861'>🔐</emoji> **𝐔sᴇʀɴᴀᴍᴇ:** {username}\n"
                f"<emoji id='6334696528145286813'>📈</emoji> **𝐌ᴇᴍʙᴇʀs:** {count}</blockquote>\n\n"
                f"<blockquote><emoji id='6334789677396002338'>👤</emoji> **𝐀ᴅᴅᴇᴅ 𝐁ʏ:** {added_by}</blockquote>"
            )
            
            # Adding Button if Link is available
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("sᴇᴇ ɢʀᴏᴜᴘ 👀", url=link)]
            ]) if link.startswith("http") else None

            await app.send_photo(
                LOG_GROUP_ID, 
                photo=random.choice(photo), 
                caption=msg, 
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )


@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    if (await app.get_me()).id == message.left_chat_member.id:
        remove_by = message.from_user.mention if message.from_user else "Unknown Admin"
        title = message.chat.title
        username = f"@{message.chat.username}" if message.chat.username else "Private Group"
        chat_id = message.chat.id
        
        # 🔥 Premium & Modern 'Left Group' Message
        left_msg = (
            f"<emoji id='6334598469746952256'>💔</emoji> **𝐁ᴏᴛ 𝐑ᴇᴍᴏᴠᴇᴅ 𝐅ʀᴏᴍ 𝐆ʀᴏᴜᴘ** <emoji id='6334598469746952256'>💔</emoji>\n\n"
            f"<blockquote><emoji id='6334333036473091884'>📌</emoji> **𝐂ʜᴀᴛ 𝐍ᴀᴍᴇ:** {title}\n"
            f"<emoji id='6334648089504122382'>🍂</emoji> **𝐂ʜᴀᴛ 𝐈ᴅ:** `{chat_id}`\n"
            f"<emoji id='6334672948774831861'>🔐</emoji> **𝐔sᴇʀɴᴀᴍᴇ:** {username}</blockquote>\n\n"
            f"<blockquote><emoji id='6334381440754517833'>👤</emoji> **𝐑ᴇᴍᴏᴠᴇᴅ 𝐁ʏ:** {remove_by}</blockquote>"
        )
        
        await app.send_photo(
            LOG_GROUP_ID, 
            photo=random.choice(photo), 
            caption=left_msg,
            parse_mode=ParseMode.HTML
        )
        

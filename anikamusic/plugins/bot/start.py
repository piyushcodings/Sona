import os
import time
import random
import asyncio
import traceback
import aiohttp 
import json
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.types import CallbackQuery
from youtubesearchpython.__future__ import VideosSearch

import config
from anikamusic import app
from anikamusic.misc import _boot_
from anikamusic.plugins.sudo.sudoers import sudoers_list
from anikamusic.utils.database import get_served_chats, get_served_users, get_sudoers
from anikamusic.utils import bot_sys_stats
from anikamusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from anikamusic.utils.decorators.language import LanguageStart
from anikamusic.utils.formatters import get_readable_time
from anikamusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string
from anikamusic.misc import mongodb

# --- RPG DATABASE ---
game_db = mongodb["wordgame_leaderboard"]

YUMI_PICS = [
    "https://files.catbox.moe/eje8y8.jpeg",
    "https://files.catbox.moe/ey2jzp.jpeg",
    "https://files.catbox.moe/ah5y0f.jpeg",
    "https://files.catbox.moe/we4yju.jpeg",
]

PROMO =  "───────────────────────\n<emoji id='5999100917645841519'>💀</emoji> <b>ᴘᴧɪᴅ ᴘʀσϻσᴛɪση ᴧᴠᴧɪʟᴧʙʟє</b> <emoji id='5999100917645841519'>💀</emoji>\n───────────────────────\n<blockquote><emoji id='6080189526532167993'>😉</emoji> ᴄʜᴧᴛᴛɪηɢ ɢʀσυᴘ's\n<emoji id='5413546177683539369'>😈</emoji> ᴄσʟσʀ ᴛʀᴧᴅɪηɢ ɢᴧϻє's\n<emoji id='6080176744709495278'>🐾</emoji> ᴄʜᴧηηєʟ's | ɢʀσυᴘ's .....\n<emoji id='5415586682286128590'>🔫</emoji> ʙєᴛᴛɪηɢ ᴧᴅs σʀ ᴧηʏᴛʜɪηɢ</blockquote>\n\n───────────────────────\n<emoji id='6080202089311507876'>😎</emoji> <b>ᴘʟᴧηꜱ -</b>\n<blockquote>||<emoji id='5413415116756500503'>☠️</emoji> ᴅᴧɪʟʏ\n<emoji id='5413415116756500503'>☠️</emoji> ᴡєєᴋʟʏ\n<emoji id='5413415116756500503'>☠️</emoji> ϻσηᴛʜʟʏ||</blockquote>\n───────────────────────\n<emoji id='6001132493011425597'>💖</emoji> <b>ᴄσηᴛᴧᴄᴛ -</b> <a href='https://t.me/hehe_stalker'>愛 | 𝗦𝗧么𝗟𝗞𝚵𝗥</a>\n───────────────────────"

GREET = ["💞", "🥂", "🔍", "🧪", "🥂", "⚡️", "🔥"]

# 🔥 SAFETY HELPER
def get_raw_markup(markup):
    if hasattr(markup, 'inline_keyboard'):
        raw_kb = []
        for row in markup.inline_keyboard:
            raw_row = []
            for btn in row:
                raw_btn = {"text": btn.text}
                if btn.callback_data: raw_btn["callback_data"] = btn.callback_data
                if btn.url: raw_btn["url"] = btn.url
                raw_row.append(raw_btn)
            raw_kb.append(raw_row)
        return raw_kb
    return markup

# 🔥 INJECT PREMIUM BUTTONS
async def inject_premium_markup(chat_id, message_id, markup):
    try:
        markup = get_raw_markup(markup)
        token = getattr(config, "BOT_TOKEN", getattr(app, "bot_token", None))
        url = f"https://api.telegram.org/bot{token}/editMessageReplyMarkup"
        payload = {"chat_id": chat_id, "message_id": message_id, "reply_markup": {"inline_keyboard": markup}}
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=payload)
    except Exception as e:
        pass

# 🔥 THE MAGIC START FUNCTION
async def send_magic_start(chat_id, photo_url, caption, markup, reply_to_id=None):
    markup = get_raw_markup(markup)
    try:
        token = getattr(config, "BOT_TOKEN", getattr(app, "bot_token", None))
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        
        payload = {
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML",
            "has_spoiler": True,  
            "message_effect_id": "5159385139981059251", # ❤️ Hearts Animation
            "reply_markup": {"inline_keyboard": markup}
        }
        if reply_to_id:
            payload["reply_to_message_id"] = reply_to_id
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                res = await resp.json()
                
                if not res.get("ok"):
                    run = await app.send_photo(chat_id, photo=photo_url, caption=caption, has_spoiler=True) 
                    await inject_premium_markup(chat_id, run.id, markup)
                    
    except Exception as e:
        run = await app.send_photo(chat_id, photo=photo_url, caption=caption, has_spoiler=True)
        await inject_premium_markup(chat_id, run.id, markup)


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    
    try:
        await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji="🥰")
    except: pass
        
    try:
        stk = await message.reply_sticker("CAACAgUAAxkBAAFGelBp0ipffTacP6bK3ik2BabuZJohkwACoh0AAsI8kFYAARHuC8AH2Jw7BA")
        await asyncio.sleep(2) 
        await stk.delete()     
    except: pass

    loading_1 = await message.reply_text(random.choice(GREET))
    await add_served_user(message.from_user.id)
    
    await asyncio.sleep(0.4)
    await loading_1.edit_text("<emoji id='5413546177683539369'>😈</emoji> <b>ᴅɪηɢ ᴅᴏηɢ.</b>")
    await asyncio.sleep(0.4)
    await loading_1.edit_text("<emoji id='5413546177683539369'>😈</emoji> <b>ᴅɪηɢ ᴅᴏηɢ..</b>")
    await asyncio.sleep(0.4)
    await loading_1.edit_text("<emoji id='6080202089311507876'>😎</emoji> <b>sᴛᴧʀᴛɪηɢ...</b>")
    await asyncio.sleep(0.4)
    await loading_1.edit_text("<emoji id='6001132493011425597'>💖</emoji> <b>ʜєʏ ʙᴧʙʏ!</b>")
    await asyncio.sleep(0.4)
    await loading_1.edit_text("<emoji id='5413840936994097463'>🌺</emoji> <b>𝐀ɴɪᴋᴀ ꭙ ϻᴜsɪᴄ ♪\nsᴛᴧʀᴛed!</b>")
    await asyncio.sleep(0.5)
    await loading_1.delete()
    
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        
        # 🔥 CLAIMX REWARD HANDLER (DM ECO LOGIC)
        if name == "claimx":
            user_id = message.from_user.id
            user_data = await game_db.find_one({"user_id": user_id})
            
            current_time = time.time()
            last_daily = user_data.get("last_daily", 0) if user_data else 0
            
            if current_time - last_daily < 86400:
                remaining = int(86400 - (current_time - last_daily))
                hours = remaining // 3600
                mins = (remaining % 3600) // 60
                claim_text = (
                    f"⏳ **Dᴀɪʟʏ Aʟʀᴇᴀᴅʏ Cʟᴀɪᴍᴇᴅ!**\n\n"
                    f"You already claimed your daily reward! Come back in **{hours}h {mins}m**.\n\n"
                    f"*(You are ready to attack in groups!)*"
                )
            else:
                await game_db.update_one(
                    {"user_id": user_id}, 
                    {"$inc": {"points": 1000}, "$set": {"last_daily": current_time, "name": message.from_user.first_name}}, 
                    upsert=True
                )
                claim_text = (
                    "🎁 **Pʀᴏғɪʟᴇ Vᴇʀɪғɪᴇᴅ & Rᴇᴡᴀʀᴅ Cʟᴀɪᴍᴇᴅ!**\n\n"
                    "<emoji id='6334471179801200139'>🎉</emoji> You have successfully claimed your daily **$1000** bonus!\n\n"
                    "<emoji id='6071252777625981483'>🚀</emoji> **Go back to the group and use `/kill` or `/rob` to dominate!**"
                )
                
            await client.send_message(message.chat.id, claim_text)
            
            # Show normal start panel after claim status
            out = private_panel(_)
            UP, CPU, RAM, DISK = await bot_sys_stats()
            served_chats, served_users = len(await get_served_chats()), len(await get_served_users())
            caption_text = _["start_2"].format(message.from_user.mention, app.mention, UP, DISK, CPU, RAM, served_users, served_chats)
            return await send_magic_start(message.chat.id, random.choice(YUMI_PICS), caption_text, out)

        # --- NORMAL CLAIM REWARD ---
        elif name.startswith("claim"):
            claim_text = "🎉 **Welcome to the DM!**\n\n<emoji id='6334471179801200139'>🎉</emoji> You've successfully connected. Your mini-game profile is active and your points are safe!"
            await client.send_message(message.chat.id, claim_text)
            
            out = private_panel(_)
            UP, CPU, RAM, DISK = await bot_sys_stats()
            served_chats, served_users = len(await get_served_chats()), len(await get_served_users())
            caption_text = _["start_2"].format(message.from_user.mention, app.mention, UP, DISK, CPU, RAM, served_users, served_chats)
            return await send_magic_start(message.chat.id, random.choice(YUMI_PICS), caption_text, out)

        # --- HELP COMMAND ---
        if name[0:4] == "help":
            keyboard = help_pannel(_, True) 
            return await send_magic_start(
                chat_id=message.chat.id, 
                photo_url=random.choice(YUMI_PICS), 
                caption=_["help_1"].format(config.SUPPORT_CHAT), 
                markup=keyboard
            )
            
        # --- SUDO LIST ---
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"<blockquote><emoji id='6080176744709495278'>🐾</emoji> {message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.</blockquote>",
                )
            return
            
        # --- INFO COMMAND ---
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title, duration, views = result["title"], result["duration"], result["viewCount"]["short"]
                channellink, channel = result["channel"]["link"], result["channel"]["name"]
                link, published = result["link"], result["publishedTime"]
                
            searched_text = _["start_6"].format(title, duration, views, published, channellink, channel, app.mention)
            key = [[
                {"text": _["S_B_8"], "url": link, "style": "primary", "icon_custom_emoji_id": "6080202089311507876"},
                {"text": _["S_B_9"], "url": config.SUPPORT_CHAT, "style": "danger", "icon_custom_emoji_id": "5999100917645841519"},
            ]]
            await m.delete()
            
            safe_thumbnail = "https://files.catbox.moe/i3w4v7.jpeg"
            return await send_magic_start(message.chat.id, safe_thumbnail, searched_text, key)

    else:
        # --- NORMAL START ---
        out = private_panel(_)
        served_chats, served_users = len(await get_served_chats()), len(await get_served_users())
        UP, CPU, RAM, DISK = await bot_sys_stats()
        
        caption_text = _["start_2"].format(message.from_user.mention, app.mention, UP, DISK, CPU, RAM, served_users, served_chats)
        
        await send_magic_start(message.chat.id, random.choice(YUMI_PICS), caption_text, out)
        
        if await is_on_off(2):
            return await app.send_message(
                chat_id=config.LOGGER_ID,
                text=f"<emoji id='6080176744709495278'>🐾</emoji> {message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n<emoji id='5413415116756500503'>☠️</emoji> <b>ᴜsᴇʀ ɪᴅ ➠</b> <code>{message.from_user.id}</code>",
            )

@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    try:
        await client.send_reaction(chat_id=message.chat.id, message_id=message.id, emoji="❤️")
    except: pass
    
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    caption = _["start_1"].format(app.mention, get_readable_time(uptime))
    
    await send_magic_start(message.chat.id, random.choice(YUMI_PICS), caption, out, reply_to_id=message.id)

@app.on_message(filters.command("promo") & filters.private)
async def about_command(client: Client, message: Message):
    await message.reply_photo(
        random.choice(YUMI_PICS),
        caption=PROMO,
        has_spoiler=True
    )

@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            if await is_banned_user(member.id):
                try: await message.chat.ban_member(member.id)
                except: pass
            
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(_["start_5"].format(app.mention, f"https://t.me/{app.username}?start=sudolist", config.SUPPORT_CHAT))
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                bot_welcome = f"<emoji id='6080202089311507876'>😎</emoji> <b>𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝖳𝗈 {message.chat.title}</b>\n<emoji id='6001132493011425597'>💖</emoji> 𝖳𝗁𝖺𝗇𝗄𝗌 𝖿𝗈𝗋 𝖺𝖽𝖽𝗂𝗇𝗀 𝗆𝖾, 𝖨 𝖺𝗆 𝗋𝖾𝖺𝖽𝗒 𝗍𝗈 𝗉𝗅𝖺𝗒!"
                
                run = await message.reply_text(text=bot_welcome)
                await inject_premium_markup(message.chat.id, run.id, out)
                
                await add_served_chat(message.chat.id)
                
                async def delete_bot_msg():
                    await asyncio.sleep(10)
                    try: await run.delete()
                    except: pass
                asyncio.create_task(delete_bot_msg())
                
                await message.stop_propagation()
            else:
                user_welcome = f"<emoji id='5413840936994097463'>🌺</emoji> <b>𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝖳𝗈 {message.chat.title}, {member.mention}!</b>"
                run = await message.reply_text(text=user_welcome)
                
                async def delete_user_msg():
                    await asyncio.sleep(10)
                    try: await run.delete()
                    except: pass
                asyncio.create_task(delete_user_msg())

        except Exception as ex:
            pass
        

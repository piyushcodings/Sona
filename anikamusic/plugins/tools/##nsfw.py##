import os
import random
import asyncio
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

# 🔥 NudeNet Offline AI Library
from nudenet import NudeDetector

from anikamusic import app
from config import BANNED_USERS

# ─────────────────────────────
# 🔥 INITIALIZE OFFLINE AI ENGINE
# ─────────────────────────────
print("Loading NudeNet AI Model into RAM... Please wait.")
detector = NudeDetector() # Ek hi baar load hoga RAM mein
print("NudeNet AI Model Loaded Successfully! 🚀")

# ─────────────────────────────
# 🔥 STATE, EMOJIS & DATABASE CACHE
# ─────────────────────────────
chat_nsfw_state = {}
BANNED_STICKERS = set() # Single blocked stickers
BANNED_PACKS = set()    # Full blocked packs
SAFE_STICKERS = set()   # Safe stickers cache

PREMIUM_EMOJIS = [
    '🎀', '✨', '❌', '⚠️', '🛡️', '🤖', '💀', '👀'
]

# ─────────────────────────────
# 🧹 CLEAR SAFE CACHE COMMAND
# ─────────────────────────────
@app.on_message(filters.command(["clearstic"]) & ~BANNED_USERS)
async def clear_safe_cache(client, message: Message):
    SAFE_STICKERS.clear()
    emo = random.choice(PREMIUM_EMOJIS)
    await message.reply(f"<blockquote>✅ **Sᴀғᴇ Sᴛɪᴄᴋᴇʀs Cᴀᴄʜᴇ ᴄʟᴇᴀʀᴇᴅ!**\nNᴇxᴛ ᴛɪᴍᴇ ᴀʟʟ sᴛɪᴄᴋᴇʀs ᴡɪʟʟ ʙᴇ ʀᴇ-sᴄᴀɴɴᴇᴅ. 🧹{emo}</blockquote>", parse_mode=ParseMode.HTML)

# ─────────────────────────────
# 🛠️ MANUAL BAN COMMAND
# ─────────────────────────────
@app.on_message(filters.command("bansticker") & filters.reply & filters.group)
async def ban_manual_sticker(client, message: Message):
    if not message.reply_to_message.sticker:
        return await message.reply("<blockquote>⚠️ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ ᴛᴏ ʙᴀɴ ɪᴛ!</blockquote>", parse_mode=ParseMode.HTML)
    
    sticker = message.reply_to_message.sticker
    sticker_id = sticker.file_unique_id
    pack_name = sticker.set_name
    
    if len(message.command) > 1 and message.command[1].lower() == "pack" and pack_name:
        BANNED_PACKS.add(pack_name)
        text = f"<blockquote>✅ ғᴜʟʟ sᴛɪᴄᴋᴇʀ ᴘᴀᴄᴋ ᴀᴅᴅᴇᴅ ᴛᴏ ʙʟᴀᴄᴋʟɪsᴛ! {random.choice(PREMIUM_EMOJIS)}</blockquote>"
    else:
        BANNED_STICKERS.add(sticker_id)
        if sticker_id in SAFE_STICKERS:
            SAFE_STICKERS.remove(sticker_id)
        text = f"<blockquote>✅ sɪɴɢʟᴇ sᴛɪᴄᴋᴇʀ ᴀᴅᴅᴇᴅ ᴛᴏ ʙʟᴀᴄᴋʟɪsᴛ! {random.choice(PREMIUM_EMOJIS)}</blockquote>"
    
    try:
        await message.reply_to_message.delete()
    except: pass
    
    msg = await message.reply(text, parse_mode=ParseMode.HTML)
    await asyncio.sleep(15)
    try:
        await msg.delete()
    except: pass

# ─────────────────────────────
# 🛠️ ON/OFF COMMAND
# ─────────────────────────────
@app.on_message(filters.command(["nsfw", "vision"]) & filters.group & ~BANNED_USERS)
async def toggle_nsfw(client, message: Message):
    chat_id = message.chat.id
    emo = random.choice(PREMIUM_EMOJIS)
    
    if len(message.command) < 2:
        state = chat_nsfw_state.get(chat_id, True)
        status = "ᴏɴ ✅" if state else "ᴏғғ ❌"
        msg_text = f"<blockquote>ᴠɪsɪᴏɴ sᴄᴀɴɴᴇʀ ɪs ᴄᴜʀʀᴇɴᴛʟʏ **{status}**.\nᴛᴏ ᴄʜᴀɴɢᴇ, ᴛʏᴘᴇ: `/nsfw on` ᴏʀ `/nsfw off` {emo}</blockquote>"
        return await message.reply(msg_text, parse_mode=ParseMode.HTML)
    
    cmd = message.command[1].lower()
    if cmd == "on":
        chat_nsfw_state[chat_id] = True
        msg_text = f"<blockquote>✅ ᴠɪsɪᴏɴ sᴄᴀɴɴᴇʀ ɪs ɴᴏᴡ ᴏɴ. {emo}</blockquote>"
    elif cmd == "off":
        chat_nsfw_state[chat_id] = False
        msg_text = f"<blockquote>❌ ᴠɪsɪᴏɴ sᴄᴀɴɴᴇʀ ɪs ɴᴏᴡ ᴏғғ. {emo}</blockquote>"
        
    msg = await message.reply(msg_text, parse_mode=ParseMode.HTML)
    await asyncio.sleep(15)
    try:
        await msg.delete()
    except: pass

# ─────────────────────────────
# 👁️ OFFLINE NUDENET ENGINE (Non-Blocking)
# ─────────────────────────────
async def analyze_media_offline(image_path):
    try:
        # 1. Run detection in a separate thread so music doesn't lag
        results = await asyncio.to_thread(detector.detect, image_path)
        
        # 2. Define highly explicit NSFW classes
        explicit_classes = [
            "EXPOSED_ANUS", "EXPOSED_BUTTOCKS", "EXPOSED_BREAST_F", 
            "EXPOSED_GENITALIA_M", "EXPOSED_GENITALIA_F"
        ]
        
        # 3. Find the highest probability of an explicit part
        max_score = 0.0
        for item in results:
            if item.get("class") in explicit_classes:
                score = item.get("score", 0.0)
                if score > max_score:
                    max_score = score
                    
        # 4. Convert to 0-100 percentage
        return int(max_score * 100)
        
    except Exception as e:
        print(f"Offline AI Crash: {e}")
        return -1

# ─────────────────────────────
# 🧪 TEST STICKER COMMAND
# ─────────────────────────────
@app.on_message(filters.command("teststic") & filters.reply)
async def test_sticker(client, message: Message):
    if not message.reply_to_message.sticker and not message.reply_to_message.photo:
        return await message.reply("<blockquote>⚠️ ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ sᴛɪᴄᴋᴇʀ ᴏʀ ᴘʜᴏᴛᴏ ᴛᴏ ᴛᴇsᴛ!</blockquote>", parse_mode=ParseMode.HTML)
    
    wait_msg = await message.reply("<blockquote>⏳ sᴄᴀɴɴɪɴɢ ɪᴍᴀɢᴇ ᴠɪᴀ ᴏғғʟɪɴᴇ ᴀɪ...</blockquote>", parse_mode=ParseMode.HTML)
    
    dl_path = None
    target_msg = message.reply_to_message
    
    try:
        if target_msg.sticker and (target_msg.sticker.is_animated or target_msg.sticker.is_video):
            if target_msg.sticker.thumbs:
                thumb_id = target_msg.sticker.thumbs[0].file_id
                dl_path = await client.download_media(thumb_id)
        else:
            dl_path = await target_msg.download()
            
        if not dl_path:
            return await wait_msg.edit("<blockquote>❌ FAILED TO DOWNLOAD MEDIA.</blockquote>", parse_mode=ParseMode.HTML)

        score = await analyze_media_offline(dl_path)
        
        if os.path.exists(dl_path):
            os.remove(dl_path)
            
        if score == -1:
            return await wait_msg.edit("<blockquote>❌ OFFLINE AI ERROR.</blockquote>", parse_mode=ParseMode.HTML)
            
        action = "🟢 SAFE (Added to Safe DB)"
        if score >= 80:
            action = "🔴 HIGH NSFW (Banning Full Pack)"
            if target_msg.sticker and target_msg.sticker.set_name:
                BANNED_PACKS.add(target_msg.sticker.set_name)
        elif score >= 50:
            action = "🟠 MED NSFW (Banning Single Sticker)"
            if target_msg.sticker:
                BANNED_STICKERS.add(target_msg.sticker.file_unique_id)
        else:
            if target_msg.sticker:
                SAFE_STICKERS.add(target_msg.sticker.file_unique_id)
            
        result_text = f"<blockquote>👁️ **ᴠɪsɪᴏɴ ᴛᴇsᴛ ʀᴇsᴜʟᴛs:**\n\n📊 **NSFW sᴄᴏʀᴇ:** {score}%\n🎯 **ᴀᴄᴛɪᴏɴ:** {action}</blockquote>"
        await wait_msg.edit(result_text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await wait_msg.edit(f"<blockquote>❌ Error: {e}</blockquote>", parse_mode=ParseMode.HTML)

# ─────────────────────────────
# 🚨 MAIN SCANNER (SILENT, SMART PACK BAN & CACHING)
# ─────────────────────────────
@app.on_message((filters.photo | filters.sticker) & filters.group & ~BANNED_USERS)
async def nsfw_scanner(client, message: Message):
    chat_id = message.chat.id
    if not chat_nsfw_state.get(chat_id, True):
        return

    # 1. SMART DATABASE CHECK (Fastest)
    if message.sticker:
        sticker_id = message.sticker.file_unique_id
        pack_name = message.sticker.set_name
        
        if sticker_id in BANNED_STICKERS or (pack_name and pack_name in BANNED_PACKS):
            try:
                await message.delete()
            except Exception: pass
            return
            
        if sticker_id in SAFE_STICKERS:
            return

    # 2. DOWNLOAD & SCAN
    dl_path = None
    try:
        if message.sticker and (message.sticker.is_animated or message.sticker.is_video):
            if message.sticker.thumbs:
                dl_path = await client.download_media(message.sticker.thumbs[0].file_id)
            else:
                return 
        else:
            dl_path = await message.download()
        
        if dl_path:
            score = await analyze_media_offline(dl_path)
            
            if os.path.exists(dl_path):
                os.remove(dl_path)
                
            if score >= 50:
                if message.sticker:
                    if score >= 80 and message.sticker.set_name:
                        BANNED_PACKS.add(message.sticker.set_name)
                    else:
                        BANNED_STICKERS.add(message.sticker.file_unique_id)
                        
                try:
                    await message.delete()
                except Exception as e:
                    if "MESSAGE_DELETE_FORBIDDEN" in str(e) or "chat_admin_required" in str(e).lower():
                         perm_msg = await client.send_message(chat_id, f"<blockquote>⚠️ ɪ ɴᴇᴇᴅ 'ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇs' ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ʀᴇᴍᴏᴠᴇ ɴsғᴡ ᴄᴏɴᴛᴇɴᴛ! 🛡️</blockquote>", parse_mode=ParseMode.HTML)
                         await asyncio.sleep(10)
                         try: await perm_msg.delete()
                         except: pass
            
            elif score != -1:
                if message.sticker:
                    SAFE_STICKERS.add(message.sticker.file_unique_id)
                         
    except Exception as e:
        print(f"Scanner crash: {e}")
        if dl_path and os.path.exists(dl_path):
            os.remove(dl_path)
                                   

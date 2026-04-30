import asyncio
from pyrogram import filters
from pyrogram.types import Message, ChatMemberUpdated

# anikamusic bot instance and MongoDB
from anikamusic import app 
from anikamusic.misc import mongodb

# ─────────────────────────────
# MONGODB DATABASE SETUP
# ─────────────────────────────
namesdb = mongodb.name_tracker

async def get_user_history(user_id: int):
    user = await namesdb.find_one({"_id": user_id})
    return user if user else None

async def update_user_history(user_id: int, names: list, usernames: list):
    await namesdb.update_one(
        {"_id": user_id},
        {"$set": {"names": names, "usernames": usernames}},
        upsert=True
    )

# ─────────────────────────────
# AESTHETIC SMALL CAPS TEXT CONVERTER
# ─────────────────────────────
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

# ─────────────────────────────
# HELPER FUNCTION
# ─────────────────────────────
def get_full_name(user):
    if not user:
        return "Unknown"
    name = user.first_name or ""
    if user.last_name:
        name += f" {user.last_name}"
    return name.strip()

# ─────────────────────────────
# TRACKER LOGIC (MONGODB)
# ─────────────────────────────
async def check_user_profile(client, chat_id, user):
    if not user or user.is_bot:
        return

    user_id = user.id
    current_name = get_full_name(user)
    current_username = f"@{user.username}" if user.username else "None"

    # Fetch history from MongoDB
    user_data = await get_user_history(user_id)

    # If user is completely new to the database, add them silently
    if not user_data:
        await update_user_history(user_id, [current_name], [current_username])
        return

    # Fetch the LAST known name and username from history
    names_list = user_data.get("names", [])
    usernames_list = user_data.get("usernames", [])
    
    old_name = names_list[-1] if names_list else "Unknown"
    old_username = usernames_list[-1] if usernames_list else "None"

    changes = []
    updated = False
    
    # Check if Name changed
    if old_name != current_name:
        names_list.append(current_name)
        changes.append(f"{smallcaps('name from')} **{old_name}** {smallcaps('to')} **{current_name}**")
        updated = True
    
    # Check if Username changed
    if old_username != current_username:
        usernames_list.append(current_username)
        changes.append(f"{smallcaps('username from')} **{old_username}** {smallcaps('to')} **{current_username}**")
        updated = True

    # If any changes found, update MongoDB and alert the group
    if updated:
        # Keep only the last 15 records so database doesn't get bloated
        await update_user_history(user_id, names_list[-15:], usernames_list[-15:])
        alert_text = f"👀 **{smallcaps('Profile Update Detected')}** 👀\n\n{user.mention} {smallcaps('has changed their')} " + f" {smallcaps('and')} ".join(changes) + "!"
        
        try:
            await client.send_message(chat_id, alert_text)
        except Exception:
            pass 

# ─────────────────────────────
# EVENT HANDLERS (Negative Groups for Highest Priority)
# ─────────────────────────────

# 1. Listen to all normal messages in the group BEFORE other plugins block them
@app.on_message(filters.group & ~filters.bot, group=-10)
async def on_user_message(client, message: Message):
    if message.from_user:
        await check_user_profile(client, message.chat.id, message.from_user)

# 2. Listen to Chat Member Updates
@app.on_chat_member_updated(filters.group, group=-11)
async def on_user_join_or_update(client, update: ChatMemberUpdated):
    if update.new_chat_member and update.new_chat_member.user:
        await check_user_profile(client, update.chat.id, update.new_chat_member.user)

# ─────────────────────────────
# COMMANDS: /history & /testname
# ─────────────────────────────

@app.on_message(filters.command(["history"]))
async def name_history(client, message: Message):
    try:
        await message.delete()
    except:
        pass
    
    target_user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    user_id = target_user.id
    
    user_data = await get_user_history(user_id)
    
    if not user_data:
        return await message.reply_text(smallcaps("i don't have any history for this user yet. they need to send a message first."))
        
    names = user_data.get("names", [])
    usernames = user_data.get("usernames", [])
    
    text = f"📜 **{smallcaps('History for')} {target_user.mention}**\n\n"
    
    text += f"👤 **{smallcaps('Names')}**:\n"
    for i, n in enumerate(names, 1):
        text += f"{i}. {n}\n"
        
    text += f"\n🌐 **{smallcaps('Usernames')}**:\n"
    for i, u in enumerate(usernames, 1):
        text += f"{i}. {u}\n"
        
    await message.reply_text(text)

@app.on_message(filters.command(["testname"]))
async def test_name(client, message: Message):
    try:
        await message.delete()
    except:
        pass
    
    user_id = message.from_user.id
    user_data = await get_user_history(user_id)
    
    if not user_data:
        await check_user_profile(client, message.chat.id, message.from_user)
        return await message.reply_text(smallcaps("you were not in the database. i just added you! change your name now and send a message to test."))
        
    names_list = user_data.get("names", [])
    usernames_list = user_data.get("usernames", [])
    
    current_saved_name = names_list[-1] if names_list else "Unknown"
    current_saved_username = usernames_list[-1] if usernames_list else "None"
    
    text = f"🛠 **{smallcaps('Test Tracker Data')}**\n\n"
    text += f"📝 {smallcaps('Saved Name in Bot')}: **{current_saved_name}**\n"
    text += f"🔗 {smallcaps('Saved Username in Bot')}: **{current_saved_username}**\n\n"
    text += f"👤 {smallcaps('Your Current Name')}: **{get_full_name(message.from_user)}**\n\n"
    text += smallcaps("if you change your name in telegram now and send a message, i will detect the change!")
    
    await message.reply_text(text)
    

import os
import time
import math
import aiohttp
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ParseMode

import config
from anikamusic import app
from anikamusic.misc import mongodb

# --- DATABASE COLLECTIONS ---
game_db = mongodb["wordgame_leaderboard"]
wallet_db = mongodb["group_wallets"]

# --- SMM CONFIG ---
SMM_API_KEY = os.getenv("SMM_API_KEY", "")
SMM_API_URL = "https://fathersmm.com/api/v2"
SMM_SERVICE_ID = os.getenv("SMM_SERVICE_ID", "1") # Default 1, change from .env

TARGET_POINTS = 5000
REWARD_MEMBERS = 500

# --- AESTHETIC SMALL CAPS TEXT CONVERTER ---
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

# --- PREMIUM HACK INJECTION ---
async def inject_premium_markup(chat_id, message_id, markup):
    try:
        token = getattr(config, "BOT_TOKEN", getattr(app, "bot_token", None))
        url = f"https://api.telegram.org/bot{token}/editMessageReplyMarkup"
        payload = {"chat_id": chat_id, "message_id": message_id, "reply_markup": {"inline_keyboard": markup}}
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=payload)
    except Exception as e:
        print(f"❌ Markup Injection Error: {e}")

# --- HELPER FUNCTIONS ---
async def get_wallet(chat_id, title="Unknown Group"):
    wallet = await wallet_db.find_one({"chat_id": chat_id})
    if not wallet:
        wallet = {"chat_id": chat_id, "title": title, "points": 0, "history": []}
        await wallet_db.insert_one(wallet)
    # Update title to keep it fresh
    if wallet.get("title") != title:
        await wallet_db.update_one({"chat_id": chat_id}, {"$set": {"title": title}})
        wallet["title"] = title
    return wallet

async def add_transaction(chat_id, log_msg):
    wallet = await get_wallet(chat_id)
    history = wallet.get("history", [])
    history.append(log_msg)
    if len(history) > 6:
        history = history[-6:]
    await wallet_db.update_one({"chat_id": chat_id}, {"$set": {"history": history}})

async def trigger_smm_reward(client, message: Message, chat_id):
    chat = await client.get_chat(chat_id)
    
    me = await chat.get_member(client.me.id)
    if me.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        await client.send_message(chat_id, f"<emoji id='6073371665381724173'>❌</emoji> {smallcaps('Reward unlocked! But I am not an admin in this group, so I cannot add members. Make me an admin and try again!')}")
        return False

    link = f"https://t.me/{chat.username}" if chat.username else chat.invite_link
    if not link:
        link = await chat.export_invite_link()

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "key": SMM_API_KEY,
                "action": "add",
                "service": SMM_SERVICE_ID,
                "link": link,
                "quantity": REWARD_MEMBERS
            }
            async with session.post(SMM_API_URL, data=payload) as resp:
                result = await resp.json()
                if "error" in result:
                    await client.send_message(chat_id, f"<emoji id='6073371665381724173'>⚠️</emoji> {smallcaps('API Error:')} {result['error']}")
                    return False
    except Exception as e:
        print(f"SMM API Error: {e}")
        await client.send_message(chat_id, f"<emoji id='6073371665381724173'>⚠️</emoji> {smallcaps('Unable to connect to the SMM panel.')}")
        return False

    total_members = chat.members_count
    success_text = (
        f"<emoji id='6071046056555058251'>🎉</emoji> **{smallcaps('CONGRATULATIONS')} {smallcaps(chat.title)}!** <emoji id='6071046056555058251'>🎉</emoji>\n\n"
        f"<emoji id='6073117703965511893'>🏆</emoji> {smallcaps('The group has reached the')} {TARGET_POINTS} {smallcaps('points target!')}\n"
        f"<emoji id='6071252777625981483'>🚀</emoji> **{REWARD_MEMBERS} {smallcaps('New Members')}** {smallcaps('are being added to the group right now!')}\n\n"
        f"<emoji id='6073321555998282076'>📈</emoji> {smallcaps('Total Members now going up from:')} {total_members}\n\n"
        f"{smallcaps('Keep playing and growing!')} <emoji id='6073203332728491804'>🔥</emoji>"
    )
    
    markup = [[{"text": f"🤖 {smallcaps('Add Bot to Your GC')}", "url": f"https://t.me/{app.username}?startgroup=true", "style": "success", "icon_custom_emoji_id": "6073423432622544061"}]]
    
    run = await client.send_message(chat_id, success_text)
    await inject_premium_markup(chat_id, run.id, markup)
    try:
        await run.pin()
    except: pass
    
    await wallet_db.update_one({"chat_id": chat_id}, {"$inc": {"points": -TARGET_POINTS}})
    await add_transaction(chat_id, f"<emoji id='6073165416757203109'>🔄</emoji> {smallcaps('Wallet Reset after SMM Reward!')}")
    return True

# --- COMMANDS ---

@app.on_message(filters.command(["wallet", "gcwallet", "gcbal"], prefixes=["/", ".", "!"]) & filters.group)
async def check_wallet(client, message: Message):
    chat_id = message.chat.id
    try: await message.delete()
    except: pass
    
    wallet = await get_wallet(chat_id, message.chat.title)
    
    text = f"<emoji id='6073552504979722691'>🏦</emoji> **{smallcaps(message.chat.title)} {smallcaps('Group Wallet')}**\n"
    text += f"<emoji id='6071348606936289251'>🆔</emoji> {smallcaps('Wallet ID:')} `{chat_id}`\n"
    text += f"<emoji id='6073321555998282076'>💰</emoji> {smallcaps('Balance:')} **{wallet['points']} / {TARGET_POINTS}** {smallcaps('points')}\n"
    text += "➖" * 12 + "\n"
    
    if not wallet["history"]:
        text += f"<emoji id='6073117703965511893'>📝</emoji> {smallcaps('No transactions yet.')}"
    else:
        text += f"<emoji id='6071252777625981483'>📜</emoji> **{smallcaps('Last 6 Transactions:')}**\n"
        for log in reversed(wallet["history"]):
            text += f"➥ {log}\n"
            
    await client.send_message(chat_id, text)

@app.on_message(filters.command(["donate"], prefixes=["/", ".", "!"]) & filters.group)
async def donate_points(client, message: Message):
    chat_id = message.chat.id
    try: await message.delete()
    except: pass

    if len(message.command) < 2:
        return await client.send_message(chat_id, smallcaps("How to use: /donate [amount] or .donate [amount]"))
    
    try: amount = int(message.command[1])
    except: return await client.send_message(chat_id, smallcaps("Enter the amount in numbers!"))
    
    if amount <= 0: return await client.send_message(chat_id, smallcaps("Enter a valid amount!"))
        
    user_id = message.from_user.id
    user_data = await game_db.find_one({"user_id": user_id})
    
    if not user_data or user_data.get("points", 0) < amount:
        return await client.send_message(chat_id, f"<emoji id='6073371665381724173'>❌</emoji> {smallcaps('You do not have enough points!')}")
        
    # Ensure wallet is tracked with title
    await get_wallet(chat_id, message.chat.title)
    
    # Calculate 2% fee
    fee = math.ceil(amount * 0.02)
    final_amount = amount - fee
    
    await game_db.update_one({"user_id": user_id}, {"$inc": {"points": -amount}})
    await wallet_db.update_one({"chat_id": chat_id}, {"$inc": {"points": final_amount}}, upsert=True)
    
    log_msg = f"<emoji id='6073423432622544061'>➕</emoji> {smallcaps(message.from_user.first_name)} {smallcaps('donated')} {amount} {smallcaps('pts')} ({smallcaps('-2% fee')})"
    await add_transaction(chat_id, log_msg)
    
    reply_text = (
        f"<emoji id='6071046056555058251'>💖</emoji> **{smallcaps('Thanks for donating!')}**\n"
        f"{message.from_user.mention} {smallcaps('donated')} {amount} {smallcaps('points')}.\n\n"
        f"<emoji id='6073165416757203109'>📉</emoji> {smallcaps('2% Fee:')} {fee}\n"
        f"<emoji id='6073321555998282076'>💰</emoji> {smallcaps('Added to GC:')} {final_amount}"
    )
    
    await client.send_message(chat_id, reply_text)
    
    new_wallet = await get_wallet(chat_id, message.chat.title)
    if new_wallet["points"] >= TARGET_POINTS:
        await trigger_smm_reward(client, message, chat_id)

@app.on_message(filters.command(["gtransfer"], prefixes=["/", ".", "!"]) & filters.group)
async def transfer_to_other_gc(client, message: Message):
    chat_id = message.chat.id
    try: await message.delete()
    except: pass

    if len(message.command) < 3:
        return await client.send_message(chat_id, smallcaps("How to use: /gtransfer [Target_Wallet_ID] [Amount]"))
        
    try: 
        target_chat_id = int(message.command[1])
        amount = int(message.command[2])
    except: return await client.send_message(chat_id, smallcaps("Incorrect format!"))
    
    if amount <= 0: return await client.send_message(chat_id, smallcaps("Enter a valid amount!"))
    
    user_id = message.from_user.id
    user_data = await game_db.find_one({"user_id": user_id})
    
    if not user_data or user_data.get("points", 0) < amount:
        return await client.send_message(chat_id, f"<emoji id='6073371665381724173'>❌</emoji> {smallcaps('You do not have enough points!')}")
        
    fee = math.ceil(amount * 0.03)
    final_amount = amount - fee
    
    await game_db.update_one({"user_id": user_id}, {"$inc": {"points": -amount}})
    
    # Ensure target wallet exists
    await get_wallet(target_chat_id)
    await wallet_db.update_one({"chat_id": target_chat_id}, {"$inc": {"points": final_amount}}, upsert=True)
    
    sender_name = smallcaps(message.from_user.first_name)
    await add_transaction(target_chat_id, f"<emoji id='6073321555998282076'>💸</emoji> {smallcaps('Received')} {final_amount} {smallcaps('pts from')} {sender_name} ({smallcaps('3% tax cut')})")
    
    await client.send_message(chat_id, f"<emoji id='6073423432622544061'>✅</emoji> {smallcaps('Transfer Successful!')}\n\n<emoji id='6073321555998282076'>💸</emoji> {smallcaps('Sent:')} {amount}\n<emoji id='6073165416757203109'>📉</emoji> {smallcaps('3% Tax:')} {fee}\n<emoji id='6073117703965511893'>🎯</emoji> {smallcaps('Target GC received:')} {final_amount}")
    
    target_wallet = await get_wallet(target_chat_id)
    if target_wallet["points"] >= TARGET_POINTS:
        try: await trigger_smm_reward(client, message, target_chat_id)
        except: pass
      
# ==========================================
#        UPDATED BALANCE & PRIVACY COMMANDS
# ==========================================

@app.on_message(filters.command(["bal", "balance", "mybal", "mybalance"], prefixes=["/", ".", "!"]) & filters.group)
async def check_user_balance(client, message: Message):
    chat_id = message.chat.id
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        target_user = message.from_user
        
    try: await message.delete()
    except: pass

    if not target_user:
        return await client.send_message(chat_id, smallcaps("User not found!"))

    is_self = (target_user.id == message.from_user.id)
    user_data = await game_db.find_one({"user_id": target_user.id})
    
    points = user_data.get("points", 0) if user_data else 0
    kills = user_data.get("kills", 0) if user_data else 0
    xp = user_data.get("xp", 0) if user_data else 0
    is_hidden = user_data.get("hidden", False) if user_data else False

    # Privacy Check
    if not is_self and is_hidden:
        return await client.send_message(chat_id, f"<emoji id='6073371665381724173'>❌</emoji> **{smallcaps('Privacy Alert:')}** {smallcaps('This user has hidden their balance from others!')}")

    # Calculate Global Rank
    rank = await game_db.count_documents({"points": {"$gt": points}}) + 1
    
    # Status Logic
    current_time = time.time()
    protected_until = user_data.get("protected_until", 0) if user_data else 0
    dead_until = user_data.get("dead_until", 0) if user_data else 0
    
    if current_time < dead_until:
        status_str = "dead 💀"
    elif current_time < protected_until:
        status_str = "protected 🛡️"
    else:
        status_str = "alive ❤️"

    # UI Formatting
    user_name = smallcaps(target_user.first_name)
    hidden_status = f" (👻 {smallcaps('Hidden')})" if (is_self and is_hidden) else ""

    text = f"👤 Nᴀᴍᴇ: {user_name}{hidden_status}\n"
    text += f"💰 Bᴀʟᴀɴᴄᴇ: ${points}\n"
    text += f"🏆 Gʟᴏʙᴀʟ Rᴀɴᴋ: {rank}\n"
    text += f"❤️ Sᴛᴀᴛᴜꜱ: {status_str}\n"
    text += f"⚔️ Kɪʟʟꜱ: {kills}\n"
    text += f"🐣 Rᴏᴏᴋɪᴇ: {xp}/1000\n"
    
    await client.send_message(chat_id, text)

@app.on_message(filters.command(["hide", "hidebal", "unhide", "unhidebal"], prefixes=["/", ".", "!"]) & filters.group)
async def toggle_privacy(client, message: Message):
    chat_id = message.chat.id
    try: await message.delete()
    except: pass

    user_id = message.from_user.id
    user_data = await game_db.find_one({"user_id": user_id})
    
    if not user_data:
        await game_db.insert_one({"user_id": user_id, "name": message.from_user.first_name, "points": 0, "hidden": False})
        current_status = False
    else:
        current_status = user_data.get("hidden", False)

    command = message.command[0].lower()
    
    if command in ["hide", "hidebal"]:
        new_status = True
        reply_msg = f"<emoji id='6073423432622544061'>✅</emoji> {smallcaps('Done! Your balance is now')} **{smallcaps('HIDDEN')}** {smallcaps('from other users.')} <emoji id='6073165416757203109'>👻</emoji>"
    elif command in ["unhide", "unhidebal"]:
        new_status = False
        reply_msg = f"<emoji id='6073423432622544061'>✅</emoji> {smallcaps('Done! Your balance is now')} **{smallcaps('VISIBLE')}** {smallcaps('to everyone.')} <emoji id='6071252777625981483'>🚀</emoji>"
    
    if current_status == new_status:
        return await client.send_message(chat_id, f"<emoji id='6073117703965511893'>🎯</emoji> {smallcaps('Your balance is already')} {'hidden' if new_status else 'visible'}!")

    await game_db.update_one({"user_id": user_id}, {"$set": {"hidden": new_status}})
    await client.send_message(chat_id, reply_msg)

# ==========================================
#        TOP GROUPS LEADERBOARD
# ==========================================

@app.on_message(filters.command(["topgroups", "gctop"], prefixes=["/", ".", "!"]) & filters.group)
async def top_groups_leaderboard(client, message: Message):
    chat_id = message.chat.id
    try: await message.delete()
    except: pass

    top_wallets = wallet_db.find().sort("points", -1).limit(10)
    
    text = f"<emoji id='6073117703965511893'>🏆</emoji> **{smallcaps('Top 10 Richest Groups')}** <emoji id='6073117703965511893'>🏆</emoji>\n\n"
    count, has_groups = 1, False
    
    async for wallet in top_wallets:
        has_groups = True
        title = smallcaps(wallet.get("title", "Unknown Group"))
        points = wallet.get("points", 0)
        text += f"**{count}.** {title} - `{points}` {smallcaps('points')}\n"
        count += 1
        
    if not has_groups:
        text += smallcaps("No groups have started earning points yet!")
        
    await client.send_message(chat_id, text)

# ==========================================
#        GAME & ECONOMY HELP
# ==========================================

@app.on_message(filters.command(["gamehelp", "helpgame"], prefixes=["/", ".", "!"]) & filters.group)
async def game_economy_help(client, message: Message):
    chat_id = message.chat.id
    try: await message.delete()
    except: pass

    help_text = f"""
<emoji id='6071252777625981483'>🚀</emoji> **{smallcaps('Economy & Mini-Games Help')}** <emoji id='6071252777625981483'>🚀</emoji>

<blockquote><emoji id='6073552504979722691'>🏦</emoji> <b>{smallcaps('Wallet Commands')}</b>
• <code>/wallet</code> - {smallcaps('Check the group balance and transactions')}
• <code>/donate [amount]</code> - {smallcaps('Donate your points to the group')} (2% {smallcaps('fee')})
• <code>/gtransfer [ID] [amount]</code> - {smallcaps('Send points to another group')} (3% {smallcaps('fee')})
• <code>/topgroups</code> - {smallcaps('View the global group leaderboard')}
</blockquote>

<blockquote><emoji id='6071348606936289251'>👤</emoji> <b>{smallcaps('Personal Commands')}</b>
• <code>/bal</code> - {smallcaps('Check your current points balance')}
• <code>/hide</code> - {smallcaps('Hide your balance from others')}
• <code>/unhide</code> - {smallcaps('Make your balance visible again')}
</blockquote>

<emoji id='6071046056555058251'>💖</emoji> *{smallcaps('Reach 5000 points in your group wallet to unlock a massive member reward!')}*
"""
    await client.send_message(chat_id, help_text, parse_mode=ParseMode.HTML)
    

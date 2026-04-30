import os
import time
import math
import random
import asyncio
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus

import config
from anikamusic import app
from anikamusic.misc import mongodb

# --- DATABASE COLLECTIONS ---
game_db = mongodb["wordgame_leaderboard"]
eco_db = mongodb["eco_settings"] 
wallet_db = mongodb["group_wallets"] # Added for group eco ranks

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

# ==========================================
#              GLOBAL & GROUP ECO SETTINGS
# ==========================================

async def is_global_eco_enabled():
    global_settings = await eco_db.find_one({"chat_id": "GLOBAL"})
    if global_settings:
        return global_settings.get("enabled", True)
    return True # By default global eco is ON

async def is_eco_enabled(chat_id):
    if not await is_global_eco_enabled():
        return False
        
    settings = await eco_db.find_one({"chat_id": chat_id})
    if settings:
        return settings.get("enabled", True)
    return True # Default ON for groups

# GLOBAL ECO TOGGLE (BOT OWNER ONLY)
@app.on_message(filters.command(["geco"], prefixes=["/", ".", "!"]) & filters.user(config.OWNER_ID))
async def toggle_global_economy(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("⚠️ Usage: `/geco on` or `/geco off`")
        
    cmd = message.command[1].lower()
    if cmd in ["on", "enable"]:
        await eco_db.update_one({"chat_id": "GLOBAL"}, {"$set": {"enabled": True}}, upsert=True)
        await message.reply_text("🌍 **Global Economy System ENABLED!**")
    elif cmd in ["off", "disable"]:
        await eco_db.update_one({"chat_id": "GLOBAL"}, {"$set": {"enabled": False}}, upsert=True)
        await message.reply_text("⛔️ **Global Economy System DISABLED!** Everyone is halted.")

# GROUP ECO TOGGLE (ADMINS/OWNERS ONLY)
@app.on_message(filters.command(["eco"], prefixes=["/", ".", "!"]) & filters.group)
async def toggle_economy(client, message: Message):
    chat_id = message.chat.id
    me = await client.get_chat_member(chat_id, message.from_user.id)
    
    # Check if user is admin or creator
    if me.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await message.reply_text("⚠️ Only Group Admins or the Owner can toggle the economy!")
        
    if len(message.command) < 2:
        return await message.reply_text("⚠️ Usage: `/eco on` or `/eco off`")
        
    cmd = message.command[1].lower()
    if cmd in ["on", "enable"]:
        await eco_db.update_one({"chat_id": chat_id}, {"$set": {"enabled": True}}, upsert=True)
        await message.reply_text("✅ Economy & RPG features are now **ENABLED** in this group!")
    elif cmd in ["off", "disable"]:
        await eco_db.update_one({"chat_id": chat_id}, {"$set": {"enabled": False}}, upsert=True)
        await message.reply_text("❌ Economy & RPG features are now **DISABLED** in this group!")

# ==========================================
#              AUTO RELIEF FUND (0$ FIX)
# ==========================================

async def auto_replenish_loop():
    """Background task jo har 6 minute mein 0$ walo ko $100 dega"""
    while True:
        await asyncio.sleep(360) # 6 minutes
        try:
            # Jinke paas 0 ya usse kam paise hain, unko $100 dedo chup-chaap
            await game_db.update_many({"points": {"$lte": 0}}, {"$set": {"points": 100}})
        except Exception:
            pass

# Start the background loop
asyncio.create_task(auto_replenish_loop())


# ==========================================
#              ECO LEADERBOARD
# ==========================================

@app.on_message(filters.command(["ecorank", "ecousers","topusers"], prefixes=["/", ".", "!"]) & filters.group)
async def eco_rankings(client, message: Message):
    chat_id = message.chat.id
    if not await is_eco_enabled(chat_id): return
    try: await message.delete()
    except: pass
    
    # Top Users
    top_users = game_db.find({"points": {"$gt": 0}}).sort("points", -1).limit(10)
    
    text = f"🌍 **{smallcaps('Global Economy Rankings')}** 🌍\n\n"
    text += f"👤 **{smallcaps('Top 10 Richest Users')}**\n"
    
    count = 1
    has_users = False
    async for u in top_users:
        has_users = True
        name = smallcaps(u.get("name", "Unknown")[:15])
        pts = u.get("points", 0)
        text += f"**{count}.** {name} - `${pts}`\n"
        count += 1
        
    if not has_users:
        text += smallcaps("No rich users found yet!") + "\n"
        
    # Top Groups
    text += f"\n👥 **{smallcaps('Top 5 Richest Groups')}**\n"
    top_groups = wallet_db.find({"points": {"$gt": 0}}).sort("points", -1).limit(5)
    
    count = 1
    has_groups = False
    async for g in top_groups:
        has_groups = True
        title = smallcaps(g.get("title", "Unknown Group")[:20])
        pts = g.get("points", 0)
        text += f"**{count}.** {title} - `${pts}`\n"
        count += 1
        
    if not has_groups:
        text += smallcaps("No groups have started earning yet!")
        
    await message.reply_text(text)

# ==========================================
#              DAILY REWARDS & TOP KILLS 
# ==========================================
@app.on_message(filters.command(["topkill"], prefixes=["/", ".", "!"]) & filters.group)
async def top_killers(client, message: Message):
    chat_id = message.chat.id
    if not await is_eco_enabled(chat_id): return

    try: await message.delete()
    except: pass

    text = "⚔️ **Tᴏᴘ 10 Kɪʟʟᴇʀꜱ:**\n\n"
    
    users = game_db.find({"kills": {"$gt": 0}}).sort("kills", -1).limit(10)

    count = 1
    async for user in users:
        name = user.get("name", "Unknown")[:20]
        kills = user.get("kills", 0)

        badge = "💓" if user.get("premium") else "👤"

        text += f"{badge} {smallcaps(name)}: {kills}\n"
        count += 1

    text += "\n💓 = Pʀᴇᴍɪᴜᴍ • 👤 = Nᴏʀᴍᴀʟ\n"
    text += "\n✅ Uᴘɢʀᴀᴅᴇ Tᴏ Pʀᴇᴍɪᴜᴍ : /upgrade"

    await message.reply_text(text)

@app.on_message(filters.command(["daily"], prefixes=["/", ".", "!"]) & filters.group)
async def claim_daily(client, message: Message):
    chat_id = message.chat.id
    if not await is_eco_enabled(chat_id): return
    
    user_id = message.from_user.id
    user_data = await game_db.find_one({"user_id": user_id})
    
    current_time = time.time()
    last_daily = user_data.get("last_daily", 0) if user_data else 0
    
    # 86400 seconds = 24 hours
    if current_time - last_daily < 86400:
        remaining = int(86400 - (current_time - last_daily))
        hours = remaining // 3600
        mins = (remaining % 3600) // 60
        return await message.reply_text(f"⏳ You already claimed your daily reward! Come back in **{hours}h {mins}m**.")
        
    await game_db.update_one(
        {"user_id": user_id}, 
        {"$inc": {"points": 1000}, "$set": {"last_daily": current_time, "name": message.from_user.first_name}}, 
        upsert=True
    )
    
    await message.reply_text(f"🎁 **{smallcaps('Daily Reward Claimed!')}**\n\n👤 {message.from_user.mention} received **$1000**! Come back tomorrow for more.")
# ==========================================
#              UPGRADE SYSTEM
# ==========================================
@app.on_message(filters.command(["upgrade"], prefixes=["/", ".", "!"]) & filters.group)
async def upgrade_status(client, message: Message):
    chat_id = message.chat.id
    if not await is_eco_enabled(chat_id): return

    user = message.from_user
    user_id = user.id

    data = await game_db.find_one({"user_id": user_id}) or {}

    points = data.get("points", 0)
    kills = data.get("kills", 0)
    premium = data.get("premium", False)

    REQUIRED_MONEY = 100000
    REQUIRED_KILLS = 60

    # ✅ Already Premium
    if premium:
        return await message.reply_text(
            f"💓 {smallcaps('You Already Have Premium Access!')}"
        )

    # Progress caps (so it doesn't overflow UI)
    money_progress = min(points, REQUIRED_MONEY)
    kill_progress = min(kills, REQUIRED_KILLS)

    text = "⚠️ **Pʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ ʟᴏᴄᴋᴇᴅ**\n\n"
    text += f"💰 Pʀᴏɢʀᴇꜱꜱ: {money_progress}/{REQUIRED_MONEY}\n"
    text += f"⚔️ Kɪʟʟꜱ: {kill_progress}/{REQUIRED_KILLS}\n\n"

    # Check if completed
    if points >= REQUIRED_MONEY and kills >= REQUIRED_KILLS:
        await game_db.update_one(
            {"user_id": user_id},
            {"$set": {"premium": True}},
            upsert=True
        )

        text += f"🎉 {smallcaps('Congratulations! Premium Unlocked!')}"
    else:
        text += "⏳ Cᴏᴍᴘʟᴇᴛᴇ ᴛᴏᴅᴀʏ'ꜱ ᴛᴀʀɢᴇᴛꜱ ᴛᴏ ᴜɴʟᴏᴄᴋ ᴀᴄᴄᴇꜱꜱ\n\n"
        text += "Kᴇᴇᴘ ᴘʀᴏɢʀᴇꜱꜱɪɴɢ ᴛᴏ ᴜɴʟᴏᴄᴋ Pʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ"

    await message.reply_text(text)
# ==========================================
#              DEATH & REVIVE SYSTEM
# ==========================================

@app.on_message(filters.command(["revive", "rivive"], prefixes=["/", ".", "!"]) & filters.group)
async def revive_user(client, message: Message):
    chat_id = message.chat.id
    if not await is_eco_enabled(chat_id): return
    
    user = message.from_user
    user_id = user.id
    
    data = await game_db.find_one({"user_id": user_id})
    balance = data.get("points", 0) if data else 0
    dead_until = data.get("dead_until", 0) if data else 0

    REVIVE_COST = 500

    # ✅ Already Alive
    if time.time() > dead_until:
        return await message.reply_text(
            f"✅ {smallcaps(user.first_name)} Iꜱ Aʟʀᴇᴀᴅʏ Aʟɪᴠᴇ."
        )

    # 💸 Not Enough Money
    if balance < REVIVE_COST:
        return await message.reply_text(
            f"💸 Yᴏᴜ Nᴇᴇᴅ ${REVIVE_COST} Tᴏ Rᴇᴠɪᴠᴇ, Bᴜᴛ Yᴏᴜ Hᴀᴠᴇ Oɴʟʏ ${balance}"
        )

    # ❤️ Successful Revive
    await game_db.update_one(
        {"user_id": user_id},
        {"$inc": {"points": -REVIVE_COST}, "$set": {"dead_until": 0}},
        upsert=True
    )

    await message.reply_text(
        f"❤️ Yᴏᴜ Rᴇᴠɪᴠᴇᴅ Yᴏᴜʀꜱᴇʟꜰ. -${REVIVE_COST}"
    )

# ==========================================
#              PROTECT SYSTEM
# ==========================================

@app.on_message(filters.command(["protect"], prefixes=["/", ".", "!"]) & filters.group)
async def protect_user_cmd(client, message: Message):
    chat_id = message.chat.id
    if not await is_eco_enabled(chat_id): return
    
    if len(message.command) < 2:
        return await message.reply_text("⚠️ Uꜱᴀɢᴇ: `/protect 1d` or `/protect 2d`")
        
    arg = message.command[1].lower()
    days = 1
    if arg == "2d": days = 2
    elif arg != "1d": return await message.reply_text("⚠️ Uꜱᴀɢᴇ: `/protect 1d` or `/protect 2d`")
    
    cost = 300 * days  
    
    user_data = await game_db.find_one({"user_id": message.from_user.id})
    if not user_data or user_data.get("points", 0) < cost:
        return await message.reply_text(f"⚠️ You need **${cost}** to buy {days} day(s) of protection!")
        
    new_prot_time = time.time() + (days * 86400)
    await game_db.update_one(
        {"user_id": message.from_user.id}, 
        {"$inc": {"points": -cost}, "$set": {"protected_until": new_prot_time}}, 
        upsert=True
    )
    
    await message.reply_text(f"🛡️ **{smallcaps('Payment Successful!')}**\nYou are now protected from being robbed/killed for **{days} day(s)**!")

# ==========================================
#              KILL & ROB SYSTEM
# ==========================================
@app.on_message(filters.command(["kill", "rob"], prefixes=["/", ".", "!"]) & filters.group)
async def rob_or_kill_user(client, message: Message):
    chat_id = message.chat.id
    if not await is_eco_enabled(chat_id): return
    
    robber_user = message.from_user
    robber_data = await game_db.find_one({"user_id": robber_user.id}) or {}

    # --- DAILY CHECK ---
    last_daily = robber_data.get("last_daily", 0)
    if time.time() - last_daily >= 86400:
        claim_msg = "⚠️ " + smallcaps("You haven't claimed your daily bonus yet! First claim it to perform an attack.")
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 " + smallcaps("Claim Daily Bonus"), url=f"https://t.me/{app.username}?start=claimx")]
        ])
        return await message.reply_text(claim_msg, reply_markup=markup)

    # --- REPLY CHECK ---
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply_text("⚠️ Reply to a user's message to kill/rob them!")

    target_user = message.reply_to_message.from_user

    if target_user.id == robber_user.id:
        return await message.reply_text("⚠️ You can't attack yourself!")
    if target_user.is_bot:
        return await message.reply_text("⚠️ You can't attack bots!")

    # --- COOLDOWN (ANTI-SPAM) ---
    last_attack = robber_data.get("last_attack", 0)
    if time.time() - last_attack < 30:
        return await message.reply_text("⏳ Wait 30s before attacking again!")

    # --- ATTACKER STATE ---
    robber_dead = robber_data.get("dead_until", 0)
    robber_kills = robber_data.get("kills", 0)

    if time.time() < robber_dead:
        return await message.reply_text("👻 You are dead! Use `/revive` first.")

    cmd = message.command[0].lower()

    # --- ROB UNLOCK ---
    if cmd == "rob" and robber_kills < 2:
        return await message.reply_text(
            f"🔒 Rob Locked!\nNeed **2 kills** (You: {robber_kills})"
        )

    # --- TARGET DATA ---
    target_data = await game_db.find_one({"user_id": target_user.id}) or {}

    target_prot = target_data.get("protected_until", 0)
    target_dead = target_data.get("dead_until", 0)
    target_bal = target_data.get("points", 0)

    if time.time() < target_dead:
        return await message.reply_text(f"💀 {smallcaps(target_user.first_name)} is already dead!")

    if time.time() < target_prot:
        return await message.reply_text(f"🛡️ {smallcaps(target_user.first_name)} is protected!")

    # =========================
    # 💰 ROB LOGIC
    # =========================
    if cmd == "rob":
        if target_bal <= 0:
            return await message.reply_text(f"⚠️ {smallcaps(target_user.first_name)} is already broke!")

        if len(message.command) < 2:
            return await message.reply_text("⚠️ Usage: `/rob amount`")

        try:
            amount_to_rob = int(message.command[1])
        except:
            return await message.reply_text("⚠️ Invalid amount!")

        if amount_to_rob <= 0:
            return await message.reply_text("⚠️ Amount must be > 0")

        if amount_to_rob > target_bal:
            amount_to_rob = target_bal

    # =========================
    # 🔪 KILL LOGIC
    # =========================
    else:
        if target_bal <= 0:
            amount_to_rob = 1  # allow kill even if broke
        else:
            amount_to_rob = random.randint(1, max(2, int(target_bal * 0.15)))

    # =========================
    # FINAL VALUES
    # =========================
    total_gained = amount_to_rob
    xp_gained = 15
    death_timer = time.time() + 420  # 7 min

    # --- UPDATE TARGET ---
    if cmd == "kill":
        await game_db.update_one(
            {"user_id": target_user.id},
            {
                "$inc": {"points": -amount_to_rob},
                "$set": {"dead_until": death_timer, "name": target_user.first_name}
            },
            upsert=True
        )
    else:
        await game_db.update_one(
            {"user_id": target_user.id},
            {
                "$inc": {"points": -amount_to_rob},
                "$set": {"name": target_user.first_name}
            },
            upsert=True
        )

    # --- UPDATE ATTACKER ---
    await game_db.update_one(
        {"user_id": robber_user.id},
        {
            "$inc": {
                "points": total_gained,
                "kills": 1 if cmd == "kill" else 0,
                "xp": xp_gained
            },
            "$set": {
                "last_attack": time.time(),
                "name": robber_user.first_name
            }
        },
        upsert=True
    )

    # =========================
    # OUTPUT TEXT
    # =========================
    if cmd == "kill":
        text = f"🔪 {smallcaps(robber_user.first_name)} Kɪʟʟᴇᴅ & Rᴏʙʙᴇᴅ ${amount_to_rob} from {smallcaps(target_user.first_name)}\n"
        text += f"💀 {smallcaps(target_user.first_name)} is dead for 7 min\n"
    else:
        text = f"🥷 {smallcaps(robber_user.first_name)} Rᴏʙʙᴇᴅ ${amount_to_rob} from {smallcaps(target_user.first_name)}\n"

    text += f"💰 +${total_gained} | +{xp_gained} XP"

    await message.reply_text(text)
# ==========================================
#              GIVE / SEND MONEY
# ==========================================

@app.on_message(filters.command(["give", "send", "sand"], prefixes=["/", ".", "!"]) & filters.group)
async def give_money(client, message: Message):
    chat_id = message.chat.id
    if not await is_eco_enabled(chat_id): return
    
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.reply_text("⚠️ Reply to a user's message to send them money!")
        
    target_user = message.reply_to_message.from_user
    sender_user = message.from_user
    
    if target_user.id == sender_user.id:
        return await message.reply_text("⚠️ You can't send money to yourself!")
    if target_user.is_bot:
        return await message.reply_text("⚠️ You can't send money to bots!")
        
    if len(message.command) < 2:
        return await message.reply_text("⚠️ Usage: `/give [amount]` or `/send [amount]`")
        
    try:
        amount = int(message.command[1])
    except:
        return await message.reply_text("⚠️ Invalid amount!")
        
    if amount <= 0:
        return await message.reply_text("⚠️ Amount must be greater than $0!")

    sender_data = await game_db.find_one({"user_id": sender_user.id})
    sender_bal = sender_data.get("points", 0) if sender_data else 0
    
    if sender_bal < amount:
        return await message.reply_text(f"⚠️ You don't have enough money! Your balance is **${sender_bal}**.")
        
    # Calculate 2% Tax
    tax = math.ceil(amount * 0.02)
    net_amount = amount - tax
    
    # Update DB
    await game_db.update_one({"user_id": sender_user.id}, {"$inc": {"points": -amount}})
    await game_db.update_one({"user_id": target_user.id}, {"$inc": {"points": net_amount}}, upsert=True)
    
    text = f"💸 **{smallcaps('Transfer Successful!')}**\n\n"
    text += f"👤 Sᴇɴᴅᴇʀ: {smallcaps(sender_user.first_name)}\n"
    text += f"🎯 Rᴇᴄᴇɪᴠᴇʀ: {smallcaps(target_user.first_name)}\n"
    text += f"💵 Aᴍᴏᴜɴᴛ Sᴇɴᴛ: ${amount}\n"
    text += f"📉 2% Tᴀx: ${tax}\n"
    text += f"💰 {smallcaps('Net Received')}: **${net_amount}**"
    
    await message.reply_text(text)
    

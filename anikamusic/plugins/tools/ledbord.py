import os
import time
import asyncio
from io import BytesIO
from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from anikamusic import app
from anikamusic.misc import mongodb

# Database
db = mongodb.leaderboard_db
message_collection = db.message_counts

LEADERBOARD_CACHE = {}
CACHE_TIME = 400 # TEST KARTE TIME ISKO 0 RAKHA HAI. BAAD MEIN 300 (5 mins) KAR DENA!

# ----------------- ANTI-SPAM LOGIC -----------------
USER_MESSAGE_HISTORY = {} 
USER_LAST_MESSAGE = {} 
BLOCKED_USERS = {}
spam_lock = asyncio.Lock() 

SPAM_THRESHOLD = 4 
SPAM_WINDOW = 2 
BLOCK_DURATION = 1200 
REPEAT_THRESHOLD = 5 

# ----------------- MILESTONE LOGIC -----------------
MILESTONES_REACHED = {} 
COUNT_TEST_SESSIONS = {} 

# ----------------- TIMEZONE LOGIC (6 AM IST) -----------------
def get_logical_date(timeframe="today"):
    """Returns date filters based on 6:00 AM IST reset time"""
    # IST is UTC + 5:30
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    # Shift time back by 6 hours. So 5:59 AM is treated as previous day.
    logical_now = ist_now - timedelta(hours=6)
    
    if timeframe == "today":
        return {"date": logical_now.strftime("%Y-%m-%d")}
    elif timeframe == "week":
        seven_days_ago = logical_now - timedelta(days=7)
        return {"date": {"$gte": seven_days_ago.strftime("%Y-%m-%d")}}
    return {} # overall

def get_today_string():
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    logical_now = ist_now - timedelta(hours=6)
    return logical_now.strftime("%Y-%m-%d")

# ----------------- DB FUNCTIONS -----------------
async def update_message_count_and_check_milestone(chat_id: int, chat_title: str, user_id: int, name: str):
    today = get_today_string()
    
    # Update DB with chat_title as well (useful for group rankings)
    await message_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id, "date": today},
        {"$inc": {"count": 1}, "$set": {"name": name, "chat_title": chat_title}},
        upsert=True
    )
    
    # Milestone check
    pipeline_total = [
        {"$match": {"chat_id": chat_id, "date": today}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}}
    ]
    cursor = message_collection.aggregate(pipeline_total)
    data = await cursor.to_list(length=1)
    
    if data:
        total_today = data[0]['total']
        if total_today > 0 and total_today % 1000 == 0:
            if chat_id not in MILESTONES_REACHED:
                MILESTONES_REACHED[chat_id] = []
            if total_today not in MILESTONES_REACHED[chat_id]:
                MILESTONES_REACHED[chat_id].append(total_today)
                
                ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
                current_time_str = ist_now.strftime("%H:%M")
                msg_text = f"💪 {total_today} messages reached today! ({current_time_str})"
                try:
                    await app.send_message(chat_id, msg_text)
                except:
                    pass

async def get_rank_data(timeframe: str, rank_type: str, chat_id: int = None, user_id: int = None):
    """Generic function to fetch data for all types of leaderboards"""
    match_query = get_logical_date(timeframe)
    
    if rank_type == "local" and chat_id:
        match_query["chat_id"] = chat_id
    elif rank_type == "mytop" and user_id:
        match_query["user_id"] = user_id
    
    pipeline_top = [{"$match": match_query}] if match_query else []
    
    if rank_type in ["local", "global"]:
        # Group by User
        pipeline_top.extend([
            {"$group": {"_id": "$user_id", "name": {"$first": "$name"}, "total_messages": {"$sum": "$count"}}},
            {"$sort": {"total_messages": -1}},
            {"$limit": 10}
        ])
    elif rank_type in ["groups", "mytop"]:
        # Group by Chat
        pipeline_top.extend([
            {"$group": {"_id": "$chat_id", "name": {"$first": "$chat_title"}, "total_messages": {"$sum": "$count"}}},
            {"$sort": {"total_messages": -1}},
            {"$limit": 10}
        ])
        
    cursor = message_collection.aggregate(pipeline_top)
    top_data = await cursor.to_list(length=10)

    # Clean up names if they are missing
    for item in top_data:
        if not item.get("name"):
            item["name"] = "Unknown"

    # Get grand total
    pipeline_total = [{"$match": match_query}] if match_query else []
    pipeline_total.append({"$group": {"_id": None, "grand_total": {"$sum": "$count"}}})
    
    total_cursor = message_collection.aggregate(pipeline_total)
    total_data = await total_cursor.to_list(length=1)
    total_messages = total_data[0]['grand_total'] if total_data else 0

    return top_data, total_messages

# ----------------- FORMATTING HELPER -----------------
def build_caption(data: list, total_messages: int, rank_type: str, custom_name: str = "") -> str:
    if not data or total_messages == 0:
        return f"📈 LEADERBOARD\n\n✉️ Total messages: 0\n\nEnable AI Summary in this group using the /upgrade command."
        
    if rank_type == "groups":
        text = "📈 TOP GROUPS GLOBALLY\n"
        icon = "👥"
    elif rank_type == "mytop":
        text = f"📈 TOP GROUPS | {custom_name}\n"
        icon = "👥"
    elif rank_type == "global":
        text = "🌍 GLOBAL TOP USERS\n"
        icon = "👤"
    else:
        text = "📈 LEADERBOARD\n"
        icon = "👤"
        
    for index, item in enumerate(data):
        score = f"{item['total_messages']:,}".replace(",", ".") 
        name = str(item['name'])[:15] + "..." if len(str(item['name'])) > 15 else str(item['name'])
        text += f"{index+1}. {icon} {name} • {score}\n"
        
    formatted_total = f"{total_messages:,}".replace(",", ".")
    text += f"\n✉️ Total messages: {formatted_total}\n\n"
    text += "Enable AI Summary in this group using the /upgrade command."
    return text

# ----------------- IMAGE GENERATION -----------------
def generate_leaderboard_image(data: list, timeframe: str) -> BytesIO:
    if not data:
        return None 
        
    template_path = "anikamusic/assets/template.png"
    if not os.path.exists(template_path):
        return None
        
    img = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("anikamusic/assets/font.ttf", 20) # Thoda chota kiya text fit aane ke liye
        font_small = ImageFont.truetype("anikamusic/assets/font.ttf", 16)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    bar_color = (41, 121, 255, 200) # Isko tu chahe toh red kar lena (e.g., (200, 50, 50, 200)) baad me
    text_color = (255, 255, 255, 255)
    
    # Adjusted Coordinates for Red Template match
    start_x = 200 # Bar thoda aage se shuru hogi
    start_y = 150 # Upar se distance
    gap = 42 # Gap between lines
    max_bar_width = 450 
    
    highest_score = data[0]['total_messages']
    for index, item in enumerate(data):
        score = item['total_messages']
        name = str(item['name'])[:15] + "..." if len(str(item['name'])) > 15 else str(item['name'])
        bar_width = int((score / highest_score) * max_bar_width) if highest_score > 0 else 10
        y_pos = start_y + (index * gap)
        
        # Draw Bar
        draw.rounded_rectangle([(start_x, y_pos), (start_x + bar_width, y_pos + 25)], radius=10, fill=bar_color)
        
        # Draw Name ON THE LEFT of the bar
        draw.text((30, y_pos), f"{name}", fill=text_color, font=font_small)
        
        # Draw Score INSIDE or right after the bar
        draw.text((start_x + 10, y_pos + 2), str(score), fill=text_color, font=font_small)

    image_stream = BytesIO()
    img.save(image_stream, format="PNG")
    image_stream.name = f"leaderboard_{timeframe}.png"
    image_stream.seek(0)
    return image_stream

# ----------------- BUTTONS -----------------
def lb_buttons(current_timeframe="overall", prefix="lb"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Overall ✅" if current_timeframe == "overall" else "Overall", callback_data=f"{prefix}_overall"),
            InlineKeyboardButton("Today ✅" if current_timeframe == "today" else "Today", callback_data=f"{prefix}_today"),
            InlineKeyboardButton("Week ✅" if current_timeframe == "week" else "Week", callback_data=f"{prefix}_week")
        ],
        [
            InlineKeyboardButton("Close", callback_data="lb_close")
        ]
    ])

# ----------------- HANDLERS -----------------

# 1. Message Listener & Spam Checker
@app.on_message(filters.group & ~filters.bot, group=112)
async def count_messages(client, message: Message):
    if not message.from_user:
        return
        
    user_id = message.from_user.id
    current_time = time.time()
    chat_title = message.chat.title or "Group"
    
    if user_id in BLOCKED_USERS:
        if current_time < BLOCKED_USERS[user_id]:
            return 
        else:
            del BLOCKED_USERS[user_id] 

    async with spam_lock:
        is_spammer = False
        spam_reason = ""
        
        msg_text = message.text or message.caption
        if msg_text:
            msg_text = msg_text.lower().strip() 
            if user_id not in USER_LAST_MESSAGE:
                USER_LAST_MESSAGE[user_id] = {"text": msg_text, "count": 1}
            else:
                if USER_LAST_MESSAGE[user_id]["text"] == msg_text:
                    USER_LAST_MESSAGE[user_id]["count"] += 1
                else:
                    USER_LAST_MESSAGE[user_id] = {"text": msg_text, "count": 1}
            
            if USER_LAST_MESSAGE[user_id]["count"] >= REPEAT_THRESHOLD:
                is_spammer = True
                spam_reason = "repeating the same message"
                USER_LAST_MESSAGE[user_id] = {"text": "", "count": 0} 
                
        if user_id not in USER_MESSAGE_HISTORY:
            USER_MESSAGE_HISTORY[user_id] = []
            
        USER_MESSAGE_HISTORY[user_id].append(current_time)
        USER_MESSAGE_HISTORY[user_id] = [msg_time for msg_time in USER_MESSAGE_HISTORY[user_id] if current_time - msg_time <= SPAM_WINDOW]
        
        if len(USER_MESSAGE_HISTORY[user_id]) >= SPAM_THRESHOLD:
            is_spammer = True
            spam_reason = "flooding"
            USER_MESSAGE_HISTORY[user_id] = [] 
            
        if is_spammer:
            BLOCKED_USERS[user_id] = current_time + BLOCK_DURATION
            try:
                warning_msg = await message.reply_text(f"⛔️ {message.from_user.mention} is {spam_reason}: blocked for 20 minutes from the leaderboard.")
                async def delete_warn():
                    await asyncio.sleep(10)
                    try:
                        await warning_msg.delete()
                    except:
                        pass
                asyncio.create_task(delete_warn())
            except:
                pass
            return 
            
    asyncio.create_task(update_message_count_and_check_milestone(message.chat.id, chat_title, message.from_user.id, message.from_user.first_name))

    # Live Test Logic
    session_key = (message.chat.id, message.from_user.id)
    if session_key in COUNT_TEST_SESSIONS:
        if msg_text and msg_text.startswith(("/", ".")):
            return
        COUNT_TEST_SESSIONS[session_key] += 1
        count = COUNT_TEST_SESSIONS[session_key]
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 End Count", callback_data=f"endct_{message.from_user.id}")]])
        try:
            await message.reply_text(f"📝 Message {count} | Database Updated ✅", reply_markup=btn)
        except:
            pass

# ----------------- CHAT RESET COMMAND (Wipe DB for Group) -----------------
@app.on_message(filters.command(["creset", "cresat"], prefixes=["/", "."]) & filters.group)
async def reset_chat_data(client, message: Message):
    chat_id = message.chat.id
    # Admin check lagana chahe toh yahan laga lena
    await message_collection.delete_many({"chat_id": chat_id})
    
    # Clear cache
    for tf in ["overall", "today", "week"]:
        if f"{chat_id}_{tf}" in LEADERBOARD_CACHE:
            del LEADERBOARD_CACHE[f"{chat_id}_{tf}"]
            
    await message.reply_text("🧹 **Chat history cleared!** Is group ka sara purana kachra saaf ho gaya hai. Leaderboard 0 se start hoga.")

# ----------------- MAIN RANK COMMANDS -----------------
@app.on_message(filters.command(["rank", "rankings"], prefixes=["/", "."]) & filters.group)
async def cmd_local_rank(client, message: Message):
    await send_leaderboard_ui(message, "local", "lb", chat_id=message.chat.id)

@app.on_message(filters.command(["globalrank", "rankglobal"], prefixes=["/", "."]) & filters.group)
async def cmd_global_rank(client, message: Message):
    await send_leaderboard_ui(message, "global", "glb")

@app.on_message(filters.command(["groupsrank", "gcrank"], prefixes=["/", "."]) & filters.group)
async def cmd_gc_rank(client, message: Message):
    await send_leaderboard_ui(message, "groups", "gc")

@app.on_message(filters.command(["mytop"], prefixes=["/", "."]) & filters.group)
async def cmd_my_top(client, message: Message):
    await send_leaderboard_ui(message, "mytop", "mytop", user_id=message.from_user.id, custom_name=message.from_user.first_name)

async def send_leaderboard_ui(message: Message, rank_type: str, prefix: str, chat_id=None, user_id=None, custom_name=""):
    try:
        await message.delete()
    except:
        pass 

    timeframe = "overall"
    # Create unique cache key based on type
    cache_id = chat_id if chat_id else (user_id if user_id else "global")
    cache_key = f"{rank_type}_{cache_id}_{timeframe}"
    
    msg_chat_id = message.chat.id
    
    if cache_key in LEADERBOARD_CACHE and time.time() < LEADERBOARD_CACHE[cache_key]["expiry"]:
        cache_data = LEADERBOARD_CACHE[cache_key]
        if cache_data.get("is_text_only"):
            return await app.send_message(msg_chat_id, cache_data["caption"], reply_markup=lb_buttons(timeframe, prefix))
        else:
            return await app.send_photo(msg_chat_id, photo=cache_data["image"], caption=cache_data["caption"], reply_markup=lb_buttons(timeframe, prefix), has_spoiler=True)

    data, total_msgs = await get_rank_data(timeframe, rank_type, chat_id, user_id)
    caption_text = build_caption(data, total_msgs, rank_type, custom_name)
    
    if not data or total_msgs == 0:
        sent_msg = await app.send_message(msg_chat_id, caption_text, reply_markup=lb_buttons(timeframe, prefix))
        LEADERBOARD_CACHE[cache_key] = {"is_text_only": True, "caption": caption_text, "expiry": time.time() + CACHE_TIME}
    else:
        img_stream = generate_leaderboard_image(data, timeframe)
        if img_stream:
            sent_msg = await app.send_photo(msg_chat_id, photo=img_stream, caption=caption_text, reply_markup=lb_buttons(timeframe, prefix), has_spoiler=True)
            LEADERBOARD_CACHE[cache_key] = {"is_text_only": False, "image": sent_msg.photo.file_id, "caption": caption_text, "expiry": time.time() + CACHE_TIME}
        else:
            await app.send_message(msg_chat_id, "❌ Template image not found!")

# ----------------- FORCE UPDATE -----------------
@app.on_message(filters.command(["force", "fc"], prefixes=["/", "."]) & filters.group)
async def force_leaderboard_update(client, message: Message):
    chat_id = message.chat.id
    try:
        await message.delete()
    except:
        pass
    for tf in ["overall", "today", "week"]:
        if f"local_{chat_id}_{tf}" in LEADERBOARD_CACHE:
            del LEADERBOARD_CACHE[f"local_{chat_id}_{tf}"]
    await send_leaderboard_ui(message, "local", "lb", chat_id=chat_id)

# ----------------- CALLBACK HANDLER FOR ALL LEADERBOARDS -----------------
@app.on_callback_query(filters.regex(r"^(lb|glb|gc|mytop)_(overall|today|week)$"))
async def leaderboard_callback(client, query):
    prefix = query.matches[0].group(1)
    timeframe = query.matches[0].group(2)
    chat_id = query.message.chat.id
    
    # Map prefix back to rank_type
    rank_type = "local"
    target_id = chat_id
    custom_name = ""
    user_id = None
    
    if prefix == "glb":
        rank_type = "global"
        target_id = "global"
    elif prefix == "gc":
        rank_type = "groups"
        target_id = "global"
    elif prefix == "mytop":
        rank_type = "mytop"
        user_id = query.from_user.id
        target_id = user_id
        custom_name = query.from_user.first_name

    cache_key = f"{rank_type}_{target_id}_{timeframe}"
    is_current_msg_photo = bool(query.message.photo)

    await query.answer("wait....", show_alert=False)
    
    data, total_msgs = await get_rank_data(timeframe, rank_type, chat_id if rank_type=="local" else None, user_id)
    caption_text = build_caption(data, total_msgs, rank_type, custom_name)
    
    if not data or total_msgs == 0:
        if is_current_msg_photo:
            await query.message.delete()
            await app.send_message(chat_id, caption_text, reply_markup=lb_buttons(timeframe, prefix))
        else:
            await query.edit_message_text(caption_text, reply_markup=lb_buttons(timeframe, prefix))
    else:
        img_stream = generate_leaderboard_image(data, timeframe)
        if img_stream:
            if not is_current_msg_photo:
                await query.message.delete()
                await app.send_photo(chat_id, photo=img_stream, caption=caption_text, reply_markup=lb_buttons(timeframe, prefix), has_spoiler=True)
            else:
                await query.edit_message_media(media=InputMediaPhoto(media=img_stream, caption=caption_text, has_spoiler=True), reply_markup=lb_buttons(timeframe, prefix))
        else:
            await query.answer("Error generating image.", show_alert=True)

@app.on_callback_query(filters.regex(r"^lb_close$"))
async def close_leaderboard_callback(client, query):
    try:
        await query.message.delete()
    except:
        await query.answer("❌ Failed to delete message.", show_alert=True)

# ----------------- LIVE TEST COMMANDS -----------------
@app.on_message(filters.command(["cunttest", "counttest"], prefixes=["/", "."]) & filters.group)
async def start_count_test(client, message: Message):
    session_key = (message.chat.id, message.from_user.id)
    COUNT_TEST_SESSIONS[session_key] = 0
    btn = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 End Count", callback_data=f"endct_{message.from_user.id}")]])
    await message.reply_text(f"✅ **Test Started for {message.from_user.mention}!**\nAb tu jo bhi message bhejega, main report doonga.", reply_markup=btn)

@app.on_callback_query(filters.regex(r"^endct_(\d+)$"))
async def end_count_cb(client, query):
    user_id = int(query.matches[0].group(1))
    if query.from_user.id != user_id:
        return await query.answer("Ye test tumhara nahi hai!", show_alert=True)
    session_key = (query.message.chat.id, user_id)
    if session_key in COUNT_TEST_SESSIONS:
        del COUNT_TEST_SESSIONS[session_key]
        try:
            await query.message.edit_text("✅ **Count test ended manually.**")
        except:
            pass
    else:
        await query.answer("Test already ended!", show_alert=True)

@app.on_message(filters.command(["spamtest", "testspam"], prefixes=["/", "."]) & filters.group)
async def manual_spam_trigger(client, message: Message):
    user_id = message.from_user.id
    BLOCKED_USERS[user_id] = time.time() + BLOCK_DURATION
    USER_MESSAGE_HISTORY[user_id] = []
    try:
        await message.delete()
        warning_msg = await message.reply_text(f"⛔️ [TEST] {message.from_user.mention} is flooding: blocked for 20 minutes.")
        async def delete_warn():
            await asyncio.sleep(60)
            try:
                await warning_msg.delete()
            except:
                pass
        asyncio.create_task(delete_warn())
    except:
        pass

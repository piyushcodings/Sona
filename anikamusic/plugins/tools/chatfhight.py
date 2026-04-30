import time
import asyncio
import os
import random
import aiohttp
from PIL import Image, ImageDraw, ImageFont
from pyrogram import filters
from pyrogram.types import Message

import config
from anikamusic import app
from anikamusic.misc import mongodb
from anikamusic.utils.database import get_served_users

# 🔥 MONGODB COLLECTION FOR LEADERBOARD 🔥
game_db = mongodb["wordgame_leaderboard"]

# --- GLOBAL TRACKERS ---
last_message_time = {}
active_games = {}
user_cooldowns = {} 
INACTIVITY_LIMIT = 300  
PENALTY_TIME = 60 

# --- FILE PATHS ---
TEMPLATE_PATH = "anikamusic/assets/template.jpg"
FONT_PATH = "anikamusic/assets/arial.ttf"

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

# --- RANDOM WARNING MESSAGES ---
WARNING_MESSAGES = [
    f"<emoji id='6334789677396002338'>⏱</emoji> {smallcaps('Time passes. Tick tock, tick tock...')}",
    f"⚠️ {smallcaps('Alarm: time is running out!!')}",
    f"🥱 {smallcaps('It is too quiet here... let us play a game!')}",
    f"👀 {smallcaps('Anyone there? Get ready to type...')}"
]

EMOJIS = ["🍏","🍎","🍐","🍊","🍋","🍌","🍉","🍇","🍓","🫐","🍈","🍒","🍑","🥭","🍍","🥥","🥝","🍅","🍆","🥑","🥦","🥬","🥒","🌶","🌽","🥕","🥔","🍠","🥐","🥯","🍞","🥖","🥨","🧀","🥚","🍳","🧈","🥞","🧇","🥓","🥩","🍗","🍖","🌭","🍔","🍟","🍕","🥪","🥙","🌮","🌯","🥗","🥘","🥫","🍝","🍜","🍲","🍛","🍣","🍱","🥟","🍤","🍙","🍚","🍘","🍥","🥮","🍢","🍡","🍧","🍨","🍦","🥧","🧁","🍰","🎂","🍮","🍭","🍬","🍫","🍿","🍩","🍪","🍯","🥛","🍼","☕","🍵","🧃","🥤","🍺","🍻","🥂","🍷","🥃","🍸","🍹","🧉","🍾","🧊"]

COUNTRIES = [
    {"name": "India", "code": "in"}, {"name": "USA", "code": "us"}, {"name": "Japan", "code": "jp"}, 
    {"name": "Brazil", "code": "br"}, {"name": "Canada", "code": "ca"}, {"name": "UK", "code": "gb"},
    {"name": "France", "code": "fr"}, {"name": "Germany", "code": "de"}, {"name": "Italy", "code": "it"},
    {"name": "Russia", "code": "ru"}, {"name": "China", "code": "cn"}, {"name": "Australia", "code": "au"},
    {"name": "Spain", "code": "es"}, {"name": "Mexico", "code": "mx"}, {"name": "South Korea", "code": "kr"}
]

# --- PREMIUM HACK INJECTION ---
async def inject_premium_markup(chat_id, message_id, markup):
    try:
        token = getattr(config, "BOT_TOKEN", getattr(app, "bot_token", None))
        url = f"https://api.telegram.org/bot{token}/editMessageReplyMarkup"
        payload = {"chat_id": chat_id, "message_id": message_id, "reply_markup": {"inline_keyboard": markup}}
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=payload)
    except Exception as e:
        pass

# ==========================================
#              IMAGE GENERATION LOGIC
# ==========================================

def create_game_image(text, is_emoji=False):
    output_path = f"game_{random.randint(1000,9999)}.jpg"
    if not os.path.exists(TEMPLATE_PATH):
        os.makedirs(os.path.dirname(TEMPLATE_PATH), exist_ok=True)
        img = Image.new('RGB', (800, 400), color=(15, 15, 15))
        img.save(TEMPLATE_PATH)

    bg = Image.open(TEMPLATE_PATH).convert("RGBA")
    if not is_emoji:
        draw = ImageDraw.Draw(bg)
        try: font = ImageFont.truetype(FONT_PATH, 65)
        except: font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = (bg.size[0] - text_w) / 2, ((bg.size[1] - text_h) / 2) - 10
        draw.text((x, y), text, fill="white", font=font)
        bg = bg.convert("RGB")
        bg.save(output_path)
        return output_path

async def create_emoji_or_flag_image(identifier, is_flag=False):
    output_path = f"game_{random.randint(1000,9999)}.jpg"
    if is_flag: url = f"https://flagcdn.com/256x192/{identifier}.png"
    else:
        hex_code = "-".join(f"{ord(c):x}" for c in identifier).replace("-fe0f", "")
        url = f"https://cdn.jsdelivr.net/gh/jdecked/twemoji@15.0.3/assets/72x72/{hex_code}.png"
    
    bg = Image.open(TEMPLATE_PATH).convert("RGBA")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    img_bytes = await resp.read()
                    temp_name = f"temp_{random.randint(100,999)}.png"
                    with open(temp_name, "wb") as f: f.write(img_bytes)
                    img_layer = Image.open(temp_name).convert("RGBA")
                    if not is_flag: img_layer = img_layer.resize((160, 160), Image.Resampling.LANCZOS)
                    bg.paste(img_layer, ((bg.size[0]-img_layer.size[0])//2, (bg.size[1]-img_layer.size[1])//2), img_layer)
                    os.remove(temp_name)
    except Exception: pass 
    bg = bg.convert("RGB")
    bg.save(output_path)
    return output_path

# ==========================================
#              WORD GAME LOGIC
# ==========================================

async def get_random_word():
    fallback_words = ["BACTERIAL", "GAMUT", "PANDEMIC", "AESTHETIC", "RESONATE", "ILLUSION", "HELLFIRE", "DEVELOPER"]
    if not hasattr(config, "GROQ_API_KEY") or not config.GROQ_API_KEY: return random.choice(fallback_words)
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": "Reply with only ONE random difficult English word. No punctuation."}],
            "temperature": 0.9
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                word = data['choices'][0]['message']['content'].strip().upper()
                return ''.join(e for e in word if e.isalnum()) or random.choice(fallback_words)
    except Exception: return random.choice(fallback_words)

def hide_letters(word):
    num_to_hide = max(1, len(word) // 2)
    indices_to_hide = random.sample(range(len(word)), num_to_hide)
    hidden_word = list(word)
    for i in indices_to_hide: hidden_word[i] = "_"
    return "".join(hidden_word)

async def start_word_game(chat_id):
    try:
        original_word = await get_random_word()
        is_missing = random.choice([True, False])
        display_word = hide_letters(original_word) if is_missing else original_word
        
        img_path = create_game_image(display_word)
        caption = f"<emoji id='6334696528145286813'>⚡</emoji> **{smallcaps('Be the first to write the word shown in the photo!')}**\n\n<emoji id='6334789677396002338'>⏱</emoji> **{smallcaps('Time remaining: 10 minutes')}**"
        
        sent_msg = await app.send_photo(chat_id, photo=img_path, caption=caption, has_spoiler=True)
        if os.path.exists(img_path): os.remove(img_path) 
        active_games[chat_id] = {"type": "word", "answer": original_word, "start_time": time.time(), "message_id": sent_msg.id}
        
        if is_missing:
            # 🔥 Custom Emoji Added to Give Up
            markup = [[{"text": f"🏳️ {smallcaps('Give Up')}", "callback_data": f"giveup_{chat_id}", "style": "danger", "icon_custom_emoji_id": "5999100917645841519"}]]
            await inject_premium_markup(chat_id, sent_msg.id, markup)
    except Exception: pass

# ==========================================
#              EMOJI GAME LOGIC
# ==========================================

async def start_emoji_game(chat_id):
    try:
        correct_emoji = random.choice(EMOJIS)
        options = random.sample([e for e in EMOJIS if e != correct_emoji], 11) + [correct_emoji]
        random.shuffle(options)

        img_path = await create_emoji_or_flag_image(correct_emoji, is_flag=False)
        caption = f"👇 **{smallcaps('Identify the emoji in the photo and select it below!')}**\n\n<emoji id='6334789677396002338'>⏱</emoji> **{smallcaps('Time remaining: 10 minutes')}**"
        
        sent_msg = await app.send_photo(chat_id, photo=img_path, caption=caption, has_spoiler=True)
        if os.path.exists(img_path): os.remove(img_path)

        markup, row = [], []
        for em in options:
            row.append({"text": em, "callback_data": f"emg_{chat_id}_{em}", "style": "primary"})
            if len(row) == 3: markup.append(row); row = []
        if row: markup.append(row)

        await inject_premium_markup(chat_id, sent_msg.id, markup)
        active_games[chat_id] = {"type": "emoji", "answer": correct_emoji, "start_time": time.time(), "message_id": sent_msg.id}
    except Exception: pass

# ==========================================
#              FLAG GAME LOGIC
# ==========================================

async def start_flag_game(chat_id):
    try:
        correct_country = random.choice(COUNTRIES)
        options_pool = [c for c in COUNTRIES if c['code'] != correct_country['code']]
        options = random.sample(options_pool, min(11, len(options_pool))) + [correct_country]
        random.shuffle(options)

        img_path = await create_emoji_or_flag_image(correct_country['code'], is_flag=True)
        caption = f"🌍 **{smallcaps('Guess the country from its flag and select the correct option!')}**\n\n<emoji id='6334789677396002338'>⏱</emoji> **{smallcaps('Time remaining: 10 minutes')}**"
        
        sent_msg = await app.send_photo(chat_id, photo=img_path, caption=caption, has_spoiler=True)
        if os.path.exists(img_path): os.remove(img_path)

        markup, row = [], []
        for c in options:
            # 🔥 Custom Emoji Added to Flags
            row.append({"text": smallcaps(c['name']), "callback_data": f"flg_{chat_id}_{c['code']}", "style": "primary", "icon_custom_emoji_id": "6080202089311507876"})
            if len(row) == 2: markup.append(row); row = []
        if row: markup.append(row)

        await inject_premium_markup(chat_id, sent_msg.id, markup)
        active_games[chat_id] = {"type": "flag", "answer": correct_country['code'], "name": correct_country['name'], "start_time": time.time(), "message_id": sent_msg.id}
    except Exception: pass

# ==========================================
#              CALLBACK HANDLERS
# ==========================================

async def check_cooldown(user_id, callback_query):
    if user_id in user_cooldowns:
        time_passed = time.time() - user_cooldowns[user_id]
        if time_passed < PENALTY_TIME:
            wait_time = int(PENALTY_TIME - time_passed)
            await callback_query.answer(f"⏳ {smallcaps('Penalty active!')} {wait_time} {smallcaps('seconds remaining.')}", show_alert=True)
            return True
    return False

# 🔥 BULLETPROOF REWARD CLAIM CHECKER
async def check_and_send_claim(client, chat_id, user_id, message_id, success_text):
    is_registered = False
    try:
        # Check if user is already in bot's database
        served_users = await get_served_users()
        for u in served_users:
            uid = u.get("user_id") if isinstance(u, dict) else u
            if str(uid) == str(user_id):
                is_registered = True
                break
    except Exception as e:
        print(f"DB Check Error: {e}")
        # Agar db check fail ho jaye, toh safety ke liye button bhej denge
        is_registered = False

    run = await client.send_message(chat_id, success_text)
    
    # Agar registered NAHI hai, tabhi claim button bhejo
    if not is_registered:
        markup = [[{"text": f"💓 {smallcaps('Start in DM to Claim')}", "url": f"https://t.me/{app.username}?start=claim", "style": "success", "icon_custom_emoji_id": "6001132493011425597"}]]
        await inject_premium_markup(chat_id, run.id, markup)

@app.on_callback_query(filters.regex(r"^(emg|flg)_"))
async def guess_game_callback(client, callback_query):
    user = callback_query.from_user
    if await check_cooldown(user.id, callback_query): return

    data = callback_query.data.split("_")
    game_type, chat_id, selected_option = data[0], int(data[1]), data[2]
    
    if chat_id not in active_games: return await callback_query.answer(smallcaps("Game ended or expired!"), show_alert=True)
    game_data = active_games[chat_id]
    
    if (game_type == "emg" and game_data.get("type") != "emoji") or (game_type == "flg" and game_data.get("type") != "flag"):
         return await callback_query.answer(smallcaps("Invalid game interaction!"), show_alert=True)
         
    if selected_option == game_data["answer"]:
        time_taken = round(time.time() - game_data["start_time"], 1)
        points_won = 3 if game_type == "emg" else 5
        game_name_str = "emoji" if game_type == "emg" else game_data['name']
        
        success_text = f"🎉 **{smallcaps(f'The {game_name_str} was guessed correctly by')} {user.mention} {smallcaps(f'in {time_taken} seconds!')}**\n*+{points_won} {smallcaps('points')}*"
        
        del active_games[chat_id] 
        # Points are instantly saved, they are 100% safe!
        user_data = await game_db.find_one({"user_id": user.id})
        if user_data: await game_db.update_one({"user_id": user.id}, {"$set": {"points": user_data["points"] + points_won, "name": user.first_name}})
        else: await game_db.insert_one({"user_id": user.id, "name": user.first_name, "points": points_won})
            
        await callback_query.message.delete()
        await check_and_send_claim(client, chat_id, user.id, callback_query.message.id, success_text)
    else:
        user_cooldowns[user.id] = time.time()
        await callback_query.answer(f"❌ {smallcaps('Wrong answer! You have a 1-minute penalty.')}", show_alert=True)

@app.on_callback_query(filters.regex(r"^giveup_"))
async def giveup_callback(client, callback_query):
    data = callback_query.data.split("_")
    chat_id = int(data[1])
    
    if chat_id not in active_games or active_games[chat_id].get("type") != "word":
        return await callback_query.answer(smallcaps("Game already ended!"), show_alert=True)
        
    correct_word = active_games[chat_id]["answer"]
    del active_games[chat_id]
    await callback_query.message.delete()
    await client.send_message(chat_id, f"🏳️ **{smallcaps('Game Over!')}** {callback_query.from_user.mention} {smallcaps('gave up.')}\n\n{smallcaps('The correct word was:')} **{correct_word}**")

# ==========================================
#              COMMANDS & TRACKERS (OWNER ONLY FOR TEST)
# ==========================================

# 🔥 Added filters.user(config.OWNER_ID) so only you can trigger test games!
@app.on_message(filters.command("testword") & filters.group & filters.user(config.OWNER_ID))
async def test_word_cmd(client, message: Message):
    if message.from_user: await start_word_game(message.chat.id)

@app.on_message(filters.command("testemoji") & filters.group & filters.user(config.OWNER_ID))
async def test_emoji_cmd(client, message: Message):
    if message.from_user: await start_emoji_game(message.chat.id)
    
@app.on_message(filters.command("testflag") & filters.group & filters.user(config.OWNER_ID))
async def test_flag_cmd(client, message: Message):
    if message.from_user: await start_flag_game(message.chat.id)

@app.on_message(filters.group & ~filters.bot, group=10)
async def chat_activity_tracker(client, message: Message):
    chat_id = message.chat.id
    if not message.from_user: return
    user_id = message.from_user.id
    last_message_time[chat_id] = time.time()
    
    if chat_id in active_games and active_games[chat_id].get("type") == "word" and message.text:
        correct_word = active_games[chat_id]["answer"]
        if message.text.strip().upper() == correct_word:
            time_taken = round(time.time() - active_games[chat_id]["start_time"], 1)
            del active_games[chat_id] 
            try: await client.send_reaction(chat_id=chat_id, message_id=message.id, emoji="❤️")
            except: pass
                
            user_data = await game_db.find_one({"user_id": user_id})
            if user_data: await game_db.update_one({"user_id": user_id}, {"$set": {"points": user_data["points"] + 15, "name": message.from_user.first_name}})
            else: await game_db.insert_one({"user_id": user_id, "name": message.from_user.first_name, "points": 15})
            
            msg = (f"<emoji id='6334696528145286813'>⚡</emoji> **{smallcaps('How fast!')}** ({time_taken} {smallcaps('seconds')})\n"
                   f"<emoji id='6334471179801200139'>🎉</emoji> {message.from_user.mention} {smallcaps('guessed the word in record time!')}\n"
                   f"{smallcaps('Correct Word:')} **{correct_word}**\n*+15 {smallcaps('in the global game ranking')}*")
            
            await check_and_send_claim(client, chat_id, user_id, message.id, msg)

@app.on_message(filters.command(["wordleaderboard", "gametop"]) & filters.group)
async def word_leaderboard(client, message: Message):
    top_users = game_db.find().sort("points", -1).limit(10)
    text = f"<emoji id='6334381440754517833'>🏆</emoji> **{smallcaps('Mini-Game Global Leaderboard')}** <emoji id='6334381440754517833'>🏆</emoji>\n\n"
    count, has_users = 1, False
    async for user in top_users:
        has_users = True
        text += f"**{count}.** {smallcaps(user.get('name', 'Unknown User'))} - `{user['points']}` {smallcaps('points')}\n"
        count += 1
    if not has_users: text += smallcaps("No one has scored points yet! Wait for a game to start.")
    await message.reply_text(text)

async def inactivity_checker_loop():
    while True:
        await asyncio.sleep(60) 
        current_time = time.time()
        for chat_id, game_data in list(active_games.items()):
            if (current_time - game_data["start_time"]) > 600:
                try: await app.delete_messages(chat_id, game_data["message_id"])
                except: pass
                del active_games[chat_id]
                if chat_id in last_message_time: del last_message_time[chat_id]

        for chat_id, last_time in list(last_message_time.items()):
            if (current_time - last_time) > INACTIVITY_LIMIT and chat_id not in active_games:
                try:
                    warning = await app.send_message(chat_id, random.choice(WARNING_MESSAGES))
                    await asyncio.sleep(3)
                    await warning.delete()
                    game_choice = random.choice(["word", "emoji", "flag"])
                    if game_choice == "word": await start_word_game(chat_id)
                    elif game_choice == "emoji": await start_emoji_game(chat_id)
                    else: await start_flag_game(chat_id)
                except Exception: pass

asyncio.create_task(inactivity_checker_loop())
    

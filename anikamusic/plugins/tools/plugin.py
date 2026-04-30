import os
import sys
import aiohttp
import asyncio
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import config
from anikamusic import app

# Temporary storage for pending plugin installations
PENDING_PLUGINS = {}

@app.on_message(filters.command(["plugin", "install"], prefixes=["/", ".", "!"]) & filters.user(config.OWNER_ID))
async def install_plugin_cmd(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ **Usage:** `.plugin [Raw_GitHub_URL]`\n\n"
            "Example: `.plugin https://raw.githubusercontent.com/user/repo/main/Eco.py`"
        )
        
    url = message.command[1]
    
    if not url.startswith("https://raw.githubusercontent.com/") and not url.startswith("https://pastebin.com/raw/"):
        return await message.reply_text("❌ Please provide a valid **Raw GitHub** or **Raw Pastebin** URL!")

    # Extract filename from URL
    filename = url.split("/")[-1]
    if not filename.endswith(".py"):
        filename += ".py"
        
    msg = await message.reply_text("⏳ **Fetching plugin details...**")
    
    try:
        # Code ko pehle hi download kar lenge memory mein
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return await msg.edit_text(f"❌ **Failed to fetch code!** HTTP Status: {response.status}")
                
                code_content = await response.text()
    except Exception as e:
        return await msg.edit_text(f"❌ **Error fetching URL:**\n`{str(e)}`")
        
    # --- PARSE DETAILS FROM COMMENTS ---
    plugin_name = filename
    plugin_desc = "No details provided by the developer."
    
    # Code ki shuruati 30 lines check karenge
    for line in code_content.split("\n")[:30]:
        if line.startswith("# NAME:"):
            plugin_name = line.replace("# NAME:", "").strip()
        elif line.startswith("# DESC:"):
            plugin_desc = line.replace("# DESC:", "").strip()
            
    # Generate a unique task ID and Store Data
    task_id = str(message.id)
    PENDING_PLUGINS[task_id] = {
        "filename": filename,
        "code": code_content,
        "url": url
    }
    
    text = (
        "📦 **Plugin Installation Request**\n\n"
        f"🏷 **Name:** `{plugin_name}`\n"
        f"📄 **File:** `{filename}`\n"
        f"📝 **Details:** {plugin_desc}\n"
        f"🔗 **Source:** [View Code]({url})\n\n"
        "⚠️ *Note: If this file already exists, it will be overwritten (Updated).* \n"
        "Do you want to install and restart the bot?"
    )
    
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm & Install", callback_data=f"plg_yes_{task_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"plg_no_{task_id}")
        ]
    ])
    
    await msg.edit_text(text, reply_markup=markup, disable_web_page_preview=True)


@app.on_callback_query(filters.regex(r"^plg_(yes|no)_") & filters.user(config.OWNER_ID))
async def plugin_callback(client, query):
    action = query.matches[0].group(1)
    task_id = query.data.split("_")[-1]
    
    if task_id not in PENDING_PLUGINS:
        return await query.answer("This installation request has expired or is invalid.", show_alert=True)
        
    if action == "no":
        del PENDING_PLUGINS[task_id]
        return await query.message.edit_text("❌ **Plugin installation cancelled.**")
        
    # Proceed with installation
    plugin_data = PENDING_PLUGINS[task_id]
    code_content = plugin_data["code"]
    filename = plugin_data["filename"]
    
    # Path jahan file save hogi (tools folder mein)
    save_path = os.path.join("anikamusic", "plugins", "tools", filename)
    
    await query.message.edit_text(f"⏳ **Installing `{filename}`...**")
    
    try:
        # Save the file (Direct overwrite)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(code_content)
            
        del PENDING_PLUGINS[task_id]
        
        await query.message.edit_text(
            f"✅ **Plugin `{filename}` installed successfully!**\n\n"
            "🔄 Restarting bot to apply changes... Please wait 10-15 seconds."
        )
        
        # Bot Restart Logic
        os.execl(sys.executable, sys.executable, "-m", "anikamusic")
        
    except Exception as e:
        await query.message.edit_text(f"❌ **Error during installation:**\n`{str(e)}`")
          

import os
import future
import asyncio
import requests
import wget
import time
import aiohttp
import aiofiles
import yt_dlp
from urllib.parse import urlparse
from youtube_search import YoutubeSearch
from yt_dlp import YoutubeDL
from anikamusic import app, YouTube
from pyrogram import filters
from pyrogram import Client, filters
from pyrogram.types import Message
from youtubesearchpython import VideosSearch
from youtubesearchpython import SearchVideos
import re
from pykeyboard import InlineKeyboard
from pyrogram.enums import ChatAction
from pyrogram.types import (InlineKeyboardButton,
                            InlineKeyboardMarkup, InputMediaAudio,
                            InputMediaVideo, Message)

from config import (BANNED_USERS, SONG_DOWNLOAD_DURATION,
                    SONG_DOWNLOAD_DURATION_LIMIT)
from anikamusic.utils.decorators.language import language, languageCB
from anikamusic.utils.formatters import convert_bytes
from anikamusic.utils.inline.song import song_markup

# TERA DEFAULT THUMBNAIL
DEFAULT_THUMB = "https://files.catbox.moe/5f5clw.jpg"

# Command
SONG_COMMAND = ["song"]

@app.on_message(
    filters.command(SONG_COMMAND)
    & filters.group
    & ~BANNED_USERS
)
@language
async def song_commad_group(client, message: Message, _):
    upl = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=_["SG_B_1"],
                    url=f"https://t.me/{app.username}?start=song",
                ),
            ]
        ]
    )
    await message.reply_text(_["song_1"], reply_markup=upl)

# Song Module
@app.on_message(
    filters.command(SONG_COMMAND)
    & filters.private
    & ~BANNED_USERS
)
@language
async def song_commad_private(client, message: Message, _):
    await message.delete()
    url = await YouTube.url(message)
    if url:
        if not await YouTube.exists(url):
            return await message.reply_text(_["song_5"])
        mystic = await message.reply_text(_["play_1"])
        (
            title,
            duration_min,
            duration_sec,
            thumbnail, # Asli thumbnail ignore marenge aage
            vidid,
        ) = await YouTube.details(url)
        if str(duration_min) == "None":
            return await mystic.edit_text(_["song_3"])
        if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_4"].format(
                    SONG_DOWNLOAD_DURATION, duration_min
                )
            )
        buttons = song_markup(_, vidid)
        await mystic.delete()
        return await message.reply_photo(
            photo=DEFAULT_THUMB, # DEFAULT THUMBNAIL YAHAN LAGA DIYA
            has_spoiler=True,    # SPOILER EFFECT YAHAN LAGA DIYA
            caption=_["song_4"].format(title),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        if len(message.command) < 2:
            return await message.reply_text(_["song_2"])
    mystic = await message.reply_text(_["play_1"])
    query = message.text.split(None, 1)[1]
    try:
        (
            title,
            duration_min,
            duration_sec,
            thumbnail,
            vidid,
        ) = await YouTube.details(query)
    except:
        return await mystic.edit_text(_["play_3"])
    if str(duration_min) == "None":
        return await mystic.edit_text(_["song_3"])
    if int(duration_sec) > SONG_DOWNLOAD_DURATION_LIMIT:
        return await mystic.edit_text(
            _["play_6"].format(SONG_DOWNLOAD_DURATION, duration_min)
        )
    buttons = song_markup(_, vidid)
    await mystic.delete()
    return await message.reply_photo(
        photo=DEFAULT_THUMB, # DEFAULT THUMBNAIL YAHAN LAGA DIYA
        has_spoiler=True,    # SPOILER EFFECT YAHAN LAGA DIYA
        caption=_["song_4"].format(title),
        reply_markup=InlineKeyboardMarkup(buttons),
    )

@app.on_callback_query(
    filters.regex(pattern=r"song_back") & ~BANNED_USERS
)
@languageCB
async def songs_back_helper(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    buttons = song_markup(_, vidid)
    return await CallbackQuery.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(
    filters.regex(pattern=r"song_helper") & ~BANNED_USERS
)
@languageCB
async def song_helper_cb(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, vidid = callback_request.split("|")
    try:
        await CallbackQuery.answer(_["song_6"], show_alert=True)
    except:
        pass
    if stype == "audio":
        try:
            formats_available, link = await YouTube.formats(vidid, True)
        except:
            return await CallbackQuery.edit_message_text(_["song_7"])
        keyboard = InlineKeyboard()
        done = []
        for x in formats_available:
            check = x["format"]
            if "audio" in check:
                if x["filesize"] is None:
                    continue
                form = x["format_note"].title()
                if form not in done:
                    done.append(form)
                else:
                    continue
                sz = convert_bytes(x["filesize"])
                fom = x["format_id"]
                keyboard.row(
                    InlineKeyboardButton(
                        text=f"{form} Quality Audio = {sz}",
                        callback_data=f"song_download {stype}|{fom}|{vidid}",
                    ),
                )
        keyboard.row(
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data=f"song_back {stype}|{vidid}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data=f"close"
            ),
        )
        return await CallbackQuery.edit_message_reply_markup(reply_markup=keyboard)
    else:
        try:
            formats_available, link = await YouTube.formats(vidid, True)
        except Exception as e:
            print(e)
            return await CallbackQuery.edit_message_text(_["song_7"])
        keyboard = InlineKeyboard()
        done = [160, 133, 134, 135, 136, 137, 298, 299, 264, 304, 266]
        for x in formats_available:
            check = x["format"]
            if x["filesize"] is None:
                continue
            if int(x["format_id"]) not in done:
                continue
            sz = convert_bytes(x["filesize"])
            ap = check.split("-")[1]
            to = f"{ap} = {sz}"
            keyboard.row(
                InlineKeyboardButton(
                    text=to,
                    callback_data=f"song_download {stype}|{x['format_id']}|{vidid}",
                )
            )
        keyboard.row(
            InlineKeyboardButton(
                text=_["BACK_BUTTON"],
                callback_data=f"song_back {stype}|{vidid}",
            ),
            InlineKeyboardButton(
                text=_["CLOSE_BUTTON"], callback_data=f"close"
            ),
        )
        return await CallbackQuery.edit_message_reply_markup(reply_markup=keyboard)


# 🚀 TERA YUKI API IMPLEMENTATION YAHAN HAI 🚀
@app.on_callback_query(
    filters.regex(pattern=r"song_download") & ~BANNED_USERS
)
@languageCB
async def song_download_cb(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer("Downloading from YUKI API...")
    except:
        pass
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    stype, format_id, vidid = callback_request.split("|")
    mystic = await CallbackQuery.edit_message_text("🔄 Requesting YUKI API for fast stream...")
    
    # Title nikalne ke liye YouTube details (API format ke liye title zaroori hota hai upload mein)
    try:
        (title, _, _, _, _) = await YouTube.details(vidid)
        title = re.sub("\W+", " ", title).title()
    except:
        title = "YUKI_Music_Track"

    ext = "mp3" if stype == "audio" else "mp4"
    file_path = f"downloads/{vidid}.{ext}"
    os.makedirs("downloads", exist_ok=True)

    try:
        # 1. YUKI API se Token Mangwana
        async with aiohttp.ClientSession() as session:
            token_url = f"https://yukiapi.site/download?url={vidid}&type={stype}"
            async with session.get(token_url) as resp:
                data = await resp.json()
                token = data.get("download_token")
                
            if not token:
                return await mystic.edit_text("❌ YUKI API Error: Token nahi mila!")

            await mystic.edit_text("⚡ Downloading at God Speed from YUKI API...")

            # 2. Token use karke gaana bot server pe lana
            stream_url = f"https://yukiapi.site/stream/{vidid}?type={stype}&token={token}"
            async with session.get(stream_url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(file_path, mode='wb')
                    await f.write(await resp.read())
                    await f.close()
                else:
                    return await mystic.edit_text("❌ YUKI API Streaming Error!")
    except Exception as e:
        return await mystic.edit_text(f"❌ API Connection Error: {e}")

    # 3. File Telegram pe upload karna
    await mystic.edit_text(_["song_11"])
    
    if stype == "video":
        await app.send_chat_action(
            chat_id=CallbackQuery.message.chat.id,
            action=ChatAction.UPLOAD_VIDEO,
        )
        med = InputMediaVideo(
            media=file_path,
            thumb=DEFAULT_THUMB,
            caption=title,
            supports_streaming=True,
        )
    else:
        await app.send_chat_action(
            chat_id=CallbackQuery.message.chat.id,
            action=ChatAction.UPLOAD_AUDIO,
        )
        med = InputMediaAudio(
            media=file_path,
            caption=title,
            thumb=DEFAULT_THUMB,
            title=title,
            performer="YUKI API"
        )
        
    try:
        await CallbackQuery.edit_message_media(media=med)
    except Exception as e:
        print(e)
        return await mystic.edit_text(_["song_10"])
        
    # Cache clear from local bot server (Yuki API pe toh saved rahega hi)
    if os.path.exists(file_path):
        os.remove(file_path)


# Instagram Reels Module
@app.on_message(filters.command(["ig"], ["/", "!", "."]))
async def download_instareels(c: app, m: Message):
    try:
        reel_ = m.command[1]
    except IndexError:
        await m.reply_text("Give me an link to download it...")
        return
    if not reel_.startswith("https://www.instagram.com/reel/"):
        await m.reply_text("In order to obtain the requested reel, a valid link is necessary. Kindly provide me with the required link.")
        return
    OwO = reel_.split(".",1)
    Reel_ = ".dd".join(OwO)
    try:
        await m.reply_video(Reel_)
        return
    except Exception:
        try:
            await m.reply_photo(Reel_)
            return
        except Exception:
            try:
                await m.reply_document(Reel_)
                return
            except Exception:
                await m.reply_text("I am unable to reach to this reel.")

@app.on_message(filters.command(["reel"], ["/", "!", "."]))
async def instagram_reel(client, message):
    if len(message.command) == 2:
        url = message.command[1]
        response = requests.post(f"https://lexica-api.vercel.app/download/instagram?url={url}")
        data = response.json()

        if data['code'] == 2:
            media_urls = data['content']['mediaUrls']
            if media_urls:
                video_url = media_urls[0]['url']
                await message.reply_video(f"{video_url}")
            else:
                await message.reply("No video found in the response. may be accountbis private.")
        else:
            await message.reply("Request was not successful.")
    else:
        await message.reply("Please provide a valid Instagram URL using the /reels command.")
              

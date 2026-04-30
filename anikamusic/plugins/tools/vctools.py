import asyncio
from typing import Optional
from random import randint
from pyrogram.types import Message, ChatPrivileges, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.messages import GetFullChat
from pyrogram.raw.types import InputGroupCall, InputPeerChannel, InputPeerChat
from anikamusic.utils.database import *
from pyrogram.raw.functions.phone import CreateGroupCall, DiscardGroupCall, EditGroupCallTitle
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant, ChatAdminRequired
from anikamusic import app, Userbot
from typing import List, Union
from anikamusic.core.call import ANIKA
from pyrogram.types import VideoChatEnded
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.exceptions import (NoActiveGroupCall, TelegramServerError, AlreadyJoinedError)

# ==================================================
# 🔥 VC SOUND STATE & VOLUME BAR TRACKER 🔥
# ==================================================
vc_data = {}

def get_sound_panel(chat_id):
    data = vc_data.get(chat_id, {"vol": 100, "muted": False})
    mute_text = "🔊 ᴜɴᴍᴜᴛᴇ" if data["muted"] else "🔇 ᴍᴜᴛᴇ"
    mute_btn = InlineKeyboardButton(mute_text, callback_data=f"vc_mute_{chat_id}")
    return InlineKeyboardMarkup([
        [mute_btn],
        [
            InlineKeyboardButton("➖", callback_data=f"vc_voldn_{chat_id}"),
            InlineKeyboardButton(f"🔈 {data['vol']}%", callback_data="vc_noop"),
            InlineKeyboardButton("➕", callback_data=f"vc_volup_{chat_id}")
        ]
    ])

def generate_vol_bar(vol):
    filled = vol // 20
    empty = 10 - filled
    return "▰" * filled + "▱" * empty


@app.on_message(filters.command(["vcinfo"], ["/", "!"]))
async def strcall(client, message):
    assistant = await group_assistant(ANIKA, message.chat.id)
    try:
        await assistant.join_group_call(message.chat.id, AudioPiped("./anikamusic/assets/call.mp3"), stream_type=StreamType().pulse_stream)
        text = "<blockquote><emoji id='6334598469746952256'>🫶</emoji> ʙᴇʟᴏᴠᴇᴅꜱ ɪɴ ᴛʜᴇ ᴄᴀʟʟ :\n\n"
        participants = await assistant.get_participants(message.chat.id)
        k = 0
        for participant in participants:
            info = participant
            if info.muted == False:
                mut = "ꜱᴘᴇᴀᴋɪɴɢ 🗣 "
            else:
                mut = "ᴍᴜᴛᴇᴅ 🔕 "
            user = await client.get_users(participant.user_id)
            k += 1
            text += f"{k} ➤ {user.mention} ➤ {mut}\n"
        text += f"\n<emoji id='6334672948774831861'>📈</emoji> ɴᴜᴍʙᴇʀ ᴏꜰ ᴘᴀʀᴛɪᴄɪᴘᴀɴᴛꜱ : {len(participants)}</blockquote>"
        await message.reply(f"{text}")
        await asyncio.sleep(7)
        await assistant.leave_group_call(message.chat.id)
    except NoActiveGroupCall:
        await message.reply("<blockquote><emoji id='6334648089504122382'>❌</emoji> ᴛʜᴇ ᴄᴀʟʟ ɪꜱ ɴᴏᴛ ᴏᴘᴇɴ ᴀᴛ ᴀʟʟ</blockquote>")
    except TelegramServerError:
        await message.reply("<blockquote><emoji id='6334333036473091884'>⚠️</emoji> ꜱᴇɴᴅ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ ᴀɢᴀɪɴ, ᴛʜᴇʀᴇ ɪꜱ ᴀ ᴘʀᴏʙʟᴇᴍ ᴡɪᴛʜ ᴛʜᴇ ᴛᴇʟᴇɢʀᴀᴍ ꜱᴇʀᴠᴇʀ</blockquote>")
    except AlreadyJoinedError:
        text = "<blockquote><emoji id='6334598469746952256'>🫶</emoji> ʙᴇʟᴏᴠᴇᴅꜱ ɪɴ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ :\n\n"
        participants = await assistant.get_participants(message.chat.id)
        k = 0
        for participant in participants:
            info = participant
            if info.muted == False:
                mut = "ꜱᴘᴇᴀᴋɪɴɢ 🗣"
            else:
                mut = "ᴍᴜᴛᴇᴅ 🔕 "
            user = await client.get_users(participant.user_id)
            k += 1
            text += f"{k} ➤ {user.mention} ➤ {mut}\n"
        text += f"\n<emoji id='6334672948774831861'>📈</emoji> ɴᴜᴍʙᴇʀ ᴏꜰ ᴘᴀʀᴛɪᴄɪᴘᴀɴᴛꜱ : {len(participants)}</blockquote>"
        await message.reply(f"{text}")


other_filters = filters.group  & ~filters.via_bot & ~filters.forwarded
other_filters2 = (
    filters.private  & ~filters.via_bot & ~filters.forwarded
)


def command(commands: Union[str, List[str]]):
    return filters.command(commands, "")


async def get_group_call(
    client: Client, message: Message, err_msg: str = ""
) -> Optional[InputGroupCall]:
    assistant = await get_assistant(message.chat.id)
    chat_peer = await assistant.resolve_peer(message.chat.id)
    if isinstance(chat_peer, (InputPeerChannel, InputPeerChat)):
        if isinstance(chat_peer, InputPeerChannel):
            full_chat = (
                await assistant.invoke(GetFullChannel(channel=chat_peer))
            ).full_chat
        elif isinstance(chat_peer, InputPeerChat):
            full_chat = (
                await assistant.invoke(GetFullChat(chat_id=chat_peer.chat_id))
            ).full_chat
        if full_chat is not None:
            return full_chat.call
    await app.send_message(message.chat.id, f"<blockquote><emoji id='6334648089504122382'>❌</emoji> ɴᴏ ɢʀᴏᴜᴘ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ꜰᴏᴜɴᴅ** {err_msg}</blockquote>")
    return False


@app.on_message(filters.command(["vcstart","startvc"], ["/", "!"]))
async def start_group_call(c: Client, m: Message):
    chat_id = m.chat.id
    assistant = await get_assistant(chat_id)
    ass = await assistant.get_me()
    assid = ass.id
    if assistant is None:
        await app.send_message(chat_id, "<blockquote><emoji id='6334333036473091884'>⚠️</emoji> ᴇʀʀᴏʀ ᴡɪᴛʜ ᴀꜱꜱɪꜱᴛᴀɴᴛ</blockquote>")
        return
    msg = await app.send_message(chat_id, "<blockquote><emoji id='6334696528145286813'>⏳</emoji> ꜱᴛᴀʀᴛɪɴɢ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ..</blockquote>")
    try:
        peer = await assistant.resolve_peer(chat_id)
        await assistant.invoke(
            CreateGroupCall(
                peer=InputPeerChannel(
                    channel_id=peer.channel_id,
                    access_hash=peer.access_hash,
                ),
                random_id=assistant.rnd_id() // 9000000000,
            )
        )
        await msg.edit_text("<blockquote><emoji id='6334789677396002338'>✨</emoji> ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ~!</blockquote>")
    except ChatAdminRequired:
      try:    
        await app.promote_chat_member(chat_id, assid, privileges=ChatPrivileges(
                can_manage_chat=False,
                can_delete_messages=False,
                can_manage_video_chats=True,
                can_restrict_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_promote_members=False,
            ),
        )
        peer = await assistant.resolve_peer(chat_id)
        await assistant.invoke(
            CreateGroupCall(
                peer=InputPeerChannel(
                    channel_id=peer.channel_id,
                    access_hash=peer.access_hash,
                ),
                random_id=assistant.rnd_id() // 9000000000,
            )
        )
        await app.promote_chat_member(chat_id, assid, privileges=ChatPrivileges(
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_promote_members=False,
            ),
        )                              
        await msg.edit_text("<blockquote><emoji id='6334789677396002338'>✨</emoji> ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ~!</blockquote>")
      except:
         await msg.edit_text("<blockquote><emoji id='6334471179801200139'>⚠️</emoji> ɢɪᴠᴇ ᴛʜᴇ ʙᴏᴛ ᴀʟʟ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ</blockquote>")


@app.on_message(filters.command(["vcend","endvc"], ["/", "!"]))
async def stop_group_call(c: Client, m: Message):
    chat_id = m.chat.id
    assistant = await get_assistant(chat_id)
    ass = await assistant.get_me()
    assid = ass.id
    if assistant is None:
        await app.send_message(chat_id, "<blockquote><emoji id='6334333036473091884'>⚠️</emoji> ᴇʀʀᴏʀ ᴡɪᴛʜ ᴀꜱꜱɪꜱᴛᴀɴᴛ</blockquote>")
        return
    msg = await app.send_message(chat_id, "<blockquote><emoji id='6334696528145286813'>⏳</emoji> ᴄʟᴏꜱɪɴɢ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ..</blockquote>")
    try:
        if not (
           group_call := (
               await get_group_call(assistant, m, err_msg=", ɢʀᴏᴜᴘ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴀʟʀᴇᴀᴅʏ ᴇɴᴅᴇᴅ")
           )
        ):  
           return
        await assistant.invoke(DiscardGroupCall(call=group_call))
        await msg.edit_text("<blockquote><emoji id='6334381440754517833'>✨</emoji> ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴄʟᴏꜱᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ~!</blockquote>")
    except Exception as e:
      if "GROUPCALL_FORBIDDEN" in str(e):
       try:    
         await app.promote_chat_member(chat_id, assid, privileges=ChatPrivileges(
                can_manage_chat=False,
                can_delete_messages=False,
                can_manage_video_chats=True,
                can_restrict_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_promote_members=False,
             ),
         )
         if not (
           group_call := (
               await get_group_call(assistant, m, err_msg=", ɢʀᴏᴜᴘ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴀʟʀᴇᴀᴅʏ ᴇɴᴅᴇᴅ")
           )
         ):  
           return
         await assistant.invoke(DiscardGroupCall(call=group_call))
         await app.promote_chat_member(chat_id, assid, privileges=ChatPrivileges(
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_promote_members=False,
            ),
         )                              
         await msg.edit_text("<blockquote><emoji id='6334381440754517833'>✨</emoji> ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴄʟᴏꜱᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ~!</blockquote>")
       except:
         await msg.edit_text("<blockquote><emoji id='6334471179801200139'>⚠️</emoji> ɢɪᴠᴇ ᴛʜᴇ ʙᴏᴛ ᴀʟʟ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ</blockquote>")


# ==================================================
# 🔥 NEW FEATURE: SET VC NAME (VC Title Changer) 🔥
# ==================================================
@app.on_message(filters.command(["setvcname", "vctag", "vcname"], ["/", ".", "!"]))
async def set_vc_name_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("<blockquote><emoji id='6334648089504122382'>❌</emoji> ʙʜᴀɪ, ᴠᴄ ᴋᴀ ɴᴀʏᴀ ɴᴀᴀᴍ ʙʜɪ ᴛᴏʜ ʙᴀᴛᴀ!\n**ᴇxᴀᴍᴘʟᴇ:** `/vctag 🍷 ʟᴀᴛᴇ ɴɪɢʜᴛ ᴠɪʙᴇꜱ`</blockquote>")
    
    chat_id = message.chat.id
    title = message.text.split(None, 1)[1]
        
    msg = await message.reply("<blockquote><emoji id='6334696528145286813'>⏳</emoji> ᴄʜᴀɴɢɪɴɢ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴛɪᴛʟᴇ..</blockquote>")
    try:
        peer = await client.resolve_peer(chat_id)
        if isinstance(peer, InputPeerChannel):
            full_chat = (await client.invoke(GetFullChannel(channel=peer))).full_chat
        elif isinstance(peer, InputPeerChat):
            full_chat = (await client.invoke(GetFullChat(chat_id=peer.chat_id))).full_chat
        else:
            return await msg.edit_text("<blockquote><emoji id='6334648089504122382'>❌</emoji> ʏᴇ ɢʀᴏᴜᴘ ᴠᴀʟɪᴅ ɴᴀʜɪ ʜᴀɪ.</blockquote>")
            
        if not full_chat or not full_chat.call:
            return await msg.edit_text("<blockquote><emoji id='6334648089504122382'>❌</emoji> ᴘᴇʜʟᴇ ᴠᴄ ᴛᴏʜ ᴄʜᴀʟᴜ ᴋᴀʀ ʟᴇ ʙʜᴀɪ!</blockquote>")
            
        group_call = full_chat.call
        
        await client.invoke(EditGroupCallTitle(call=group_call, title=title))
        await msg.edit_text(f"<blockquote><emoji id='6334381440754517833'>✨</emoji> ᴠᴄ ᴛɪᴛʟᴇ ꜱᴇᴛ ᴛᴏ:\n**{title}**</blockquote>")
    except ChatAdminRequired:
        await msg.edit_text("<blockquote><emoji id='6334471179801200139'>⚠️</emoji> ʙʜᴀɪ, **ᴍᴀɪɴ ʙᴏᴛ** ᴋᴏ 'ᴍᴀɴᴀɢᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛꜱ' ᴋɪ ᴘᴇʀᴍɪꜱꜱɪᴏɴ ᴅᴇ ᴘᴇʜʟᴇ! ᴀꜱꜱɪꜱᴛᴀɴᴛ ᴋɪ ᴢᴀʀᴏᴏʀᴀᴛ ɴᴀʜɪ ʜᴀɪ ᴀʙ.</blockquote>")
    except Exception as e:
        await msg.edit_text(f"<blockquote><emoji id='6334648089504122382'>❌</emoji> ᴇʀʀᴏʀ ᴀᴀɢᴀʏᴀ: {e}</blockquote>")


# ==================================================
# 🔥 NEW FEATURE: SOUND CONTROL PANEL 🔥
# ==================================================
@app.on_message(filters.command(["sound"], ["/", ".", "!"]))
async def sound_panel_cmd(client: Client, message: Message):
    chat_id = message.chat.id
    vol = vc_data.get(chat_id, {"vol": 100})["vol"]
    bar = generate_vol_bar(vol)
    text = f"<blockquote><emoji id='6334598469746952256'>🎛</emoji> **ᴠᴄ ꜱᴏᴜɴᴅ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ**\n\n<emoji id='6334672948774831861'>🔊</emoji> ᴠᴏʟᴜᴍᴇ: {vol}%\n{bar}</blockquote>"
    await message.reply(text, reply_markup=get_sound_panel(chat_id))


@app.on_callback_query(filters.regex(r"^vc_"))
async def vc_sound_callback(client: Client, cq: CallbackQuery):
    data = cq.data.split("_")
    action = data[1]
    
    if action == "noop":
        return await cq.answer("ʏᴇ ʙᴜᴛᴛᴏɴ ʙᴀꜱ ᴄᴜʀʀᴇɴᴛ ᴠᴏʟᴜᴍᴇ ᴅɪᴋʜᴀɴᴇ ᴋᴇ ʟɪʏᴇ ʜᴀɪ ʙʜᴀɪ! 👀", show_alert=True)
        
    chat_id = int(data[2])
    if cq.message.chat.id != chat_id:
        return await cq.answer("ʙʜᴀɪ ʏᴇ ᴘᴀɴᴇʟ ɪꜱ ᴄʜᴀᴛ ᴋᴀ ɴᴀʜɪ ʜᴀɪ!", show_alert=True)
        
    if chat_id not in vc_data:
        vc_data[chat_id] = {"vol": 100, "muted": False}
        
    state = vc_data[chat_id]
    
    try:
        if action == "mute":
            if state["muted"]:
                await ANIKA.unmute_stream(chat_id)
                state["muted"] = False
                await cq.answer("ᴠᴄ ᴜɴᴍᴜᴛᴇᴅ! ᴀᴀᴡᴀᴢ ᴀᴀʏᴇɢɪ ᴀʙ 🔊")
            else:
                await ANIKA.mute_stream(chat_id)
                state["muted"] = True
                await cq.answer("ᴠᴄ ᴍᴜᴛᴇᴅ! ꜱʜᴀᴀɴᴛɪ 🔇")
                
        elif action == "volup":
            if state["vol"] >= 200:
                return await cq.answer("ʙʜᴀɪ ꜰᴜʟʟ ᴀᴀᴡᴀᴢ ʜᴀɪ, ꜱᴘᴇᴀᴋᴇʀ ꜰᴀᴀᴅᴇɢᴀ ᴋʏᴀ? 🙉", show_alert=True)
            state["vol"] = min(200, state["vol"] + 10)
            await ANIKA.change_volume_call(chat_id, state["vol"])
            await cq.answer(f"ᴠᴏʟᴜᴍᴇ ʙᴀᴅʜᴀ ᴅɪ: {state['vol']}% 📈")
            
        elif action == "voldn":
            if state["vol"] <= 10:
                return await cq.answer("ɪꜱꜱᴇ ᴋᴀᴍ ᴍᴇ ɢʜᴀɴᴛᴀ ᴋᴜᴄʜ ɴᴀʜɪ ꜱᴜɴᴀɪ ᴅᴇɢᴀ! 📉", show_alert=True)
            state["vol"] = max(10, state["vol"] - 10)
            await ANIKA.change_volume_call(chat_id, state["vol"])
            await cq.answer(f"ᴠᴏʟᴜᴍᴇ ᴋᴀᴍ ᴋᴀʀ ᴅɪ: {state['vol']}% 📉")

        vol = state["vol"]
        bar = generate_vol_bar(vol)
        text = f"<blockquote><emoji id='6334598469746952256'>🎛</emoji> **ᴠᴄ ꜱᴏᴜɴᴅ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ**\n\n<emoji id='6334672948774831861'>🔊</emoji> ᴠᴏʟᴜᴍᴇ: {vol}%\n{bar}</blockquote>"
        
        await cq.message.edit_text(text, reply_markup=get_sound_panel(chat_id))
        
    except NoActiveGroupCall:
        await cq.answer("ʙʜᴀɪ ᴘᴇʜʟᴇ ᴠᴄ ᴍᴇ ɢᴀᴀɴᴀ ᴛᴏʜ ᴘʟᴀʏ ᴋᴀʀ ʟᴇ! 🤦‍♂️", show_alert=True)
    except Exception as e:
        await cq.answer(f"ᴛʜᴏᴅᴀ ᴡᴀɪᴛ ᴋᴀʀ ʏᴀ ᴇʀʀᴏʀ ᴅᴇᴋʜ: {str(e)[:50]}", show_alert=True)
        

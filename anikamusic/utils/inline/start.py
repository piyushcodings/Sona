import config
from anikamusic import app

# 🔥 HELLFIRE DEVS HACK: Raw API Button Generator
def api_btn(text, callback_data=None, url=None, style=None, custom_emoji_id=None):
    btn = {"text": text}
    if callback_data:
        btn["callback_data"] = callback_data
    if url:
        url_str = str(url)
        if not url_str.startswith("http") and not url_str.startswith("tg://"):
            url_str = f"https://t.me/{url_str.replace('@', '')}"
        btn["url"] = url_str
        
    if style in ["primary", "danger", "success"]:
        btn["style"] = style  
        
    if custom_emoji_id:
        btn["icon_custom_emoji_id"] = str(custom_emoji_id) 
    return btn


def start_panel(_):
    buttons = [
        [
            # Add to Group (Blue)
            api_btn(
                text=_["S_B_1"], 
                url=f"https://t.me/{app.username}?startgroup=true", 
                style="success", 
                custom_emoji_id="6001132493011425597"
            ),
            # Support Chat (Red)
            api_btn(
                text=_["S_B_2"], 
                url=config.SUPPORT_CHAT, 
                style="danger", 
                custom_emoji_id="5999100917645841519"
            ),
        ],
    ]
    return buttons


def private_panel(_):
    safe_owner_id = config.OWNER_ID[0] if isinstance(config.OWNER_ID, list) else config.OWNER_ID
    
    buttons = [
        [
            # Add to Group (Blue)
            api_btn(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true",
                style="success",
                custom_emoji_id="6080202089311507876"
            )
        ],
        [
            # Settings/Help (Green/Primary)
            api_btn(
                text=_["S_B_4"], 
                callback_data="settings_back_helper", 
                style="primary", 
                custom_emoji_id="6080176744709495278"
            ),
            # Version Button (Blue) - Changed from Mimi Tunes
            api_btn(
                text="˹ᴠᴇʀsɪᴏɴ˼♪", 
                callback_data="yuki_version_info", 
                style="primary", 
                custom_emoji_id="5413840936994097463"
            ),
        ],
        [
            # Updates/Channel (Blue)
            api_btn(
                text=_["S_B_6"], 
                url=config.SUPPORT_CHANNEL, 
                style="primary", 
                custom_emoji_id="5415586682286128590"
            ),
            # Support Chat (Red)
            api_btn(
                text=_["S_B_2"], 
                url=config.SUPPORT_CHAT, 
                style="danger", 
                custom_emoji_id="5413415116756500503"
            ),
        ],
        [
            # Owner (Red)
            api_btn(
                text=_["S_B_5"], 
                url=f"tg://user?id={safe_owner_id}", 
                style="danger", 
                custom_emoji_id="5413546177683539369"
            ),
        ],
    ]
    return buttons
    

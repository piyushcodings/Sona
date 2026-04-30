from typing import Union
from anikamusic import app
from anikamusic.utils.formatters import time_to_seconds

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


def queue_markup(
    _,
    DURATION,
    CPLAY,
    videoid,
    played: Union[bool, int] = None,
    dur: Union[bool, int] = None,
):
    not_dur = [
        [
            # Get Queued Button (Blue + 💖)
            api_btn(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}",
                style="primary",
                custom_emoji_id="6001132493011425597"
            ),
            # Close Button (Red + 💀)
            api_btn(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
                style="danger",
                custom_emoji_id="5999100917645841519"
            ),
        ]
    ]
    dur_buttons = [
        [
            # Timer Button (Green + 😉)
            api_btn(
                text=_["QU_B_2"].format(played, dur),
                callback_data="GetTimer",
                style="success",
                custom_emoji_id="6080189526532167993"
            )
        ],
        [
            # Get Queued Button (Blue + 💖)
            api_btn(
                text=_["QU_B_1"],
                callback_data=f"GetQueued {CPLAY}|{videoid}",
                style="primary",
                custom_emoji_id="6001132493011425597"
            ),
            # Close Button (Red + 💀)
            api_btn(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
                style="danger",
                custom_emoji_id="5999100917645841519"
            ),
        ],
    ]
    # 🔥 HACK: InlineKeyboardMarkup hata diya hai, ab ye raw list return karega API ke liye
    return not_dur if DURATION == "Unknown" else dur_buttons


def queue_back_markup(_, CPLAY):
    upl = [
        [
            # Back Button (Blue + 🐾)
            api_btn(
                text=_["BACK_BUTTON"],
                callback_data=f"queue_back_timer {CPLAY}",
                style="primary",
                custom_emoji_id="6080176744709495278"
            ),
            # Close Button (Red + 💀)
            api_btn(
                text=_["CLOSE_BUTTON"],
                callback_data="close",
                style="danger",
                custom_emoji_id="5999100917645841519"
            ),
        ]
    ]
    return upl


def aq_markup(_, chat_id):
    buttons = [
        [
            # Resume (Green)
            api_btn(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style="success"),
            # Pause (Blue)
            api_btn(text="II", callback_data=f"ADMIN Pause|{chat_id}", style="primary"),
            # Skip (Blue)
            api_btn(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style="primary"),
            # Stop (Red)
            api_btn(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style="danger"),
        ],
        [
            # Close (Red + 💀)
            api_btn(
                text=_["CLOSE_BUTTON"], 
                callback_data="close", 
                style="danger", 
                custom_emoji_id="5999100917645841519"
            )
        ],
    ]
    return buttons
    

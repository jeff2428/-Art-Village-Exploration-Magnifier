"""Application configuration and static catalogue data."""

import os
import streamlit as st

# ==========================================
# 系統常數與設定 (Config & Constants)
# ==========================================


def _read_streamlit_secret(key):
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError, RuntimeError):
        return None


PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY") or _read_streamlit_secret("PLANTNET_API_KEY") or ""
REQUEST_TIMEOUT_SECONDS = (3.05, 12)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})

# 藝素村動物圖鑑資料庫
ANIMALS_DB = {
    "貝貝": {"type": "dog", "emoji": "🐶", "desc": "映澄最心愛的米克斯母狗，也是藝素村最溫柔的導嚮員。"},
    "牧耳": {"type": "dog", "emoji": "🐕", "desc": "充滿活力的夥伴，最喜歡在東北角的草地上奔跑。"},
    "小飛俠": {"type": "cat", "emoji": "🐈", "desc": "身手矯健，總是在屋頂上觀察探險家們。"},
    "嘿皮": {"type": "cat", "emoji": "🐈‍⬛", "desc": "個性大方的黑貓，討摸是牠的日常。"},
    "冬瓜": {"type": "cat", "emoji": "🐱", "desc": "圓滾滾的橘貓，是村裡的慵懶大王。"}
}

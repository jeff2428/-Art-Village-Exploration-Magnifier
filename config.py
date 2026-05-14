# config.py
import streamlit as st

# ==========================================
# 系統常數與設定 (Config & Constants)
# ==========================================
# 建議將金鑰放在 Streamlit Secrets，若本地測試可直接填入字串
try:
    PLANTNET_API_KEY = st.secrets["PLANTNET_API_KEY"]
except KeyError:
    PLANTNET_API_KEY = "2b1004UqTrbWJn4mj5hqcaZN" # 替換為您的 API KEY

# 藝素村動物圖鑑資料庫
ANIMALS_DB = {
    "貝貝": {"type": "dog", "emoji": "🐶", "desc": "映澄最心愛的米克斯母狗，也是藝素村最溫柔的導嚮員。"},
    "牧耳": {"type": "dog", "emoji": "🐕", "desc": "充滿活力的夥伴，最喜歡在東北角的草地上奔跑。"},
    "小飛俠": {"type": "cat", "emoji": "🐈", "desc": "身手矯健，總是在屋頂上觀察探險家們。"},
    "嘿皮": {"type": "cat", "emoji": "🐈‍⬛", "desc": "個性大方的黑貓，討摸是牠的日常。"},
    "冬瓜": {"type": "cat", "emoji": "🐱", "desc": "圓滾滾的橘貓，是村裡的慵懶大王。"}
}

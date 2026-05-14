# config.py
import streamlit as st

# 安全讀取 API Key
PLANTNET_API_KEY = st.secrets["PLANTNET_API_KEY"]

ANIMALS_DB = {
    "貝貝": {"type": "dog", "emoji": "🐶", "desc": "映澄最心愛的米克斯母狗..."},
    # ... 其他動物
}

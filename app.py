# app.py
from html import escape
from pathlib import Path

import streamlit as st
from config import ANIMALS_DB
from api_handler import identify_plant_from_api


BASE_DIR = Path(__file__).resolve().parent


# 讀取獨立的 CSS 檔案
def load_local_css(file_name):
    css_path = BASE_DIR / file_name
    with css_path.open("r", encoding="utf-8") as f:
        st.markdown(f"<style>\n{f.read()}\n</style>", unsafe_allow_html=True)


def safe_text(value, default="N/A"):
    return escape(str(value if value not in (None, "") else default), quote=True)


def render_result_card(title, description, icon="🌱", meta_html=""):
    st.markdown(
        f"""
        <section class="result-card" aria-label="{safe_text(title)}">
            <h2>{safe_text(icon)} {safe_text(title)}</h2>
            {meta_html}
            <p>{safe_text(description)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("🌿 探險圖鑑詳情")
def show_detail_dialog(item_data):
    meta_html = f"""
        <dl class="detail-list">
            <div><dt>英文名稱</dt><dd>{safe_text(item_data.get('eng_name'))}</dd></div>
            <div><dt>拉丁學名</dt><dd><i>{safe_text(item_data.get('sci_name'))}</i></dd></div>
        </dl>
    """
    render_result_card(
        item_data.get("zh_name", "未知生物"),
        item_data.get("desc", ""),
        item_data.get("emoji", "🌱"),
        meta_html,
    )

def init_session_state():
    if 'pokedex' not in st.session_state:
        st.session_state.pokedex = {}
    if 'active_pet' not in st.session_state:
        st.session_state.active_pet = None

def main():
    st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")
    
    # 載入外部 CSS
    load_local_css("style.css")
    init_session_state()

    st.markdown("<h1>探險放大鏡 🔍</h1>", unsafe_allow_html=True)

    mode = st.radio("探索模式", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True, label_visibility="collapsed")

    if mode == "🌿 尋找植物":
        picture = st.camera_input("拍攝植物照片", label_visibility="collapsed")
        if picture:
            with st.status("💎 正在透過放大鏡比對圖鑑...", expanded=False) as status:
                plant_data = identify_plant_from_api(picture)
                if plant_data["success"]:
                    status.update(label="✨ 辨識成功", state="complete")
                    render_result_card(
                        plant_data["zh_name"],
                        plant_data["desc"],
                        "🌱",
                        '<p class="card-note">已自動加入下方探險圖庫</p>',
                    )
                    st.session_state.pokedex[plant_data['zh_name']] = plant_data
                else:
                    status.update(label="❌ 辨識失敗", state="error")
                    st.error(plant_data["error"])

    elif mode == "🐾 認識動物":
        st.markdown("<br>", unsafe_allow_html=True)
        tabs = st.tabs(["🐶 狗狗小隊", "🐱 貓咪軍團"])
        
        with tabs[0]:
            cols = st.columns(2)
            for i, name in enumerate(["貝貝", "牧耳"]):
                with cols[i]:
                    data = ANIMALS_DB[name]
                    if st.button(f"{data['emoji']} {name}", key=f"pet_{name}"):
                        st.session_state.active_pet = name

        with tabs[1]:
            cols = st.columns(3)
            for i, name in enumerate(["嘿皮", "冬瓜", "小飛俠"]):
                with cols[i]:
                    data = ANIMALS_DB[name]
                    if st.button(f"{data['emoji']} {name}", key=f"pet_{name}"):
                        st.session_state.active_pet = name
                        
        if st.session_state.active_pet:
            pet = ANIMALS_DB[st.session_state.active_pet]
            animal_info = {
                "zh_name": st.session_state.active_pet,
                "emoji": pet['emoji'],
                "desc": pet['desc'],
                "type": "animal"
            }
            st.session_state.pokedex[st.session_state.active_pet] = animal_info
            render_result_card(f"遇見了 {st.session_state.active_pet}！", pet["desc"], "✨")

    st.markdown("<br><br><h2 class='gallery-heading'>🎒 探險圖庫</h2>", unsafe_allow_html=True)
    if not st.session_state.pokedex:
        st.info("圖庫目前空空如也，快點擊上方「模式」開始探索！")
    else:
        count = len(st.session_state.pokedex)
        st.write(f"🌟 已收集 **{count}** 種生物")
        st.progress(min(count / 10, 1.0))

        items = list(st.session_state.pokedex.items())
        for i in range(0, len(items), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(items):
                    name, data = items[i + j]
                    with cols[j]:
                        icon = "🌿" if data.get("type") == "plant" else data.get("emoji", "🐾")
                        if st.button(f"{icon} {name}", key=f"gallery_{name}", use_container_width=True):
                            show_detail_dialog(data)

if __name__ == "__main__":
    main()

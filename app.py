# app.py
import streamlit as st

# 從我們拆分的模組中引入資料與功能
from config import ANIMALS_DB
from api_handler import identify_plant_from_api

# ==========================================
# 1. 初始化與樣式載入
# ==========================================
def load_local_css(file_name):
    """讀取外部 CSS 檔案並注入 Streamlit"""
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>\n{f.read()}\n</style>", unsafe_allow_html=True)

def init_session_state():
    if 'pokedex' not in st.session_state:
        st.session_state.pokedex = {}
    if 'active_pet' not in st.session_state:
        st.session_state.active_pet = None

# ==========================================
# 2. UI 渲染模組
# ==========================================
@st.dialog("🌿 探險圖鑑詳情")
def show_detail_dialog(item_data):
    st.markdown(f"""
        <div class="result-card">
            <h2 style='color:#33691E; margin-top:0;'>{item_data.get('emoji', '🌱')} {item_data['zh_name']}</h2>
            <p style='color:#5D4037;'><b>🇬🇧 英文名稱：</b> {item_data.get('eng_name', 'N/A')}</p>
            <p style='color:#5D4037;'><b>🔬 拉丁學名：</b> <i>{item_data.get('sci_name', 'N/A')}</i></p>
            <hr style='border: 0.5px solid rgba(141,110,99,0.2);'>
            <p style='line-height:1.6; font-size: 1rem; color:#4E342E !important;'>{item_data['desc']}</p>
        </div>
    """, unsafe_allow_html=True)

def render_plant_explorer():
    picture = st.camera_input("")
    if picture:
        with st.status("💎 正在透過放大鏡比對圖鑑...", expanded=False) as status:
            plant_data = identify_plant_from_api(picture)
            if plant_data["success"]:
                status.update(label="✨ 辨識成功", state="complete")
                st.markdown(f"""
                    <div class="result-card">
                        <h2 style='color:#33691E; margin-top:0;'>🌱 {plant_data['zh_name']}</h2>
                        <p style='line-height:1.6; color:#4E342E !important;'>{plant_data['desc']}</p>
                        <p style='font-size:0.8rem; color:#8D6E63; margin-top:10px;'>✔️ 已自動加入下方探險圖庫</p>
                    </div>
                """, unsafe_allow_html=True)
                st.session_state.pokedex[plant_data['zh_name']] = plant_data
            else:
                status.update(label="❌ 辨識失敗", state="error")
                st.error(plant_data["error"])

def render_animal_explorer():
    tabs = st.tabs(["🐶 狗狗小隊", "🐱 貓咪軍團"])
    for idx, (p_type, emoji) in enumerate([("dog", "🐶"), ("cat", "🐱")]):
        with tabs[idx]:
            cols = st.columns(2)
            pets = {k: v for k, v in ANIMALS_DB.items() if v["type"] == p_type}
            for i, (name, data) in enumerate(pets.items()):
                with cols[i % 2]:
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
        st.markdown(f"<div class='result-card'><h3>✨ 遇見了 {st.session_state.active_pet}！</h3><p style='color:#4E342E !important;'>{pet['desc']}</p></div>", unsafe_allow_html=True)

def render_pokedex_gallery():
    st.markdown("<br><br><h2 style='text-align:center; color:#5D4037; font-weight:800;'>🎒 探險圖庫</h2>", unsafe_allow_html=True)
    if not st.session_state.pokedex:
        st.info("圖庫目前空空如也，快點擊上方「模式」開始探索！")
        return

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

# ==========================================
# 4. 主程式流程 (Main Execution)
# ==========================================
def main():
    st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")
    
    # 載入我們獨立出來的 CSS 檔案
    load_local_css("style.css")
    init_session_state()

    st.markdown("<h1>探險放大鏡 🔍</h1>", unsafe_allow_html=True)
    mode = st.radio("", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True)

    if mode == "🌿 尋找植物":
        render_plant_explorer()
    elif mode == "🐾 認識動物":
        render_animal_explorer()

    render_pokedex_gallery()

if __name__ == "__main__":
    main()

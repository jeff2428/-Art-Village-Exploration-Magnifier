import streamlit as st
import requests
from opencc import OpenCC

# ==========================================
# 1. 系統常數與設定 (Config & Constants)
# ==========================================
PLANTNET_API_KEY = "2b1004UqTrbWJn4mj5hqcaZN"
CC_CONVERTER = OpenCC('s2t')

ANIMALS_DB = {
    "貝貝": {"type": "dog", "emoji": "🐶", "desc": "映澄最心愛的米克斯母狗，也是藝素村最溫柔的導嚮員。"},
    "牧耳": {"type": "dog", "emoji": "🐕", "desc": "充滿活力的夥伴，最喜歡在東北角的草地上奔跑。"},
    "小飛俠": {"type": "cat", "emoji": "🐈", "desc": "身手矯健，總是在屋頂上觀察探險家們。"},
    "嘿皮": {"type": "cat", "emoji": "🐈‍⬛", "desc": "個性大方的黑貓，討摸是牠的日常。"},
    "冬瓜": {"type": "cat", "emoji": "🐱", "desc": "圓滾滾的橘貓，是村裡的慵懶大王。"}
}

# ==========================================
# 2. 核心邏輯處理 (Core Logic API)
# ==========================================
def identify_plant_from_api(image_file):
    api_url = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANTNET_API_KEY}&lang=zh"
    files = [('images', (image_file.name, image_file.getvalue(), image_file.type))]
    
    try:
        response = requests.post(api_url, files=files)
        if response.status_code != 200:
            return {"success": False, "error": "辨識失敗，請確認圖片清晰度或網路狀態。"}

        result = response.json()
        if not result.get('results'):
            return {"success": False, "error": "找不到匹配的植物。"}

        best_match = result['results'][0]
        sci_name = best_match['species']['scientificNameWithoutAuthor']
        common_names = best_match['species'].get('commonNames', [])
        
        eng_name = next((n for n in common_names if n.replace(" ","").isascii()), "N/A")
        raw_zh_name = next((n for n in common_names if any('\u4e00' <= c <= '\u9fff' for c in n)), sci_name)
        zh_name = CC_CONVERTER.convert(raw_zh_name)

        description = "這是一株神秘的植物，百科中暫時找不到詳細故事。"
        try:
            wiki_res = requests.get(f"https://zh.wikipedia.org/api/rest_v1/page/summary/{zh_name}?redirect=true", headers={'Accept-Language': 'zh-tw'})
            if wiki_res.status_code == 200:
                description = CC_CONVERTER.convert(wiki_res.json().get('extract', description))
        except: pass

        return {
            "success": True,
            "sci_name": sci_name,
            "eng_name": eng_name,
            "zh_name": zh_name,
            "desc": description,
            "type": "plant"
        }
    except Exception as e:
        return {"success": False, "error": f"連線異常：{e}"}

# ==========================================
# 3. 介面渲染模組 (UI Components)
# ==========================================
def load_custom_css():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(-45deg, #F9FBE7, #E8F5E9, #DCEDC8); background-size: 400% 400%; animation: gradientBG 15s ease infinite; color: #33691E; font-family: '微軟正黑體', sans-serif; }
        @keyframes gradientBG { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        
        /* 放大鏡與相機樣式 (延用森林主題) */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"]) { display: flex; justify-content: center; position: relative; margin-top: 30px; margin-bottom: 130px !important; z-index: 10; }
        [data-testid="stCameraInput"] { width: 320px !important; height: 320px !important; border-radius: 50% !important; border: 10px solid #FFF8E1 !important; box-shadow: 0 0 0 6px #8D6E63, 0 20px 40px rgba(94, 53, 17, 0.2), inset 0 0 25px rgba(0,0,0,0.6) !important; overflow: hidden !important; background-color: #000 !important; position: relative !important; margin: 0 auto !important; }
        [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img, [data-testid="stCameraInput"] canvas { object-fit: cover !important; width: 100% !important; height: 100% !important; position: absolute !important; top: 0 !important; left: 0 !important; }
        
        /* 相機按鈕修復 */
        [data-testid="stCameraInput"] button { background: rgba(141, 110, 99, 0.7) !important; backdrop-filter: blur(5px) !important; border: 1px solid rgba(255, 255, 255, 0.5) !important; z-index: 50 !important; color: white !important; }
        [data-testid="stCameraInput"] button:has(svg) { position: absolute !important; top: 25px !important; right: 25px !important; border-radius: 50% !important; width: 45px !important; height: 45px !important; }
        [data-testid="stCameraInput"] button:not(:has(svg)) { position: absolute !important; bottom: 30px !important; left: 50% !important; transform: translateX(-50%) !important; border-radius: 30px !important; padding: 5px 25px !important; }

        /* 圖鑑卡片樣式 */
        .pokedex-card {
            background: rgba(255, 255, 255, 0.5);
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            border: 1px solid rgba(141, 110, 99, 0.2);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .pokedex-card:hover {
            background: rgba(255, 255, 255, 0.8);
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        /* 資訊卡片 (彈窗或結果) */
        .result-card { background: rgba(255, 255, 255, 0.75); backdrop-filter: blur(15px); padding: 25px; border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.8); color: #4E342E; }
        
        h1 { text-align: center; background: -webkit-linear-gradient(45deg, #33691E 0%, #7CB342 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; }
        </style>
    """, unsafe_allow_html=True)

# 彈出視窗介紹卡片
@st.dialog("🌿 探險圖鑑詳情")
def show_detail_dialog(item_data):
    st.markdown(f"""
        <div class="result-card">
            <h2 style='color:#33691E; margin-top:0;'>{item_data.get('emoji', '🌱')} {item_data['zh_name']}</h2>
            <p style='color:#5D4037;'><b>🇬🇧 英文名稱：</b> {item_data.get('eng_name', 'N/A')}</p>
            <p style='color:#5D4037;'><b>🔬 拉丁學名：</b> <i>{item_data.get('sci_name', 'N/A')}</i></p>
            <hr style='border: 0.5px solid rgba(141,110,99,0.2);'>
            <p style='line-height:1.6; font-size: 1rem;'>{item_data['desc']}</p>
        </div>
    """, unsafe_allow_html=True)

def init_session_state():
    if 'pokedex' not in st.session_state:
        st.session_state.pokedex = {} # 改為字典儲存完整資料
    if 'active_pet' not in st.session_state:
        st.session_state.active_pet = None

def render_plant_explorer():
    picture = st.camera_input("")
    if picture:
        with st.status("💎 正在進行光學與圖鑑比對...", expanded=False) as status:
            plant_data = identify_plant_from_api(picture)
            if plant_data["success"]:
                status.update(label="✨ 分析完成", state="complete")
                st.markdown(f"""
                    <div class="result-card">
                        <h2 style='color:#33691E; margin-top:0;'>🌱 {plant_data['zh_name']}</h2>
                        <p style='line-height:1.6;'>{plant_data['desc']}</p>
                    </div>
                """, unsafe_allow_html=True)
                # 存入圖鑑 (儲存完整字典)
                st.session_state.pokedex[plant_data['zh_name']] = plant_data
            else:
                status.update(label="❌ 分析失敗", state="error")
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
        # 包裝成與植物一致的格式存入圖鑑
        animal_info = {
            "zh_name": st.session_state.active_pet,
            "emoji": pet['emoji'],
            "desc": pet['desc'],
            "type": "animal"
        }
        st.session_state.pokedex[st.session_state.active_pet] = animal_info
        st.markdown(f"<div class='result-card'><h3>✨ 遇見了 {st.session_state.active_pet}！</h3><p>{pet['desc']}</p></div>", unsafe_allow_html=True)

def render_pokedex_gallery():
    """渲染圖庫網格介面"""
    st.markdown("<br><br><h2 style='text-align:center; color:#5D4037;'>🎒 探險圖庫</h2>", unsafe_allow_html=True)
    
    if not st.session_state.pokedex:
        st.info("圖庫目前空空如也，快去村莊裡探索吧！")
        return

    # 計算進度
    count = len(st.session_state.pokedex)
    st.write(f"🌟 已收集 **{count}** 種生物")
    st.progress(min(count / 10, 1.0))

    # 建立網格 (每列 3 個)
    items = list(st.session_state.pokedex.items())
    for i in range(0, len(items), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(items):
                name, data = items[i + j]
                with cols[j]:
                    # 顯示卡片按鈕
                    icon = "🌿" if data.get("type") == "plant" else data.get("emoji", "🐾")
                    if st.button(f"{icon}\n\n{name}", key=f"gallery_{name}"):
                        show_detail_dialog(data)

# ==========================================
# 4. 主程式流程 (Main Execution)
# ==========================================
def main():
    load_custom_css()
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

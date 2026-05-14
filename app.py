import streamlit as st
import requests
from opencc import OpenCC

# ==========================================
# 1. 系統常數與資安設定 (Config & Security)
# ==========================================
try:
    PLANTNET_API_KEY = st.secrets["PLANTNET_API_KEY"]
except KeyError:
    st.error("⚠️ 系統設定錯誤：遺失 API 授權金鑰。請管理員至 Secrets 中設定。")
    st.stop()

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
        response = requests.post(api_url, files=files, timeout=15)
        
        if response.status_code == 401 or response.status_code == 403:
            return {"success": False, "error": "驗證失敗，請確認圖鑑系統授權狀態。"}
        elif response.status_code != 200:
            return {"success": False, "error": "魔法放大鏡暫時失去焦點，請稍後再試。"}

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
            wiki_res = requests.get(f"https://zh.wikipedia.org/api/rest_v1/page/summary/{zh_name}?redirect=true", headers={'Accept-Language': 'zh-tw'}, timeout=5)
            if wiki_res.status_code == 200:
                description = CC_CONVERTER.convert(wiki_res.json().get('extract', description))
        except:
            pass

        return {
            "success": True,
            "sci_name": sci_name,
            "eng_name": eng_name,
            "zh_name": zh_name,
            "desc": description,
            "type": "plant"
        }
    except Exception:
        return {"success": False, "error": "系統網路通訊異常，請確認連線狀態後重試。"}

# ==========================================
# 3. 介面渲染模組 (UI Components)
# ==========================================
def load_custom_css():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(-45deg, #F9FBE7, #E8F5E9, #DCEDC8); background-size: 400% 400%; animation: gradientBG 15s ease infinite; font-family: '微軟正黑體', sans-serif; }
        @keyframes gradientBG { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

        div[role="radiogroup"] label, div[role="radiogroup"] div, div[role="radiogroup"] p { color: #2E7D32 !important; font-weight: 800 !important; font-size: 1rem !important; }
        .stRadio > div { background: rgba(255,255,255,0.85) !important; padding: 10px 20px; border-radius: 30px; border: 2px solid rgba(141,110,99,0.3) !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }

        button[data-baseweb="tab"] p, button[data-baseweb="tab"] span { color: #4E342E !important; font-weight: 800 !important; font-size: 1.1rem !important; }
        button[data-baseweb="tab"][aria-selected="true"] p, button[data-baseweb="tab"][aria-selected="true"] span { color: #2E7D32 !important; }
        div[data-baseweb="tab-highlight"] { background-color: #2E7D32 !important; }

        div.stButton > button { background: rgba(255, 255, 255, 0.85) !important; color: #4E342E !important; border: 2px solid rgba(141, 110, 99, 0.3) !important; border-radius: 20px !important; font-weight: 800 !important; transition: all 0.3s ease !important; }
        div.stButton > button:hover { background: rgba(255, 255, 255, 1) !important; border-color: #8D6E63 !important; transform: translateY(-2px) !important; box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important; }

        .stMarkdown p, .stMarkdown span, .stMarkdown div { color: #4E342E !important; }

        /* ================= 放大鏡容器與圓框設計 ================= */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"]) { display: flex; justify-content: center; position: relative; margin-top: 40px; margin-bottom: 160px !important; z-index: 10; }
        
        [data-testid="stCameraInput"] { 
            width: 320px !important; height: 320px !important; border-radius: 50% !important; border: 12px solid #FFF8E1 !important; 
            box-shadow: 0 0 0 2px #A1887F, 0 0 0 10px #5D4037, 0 25px 50px rgba(94, 53, 17, 0.3), inset 0 0 30px rgba(0,0,0,0.8) !important; 
            overflow: visible !important; /* 允許實體按鈕掛在外面 */
            background-color: #000 !important; position: relative !important; margin: 0 auto !important; padding: 0 !important; 
            box-sizing: border-box !important;
        }
        
        /* 💡 終極防禦：強制所有內部包裹的 div 變成透明，徹底消滅礙眼的白底方形！ */
        [data-testid="stCameraInput"] div { 
            background: transparent !important; 
            border: none !important; 
            position: static !important; 
        }
        
        /* 影片與截圖必須強制裁切成圓角，避免溢出 */
        [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img, [data-testid="stCameraInput"] canvas { 
            object-fit: cover !important; width: 100% !important; height: 100% !important; 
            position: absolute !important; top: 0 !important; left: 0 !important; 
            z-index: 1 !important; border-radius: 50% !important; 
        }

        /* ================= 握把設計 (容納兩個按鈕) ================= */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"])::after { 
            content: ''; position: absolute; top: 305px; left: 50%; transform: translateX(-50%); 
            width: 52px; height: 120px; 
            background: linear-gradient(to right, #4E342E, #8D6E63, #4E342E); 
            border-radius: 0 0 26px 26px; 
            box-shadow: 0 15px 30px rgba(94, 53, 17, 0.4), inset 0 -5px 15px rgba(0,0,0,0.3); z-index: 5; 
        }

        /* ================= 握把上的實體按鍵 (金屬鑲嵌風格) ================= */
        [data-testid="stCameraInput"] button {
            position: absolute !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: 38px !important;
            height: 38px !important;
            border-radius: 50% !important;
            padding: 0 !important;
            margin: 0 !important;
            background: linear-gradient(145deg, #6d4c41, #3e2723) !important; /* 原木金屬質感 */
            border: 2px solid #A1887F !important;
            box-shadow: inset 2px 2px 5px rgba(255,255,255,0.2), 0 4px 8px rgba(0,0,0,0.7) !important;
            z-index: 9999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.2s ease !important;
        }

        /* 徹底隱藏 Streamlit 原生的文字與圖示 (避免干擾) */
        [data-testid="stCameraInput"] button * { display: none !important; }

        /* 🔴 上方按鈕：切換鏡頭 (未拍照時，具有 svg 的按鈕) */
        [data-testid="stCameraInput"]:not(:has(img)) button:has(svg) {
            top: 315px !important; bottom: auto !important;
        }
        [data-testid="stCameraInput"]:not(:has(img)) button:has(svg)::after {
            content: '🔄'; font-size: 20px; display: block; line-height: 1;
        }

        /* 🟡 下方按鈕：拍照 (未拍照時，沒有 svg 的按鈕) */
        [data-testid="stCameraInput"]:not(:has(img)) button:not(:has(svg)) {
            top: 365px !important; bottom: auto !important;
        }
        [data-testid="stCameraInput"]:not(:has(img)) button:not(:has(svg))::after {
            content: '📸'; font-size: 20px; display: block; line-height: 1;
        }

        /* 🟡 下方按鈕：重拍 (已拍照時的唯一按鈕) */
        [data-testid="stCameraInput"]:has(img) button {
            top: 365px !important; bottom: auto !important;
        }
        [data-testid="stCameraInput"]:has(img) button::after {
            content: '✖️'; font-size: 16px; display: block; line-height: 1; color: white;
        }

        /* 按壓回饋：有真實按鈕陷下去的感覺 */
        [data-testid="stCameraInput"] button:active {
            box-shadow: inset 2px 2px 10px rgba(0,0,0,0.9) !important;
            transform: translateX(-50%) scale(0.95) !important;
        }

        /* 鏡面高光 (放在最後以確保疊在影片上層) */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"])::before { content: ''; position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 320px; height: 320px; border-radius: 50%; background: radial-gradient(circle at 70% 30%, rgba(255,255,255,0.35) 0%, rgba(255,255,255,0) 60%); pointer-events: none; z-index: 15; }

        .result-card { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(15px); padding: 25px; border-radius: 24px; border: 1px solid rgba(141, 110, 99, 0.3); color: #4E342E; margin-top: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
        .pokedex-card { background: rgba(255, 255, 255, 0.7); border-radius: 15px; padding: 15px; text-align: center; border: 2px solid rgba(141, 110, 99, 0.2); transition: all 0.3s ease; cursor: pointer; color: #4E342E !important; font-weight: bold; }
        .pokedex-card:hover { background: rgba(255, 255, 255, 0.95); transform: translateY(-5px); border-color: #8D6E63; }

        h1 { text-align: center; background: -webkit-linear-gradient(45deg, #2E7D32 0%, #7CB342 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900; letter-spacing: 2px; text-shadow: 0px 4px 10px rgba(46, 125, 50, 0.2); margin-bottom: 20px; }
        </style>
    """, unsafe_allow_html=True)

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

def init_session_state():
    if 'pokedex' not in st.session_state:
        st.session_state.pokedex = {}
    if 'active_pet' not in st.session_state:
        st.session_state.active_pet = None

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

import streamlit as st
import requests
from opencc import OpenCC

# ==========================================
# 1. 系統常數與設定 (Config & Constants)
# ==========================================
PLANTNET_API_KEY = "2b1004UqTrbWJn4mj5hqcaZN" # API KEY
CC_CONVERTER = OpenCC('s2t')

# 動物圖鑑資料庫
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
    except Exception as e:
        return {"success": False, "error": f"連線異常：{e}"}

# ==========================================
# 3. 介面渲染模組與自定義 CSS (UI Components)
# ==========================================
def load_custom_css():
    # 將您設計的完美 CSS 樣式直接注入
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(-45deg, #F9FBE7, #E8F5E9, #DCEDC8);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
            font-family: '微軟正黑體', sans-serif;
        }

        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        div[role="radiogroup"] label,
        div[role="radiogroup"] div,
        div[role="radiogroup"] p {
            color: #2E7D32 !important;
            font-weight: 800 !important;
            font-size: 1rem !important;
        }

        .stRadio > div {
            background: rgba(255,255,255,0.85) !important;
            padding: 10px 20px;
            border-radius: 30px;
            border: 2px solid rgba(141,110,99,0.3) !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }

        .stMarkdown p,
        .stMarkdown span,
        .stMarkdown div {
            color: #4E342E !important;
        }

        /* ================= 放大鏡容器 ================= */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"]) {
            display: flex;
            justify-content: center;
            position: relative;
            margin-top: 40px;
            margin-bottom: 240px !important;
            z-index: 10;
        }

        /* ================= 主鏡頭 ================= */
        [data-testid="stCameraInput"] {
            width: min(88vw, 320px) !important;
            height: min(88vw, 320px) !important;
            border-radius: 50% !important;
            border: 12px solid #FFF8E1 !important;
            box-shadow:
                0 0 0 2px #A1887F,
                0 0 0 10px #4E342E,
                0 25px 50px rgba(94, 53, 17, 0.3),
                inset 0 0 30px rgba(0,0,0,0.8) !important;
            overflow: visible !important;
            background-color: #000 !important;
            position: relative !important;
            margin: 0 auto !important;
            padding: 0 !important;
            box-sizing: border-box !important;
        }

        /* 消滅白底 */
        [data-testid="stCameraInput"] div {
            background: transparent !important;
            border: none !important;
            position: static !important;
        }

        /* 鏡頭影像 */
        [data-testid="stCameraInput"] video,
        [data-testid="stCameraInput"] img,
        [data-testid="stCameraInput"] canvas {
            object-fit: cover !important;
            width: 100% !important;
            height: 100% !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            z-index: 1 !important;
            border-radius: 50% !important;
        }

        /* ================= 放大鏡握把 ================= */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"])::after {
            content: '';
            position: absolute;
            top: 285px;
            left: 50%;
            transform: translateX(-50%);
            width: 86px;
            height: 230px;
            background: #4a2f24;
            border-radius: 43px;
            border: 2px solid #1a0f0a;
            box-shadow:
                inset 0 0 0 2px #5d3c2e,
                inset 0 0 0 5px #382117,
                inset 0 0 0 6px dashed #9e7a68,
                0 15px 30px rgba(0,0,0,0.6);
            z-index: 5;
        }

        /* ================= 手機按鈕修正版 ================= */
        [data-testid="stCameraInput"] button {
            -webkit-appearance: none !important;
            appearance: none !important;
            position: absolute !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: 66px !important;
            height: 66px !important;
            border-radius: 50% !important;
            padding: 0 !important;
            margin: 0 !important;
            box-sizing: border-box !important;
            color: transparent !important;
            font-size: 0 !important;
            text-indent: -9999px !important;
            background: radial-gradient(
                circle at 35% 30%,
                #e8bc96 0%,
                #c48c66 25%,
                #875030 65%,
                #472211 100%
            ) !important;
            border: none !important;
            box-shadow:
                inset 1px 1px 4px rgba(255,255,255,0.5),
                inset -3px -3px 8px rgba(0,0,0,0.8),
                0 0 0 3px #3d1f11,
                0 0 0 5px #916142,
                0 0 0 6px #1a0f0a,
                0 10px 15px rgba(0,0,0,0.9) !important;
            z-index: 9999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
        }

        /* 隱藏原生 icon */
        [data-testid="stCameraInput"] button * {
            display: none !important;
        }

        /* 共通 emoji */
        [data-testid="stCameraInput"] button::after {
            position: absolute !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            font-size: 30px !important;
            text-indent: 0 !important;
            color: white !important;
            line-height: 1 !important;
            display: block !important;
            filter: drop-shadow(0 2px 2px rgba(0,0,0,0.4));
        }

        /* ================= 第一顆按鈕 ================= */
        /* 如果手機有多鏡頭 -> Streamlit 自動生成切換按鈕 */
        [data-testid="stCameraInput"]:not(:has(img)) button:nth-of-type(1) {
            top: 305px !important;
        }
        [data-testid="stCameraInput"]:not(:has(img)) button:nth-of-type(1)::after {
            content: "🔄";
        }

        /* ================= 第二顆按鈕 ================= */
        /* 拍照 */
        [data-testid="stCameraInput"]:not(:has(img)) button:nth-of-type(2) {
            top: 410px !important;
        }
        [data-testid="stCameraInput"]:not(:has(img)) button:nth-of-type(2)::after {
            content: "📸";
        }

        /* ================= 只有一顆鏡頭 ================= */
        /* 沒有切換功能時，唯一按鈕直接當拍照 */
        [data-testid="stCameraInput"]:not(:has(img)) button:only-of-type {
            top: 410px !important;
        }
        [data-testid="stCameraInput"]:not(:has(img)) button:only-of-type::after {
            content: "📸";
        }

        /* ================= 已拍照 ================= */
        [data-testid="stCameraInput"]:has(img) button {
            top: 410px !important;
        }
        [data-testid="stCameraInput"]:has(img) button::after {
            content: "✖️";
            font-size: 24px !important;
        }

        /* ================= 按壓效果 ================= */
        [data-testid="stCameraInput"] button:active {
            box-shadow:
                inset 2px 2px 10px rgba(0,0,0,0.8),
                0 0 0 3px #3d1f11,
                0 0 0 5px #916142,
                0 0 0 6px #1a0f0a,
                0 3px 5px rgba(0,0,0,0.9) !important;
            transform: translateX(-50%) translateY(4px) !important;
        }

        /* ================= 鏡面高光 ================= */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"])::before {
            content: '';
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: min(88vw, 320px);
            height: min(88vw, 320px);
            border-radius: 50%;
            background: radial-gradient(
                circle at 70% 30%,
                rgba(255,255,255,0.35) 0%,
                rgba(255,255,255,0) 60%
            );
            pointer-events: none;
            z-index: 15;
        }

        /* ================= 卡片 ================= */
        .result-card {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(15px);
            padding: 25px;
            border-radius: 24px;
            border: 1px solid rgba(141, 110, 99, 0.3);
            color: #4E342E;
            margin-top: 20px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }

        .pokedex-card {
            background: rgba(255, 255, 255, 0.7);
            border-radius: 15px;
            padding: 15px;
            text-align: center;
            border: 2px solid rgba(141, 110, 99, 0.2);
            transition: all 0.3s ease;
            cursor: pointer;
            color: #4E342E !important;
            font-weight: bold;
        }

        .pokedex-card:hover {
            background: rgba(255, 255, 255, 0.95);
            transform: translateY(-5px);
            border-color: #8D6E63;
        }

        h1 {
            text-align: center;
            background: -webkit-linear-gradient(45deg, #2E7D32 0%, #7CB342 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
            letter-spacing: 2px;
            text-shadow: 0px 4px 10px rgba(46, 125, 50, 0.2);
            margin-bottom: 20px;
        }
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
            <p style='line-height:1.6; font-size: 1rem;'>{item_data['desc']}</p>
        </div>
    """, unsafe_allow_html=True)

def init_session_state():
    if 'pokedex' not in st.session_state:
        st.session_state.pokedex = {}
    if 'active_pet' not in st.session_state:
        st.session_state.active_pet = None

# ==========================================
# 4. 主程式流程 (Main Execution)
# ==========================================
def main():
    st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")
    
    # 載入我們結合好的 CSS
    load_custom_css()
    init_session_state()

    st.markdown("<h1>探險放大鏡 🔍</h1>", unsafe_allow_html=True)

    mode = st.radio("", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True)

    if mode == "🌿 尋找植物":
        # 原生的 st.camera_input，這樣就能觸發後端 API 運作
        picture = st.camera_input("")
        
        if picture:
            with st.status("💎 正在透過放大鏡比對圖鑑...", expanded=False) as status:
                plant_data = identify_plant_from_api(picture)
                if plant_data["success"]:
                    status.update(label="✨ 辨識成功", state="complete")
                    st.markdown(f"""
                        <div class="result-card">
                            <h2 style='color:#33691E; margin-top:0;'>🌱 {plant_data['zh_name']}</h2>
                            <p style='line-height:1.6;'>{plant_data['desc']}</p>
                            <p style='font-size:0.8rem; color:#8D6E63; margin-top:10px;'>✔️ 已自動加入下方探險圖庫</p>
                        </div>
                    """, unsafe_allow_html=True)
                    # 加入圖鑑
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
            # 加入圖鑑
            st.session_state.pokedex[st.session_state.active_pet] = animal_info
            st.markdown(f"<div class='result-card'><h3>✨ 遇見了 {st.session_state.active_pet}！</h3><p>{pet['desc']}</p></div>", unsafe_allow_html=True)

    # 探險圖庫列表 (背包)
    st.markdown("<br><br><h2 style='text-align:center; color:#5D4037; font-weight:800;'>🎒 探險圖庫</h2>", unsafe_allow_html=True)
    if not st.session_state.pokedex:
        st.info("圖庫目前空空如也，快點擊上方「模式」開始探索！")
    else:
        count = len(st.session_state.pokedex)
        st.write(f"🌟 已收集 **{count}** 種生物")
        st.progress(min(count / 10, 1.0))

        # 展示圖鑑卡片 (3欄)
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

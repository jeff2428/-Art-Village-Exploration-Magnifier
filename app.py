import streamlit as st
import requests
from opencc import OpenCC

# ==========================================
# 1. 系統常數與設定 (Config & Constants)
# ==========================================
PLANTNET_API_KEY = "2b1004UqTrbWJn4mj5hqcaZN" # 請將您的 API KEY 填入此處
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
# 3. 介面渲染模組與終極 CSS (UI Components)
# ==========================================
def load_custom_css():
    st.markdown("""
        <style>
        /* 全域漸層背景 */
        .stApp { background: linear-gradient(-45deg, #F9FBE7, #E8F5E9, #DCEDC8); background-size: 400% 400%; animation: gradientBG 15s ease infinite; font-family: '微軟正黑體', sans-serif; }
        @keyframes gradientBG { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

        /* 選單樣式 */
        div[role="radiogroup"] label, div[role="radiogroup"] div, div[role="radiogroup"] p { color: #2E7D32 !important; font-weight: 800 !important; font-size: 1rem !important; }
        .stRadio > div { background: rgba(255,255,255,0.85) !important; padding: 10px 20px; border-radius: 30px; border: 2px solid rgba(141,110,99,0.3) !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        button[data-baseweb="tab"] p, button[data-baseweb="tab"] span { color: #4E342E !important; font-weight: 800 !important; font-size: 1.1rem !important; }
        button[data-baseweb="tab"][aria-selected="true"] p, button[data-baseweb="tab"][aria-selected="true"] span { color: #2E7D32 !important; }
        div[data-baseweb="tab-highlight"] { background-color: #2E7D32 !important; }

        div.stButton > button { background: rgba(255, 255, 255, 0.85) !important; color: #4E342E !important; border: 2px solid rgba(141, 110, 99, 0.3) !important; border-radius: 20px !important; font-weight: 800 !important; transition: all 0.3s ease !important; }
        div.stButton > button:hover { background: rgba(255, 255, 255, 1) !important; border-color: #8D6E63 !important; transform: translateY(-2px) !important; box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important; }
        .stMarkdown p, .stMarkdown span, .stMarkdown div { color: #4E342E !important; }

        /* ================= 放大鏡容器與主體圓框 ================= */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"]) { display: flex; justify-content: center; position: relative; margin-top: 40px; margin-bottom: 240px !important; z-index: 10; }

        [data-testid="stCameraInput"] { 
            width: min(88vw, 320px) !important; height: min(88vw, 320px) !important; border-radius: 50% !important; border: 12px solid #FFF8E1 !important; 
            box-shadow: 0 0 0 2px #A1887F, 0 0 0 10px #4E342E, 0 25px 50px rgba(94, 53, 17, 0.3), inset 0 0 30px rgba(0,0,0,0.8) !important; 
            overflow: visible !important; background-color: #000 !important; position: relative !important; margin: 0 auto !important; padding: 0 !important; 
            box-sizing: border-box !important;
        }

        /* 消滅原生白底 */
        [data-testid="stCameraInput"] div { background: transparent !important; border: none !important; position: static !important; }

        /* 影片維持圓角覆蓋 */
        [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img, [data-testid="stCameraInput"] canvas { 
            object-fit: cover !important; width: 100% !important; height: 100% !important; 
            position: absolute !important; top: 0 !important; left: 0 !important; 
            z-index: 1 !important; border-radius: 50% !important; 
        }

        /* 鏡面高光 */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"])::before { content: ''; position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: min(88vw, 320px); height: min(88vw, 320px); border-radius: 50%; background: radial-gradient(circle at 70% 30%, rgba(255,255,255,0.35) 0%, rgba(255,255,255,0) 60%); pointer-events: none; z-index: 15; }

        /* ================= 8字型皮革墊片 ================= */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"])::after { 
            content: ''; position: absolute; top: 285px; left: 50%; transform: translateX(-50%); 
            width: 86px; height: 230px; 
            background: #4a2f24; border-radius: 43px; border: 2px solid #1a0f0a; 
            box-shadow: inset 0 0 0 2px #5d3c2e, inset 0 0 0 5px #382117, inset 0 0 0 6px dashed #9e7a68, 0 15px 30px rgba(0,0,0,0.6); 
            z-index: 5; 
        }

        /* ================= 🛠️ 完美的青銅相機按鈕 ================= */
        [data-testid="stCameraInput"] button {
            -webkit-appearance: none !important; appearance: none !important; 
            position: absolute !important; left: 50% !important; transform: translateX(-50%) !important;
            width: 66px !important; height: 66px !important; border-radius: 50% !important;
            padding: 0 !important; margin: 0 !important; box-sizing: border-box !important;
            
            /* 徹底隱藏原生文字 */
            color: transparent !important; font-size: 0px !important; line-height: 0 !important; text-indent: -9999px !important;
            
            /* 青銅金屬漸層與 3D 雕刻陰影 */
            background: radial-gradient(circle at 35% 30%, #e8bc96 0%, #c48c66 25%, #875030 65%, #472211 100%) !important; 
            border: none !important;
            box-shadow: 
                inset 1px 1px 4px rgba(255,255,255,0.5), inset -3px -3px 8px rgba(0,0,0,0.8), 
                0 0 0 3px #3d1f11, 0 0 0 5px #916142, 0 0 0 6px #1a0f0a, 
                0 10px 15px rgba(0,0,0,0.9) !important; 
                
            z-index: 9999 !important; display: block !important; cursor: pointer !important;
            transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        /* 隱藏原生多餘圖示 */
        [data-testid="stCameraInput"] button * { display: none !important; color: transparent !important; }

        /* ================= 🔴 上方按鈕：切換鏡頭 (若設備支援) ================= */
        [data-testid="stCameraInput"] > div > button { 
            top: 305px !important; bottom: auto !important; 
        }
        [data-testid="stCameraInput"] > div > button::after { 
            content: ''; position: absolute !important; top: 50% !important; left: 50% !important; transform: translate(-50%, -50%) !important; 
            width: 32px !important; height: 32px !important; background-size: cover !important;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%232b1308'%3E%3Cpath d='M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46A7.93 7.93 0 0 0 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74A7.93 7.93 0 0 0 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z'/%3E%3C/svg%3E") !important;
            filter: drop-shadow(0px 1.5px 1px rgba(255,255,255,0.45)) !important; text-indent: 0 !important;
        }

        /* ================= 🟡 下方按鈕：拍照或重拍 ================= */
        [data-testid="stCameraInput"] > button { 
            top: 410px !important; bottom: auto !important; 
        }
        
        /* 預設拍照相機圖示 */
        [data-testid="stCameraInput"] > button::after { 
            content: ''; position: absolute !important; top: 50% !important; left: 50% !important; transform: translate(-50%, -50%) !important; 
            width: 34px !important; height: 34px !important; background-size: cover !important;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%232b1308'%3E%3Cpath d='M20 5h-3.17L15 3H9L7.17 5H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 14H4V7h4.05l1.83-2h4.24l1.83 2H20v12z'/%3E%3Cpath d='M12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.65 0-3 1.35-3 3s1.35 3 3 3 3-1.35 3-3-1.35-3-3-3z'/%3E%3C/svg%3E") !important;
            filter: drop-shadow(0px 1.5px 1px rgba(255,255,255,0.45)) !important; text-indent: 0 !important;
        }

        /* 拍攝完成，轉為重拍圖示 */
        [data-testid="stCameraInput"]:has(img) > button::after { 
            width: 28px !important; height: 28px !important; 
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%232b1308'%3E%3Cpath d='M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z'/%3E%3C/svg%3E") !important;
        }

        /* --- 🕹️ 真實機械按壓物理回饋 --- */
        [data-testid="stCameraInput"] button:active { 
            box-shadow: 
                inset 2px 2px 10px rgba(0,0,0,0.8), 
                0 0 0 3px #3d1f11, 0 0 0 5px #916142, 0 0 0 6px #1a0f0a, 
                0 3px 5px rgba(0,0,0,0.9) !important; 
            transform: translateX(-50%) translateY(4px) !important; 
        }

        /* 資訊卡片 */
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
    
    load_custom_css()
    init_session_state()

    st.markdown("<h1>探險放大鏡 🔍</h1>", unsafe_allow_html=True)

    mode = st.radio("", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True)

    if mode == "🌿 尋找植物":
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
            st.markdown(f"<div class='result-card'><h3>✨ 遇見了 {st.session_state.active_pet}！</h3><p>{pet['desc']}</p></div>", unsafe_allow_html=True)

    st.markdown("<br><br><h2 style='text-align:center; color:#5D4037; font-weight:800;'>🎒 探險圖庫</h2>", unsafe_allow_html=True)
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

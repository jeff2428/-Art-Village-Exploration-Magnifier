import streamlit as st
import requests
from opencc import OpenCC

# ==========================================
# 1. 系統常數與設定 (Config & Constants)
# ==========================================
PLANTNET_API_KEY = "2b1004UqTrbWJn4mj5hqcaZN"
CC_CONVERTER = OpenCC('s2t') # 初始化繁簡轉換器 (s2t: 簡體轉台灣繁體)

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
    """
    負責呼叫 PlantNet API 與 Wikipedia API 進行植物辨識與資料擷取。
    回傳字典格式： {"success": bool, "sci_name": str, "eng_name": str, "zh_name": str, "desc": str, "error": str}
    """
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
        
        # 解析英文與中文俗名
        eng_name = next((n for n in common_names if n.replace(" ","").isascii()), "N/A")
        raw_zh_name = next((n for n in common_names if any('\u4e00' <= c <= '\u9fff' for c in n)), sci_name)
        zh_name = CC_CONVERTER.convert(raw_zh_name)

        # 抓取維基百科資料
        description = "這是一株神秘的植物，百科中暫時找不到詳細故事。"
        try:
            wiki_res = requests.get(f"https://zh.wikipedia.org/api/rest_v1/page/summary/{zh_name}?redirect=true", headers={'Accept-Language': 'zh-tw'})
            if wiki_res.status_code == 200:
                description = CC_CONVERTER.convert(wiki_res.json().get('extract', description))
        except Exception:
            pass

        return {
            "success": True,
            "sci_name": sci_name,
            "eng_name": eng_name,
            "zh_name": zh_name,
            "desc": description
        }

    except Exception as e:
        return {"success": False, "error": f"連線異常：{e}"}

# ==========================================
# 3. 介面渲染模組 (UI Components)
# ==========================================
def load_custom_css():
    """載入自訂義的 CSS 樣式 (森林微語 - 大地暖色主題 & 按鈕修復版)"""
    st.markdown("""
        <style>
        /* 1. 動態晨曦森林漸層背景 */
        .stApp { 
            background: linear-gradient(-45deg, #F9FBE7, #E8F5E9, #DCEDC8); 
            background-size: 400% 400%; 
            animation: gradientBG 15s ease infinite; 
            color: #33691E; 
            font-family: '微軟正黑體', sans-serif; 
        }
        @keyframes gradientBG { 
            0% { background-position: 0% 50%; } 
            50% { background-position: 100% 50%; } 
            100% { background-position: 0% 50%; } 
        }

        /* 2. 放大鏡容器定位 */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"]) { 
            display: flex; 
            justify-content: center; 
            position: relative; 
            margin-top: 30px; 
            margin-bottom: 130px !important; 
            z-index: 10; 
        }

        /* 3. 放大鏡本體：木質外框與暖色陰影 */
        [data-testid="stCameraInput"] { 
            width: 320px !important; 
            height: 320px !important; 
            border-radius: 50% !important; 
            border: 10px solid #FFF8E1 !important; 
            box-shadow: 
                0 0 0 6px #8D6E63, 
                0 20px 40px rgba(94, 53, 17, 0.2), 
                inset 0 0 25px rgba(0,0,0,0.6) !important; 
            overflow: hidden !important; 
            background-color: #000 !important; 
            position: relative !important; 
            margin: 0 auto !important; 
            padding: 0 !important; 
        }

        /* 4. 相機畫面滿版裁切 */
        [data-testid="stCameraInput"] video, [data-testid="stCameraInput"] img, [data-testid="stCameraInput"] canvas { 
            object-fit: cover !important; 
            width: 100% !important; height: 100% !important; 
            min-width: 100% !important; min-height: 100% !important; 
            position: absolute !important; top: 0 !important; left: 0 !important; 
        }

        /* ==================================================== */
        /* 5. 原生相機按鈕修復：將切換鏡頭與拍照按鈕分開處理 */
        /* ==================================================== */
        
        /* 所有按鈕共同底色：大地色毛玻璃 */
        [data-testid="stCameraInput"] button { 
            background: rgba(141, 110, 99, 0.7) !important; 
            backdrop-filter: blur(5px) !important; 
            border: 1px solid rgba(255, 255, 255, 0.5) !important; 
            z-index: 50 !important; 
            box-shadow: 0 4px 10px rgba(0,0,0,0.2) !important; 
            color: white !important;
        }
        [data-testid="stCameraInput"] button p, [data-testid="stCameraInput"] button div { 
            color: white !important; font-weight: bold !important; 
        }

        /* 5-1. 真正的原生「切換鏡頭」按鈕 (判斷特徵：按鈕內只有 SVG 圖示) */
        [data-testid="stCameraInput"] button:has(svg) {
            position: absolute !important; 
            top: 25px !important; 
            right: 25px !important; /* 往內縮進，避免被圓形邊緣切掉 */
            border-radius: 50% !important; 
            padding: 8px !important;
            width: 45px !important;
            height: 45px !important;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* 5-2. 「拍照 / 清除照片」按鈕 (判斷特徵：不包含 SVG，代表是有文字的按鈕) */
        [data-testid="stCameraInput"] button:not(:has(svg)) {
            position: absolute !important; 
            bottom: 30px !important; 
            left: 50% !important; 
            transform: translateX(-50%) !important; 
            border-radius: 30px !important; 
            padding: 5px 25px !important; 
        }

        /* 6. 鏡面反光：溫暖的陽光折射 */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"])::before { 
            content: ''; position: absolute; top: 0; left: 50%; transform: translateX(-50%); 
            width: 320px; height: 320px; border-radius: 50%; 
            background: radial-gradient(ellipse at 65% 25%, rgba(255,255,230,0.3) 0%, rgba(255,255,255,0) 50%); 
            pointer-events: none; z-index: 15; 
        }

        /* 7. 放大鏡握把：流線木紋質感 */
        [data-testid="stElementContainer"]:has([data-testid="stCameraInput"])::after { 
            content: ''; position: absolute; top: 310px; left: 50%; transform: translateX(-50%); 
            width: 44px; height: 110px; 
            background: linear-gradient(to right, #5D4037, #8D6E63, #5D4037); 
            border-radius: 6px 6px 25px 25px; 
            box-shadow: 0 15px 25px rgba(94, 53, 17, 0.4), inset 0 -5px 15px rgba(0,0,0,0.3); 
            z-index: 5; 
        }

        /* 8. 資訊卡片：暖白透光紙質 */
        .result-card { 
            background: rgba(255, 255, 255, 0.65); 
            backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); 
            padding: 30px; border-radius: 24px; margin-top: 30px; 
            border: 1px solid rgba(255, 255, 255, 0.8); 
            box-shadow: 0 8px 32px 0 rgba(100, 110, 80, 0.15); 
            color: #4E342E; 
        }

        /* 9. 標題與字體美化 */
        h1 { 
            text-align: center; 
            background: -webkit-linear-gradient(45deg, #33691E 0%, #7CB342 100%); 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
            font-weight: 800; letter-spacing: 2px; 
            text-shadow: 0px 4px 15px rgba(51, 105, 30, 0.15); margin-bottom: 20px; 
        }
        
        div.stButton > button { 
            background: rgba(255, 255, 255, 0.7); color: #5D4037; 
            border: 1px solid rgba(141, 110, 99, 0.3); border-radius: 30px; padding: 10px 20px; 
            font-weight: bold; transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background: rgba(255, 255, 255, 0.95);
            border-color: #8D6E63;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(141, 110, 99, 0.2);
        }
        
        /* 頂部選項按鈕底色 */
        .stRadio > div { background: rgba(255,255,255,0.5); padding: 8px 15px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.6); }
        </style>
    """, unsafe_allow_html=True)

def init_session_state():
    """初始化全域狀態變數"""
    if 'pokedex' not in st.session_state:
        st.session_state.pokedex = set()
    if 'active_pet' not in st.session_state:
        st.session_state.active_pet = None

def render_plant_explorer():
    """渲染路線 A：尋找植物介面"""
    picture = st.camera_input("")
    
    if picture:
        with st.status("💎 正在進行光學與圖鑑比對...", expanded=False) as status:
            plant_data = identify_plant_from_api(picture)
            
            if plant_data["success"]:
                status.update(label="✨ 分析完成", state="complete")
                
                # 渲染結果卡片
                st.markdown(f"""
                    <div class="result-card">
                        <h2 style='color:#33691E; margin-top:0; border-bottom: 1px solid rgba(141,110,99,0.2); padding-bottom: 10px;'>🌱 {plant_data['zh_name']}</h2>
                        <p style='color:#5D4037; margin-top: 15px;'><b>🇬🇧 英文俗名：</b> {plant_data['eng_name']}</p>
                        <p style='color:#5D4037;'><b>🔬 拉丁學名：</b> <i>{plant_data['sci_name']}</i></p>
                        <div style='background: rgba(255,255,255,0.5); padding: 15px; border-radius: 12px; margin-top: 15px;'>
                            <p style='line-height:1.8; font-size: 1rem; margin:0;'>{plant_data['desc']}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # 存入圖鑑
                st.session_state.pokedex.add(plant_data['zh_name'])
            else:
                status.update(label="❌ 分析失敗", state="error")
                st.error(plant_data["error"])

def render_animal_explorer():
    """渲染路線 B：認識動物介面"""
    st.write("<br>", unsafe_allow_html=True)
    tabs = st.tabs(["🐶 狗狗小隊", "🐱 貓咪軍團"])
    
    with tabs[0]:
        cols = st.columns(2)
        dogs = {k: v for k, v in ANIMALS_DB.items() if v["type"] == "dog"}
        for i, (name, data) in enumerate(dogs.items()):
            with cols[i % 2]:
                if st.button(f"{data['emoji']} {name}", key=f"dog_{name}"):
                    st.session_state.active_pet = name

    with tabs[1]:
        cols = st.columns(2)
        cats = {k: v for k, v in ANIMALS_DB.items() if v["type"] == "cat"}
        for i, (name, data) in enumerate(cats.items()):
            with cols[i % 2]:
                if st.button(f"{data['emoji']} {name}", key=f"cat_{name}"):
                    st.session_state.active_pet = name

    if st.session_state.active_pet:
        pet = ANIMALS_DB[st.session_state.active_pet]
        st.markdown(f"""
            <div class="result-card">
                <h3 style='color:#33691E; margin-top:0;'>✨ 遇見了 {st.session_state.active_pet}！</h3>
                <div style='background: rgba(255,255,255,0.5); padding: 15px; border-radius: 12px; margin-top: 15px;'>
                    <p style='font-size: 1.1rem; line-height: 1.6; margin:0; color:#4E342E;'>{pet['desc']}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.session_state.pokedex.add(st.session_state.active_pet)

def render_pokedex():
    """渲染底部成就圖鑑"""
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("🎒 我的探險圖鑑", expanded=False):
        if st.session_state.pokedex:
            count = len(st.session_state.pokedex)
            st.markdown(f"🌟 **已收集 {count} 種生物**")
            st.progress(min(count / 10, 1.0))
            st.write("，".join(st.session_state.pokedex))
            if count >= 3:
                st.balloons()
        else:
            st.write("圖鑑尚無紀錄，開始探索藝素村吧！")

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

    render_pokedex()

if __name__ == "__main__":
    main()

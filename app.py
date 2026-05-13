import streamlit as st
import requests
from opencc import OpenCC

# ================= 1. 極光漸層與毛玻璃 (Glassmorphism) 美化 CSS =================
st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    /* 動態極光/深海漸層背景 */
    .stApp {
        background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: #F8FAFC;
        font-family: '微軟正黑體', sans-serif;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* ================= 完美版放大鏡 CSS ================= */

    /* 1. 找到相機元件的外層容器，預留握把空間 */
    [data-testid="stElementContainer"]:has([data-testid="stCameraInput"]) {
        display: flex;
        justify-content: center;
        position: relative;
        margin-top: 30px;
        margin-bottom: 130px !important; /* 給下方的握把留出高度 */
        z-index: 10;
    }

    /* 2. 放大鏡本體 (相機外框) */
    [data-testid="stCameraInput"] {
        width: 320px !important;
        height: 320px !important;
        border-radius: 50% !important;
        border: 10px solid #e2e8f0 !important;
        box-shadow:
            0 0 0 5px #64748b, /* 外層深灰金屬環 */
            0 25px 50px rgba(0,0,0,0.6), /* 立體投影 */
            inset 0 0 25px rgba(0,0,0,0.8) !important;
        overflow: hidden !important;
        background-color: #000 !important;
        position: relative !important;
        margin: 0 auto !important;
        padding: 0 !important;
    }

    /* 3. 強制相機畫面(Video)完全覆蓋放大鏡內部 */
    [data-testid="stCameraInput"] video,
    [data-testid="stCameraInput"] img,
    [data-testid="stCameraInput"] canvas {
        object-fit: cover !important; /* 強制裁切填滿，不留白邊 */
        width: 100% !important;
        height: 100% !important;
        min-width: 100% !important;
        min-height: 100% !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
    }

    /* 4. 拍照按鈕美化 (半透明藥丸設計) */
    [data-testid="stCameraInput"] button {
        position: absolute !important;
        bottom: 25px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        background: rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(5px) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 30px !important;
        padding: 5px 25px !important;
        z-index: 20 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
    }
    [data-testid="stCameraInput"] button p {
        color: white !important;
        font-weight: bold !important;
    }

    /* 5. 放大鏡鏡面反光 */
    [data-testid="stElementContainer"]:has([data-testid="stCameraInput"])::before {
        content: '';
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 320px;
        height: 320px;
        border-radius: 50%;
        background: radial-gradient(ellipse at 65% 25%, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 50%);
        pointer-events: none; 
        z-index: 15; 
    }

    /* 6. 完美對齊的放大鏡握把 */
    [data-testid="stElementContainer"]:has([data-testid="stCameraInput"])::after {
        content: '';
        position: absolute;
        top: 310px; /* 緊貼圓形底部 */
        left: 50%;
        transform: translateX(-50%);
        width: 42px;
        height: 110px;
        background: linear-gradient(to right, #1e293b, #475569, #1e293b);
        border-radius: 6px 6px 20px 20px;
        box-shadow: 0 15px 25px rgba(0,0,0,0.5), inset 0 -5px 15px rgba(0,0,0,0.4);
        z-index: 5;
    }

    /* ================= 7. 放大鏡左上角：切換鏡頭 UI 按鈕 ================= */
    [data-testid="stCameraInput"]::after {
        content: '🔄 切換 ↗';
        position: absolute;
        top: 20px;
        left: 20px;
        background: rgba(30, 41, 59, 0.7); /* 深色毛玻璃底 */
        backdrop-filter: blur(5px);
        -webkit-backdrop-filter: blur(5px);
        color: #bae6fd; /* 冰藍色文字 */
        padding: 8px 16px;
        border-radius: 25px;
        font-size: 0.85rem;
        font-weight: bold;
        border: 1px solid rgba(186, 230, 253, 0.4);
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        z-index: 40; /* 確保在最上層 */
        pointer-events: none; /* 讓點擊能穿透到真實相機介面 */
    }

    /* 磨砂毛玻璃卡片 */
    .result-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 30px;
        border-radius: 24px;
        margin-top: 30px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        color: #F8FAFC;
    }

    h1 { 
        text-align: center; 
        background: -webkit-linear-gradient(45deg, #e0f2fe 0%, #7dd3fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: 2px;
        text-shadow: 0px 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    div.stButton > button {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 30px;
        padding: 10px 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 初始化繁簡轉換
cc = OpenCC('s2t')

if 'pokedex' not in st.session_state:
    st.session_state.pokedex = set()

# 動物資料庫
ANIMALS_DB = {
    "貝貝": {"type": "dog", "emoji": "🐶", "desc": "映澄最心愛的米克斯母狗，也是藝素村最溫柔的導嚮員。"},
    "牧耳": {"type": "dog", "emoji": "🐕", "desc": "充滿活力的夥伴，最喜歡在東北角的草地上奔跑。"},
    "小飛俠": {"type": "cat", "emoji": "🐈", "desc": "身手矯健，總是在屋頂上觀察探險家們。"},
    "嘿皮": {"type": "cat", "emoji": "🐈‍⬛", "desc": "個性大方的黑貓，討摸是牠的日常。"},
    "冬瓜": {"type": "cat", "emoji": "🐱", "desc": "圓滾滾的橘貓，是村裡的慵懶大王。"}
}

st.markdown("<h1>探險放大鏡 🔍</h1>", unsafe_allow_html=True)

mode = st.radio("", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True)

# ================= 3. 路線 A：尋找植物 =================
if mode == "🌿 尋找植物":
    
    # 直接呼叫相機，乾淨無包裝。CSS 會自動把手柄和左上角的按鈕渲染上去！
    picture = st.camera_input("")
    
    if picture:
        with st.status("💎 正在進行光學與圖鑑比對...", expanded=False) as status:
            API_KEY = "2b1004UqTrbWJn4mj5hqcaZN"
            api_url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}&lang=zh"
            files = [('images', (picture.name, picture.getvalue(), picture.type))]
            
            try:
                response = requests.post(api_url, files=files)
                if response.status_code == 200:
                    result = response.json()
                    best_match = result['results'][0]
                    sci_name = best_match['species']['scientificNameWithoutAuthor']
                    eng_name = next((n for n in best_match['species'].get('commonNames', []) if n.replace(" ","").isascii()), "N/A")
                    zh_name = cc.convert(next((n for n in best_match['species'].get('commonNames', []) if any('\u4e00' <= c <= '\u9fff' for c in n)), sci_name))
                    
                    description = "這是一株神秘的植物，百科中暫時找不到詳細故事。"
                    try:
                        wiki_res = requests.get(f"https://zh.wikipedia.org/api/rest_v1/page/summary/{zh_name}?redirect=true", headers={'Accept-Language': 'zh-tw'})
                        if wiki_res.status_code == 200:
                            description = cc.convert(wiki_res.json().get('extract', description))
                    except: pass
                    
                    status.update(label="✨ 分析完成", state="complete")

                    st.markdown(f"""
                        <div class="result-card">
                            <h2 style='color:#bae6fd; margin-top:0; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 10px;'>🌱 {zh_name}</h2>
                            <p style='color:#cbd5e1; margin-top: 15px;'><b>🇬🇧 英文俗名：</b> {eng_name}</p>
                            <p style='color:#cbd5e1;'><b>🔬 拉丁學名：</b> <i>{sci_name}</i></p>
                            <div style='background: rgba(0,0,0,0.2); padding: 15px; border-radius: 12px; margin-top: 15px;'>
                                <p style='line-height:1.8; font-size: 1rem; margin:0;'>{description}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.session_state.pokedex.add(zh_name)
            except Exception as e:
                st.error(f"分析失敗：{e}")

# ================= 4. 路線 B：認識動物 =================
elif mode == "🐾 認識動物":
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

    if 'active_pet' in st.session_state:
        pet = ANIMALS_DB[st.session_state.active_pet]
        st.markdown(f"""
            <div class="result-card">
                <h3 style='color:#bae6fd; margin-top:0;'>✨ 遇見了 {st.session_state.active_pet}！</h3>
                <div style='background: rgba(0,0,0,0.2); padding: 15px; border-radius: 12px; margin-top: 15px;'>
                    <p style='font-size: 1.1rem; line-height: 1.6; margin:0;'>{pet['desc']}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.session_state.pokedex.add(st.session_state.active_pet)

# ================= 5. 成就圖鑑 =================
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("🎒 我的探險圖鑑", expanded=False):
    if st.session_state.pokedex:
        count = len(st.session_state.pokedex)
        st.markdown(f"🌟 **已收集 {count} 種生物**")
        st.progress(min(count / 10, 1.0))
        st.write("，".join(st.session_state.pokedex))
        if count >= 3: st.balloons()
    else:
        st.write("圖鑑尚無紀錄，開始探索藝素村吧！")

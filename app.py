import streamlit as st
import requests
from opencc import OpenCC

# ================= 1. 冷冬風格與放大鏡進階 CSS =================
st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    /* 冷冬風格色調：深藍、銀灰、冰白 */
    .stApp {
        background: linear-gradient(135deg, #1A202C 0%, #2D3748 100%);
        color: #E2E8F0;
        font-family: '微軟正黑體', sans-serif;
    }

    /* 放大鏡核心容器 */
    .lens-container {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 20px;
    }

    /* 放大鏡圓形鏡面與邊框 */
    [data-testid="stCameraInput"] {
        width: 320px !important;
        height: 320px !important;
        border-radius: 50% !important;
        border: 14px solid #A0AEC0; /* 銀灰色邊框 */
        box-shadow: 0 0 30px rgba(0,0,0,0.5), inset 0 0 20px rgba(0,0,0,0.3);
        overflow: hidden;
        z-index: 2;
        background-color: #000;
    }

    /* 鏡面反光效果層 */
    .lens-glass {
        position: absolute;
        top: 20px;
        width: 320px;
        height: 320px;
        border-radius: 50%;
        background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0) 50%);
        pointer-events: none; /* 讓點擊穿透到相機 */
        z-index: 3;
    }

    /* 放大鏡握把 */
    .lens-handle {
        width: 35px;
        height: 100px;
        background: linear-gradient(to right, #4A5568, #A0AEC0, #4A5568);
        border-radius: 0 0 10px 10px;
        margin-top: -10px;
        z-index: 1;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }

    /* 美化切換按鈕提示 */
    .switch-tip {
        background-color: rgba(66, 153, 225, 0.2);
        color: #63B3ED;
        padding: 8px 15px;
        border-radius: 20px;
        border: 1px solid #63B3ED;
        font-size: 0.85rem;
        margin-top: 15px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* 結果顯示卡片 */
    .result-card {
        background-color: rgba(45, 55, 72, 0.8);
        backdrop-filter: blur(10px);
        padding: 25px;
        border-radius: 20px;
        margin-top: 30px;
        border: 1px solid rgba(255,255,255,0.1);
        color: #F7FAFC;
    }
    
    h1 { color: #F7FAFC; letter-spacing: 2px; }
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

st.markdown("<h1 style='text-align: center;'>探險放大鏡 🔍</h1>", unsafe_allow_html=True)

# 模式導航
mode = st.radio("", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True)

# ================= 3. 路線 A：尋找植物 =================
if mode == "🌿 尋找植物":
    st.markdown("<div class='lens-container'>", unsafe_allow_html=True)
    st.markdown("<div class='lens-glass'></div>", unsafe_allow_html=True)
    
    # 核心相機元件
    picture = st.camera_input("")
    
    st.markdown("<div class='lens-handle'></div>", unsafe_allow_html=True)
    
    # 前後鏡頭切換指引按鈕 (視覺美化)
    st.markdown("""
        <div class='switch-tip'>
            🔄 <b>提示：</b> 若想使用後鏡頭，請點擊相機右上角圖示切換
        </div>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    if picture:
        with st.status("💎 正在進行光學分析...", expanded=False) as status:
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
                            <h2 style='color:#63B3ED; margin-top:0;'>🌱 {zh_name}</h2>
                            <p style='color:#A0AEC0;'><b>🇬🇧 英文名稱：</b> {eng_name}</p>
                            <p style='color:#A0AEC0;'><b>🔬 拉丁學名：</b> <i>{sci_name}</i></p>
                            <hr style='border: 0.5px solid rgba(255,255,255,0.1);'>
                            <p style='line-height:1.8; font-size: 1.05rem;'>{description}</p>
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
            <div class="result-card" style="border-left: 5px solid #63B3ED;">
                <h3>✨ 遇見了 {st.session_state.active_pet}！</h3>
                <p style='font-size: 1.1rem; line-height: 1.6;'>{pet['desc']}</p>
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

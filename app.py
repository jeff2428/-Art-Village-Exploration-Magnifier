import streamlit as st
import requests
from opencc import OpenCC

# ================= 1. 放大鏡視覺與冷冬風格 CSS =================
st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    /* 全域冷冬風格 */
    .stApp {
        background: linear-gradient(135deg, #E6EAF0 0%, #D1D9E6 100%);
        color: #2D3748;
    }

    /* 放大鏡相機外框設計 */
    [data-testid="stCameraInput"] {
        width: 300px !important;
        height: 300px !important;
        margin: 0 auto;
        border: 12px solid #4A5568; /* 鏡框 */
        border-radius: 50% !important; /* 圓形鏡面 */
        overflow: hidden;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2), inset 0 0 20px rgba(255,255,255,0.5);
        position: relative;
        aspect-ratio: 1 / 1;
    }

    /* 放大鏡握把 */
    [data-testid="stCameraInput"]::after {
        content: "";
        position: absolute;
        bottom: -60px;
        left: 50%;
        transform: translateX(-50%);
        width: 30px;
        height: 80px;
        background: linear-gradient(to right, #2D3748, #4A5568, #2D3748);
        border-radius: 5px;
        z-index: -1;
    }

    /* 隱藏相機元件多餘的按鈕文字（選填，視需求調整） */
    [data-testid="stCameraInput"] button {
        border-radius: 10px !important;
    }

    .main-card {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-top: 80px; /* 為握把留空間 */
        border-top: 5px solid #2B6CB0;
    }
    
    h1 { color: #1A365D; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# 初始化繁簡轉換器
cc = OpenCC('s2t')

if 'pokedex' not in st.session_state:
    st.session_state.pokedex = set()

# 藝素村動物資料庫
ANIMALS_DB = {
    "貝貝": {"type": "dog", "emoji": "🐶", "desc": "溫柔可愛的米克斯母狗，是村莊的最佳嚮導。"},
    "牧耳": {"type": "dog", "emoji": "🐕", "desc": "活力充沛的夥伴，最喜歡在草地上奔跑。"},
    "小飛俠": {"type": "cat", "emoji": "🐈", "desc": "身手矯健，總是在屋頂上觀察大家。"},
    "嘿皮": {"type": "cat", "emoji": "🐈‍⬛", "desc": "個性大方的黑貓，聽到腳步聲會主動討摸。"},
    "冬瓜": {"type": "cat", "emoji": "🐱", "desc": "圓滾滾的橘貓，是村裡的慵懶大王。"}
}

st.markdown("<h1>🌿 藝素村探險放大鏡</h1>", unsafe_allow_html=True)

mode = st.radio("", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True)

# ================= 路線 A：尋找植物 =================
if mode == "🌿 尋找植物":
    st.write("<p style='text-align: center;'>💡 提示：若相機非後鏡頭，請點擊相機畫面右上角切換</p>", unsafe_allow_html=True)
    
    # 相機元件
    picture = st.camera_input("")
    
    if picture:
        with st.status("🔍 正在透過放大鏡分析中...", expanded=True) as status:
            API_KEY = "2b1004UqTrbWJn4mj5hqcaZN"
            api_url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}&lang=zh"
            files = [('images', (picture.name, picture.getvalue(), picture.type))]
            
            try:
                response = requests.post(api_url, files=files)
                if response.status_code == 200:
                    result = response.json()
                    best_match = result['results'][0]
                    sci_name = best_match['species']['scientificNameWithoutAuthor']
                    
                    # 英文俗名
                    eng_name = next((n for n in best_match['species'].get('commonNames', []) if n.replace(" ","").isascii()), "N/A")
                    # 繁體中文
                    zh_name = cc.convert(next((n for n in best_match['species'].get('commonNames', []) if any('\u4e00' <= c <= '\u9fff' for c in n)), sci_name))
                    
                    # 維基百科資料
                    description = "這是一株神秘的植物，百科中暫時找不到詳細介紹。"
                    aliases_str = ""
                    try:
                        wiki_res = requests.get(f"https://zh.wikipedia.org/api/rest_v1/page/summary/{zh_name}?redirect=true", headers={'Accept-Language': 'zh-tw'})
                        if wiki_res.status_code == 200:
                            wiki_json = wiki_res.json()
                            description = cc.convert(wiki_json.get('extract', description))
                    except: pass
                    
                    status.update(label="✅ 辨識完成！", state="complete")

                    # 結果顯示卡片
                    st.markdown(f"""
                        <div class="main-card">
                            <h2 style='color:#2C5282; margin-top:0;'>🌱 {zh_name}</h2>
                            <p><b>🇬🇧 英文名稱：</b> {eng_name}</p>
                            <p><b>🔬 拉丁學名：</b> <i>{sci_name}</i></p>
                            <hr>
                            <p style='color:#4A5568; line-height:1.6;'>{description}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    st.session_state.pokedex.add(zh_name)
                else:
                    st.error("辨識失敗，可能是額度用完或照片不清楚。")
            except Exception as e:
                st.error(f"連線異常: {e}")

# ================= 路線 B：認識動物 (略，同前版) =================
elif mode == "🐾 認識動物":
    # ... (保留前一版認識動物程式碼) ...
    st.write("請選擇您在藝素村遇到的動物夥伴！")
    # (為簡潔此處省略重複代碼，請直接沿用上一個回覆的動物部分)

import streamlit as st
import requests

# 1. 網頁基本與水彩風設定
st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")

# 注入自訂水彩繪本風 CSS (大地色系、圓角、柔和字體)
st.markdown("""
    <style>
    .stApp {
        background-color: #F7F3E8; /* 柔和米黃畫紙底色 */
        color: #4A3F35; /* 溫暖深棕色文字 */
        font-family: 'Comic Sans MS', '微軟正黑體', sans-serif;
    }
    div.stButton > button {
        background-color: #8DA399; /* 莫蘭迪綠 */
        color: white;
        border-radius: 20px;
        border: 2px solid #738A7F;
        padding: 10px 24px;
        font-weight: bold;
    }
    .animal-card {
        background: white;
        border-radius: 15px;
        padding: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌿 藝素村探險放大鏡 🔍")
st.write("拿起你的放大鏡，開始今天的村莊探險吧！")

# 2. 初始化探險圖鑑記錄 (Session State)
if 'pokedex' not in st.session_state:
    st.session_state.pokedex = set()

# 3. 建立動物靜態資料庫
ANIMALS_DB = {
    "貝比": {"img": "https://via.placeholder.com/150", "desc": "溫柔的米克斯，最喜歡在草地曬太陽。"},
    "貝果": {"img": "https://via.placeholder.com/150", "desc": "充滿活力的好夥伴，巡邏村莊是牠的任務！"},
    "大橘": {"img": "https://via.placeholder.com/150", "desc": "村裡的睡神，通常出現在溫暖的角落。"}
}

# 4. 雙入口選單
mode = st.radio("你想探索什麼呢？", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True)

st.divider()

# ================= 路線 A：尋找植物 =================
if mode == "🌿 尋找植物":
    st.subheader("拍下你眼前的植物吧！")
    
    # 提示：為了追求極致體驗，未來可在此處嵌入自訂 HTML/JS (navigator.mediaDevices.getUserMedia) 來強制鎖定後置鏡頭
    # 目前先以原生元件作為 MVP 測試
    picture = st.camera_input("📷 開啟相機")
    
    if picture:
        st.info("魔法放大鏡辨識中...")
        # 實作邏輯：
        # 1. 將 picture 傳送至 PlantNet API (帶入您的 APIKEY: 2b1004UqTrbWJn4mj5hqcaZN)
        # 2. 取得 score 最高的 scientificNameWithoutAuthor
        # 3. 將學名傳入 Wikipedia API (https://zh.wikipedia.org/w/api.php) 查詢繁體中文與摘要
        
        # 模擬辨識成功
        fake_plant_name = "台灣山蘇花"
        st.success(f"找到了！這是：**{fake_plant_name}**")
        st.write("【生物學小知識】：附生性蕨類植物，喜歡生長在潮濕的樹幹或岩石上...")
        
        # 加入圖鑑
        st.session_state.pokedex.add(fake_plant_name)

# ================= 路線 B：認識動物 =================
elif mode == "🐾 認識動物":
    st.subheader("點擊大頭貼，看看你遇到的是誰？")
    
    # 網格狀排列動物大頭貼
    cols = st.columns(3)
    for idx, (name, data) in enumerate(ANIMALS_DB.items()):
        with cols[idx % 3]:
            # 使用按鈕當作大頭貼選擇
            if st.button(f"🐶 {name}"):
                st.session_state.selected_animal = name

    # 點開後的詳細介紹
    if 'selected_animal' in st.session_state:
        animal_name = st.session_state.selected_animal
        st.markdown(f"### 嗨！我是 {animal_name}")
        st.image(ANIMALS_DB[animal_name]["img"], use_column_width=True)
        st.write(ANIMALS_DB[animal_name]["desc"])
        
        # 加入圖鑑
        st.session_state.pokedex.add(animal_name)

# ================= 探險圖鑑與彩蛋機制 =================
st.divider()
st.subheader("🎒 你的探險圖鑑")
st.write(f"目前已收集：{len(st.session_state.pokedex)} 種驚喜！")

if len(st.session_state.pokedex) > 0:
    st.write("、".join(list(st.session_state.pokedex)))

# 達成目標觸發隱藏彩蛋 (例如集滿 3 種)
if len(st.session_state.pokedex) >= 3:
    st.balloons()
    st.success("🎉 恭喜達成探險目標！解鎖隱藏彩蛋！")
    st.write("🌟 **村莊守護者稱號達成！** 感謝你用心觀察這片土地，請截圖這張專屬紀念明信片！")
    # 這裡可以放入一張精美的水彩畫紀念圖

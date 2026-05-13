import streamlit as st
import requests

# ================= 1. 網頁基本與水彩風設定 =================
st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")

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
    </style>
""", unsafe_allow_html=True)

st.title("🌿 藝素村探險放大鏡 🔍")
st.write("拿起你的放大鏡，開始今天的村莊探險吧！")

# ================= 2. 初始化探險圖鑑記錄 =================
if 'pokedex' not in st.session_state:
    st.session_state.pokedex = set()

# ================= 3. 建立動物靜態資料庫 =================
# 小提醒：未來可以將圖片網址替換為上傳到 Github 的真實照片檔名 (例如: "beibei.jpg")
ANIMALS_DB = {
    "貝貝": {"type": "dog", "img": "https://images.unsplash.com/photo-1543466835-00a7907e9de1", "desc": "溫柔可愛的狗狗，喜歡在村莊裡散步！"},
    "牧耳": {"type": "dog", "img": "https://images.unsplash.com/photo-1517849845537-4d257902454a", "desc": "充滿活力的狗狗夥伴，巡邏是牠的任務。"},
    "小飛俠": {"type": "cat", "img": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba", "desc": "身手敏捷，像飛俠一樣穿梭在村莊的各個角落。"},
    "嘿皮": {"type": "cat", "img": "https://images.unsplash.com/photo-1495360010541-f48722b34f7d", "desc": "總是開開心心的貓咪，聽到名字就會看著你。"},
    "冬瓜": {"type": "cat", "img": "https://images.unsplash.com/photo-1573865526739-10659fec78a5", "desc": "圓滾滾又慵懶，最喜歡在溫暖的地方曬太陽。"}
}

# ================= 4. 雙入口選單 =================
mode = st.radio("你想探索什麼呢？", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True)
st.divider()

# ================= 路線 A：尋找植物 =================
if mode == "🌿 尋找植物":
    st.subheader("拍下你眼前的植物吧！")
    picture = st.camera_input("📷 開啟相機")
    
    if picture:
        st.info("🔍 魔法放大鏡辨識中，請稍候...")
        
        # PlantNet API 辨識設定
        API_KEY = st.secrets["PLANTNET_API_KEY"]
        api_url = f"https://my.api.plantnet.org/v2/identify/all?api-key={API_KEY}"
        files = [('images', (picture.name, picture.getvalue(), picture.type))]
        
        try:
            # 發送照片至 PlantNet
            response = requests.post(api_url, files=files)
            result = response.json()
            
            if response.status_code == 200 and result.get('results'):
                # 取得分數最高的學名
                best_match = result['results'][0]
                scientific_name = best_match['species']['scientificNameWithoutAuthor']
                st.success(f"辨識成功！學名：*{scientific_name}*")
                
                # 透過開源 Wikipedia API 查詢繁體中文資訊
                wiki_url = f"https://zh.wikipedia.org/api/rest_v1/page/summary/{scientific_name}"
                wiki_res = requests.get(wiki_url)
                
                if wiki_res.status_code == 200:
                    wiki_data = wiki_res.json()
                    display_name = wiki_data.get('title', scientific_name)
                    # 如果維基百科沒有簡介，給予預設文字
                    description = wiki_data.get('extract', "在圖鑑裡暫時找不到這株植物的詳細中文故事，但它依然是村莊裡美麗的存在！")
                    
                    st.markdown(f"### 🌿 {display_name}")
                    st.write(description)
                    st.session_state.pokedex.add(display_name)
                else:
                    # 若維基百科查無此學名
                    st.markdown(f"### 🌿 {scientific_name}")
                    st.write("這是一株神秘的植物，百科中尚未有完整的繁體中文介紹！")
                    st.session_state.pokedex.add(scientific_name)
            else:
                st.error("辨識失敗，這株植物太神秘了，請換個角度再拍一次看看！")
        except Exception as e:
            st.error("網路連線似乎有點問題，請稍後再試！")

# ================= 路線 B：認識動物 =================
elif mode == "🐾 認識動物":
    st.subheader("點擊大頭貼，看看你遇到的是誰？")
    
    # 狗狗專區
    st.markdown("#### 🐶 狗狗夥伴")
    dog_cols = st.columns(3)
    dogs = {k: v for k, v in ANIMALS_DB.items() if v["type"] == "dog"}
    for idx, (name, data) in enumerate(dogs.items()):
        with dog_cols[idx % 3]:
            if st.button(f"🐶 {name}", key=f"btn_{name}"):
                st.session_state.selected_animal = name
                
    st.markdown("---")
    
    # 貓咪專區
    st.markdown("#### 🐱 貓咪夥伴")
    cat_cols = st.columns(3)
    cats = {k: v for k, v in ANIMALS_DB.items() if v["type"] == "cat"}
    for idx, (name, data) in enumerate(cats.items()):
        with cat_cols[idx % 3]:
            if st.button(f"🐱 {name}", key=f"btn_{name}"):
                st.session_state.selected_animal = name

    # 點開後的詳細介紹
    if 'selected_animal' in st.session_state:
        st.divider()
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

# 達成目標觸發隱藏彩蛋 (例如集滿 3 種動植物)
if len(st.session_state.pokedex) >= 3:
    st.balloons()
    st.success("🎉 恭喜達成探險目標！解鎖隱藏彩蛋！")
    st.write("🌟 **村莊守護者稱號達成！** 感謝你用心觀察這片土地，請截圖這張專屬紀念明信片！")

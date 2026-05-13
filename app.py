import streamlit as st
import requests

# ================= 1. 網頁基本與視覺風格設定 =================
st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #F7F3E8; /* 柔和米黃畫紙底色 */
        color: #4A3F35; /* 溫暖深棕色文字 */
        font-family: '微軟正黑體', 'Apple LiGothic Medium', sans-serif;
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
st.write("拿起你的放大鏡，在藝素村開啟一段與自然對話的探險吧！")

# ================= 2. 初始化探險圖鑑記錄 =================
if 'pokedex' not in st.session_state:
    st.session_state.pokedex = set()

# ================= 3. 建立動物靜態資料庫 =================
ANIMALS_DB = {
    "貝貝": {"type": "dog", "img": "https://images.unsplash.com/photo-1543466835-00a7907e9de1", "desc": "溫柔可愛的狗狗，喜歡在村莊裡散步！"},
    "牧耳": {"type": "dog", "img": "https://images.unsplash.com/photo-1517849845537-4d257902454a", "desc": "充滿活力的狗狗夥伴，巡邏是牠的任務。"},
    "小飛俠": {"type": "cat", "img": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba", "desc": "身手敏捷，像飛俠一樣穿梭在村莊的各個角落。"},
    "嘿皮": {"type": "cat", "img": "https://images.unsplash.com/photo-1495360010541-f48722b34f7d", "desc": "總是開開心心的貓咪，聽到名字就會看著你。"},
    "冬瓜": {"type": "cat", "img": "https://images.unsplash.com/photo-1573865526739-10659fec78a5", "desc": "圓滾滾又慵懶，最喜歡在溫暖的地方曬太陽。"}
}

# ================= 4. 模式切換 =================
mode = st.radio("你想探索什麼呢？", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True)
st.divider()

# ================= 路線 A：尋找植物 =================
if mode == "🌿 尋找植物":
    picture = st.camera_input("📷 拍下眼前的植物")
    
    if picture:
        st.info("🔍 魔法放大鏡辨識中，請稍候...")
        
        API_KEY = "2b1004UqTrbWJn4mj5hqcaZN"
        api_url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}&lang=zh"
        files = [('images', (picture.name, picture.getvalue(), picture.type))]
        
        try:
            response = requests.post(api_url, files=files)
            if response.status_code == 200:
                result = response.json()
                best_match = result['results'][0]
                sci_name = best_match['species']['scientificNameWithoutAuthor']
                
                # --- 中文化邏輯 ---
                display_name = sci_name
                common_names = best_match['species'].get('commonNames', [])
                for name in common_names:
                    if any('\u4e00' <= char <= '\u9fff' for char in name): # 優先選包含中文的名字
                        display_name = name
                        break
                
                # 如果還是學名，呼叫 Wikidata 進行翻譯
                if display_name == sci_name:
                    wd_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={sci_name}&language=en&format=json"
                    wd_data = requests.get(wd_url).json()
                    if wd_data.get('search'):
                        q_id = wd_data['search'][0]['id']
                        label_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={q_id}&props=labels&languages=zh-tw|zh-hant|zh&format=json"
                        labels = requests.get(label_url).json().get('entities', {}).get(q_id, {}).get('labels', {})
                        for lang in ['zh-tw', 'zh-hant', 'zh']:
                            if lang in labels:
                                display_name = labels[lang]['value']
                                break

                st.success(f"辨識成功！這是：{display_name}")

                # --- 獲取百科介紹 (加入防崩潰檢查) ---
                description = "這是一株神秘的植物，百科中暫時找不到詳細的中文故事，但它依然是村莊裡美麗的存在！"
                try:
                    # 使用 Wikipedia Summary API 並指定繁體中文
                    wiki_url = f"https://zh.wikipedia.org/api/rest_v1/page/summary/{display_name}?redirect=true"
                    wiki_res = requests.get(wiki_url)
                    if wiki_res.status_code == 200:
                        wiki_data = wiki_res.json()
                        description = wiki_data.get('extract', description)
                except:
                    pass

                st.markdown(f"### 🌿 {display_name}")
                st.write(description)
                st.session_state.pokedex.add(display_name)
            else:
                st.error(f"連線異常，請確認網路或 API 額度 (錯誤代碼: {response.status_code})")
        except Exception as e:
            st.error(f"系統忙碌中，請再拍一次看看！(錯誤資訊: {e})")

# ================= 路線 B：認識動物 =================
elif mode == "🐾 認識動物":
    st.subheader("點擊大頭貼，看看你遇到的是誰？")
    
    for pet_type, emoji in [("dog", "🐶 狗狗夥伴"), ("cat", "🐱 貓咪夥伴")]:
        st.markdown(f"#### {emoji}")
        cols = st.columns(3)
        pets = {k: v for k, v in ANIMALS_DB.items() if v["type"] == pet_type}
        for idx, (name, data) in enumerate(pets.items()):
            with cols[idx % 3]:
                if st.button(f"{name}", key=f"btn_{name}"):
                    st.session_state.selected_animal = name

    if 'selected_animal' in st.session_state:
        st.divider()
        name = st.session_state.selected_animal
        st.markdown(f"### 嗨！我是 {name}")
        st.image(ANIMALS_DB[name]["img"], use_column_width=True)
        st.write(ANIMALS_DB[name]["desc"])
        st.session_state.pokedex.add(name)

# ================= 探險圖鑑 =================
st.divider()
st.subheader("🎒 你的探險圖鑑")
st.write(f"目前已收集：{len(st.session_state.pokedex)} 種驚喜！")
if st.session_state.pokedex:
    st.write("、".join(list(st.session_state.pokedex)))

if len(st.session_state.pokedex) >= 3:
    st.balloons()
    st.success("🎉 恭喜達成探險目標！你已經是藝素村的植物小達人了！")

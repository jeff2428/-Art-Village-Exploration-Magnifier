import streamlit as st
import requests

# ================= 1. 視覺風格設定 =================
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
    /* 調整相機元件寬度 */
    .stCameraInput { width: 100%; max-width: 500px; margin: 0 auto; }
    </style>
""", unsafe_allow_html=True)

st.title("🌿 藝素村探險放大鏡 🔍")
st.write("拿起你的放大鏡，開啟一段與自然對話的探險吧！")

# ================= 2. 初始化探險圖鑑記錄 =================
if 'pokedex' not in st.session_state:
    st.session_state.pokedex = set()

# ================= 3. 建立動物靜態資料庫 =================
# 
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
    picture = st.camera_input("📷 點擊按鈕開啟相機")
    
    if picture:
        st.info("🔍 魔法放大鏡正在查閱中文圖鑑，請稍候...")
        
        # PlantNet API 辨識設定
        API_KEY = "2b1004UqTrbWJn4mj5hqcaZN"
        # 加入 lang=zh-tw 嘗試獲取原始中文支援
        api_url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}&lang=zh-tw"
        files = [('images', (picture.name, picture.getvalue(), picture.type))]
        
        try:
            response = requests.post(api_url, files=files, timeout=20)
            
            # 診斷：若伺服器回傳非 200 狀態碼
            if response.status_code != 200:
                st.error(f"📡 伺服器連線異常 (代碼 {response.status_code})")
                if response.status_code == 429:
                    st.warning("⚠️ 辨識次數已達本月上限，請明天再試試看！")
                elif response.status_code == 413:
                    st.warning("⚠️ 照片檔案太大，請嘗試拿遠一點重新拍攝。")
            else:
                result = response.json()
                if result.get('results'):
                    best_match = result['results'][0]
                    sci_name = best_match['species']['scientificNameWithoutAuthor']
                    
                    # 優先尋找中文俗名
                    display_name = sci_name
                    common_names = best_match['species'].get('commonNames', [])
                    if common_names:
                        display_name = common_names[0]
                    
                    # --- 強化中文化機制：若名稱仍為英文則調用 Wikidata ---
                    if display_name.replace(" ", "").isascii():
                        try:
                            wd_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={sci_name}&language=en&format=json"
                            wd_res = requests.get(wd_url).json()
                            if wd_res.get('search'):
                                q_id = wd_res['search'][0]['id']
                                label_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={q_id}&props=labels&languages=zh-tw|zh-hant|zh&format=json"
                                labels = requests.get(label_url).json().get('entities', {}).get(q_id, {}).get('labels', {})
                                for lang in ['zh-tw', 'zh-hant', 'zh']:
                                    if lang in labels:
                                        display_name = labels[lang]['value']
                                        break
                        except:
                            pass

                    st.success(f"辨識成功！這株植物是：{display_name}")

                    # --- 抓取維基百科內容 ---
                    description = "這是一株神秘的植物，百科中暫時找不到詳細的中文故事，但它依然是村莊裡美麗的存在！"
                    aliases_str = ""
                    try:
                        wiki_api = f"https://zh.wikipedia.org/w/api.php?action=query&prop=extracts|redirects&exintro&explaintext&titles={display_name}&format=json&redirects=1"
                        wiki_res = requests.get(wiki_api).json().get('query', {}).get('pages', {})
                        for pg_id, pg_info in wiki_res.items():
                            if pg_id != "-1":
                                description = pg_info.get('extract', description)[:250] + "..."
                                reds = pg_info.get('redirects', [])
                                if reds:
                                    aliases_str = "、".join([r['title'] for r in reds if ":" not in r['title']][:5])
                    except:
                        pass

                    st.markdown(f"### 🌿 {display_name}")
                    if aliases_str:
                        st.caption(f"💡 **別名**：{aliases_str}")
                    st.write(description)
                    st.session_state.pokedex.add(display_name)
                else:
                    st.warning("拍得不夠清楚，魔法放大鏡看不出來，請換個角度試試！")
                    
        except requests.exceptions.JSONDecodeError:
            st.error("❌ 伺服器回傳格式錯誤。可能是因為照片太大或網路不穩，請重新拍攝。")
        except Exception as e:
            st.error(f"連線異常：{e}")

# ================= 路線 B：認識動物 =================
elif mode == "🐾 認識動物":
    st.subheader("點擊大頭貼，看看你遇到的是誰？")
    
    for pet_type, emoji in [("dog", "🐶 狗狗"), ("cat", "🐱 貓咪")]:
        st.markdown(f"#### {emoji}夥伴")
        cols = st.columns(3)
        pets = {k: v for k, v in ANIMALS_DB.items() if v["type"] == pet_type}
        for idx, (name, data) in enumerate(pets.items()):
            with cols[idx % 3]:
                if st.button(f"{name}", key=f"btn_{name}"):
                    st.session_state.selected_animal = name

    if 'selected_animal' in st.session_state:
        st.divider()
        animal_name = st.session_state.selected_animal
        st.markdown(f"### 嗨！我是 {animal_name}")
        st.image(ANIMALS_DB[animal_name]["img"], use_column_width=True)
        st.write(ANIMALS_DB[animal_name]["desc"])
        st.session_state.pokedex.add(animal_name)

# ================= 探險圖鑑 =================
st.divider()
st.subheader("🎒 你的探險圖鑑")
st.write(f"目前已收集：{len(st.session_state.pokedex)} 種驚喜！")
if st.session_state.pokedex:
    st.write("、".join(list(st.session_state.pokedex)))

if len(st.session_state.pokedex) >= 3:
    st.balloons()
    st.success("🎉 恭喜達成探險目標！解鎖隱藏彩蛋！")

import streamlit as st
import requests

# ================= 1. 網頁基本與水彩風設定 =================
st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #F7F3E8;
        color: #4A3F35;
        font-family: 'Comic Sans MS', '微軟正黑體', sans-serif;
    }
    div.stButton > button {
        background-color: #8DA399;
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
        
        API_KEY = "2b1004UqTrbWJn4mj5hqcaZN"
        # 加上 lang=zh-tw 嘗試讓 PlantNet 直接回傳繁體中文
        api_url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}&lang=zh-tw"
        files = [('images', (picture.name, picture.getvalue(), picture.type))]
        
        try:
            response = requests.post(api_url, files=files)
            result = response.json()
            
            if response.status_code == 200 and result.get('results'):
                best_match = result['results'][0]
                scientific_name = best_match['species']['scientificNameWithoutAuthor']
                
                # 取得 PlantNet 的俗名，若沒有則用學名
                common_names = best_match['species'].get('commonNames', [])
                display_name = common_names[0] if common_names else scientific_name
                
                # --- 強制繁體中文翻譯機制 (利用 Wikidata) ---
                # 如果目前的名稱全是英文(isascii)，代表系統沒給中文，我們自己去開源庫查
                if display_name.isascii():
                    try:
                        # 用學名查 Wikidata 的 ID
                        wd_search_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={scientific_name}&language=en&format=json"
                        wd_res = requests.get(wd_search_url).json()
                        if wd_res.get('search'):
                            q_id = wd_res['search'][0]['id']
                            # 用 ID 抓取台灣繁體或標準中文
                            wd_entity_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={q_id}&props=labels&languages=zh-tw|zh-hant|zh&format=json"
                            entity_res = requests.get(wd_entity_url).json()
                            labels = entity_res.get('entities', {}).get(q_id, {}).get('labels', {})
                            for lang in ['zh-tw', 'zh-hant', 'zh']:
                                if lang in labels:
                                    display_name = labels[lang]['value']
                                    break
                    except Exception:
                        pass # 萬一 Wikidata 查不到，就保留原英文名

                st.success(f"辨識成功！(學名匹配：*{scientific_name}*)")
                
                # --- 準備查詢維基百科簡介與別名 ---
                description = "這是一株神秘的植物，百科中暫時找不到詳細的中文故事，但它依然是村莊裡美麗的存在！"
                aliases_str = ""
                
                try:
                    # 使用已經翻譯好的中文名稱去搜尋維基百科
                    wiki_search_url = f"https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch={display_name}&utf8=&format=json&srlimit=1"
                    wiki_res = requests.get(wiki_search_url).json()
                    
                    if wiki_res.get('query', {}).get('search'):
                        zh_title = wiki_res['query']['search'][0]['title']
                        
                        # 1. 取得中文摘要
                        wiki_summary_url = f"https://zh.wikipedia.org/api/rest_v1/page/summary/{zh_title}"
                        summary_data = requests.get(wiki_summary_url).json()
                        if summary_data.get('extract'):
                            description = summary_data['extract']
                            
                        # 2. 取得別名
                        wiki_aliases_url = f"https://zh.wikipedia.org/w/api.php?action=query&prop=redirects&titles={zh_title}&format=json&utf8="
                        aliases_data = requests.get(wiki_aliases_url).json()
                        pages = aliases_data.get('query', {}).get('pages', {})
                        for page_id, page_info in pages.items():
                            redirects = page_info.get('redirects', [])
                            if redirects:
                                aliases = [r['title'] for r in redirects if ":" not in r['title'] and "：" not in r['title'] and "List" not in r['title']]
                                if aliases:
                                    aliases_str = "、".join(aliases[:5])
                except Exception:
                    pass

                # 顯示最終結果
                st.markdown(f"### 🌿 {display_name}")
                if aliases_str:
                    st.caption(f"💡 **別名 / 相關稱呼**：{aliases_str}")
                st.write(description)
                
                # 加入圖鑑
                st.session_state.pokedex.add(display_name)
                
            else:
                st.error("辨識失敗，這株植物太神秘了，請換個角度再拍一次看看！")
        except Exception as e:
            st.error(f"系統錯誤詳細資訊：{e}")

# ================= 路線 B：認識動物 =================
elif mode == "🐾 認識動物":
    st.subheader("點擊大頭貼，看看你遇到的是誰？")
    
    st.markdown("#### 🐶 狗狗夥伴")
    dog_cols = st.columns(3)
    dogs = {k: v for k, v in ANIMALS_DB.items() if v["type"] == "dog"}
    for idx, (name, data) in enumerate(dogs.items()):
        with dog_cols[idx % 3]:
            if st.button(f"🐶 {name}", key=f"btn_{name}"):
                st.session_state.selected_animal = name
                
    st.markdown("---")
    
    st.markdown("#### 🐱 貓咪夥伴")
    cat_cols = st.columns(3)
    cats = {k: v for k, v in ANIMALS_DB.items() if v["type"] == "cat"}
    for idx, (name, data) in enumerate(cats.items()):
        with cat_cols[idx % 3]:
            if st.button(f"🐱 {name}", key=f"btn_{name}"):
                st.session_state.selected_animal = name

    if 'selected_animal' in st.session_state:
        st.divider()
        animal_name = st.session_state.selected_animal
        st.markdown(f"### 嗨！我是 {animal_name}")
        st.image(ANIMALS_DB[animal_name]["img"], use_column_width=True)
        st.write(ANIMALS_DB[animal_name]["desc"])
        
        st.session_state.pokedex.add(animal_name)

# ================= 探險圖鑑與彩蛋機制 =================
st.divider()
st.subheader("🎒 你的探險圖鑑")
st.write(f"目前已收集：{len(st.session_state.pokedex)} 種驚喜！")

if len(st.session_state.pokedex) > 0:
    st.write("、".join(list(st.session_state.pokedex)))

if len(st.session_state.pokedex) >= 3:
    st.balloons()
    st.success("🎉 恭喜達成探險目標！解鎖隱藏彩蛋！")
    st.write("🌟 **村莊守護者稱號達成！** 感謝你用心觀察這片土地，請截圖這張專屬紀念明信片！")

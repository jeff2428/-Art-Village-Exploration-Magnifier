import streamlit as st
import requests

# ================= 1. 視覺風格設定 =================
st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F7F3E8; color: #4A3F35; font-family: '微軟正黑體', sans-serif; }
    div.stButton > button { background-color: #8DA399; color: white; border-radius: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🌿 藝素村探險放大鏡 🔍")

# 初始化圖鑑
if 'pokedex' not in st.session_state:
    st.session_state.pokedex = set()

# 動物資料庫
ANIMALS_DB = {
    "貝貝": {"type": "dog", "img": "https://images.unsplash.com/photo-1543466835-00a7907e9de1", "desc": "溫柔可愛的狗狗。"},
    "牧耳": {"type": "dog", "img": "https://images.unsplash.com/photo-1517849845537-4d257902454a", "desc": "充滿活力的狗狗。"},
    "小飛俠": {"type": "cat", "img": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba", "desc": "身手敏捷的貓咪。"},
    "嘿皮": {"type": "cat", "img": "https://images.unsplash.com/photo-1495360010541-f48722b34f7d", "desc": "愛撒嬌的貓咪。"},
    "冬瓜": {"type": "cat", "img": "https://images.unsplash.com/photo-1573865526739-10659fec78a5", "desc": "圓滾滾的橘貓。"}
}

mode = st.radio("探索模式", ["🌿 尋找植物", "🐾 認識動物"], horizontal=True)

# ================= 路線 A：尋找植物 (加強中文化) =================
if mode == "🌿 尋找植物":
    picture = st.camera_input("📷 拍下植物")
    
    if picture:
        st.info("🔍 魔法放大鏡正在查閱中文圖鑑...")
        
        API_KEY = "2b1004UqTrbWJn4mj5hqcaZN"
        # 強制要求繁體中文語系回傳
        api_url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}&lang=zh-tw"
        files = [('images', (picture.name, picture.getvalue(), picture.type))]
        
        try:
            response = requests.post(api_url, files=files)
            result = response.json()
            
            if response.status_code == 200 and result.get('results'):
                best_match = result['results'][0]
                sci_name = best_match['species']['scientificNameWithoutAuthor']
                
                # 優先抓取 PlantNet 回傳的中文俗名
                display_name = sci_name
                common_names = best_match['species'].get('commonNames', [])
                if common_names:
                    display_name = common_names[0]
                
                # 如果名稱還是英文/學名，啟動 Wikidata 強制中文化
                if display_name.replace(" ", "").isascii():
                    wd_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={sci_name}&language=en&format=json"
                    wd_data = requests.get(wd_url).json()
                    if wd_data.get('search'):
                        q_id = wd_data['search'][0]['id']
                        label_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={q_id}&props=labels&languages=zh-tw|zh-hk|zh-hant|zh&format=json"
                        labels = requests.get(label_url).json().get('entities', {}).get(q_id, {}).get('labels', {})
                        for lang in ['zh-tw', 'zh-hant', 'zh-hk', 'zh']:
                            if lang in labels:
                                display_name = labels[lang]['value']
                                break

                st.success(f"辨識成功！這株植物是：{display_name}")

                # 抓取維基百科簡介與別名
                description = "這是藝素村美麗的植物夥伴！目前詳細百科還在編寫中..."
                aliases_str = ""
                
                wiki_api = f"https://zh.wikipedia.org/w/api.php?action=query&prop=extracts|redirects&exintro&explaintext&titles={display_name}&format=json&redirects=1"
                wiki_data = requests.get(wiki_api).json().get('query', {}).get('pages', {})
                
                for pg_id, pg_info in wiki_data.items():
                    if pg_id != "-1":
                        description = pg_info.get('extract', description)[:200] + "..."
                        reds = pg_info.get('redirects', [])
                        if reds:
                            aliases_str = "、".join([r['title'] for r in reds if ":" not in r['title']][:5])

                st.markdown(f"### 🌿 {display_name}")
                if aliases_str:
                    st.caption(f"💡 **別名**：{aliases_str}")
                st.write(description)
                st.session_state.pokedex.add(display_name)
            else:
                st.error("拍得不夠清楚，再試一次吧！")
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
        name = st.session_state.selected_animal
        st.markdown(f"### 嗨！我是 {name}")
        st.image(ANIMALS_DB[name]["img"], use_column_width=True)
        st.write(ANIMALS_DB[name]["desc"])
        st.session_state.pokedex.add(name)

# ================= 圖鑑機制 =================
st.divider()
st.subheader("🎒 你的探險圖鑑")
st.write(f"目前已收集：{len(st.session_state.pokedex)} 種驚喜！")
if st.session_state.pokedex:
    st.write("、".join(list(st.session_state.pokedex)))

if len(st.session_state.pokedex) >= 3:
    st.balloons()
    st.success("🎉 恭喜達成探險目標！")

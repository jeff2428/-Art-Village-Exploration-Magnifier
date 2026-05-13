import streamlit as st
import requests
from opencc import OpenCC # 引入繁簡轉換工具

# ================= 1. 視覺與網頁設定 =================
st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #F7F3E8; 
        color: #4A3F35; 
        font-family: '微軟正黑體', sans-serif;
    }
    div.stButton > button {
        background-color: #8DA399; 
        color: white; 
        border-radius: 20px; 
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌿 藝素村探險放大鏡 🔍")

# 初始化繁簡轉換器 (s2t: 簡體轉台灣繁體)
cc = OpenCC('s2t')

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

# ================= 路線 A：尋找植物 =================
if mode == "🌿 尋找植物":
    picture = st.camera_input("📷 拍下植物")
    
    if picture:
        st.info("🔍 魔法放大鏡正在轉換繁體百科...")
        API_KEY = "2b1004UqTrbWJn4mj5hqcaZN"
        api_url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}&lang=zh"
        files = [('images', (picture.name, picture.getvalue(), picture.type))]
        
        try:
            response = requests.post(api_url, files=files)
            if response.status_code == 200:
                result = response.json()
                best_match = result['results'][0]
                
                # 1. 抓取學名與英文名
                sci_name = best_match['species']['scientificNameWithoutAuthor']
                eng_name = ""
                common_names = best_match['species'].get('commonNames', [])
                
                # 尋找英文俗名 (過濾掉學名和中文)
                for name in common_names:
                    if name.replace(" ", "").isascii() and name.lower() != sci_name.lower():
                        eng_name = name
                        break

                # 2. 處理繁體中文名稱
                zh_name = sci_name
                for name in common_names:
                    if any('\u4e00' <= char <= '\u9fff' for char in name):
                        zh_name = cc.convert(name) # 轉為繁體
                        break
                
                st.success(f"辨識成功！這株植物是：{zh_name}")

                # 3. 獲取百科介紹與別名
                description = "這是一株神秘的植物，百科中暫時找不到詳細的中文故事，但它依然是村莊裡美麗的存在！"
                aliases_str = ""
                
                try:
                    # 先搜尋精確條目
                    wiki_search = f"https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch={zh_name}&format=json"
                    search_data = requests.get(wiki_search).json()
                    
                    if search_data.get('query', {}).get('search'):
                        title = search_data['query']['search'][0]['title']
                        # 抓取繁體摘要
                        summary_url = f"https://zh.wikipedia.org/api/rest_v1/page/summary/{title}"
                        wiki_res = requests.get(summary_url, headers={'Accept-Language': 'zh-tw'})
                        if wiki_res.status_code == 200:
                            description = cc.convert(wiki_res.json().get('extract', description))

                        # 抓取別名
                        alias_url = f"https://zh.wikipedia.org/w/api.php?action=query&prop=redirects&titles={title}&format=json"
                        alias_data = requests.get(alias_url).json()
                        pages = alias_data.get('query', {}).get('pages', {})
                        for pid, pinfo in pages.items():
                            reds = pinfo.get('redirects', [])
                            if reds:
                                aliases_str = "、".join([cc.convert(r['title']) for r in reds if ":" not in r['title']][:5])
                except:
                    pass

                # 顯示結果
                st.markdown(f"### 🌿 {zh_name}")
                
                # --- 清楚顯示英文名與學名 ---
                if eng_name:
                    st.markdown(f"**📖 英文俗名**：*{eng_name}*")
                st.markdown(f"**🔬 拉丁文學名**：*{sci_name}*")
                
                if aliases_str:
                    st.markdown(f"**💡 相關別名**：{aliases_str}")
                st.divider()
                st.write(description)
                st.session_state.pokedex.add(zh_name)
            else:
                st.error("拍得不夠清楚，請再試一次！")
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
        n = st.session_state.selected_animal
        st.markdown(f"### 嗨！我是 {n}")
        st.image(ANIMALS_DB[n]["img"], use_column_width=True)
        st.write(ANIMALS_DB[n]["desc"])
        st.session_state.pokedex.add(n)

# ================= 探險圖鑑 =================
st.divider()
st.subheader("🎒 你的探險圖鑑")
st.write(f"目前已收集：{len(st.session_state.pokedex)} 種驚喜！")
if st.session_state.pokedex:
    st.write("、".join(list(st.session_state.pokedex)))
if len(st.session_state.pokedex) >= 3:
    st.balloons()

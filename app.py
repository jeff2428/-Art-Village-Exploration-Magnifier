import streamlit as st
import requests
from opencc import OpenCC # 引入繁簡轉換工具

# ================= 1. 網頁基本與視覺風格設定 =================
st.set_page_config(page_title="藝素村探險放大鏡", page_icon="🔍", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F7F3E8; color: #4A3F35; font-family: '微軟正黑體', sans-serif; }
    div.stButton > button { background-color: #8DA399; color: white; border-radius: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🌿 藝素村探險放大鏡 🔍")
st.write("拿起你的放大鏡，在藝素村開啟一段與自然對話的探險吧！")

# 初始化繁簡轉換器 (簡體轉繁體)
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
    picture = st.camera_input("📷 拍下眼前的植物")
    
    if picture:
        st.info("🔍 魔法放大鏡翻閱圖鑑中...")
        API_KEY = "2b1004UqTrbWJn4mj5hqcaZN"
        api_url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}&lang=zh"
        files = [('images', (picture.name, picture.getvalue(), picture.type))]
        
        try:
            response = requests.post(api_url, files=files)
            if response.status_code == 200:
                result = response.json()
                best_match = result['results'][0]
                
                # 抓取學名與英文名
                sci_name = best_match['species']['scientificNameWithoutAuthor']
                eng_name = sci_name
                common_names = best_match['species'].get('commonNames', [])
                
                # 從俗名中找出英文
                for name in common_names:
                    if name.replace(" ", "").isascii() and name != sci_name:
                        eng_name = name
                        break

                # 從俗名中找出中文並轉為繁體
                zh_name = sci_name
                for name in common_names:
                    if any('\u4e00' <= char <= '\u9fff' for char in name):
                        zh_name = cc.convert(name) # 強制轉繁體
                        break
                
                st.success(f"辨識成功！這株植物是：{zh_name}")

                # --- 獲取百科介紹與別名 (使用繁體中文搜尋) ---
                description = "這是一株神秘的植物，百科中暫時找不到詳細的故事，但它依然是村莊裡美麗的存在！"
                aliases_str = ""
                
                try:
                    # 第一步：先用搜尋 API 找出精確的繁體標題
                    search_api = f"https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch={zh_name}&utf8=&format=json&srlimit=1"
                    search_res = requests.get(search_api).json()
                    
                    if search_res.get('query', {}).get('search'):
                        exact_title = search_res['query']['search'][0]['title']
                        
                        # 第二步：抓取介紹文 (自動繁簡轉換參數 variant=zh-tw)
                        wiki_summary_url = f"https://zh.wikipedia.org/api/rest_v1/page/summary/{exact_title}"
                        wiki_res = requests.get(wiki_summary_url, headers={'Accept-Language': 'zh-TW'})
                        if wiki_res.status_code == 200:
                            description = cc.convert(wiki_res.json().get('extract', description)) # 確保結果是繁體

                        # 第三步：抓取別名 (Redirects)
                        wiki_aliases_url = f"https://zh.wikipedia.org/w/api.php?action=query&prop=redirects&titles={exact_title}&format=json&utf8="
                        aliases_data = requests.get(wiki_aliases_url).json()
                        pages = aliases_data.get('query', {}).get('pages', {})
                        for pg_id, pg_info in pages.items():
                            redirects = pg_info.get('redirects', [])
                            if redirects:
                                # 過濾並轉為繁體
                                raw_aliases = [r['title'] for r in redirects if ":" not in r['title'] and "：" not in r['title']][:5]
                                aliases_str = "、".join([cc.convert(a) for a in raw_aliases])
                except Exception as e:
                    pass # 若維基百科查詢失敗，保留預設文字

                # --- 顯示最終結果 ---
                st.markdown(f"### 🌿 {zh_name}")
                st.markdown(f"**📖 英文/學名**：*{eng_name}*")
                if aliases_str:
                    st.markdown(f"**💡 相關別名**：{aliases_str}")
                
                st.divider()
                st.write(description)
                
                # 加入圖鑑
                st.session_state.pokedex.add(zh_name)
            else:
                st.error("拍得不夠清楚，請換個角度再拍一次吧！")
        except Exception as e:
            st.error(f"魔法放大鏡有點累了，請稍後再試！(系統訊息: {e})")

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

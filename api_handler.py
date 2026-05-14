# api_handler.py
import requests
import streamlit as st
from opencc import OpenCC

CC_CONVERTER = OpenCC('s2t')

def get_api_key():
    """安全獲取 API 金鑰"""
    try:
        return st.secrets["PLANTNET_API_KEY"]
    except KeyError:
        st.error("⚠️ 系統設定錯誤：遺失 API 授權金鑰。請管理員至 Secrets 中設定。")
        st.stop()

def identify_plant_from_api(image_file):
    """
    負責呼叫 PlantNet API 與 Wikipedia API 進行植物辨識與資料擷取。
    """
    api_key = get_api_key()
    api_url = f"https://my-api.plantnet.org/v2/identify/all?api-key={api_key}&lang=zh"
    files = [('images', (image_file.name, image_file.getvalue(), image_file.type))]
    
    try:
        response = requests.post(api_url, files=files, timeout=15)
        
        if response.status_code == 401 or response.status_code == 403:
            return {"success": False, "error": "驗證失敗，請確認圖鑑系統授權狀態。"}
        elif response.status_code != 200:
            return {"success": False, "error": "魔法放大鏡暫時失去焦點，請稍後再試。"}

        result = response.json()
        if not result.get('results'):
            return {"success": False, "error": "找不到匹配的植物。"}

        best_match = result['results'][0]
        sci_name = best_match['species']['scientificNameWithoutAuthor']
        common_names = best_match['species'].get('commonNames', [])
        
        eng_name = next((n for n in common_names if n.replace(" ","").isascii()), "N/A")
        raw_zh_name = next((n for n in common_names if any('\u4e00' <= c <= '\u9fff' for c in n)), sci_name)
        zh_name = CC_CONVERTER.convert(raw_zh_name)

        description = "這是一株神秘的植物，百科中暫時找不到詳細故事。"
        try:
            wiki_res = requests.get(f"https://zh.wikipedia.org/api/rest_v1/page/summary/{zh_name}?redirect=true", headers={'Accept-Language': 'zh-tw'}, timeout=5)
            if wiki_res.status_code == 200:
                description = CC_CONVERTER.convert(wiki_res.json().get('extract', description))
        except:
            pass

        return {
            "success": True,
            "sci_name": sci_name,
            "eng_name": eng_name,
            "zh_name": zh_name,
            "desc": description,
            "type": "plant"
        }
    except Exception:
        return {"success": False, "error": "系統網路通訊異常，請確認連線狀態後重試。"}

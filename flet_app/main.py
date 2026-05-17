from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

import flet as ft

try:
    import flet_camera as fc
except Exception:
    fc = None  # type: ignore[assignment]

from magnifier_handle import MagnifierHandle

try:
    from build_config import WORKER_URL
except ImportError:
    WORKER_URL = "https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev"

POKEDEX_STORAGE_KEY = "artVillagePokedex"
LOCAL_CACHE_DIR = Path(tempfile.gettempdir()) / "art-village-exploration-magnifier"
LOCAL_CACHE_PATH = LOCAL_CACHE_DIR / "local_pokedex_cache.json"
LOW_CONFIDENCE_THRESHOLD = 50.0
LENS_VIEWPORT_SIZE = 304
LENS_FRAME_SIZE = 336
LENS_FRAME_PADDING = 11
CAMERA_PREVIEW_SIZE = 420
CAMERA_PREVIEW_OFFSET = -58
MIN_CAMERA_ZOOM = 1.0
MAX_CAMERA_ZOOM = 2.0
CAMERA_ZOOM_STEP = 0.25
PLANT_ORGAN_OPTIONS = {
    "auto": "自動",
    "leaf": "葉",
    "flower": "花",
    "fruit": "果",
    "bark": "樹皮",
}
PLANT_ORGAN_ICONS = {
    "auto": ft.Icons.AUTO_AWESOME,
    "leaf": ft.Icons.ECO,
    "flower": ft.Icons.LOCAL_FLORIST,
    "fruit": ft.Icons.SPA,
    "bark": ft.Icons.PARK,
}
MAX_CARD_IMAGE_DATA_URL_LENGTH = 180_000
UNKNOWN_METADATA = {
    "toxicity": {"label": "資料待確認", "detail": "PlantNet 不提供毒性判斷，需查證可靠資料。"},
    "invasive": {"label": "資料待確認", "detail": "尚未建立此物種的在地外來種資料。"},
}
PLANT_METADATA = {
    "Ficus microcarpa": {
        "toxicity": {"label": "無明確毒性資料", "detail": "未作食用安全判斷，接觸後仍建議洗手。"},
        "invasive": {"label": "非外來種", "detail": "台灣常見榕屬樹種，實地仍以地方資料為準。"},
    },
    "Hibiscus rosa-sinensis": {
        "toxicity": {"label": "無明確毒性資料", "detail": "常見觀賞植物，仍不建議任意食用。"},
        "invasive": {"label": "資料待確認", "detail": "不同地區栽培與逸出狀態不同。"},
    },
}

SIMPLIFIED_TO_TRADITIONAL = str.maketrans(
    {
        "万": "萬",
        "与": "與",
        "丛": "叢",
        "东": "東",
        "丝": "絲",
        "两": "兩",
        "严": "嚴",
        "丧": "喪",
        "个": "個",
        "丰": "豐",
        "临": "臨",
        "为": "為",
        "丽": "麗",
        "举": "舉",
        "义": "義",
        "乌": "烏",
        "乐": "樂",
        "乔": "喬",
        "习": "習",
        "乡": "鄉",
        "书": "書",
        "买": "買",
        "乱": "亂",
        "争": "爭",
        "于": "於",
        "亏": "虧",
        "云": "雲",
        "亚": "亞",
        "产": "產",
        "亩": "畝",
        "亲": "親",
        "亿": "億",
        "仅": "僅",
        "从": "從",
        "仑": "崙",
        "仓": "倉",
        "仪": "儀",
        "们": "們",
        "价": "價",
        "众": "眾",
        "优": "優",
        "会": "會",
        "传": "傳",
        "伤": "傷",
        "伦": "倫",
        "伞": "傘",
        "伟": "偉",
        "侧": "側",
        "侨": "僑",
        "侦": "偵",
        "侠": "俠",
        "侣": "侶",
        "侥": "僥",
        "侩": "儈",
        "侪": "儕",
        "侬": "儂",
        "俣": "俁",
        "俦": "儔",
        "俨": "儼",
        "俩": "倆",
        "俪": "儷",
        "俭": "儉",
        "债": "債",
        "倾": "傾",
        "偻": "僂",
        "偿": "償",
        "储": "儲",
        "儿": "兒",
        "兑": "兌",
        "兰": "蘭",
        "关": "關",
        "兴": "興",
        "养": "養",
        "兽": "獸",
        "内": "內",
        "冈": "岡",
        "册": "冊",
        "写": "寫",
        "军": "軍",
        "农": "農",
        "冲": "沖",
        "决": "決",
        "况": "況",
        "冻": "凍",
        "净": "淨",
        "凉": "涼",
        "减": "減",
        "凑": "湊",
        "凤": "鳳",
        "凭": "憑",
        "凯": "凱",
        "击": "擊",
        "凿": "鑿",
        "划": "劃",
        "刘": "劉",
        "则": "則",
        "刚": "剛",
        "创": "創",
        "删": "刪",
        "别": "別",
        "刬": "剗",
        "刭": "剄",
        "剂": "劑",
        "剑": "劍",
        "办": "辦",
        "务": "務",
        "动": "動",
        "励": "勵",
        "劲": "勁",
        "劳": "勞",
        "势": "勢",
        "勋": "勳",
        "匀": "勻",
        "区": "區",
        "医": "醫",
        "华": "華",
        "协": "協",
        "单": "單",
        "卖": "賣",
        "卢": "盧",
        "卫": "衛",
        "却": "卻",
        "厂": "廠",
        "厅": "廳",
        "历": "歷",
        "厉": "厲",
        "压": "壓",
        "厌": "厭",
        "厕": "廁",
        "厢": "廂",
        "县": "縣",
        "参": "參",
        "双": "雙",
        "发": "發",
        "变": "變",
        "叙": "敘",
        "叶": "葉",
        "号": "號",
        "叹": "嘆",
        "后": "後",
        "向": "向",
        "吓": "嚇",
        "吕": "呂",
        "吗": "嗎",
        "启": "啟",
        "吴": "吳",
        "员": "員",
        "呐": "吶",
        "呕": "嘔",
        "呖": "嚦",
        "呗": "唄",
        "员": "員",
        "周": "週",
        "咏": "詠",
        "咙": "嚨",
        "咛": "嚀",
        "咸": "鹹",
        "响": "響",
        "哑": "啞",
        "哗": "嘩",
        "哟": "喲",
        "唤": "喚",
        "啬": "嗇",
        "喷": "噴",
        "团": "團",
        "园": "園",
        "圆": "圓",
        "图": "圖",
        "圣": "聖",
        "场": "場",
        "坏": "壞",
        "块": "塊",
        "坚": "堅",
        "坛": "壇",
        "坝": "壩",
        "坞": "塢",
        "坟": "墳",
        "坠": "墜",
        "垄": "壟",
        "垅": "壟",
        "垆": "壚",
        "垒": "壘",
        "垦": "墾",
        "垩": "堊",
        "垫": "墊",
        "垭": "埡",
        "垯": "墶",
        "垱": "壋",
        "垲": "塏",
        "垴": "堖",
        "埘": "塒",
        "埙": "塤",
        "埚": "堝",
        "堑": "塹",
        "塆": "壪",
        "墙": "牆",
        "壮": "壯",
        "声": "聲",
        "壳": "殼",
        "壶": "壺",
        "处": "處",
        "备": "備",
        "复": "復",
        "头": "頭",
        "夹": "夾",
        "夺": "奪",
        "奋": "奮",
        "奖": "獎",
        "奥": "奧",
        "妆": "妝",
        "妇": "婦",
        "妈": "媽",
        "妩": "嫵",
        "妪": "嫗",
        "姗": "姍",
        "姜": "薑",
        "娄": "婁",
        "娅": "婭",
        "娆": "嬈",
        "娇": "嬌",
        "娈": "孌",
        "娱": "娛",
        "娲": "媧",
        "娴": "嫻",
        "婴": "嬰",
        "婵": "嬋",
        "孙": "孫",
        "学": "學",
        "宁": "寧",
        "宝": "寶",
        "实": "實",
        "宠": "寵",
        "审": "審",
        "宪": "憲",
        "宫": "宮",
        "宽": "寬",
        "宾": "賓",
        "寝": "寢",
        "对": "對",
        "寻": "尋",
        "导": "導",
        "寿": "壽",
        "将": "將",
        "尔": "爾",
        "尘": "塵",
        "尝": "嘗",
        "尧": "堯",
        "层": "層",
        "屉": "屜",
        "届": "屆",
        "属": "屬",
        "岁": "歲",
        "岂": "豈",
        "岗": "崗",
        "岛": "島",
        "岭": "嶺",
        "岳": "嶽",
        "峡": "峽",
        "峣": "嶢",
        "峤": "嶠",
        "峥": "崢",
        "峦": "巒",
        "巅": "巔",
        "币": "幣",
        "帅": "帥",
        "师": "師",
        "帐": "帳",
        "帘": "簾",
        "帜": "幟",
        "带": "帶",
        "帧": "幀",
        "帮": "幫",
        "干": "乾",
        "并": "並",
        "广": "廣",
        "庄": "莊",
        "庆": "慶",
        "庐": "廬",
        "库": "庫",
        "应": "應",
        "庙": "廟",
        "庞": "龐",
        "废": "廢",
        "开": "開",
        "异": "異",
        "弃": "棄",
        "张": "張",
        "弥": "彌",
        "弯": "彎",
        "弹": "彈",
        "强": "強",
        "归": "歸",
        "当": "當",
        "录": "錄",
        "彦": "彥",
        "彻": "徹",
        "径": "徑",
        "忆": "憶",
        "忧": "憂",
        "忾": "愾",
        "树": "樹",
        "桠": "椏",
        "桡": "橈",
        "桢": "楨",
        "档": "檔",
        "桤": "榿",
        "桥": "橋",
        "桦": "樺",
        "桧": "檜",
        "桨": "槳",
        "桩": "樁",
        "梦": "夢",
        "梨": "梨",
        "梼": "檮",
        "棁": "梲",
        "棂": "欞",
        "椁": "槨",
        "椟": "櫝",
        "椠": "槧",
        "椤": "欏",
        "楼": "樓",
        "榄": "欖",
        "榅": "榲",
        "榇": "櫬",
        "榈": "櫚",
        "榉": "櫸",
        "槚": "檟",
        "槛": "檻",
        "槟": "檳",
        "槠": "櫧",
        "横": "橫",
        "樯": "檣",
        "樱": "櫻",
        "橥": "櫫",
        "橱": "櫥",
        "橹": "櫓",
        "橼": "櫞",
        "檩": "檁",
        "欢": "歡",
        "欧": "歐",
        "岁": "歲",
        "汉": "漢",
        "汤": "湯",
        "沟": "溝",
        "没": "沒",
        "泽": "澤",
        "洁": "潔",
        "浅": "淺",
        "浆": "漿",
        "润": "潤",
        "涩": "澀",
        "渊": "淵",
        "渍": "漬",
        "渐": "漸",
        "湾": "灣",
        "湿": "濕",
        "滞": "滯",
        "满": "滿",
        "滤": "濾",
        "滥": "濫",
        "滨": "濱",
        "滩": "灘",
        "漓": "灕",
        "潇": "瀟",
        "潜": "潛",
        "澜": "瀾",
        "濒": "瀕",
        "灭": "滅",
        "灯": "燈",
        "灵": "靈",
        "灾": "災",
        "炉": "爐",
        "点": "點",
        "炼": "煉",
        "烂": "爛",
        "烟": "煙",
        "热": "熱",
        "焕": "煥",
        "爱": "愛",
        "爷": "爺",
        "牵": "牽",
        "犊": "犢",
        "状": "狀",
        "独": "獨",
        "狭": "狹",
        "狮": "獅",
        "狰": "猙",
        "获": "獲",
        "献": "獻",
        "玛": "瑪",
        "环": "環",
        "现": "現",
        "玱": "瑲",
        "珐": "琺",
        "珑": "瓏",
        "珰": "璫",
        "琏": "璉",
        "琐": "瑣",
        "琼": "瓊",
        "瑶": "瑤",
        "瓒": "瓚",
        "瓯": "甌",
        "电": "電",
        "画": "畫",
        "畅": "暢",
        "畴": "疇",
        "疗": "療",
        "疟": "瘧",
        "疠": "癘",
        "疡": "瘍",
        "疬": "癧",
        "疮": "瘡",
        "疯": "瘋",
        "痈": "癰",
        "痉": "痙",
        "痒": "癢",
        "痨": "癆",
        "瘗": "瘞",
        "瘘": "瘺",
        "瘪": "癟",
        "瘫": "癱",
        "癞": "癩",
        "皱": "皺",
        "皲": "皸",
        "盏": "盞",
        "盐": "鹽",
        "监": "監",
        "盖": "蓋",
        "盗": "盜",
        "盘": "盤",
        "眍": "瞘",
        "着": "著",
        "睁": "睜",
        "睐": "睞",
        "瞒": "瞞",
        "矫": "矯",
        "矾": "礬",
        "矿": "礦",
        "码": "碼",
        "砖": "磚",
        "砚": "硯",
        "砜": "碸",
        "砺": "礪",
        "砻": "礱",
        "砾": "礫",
        "础": "礎",
        "硁": "硜",
        "硕": "碩",
        "硖": "硤",
        "硗": "磽",
        "硙": "磑",
        "确": "確",
        "硷": "鹼",
        "碍": "礙",
        "碛": "磧",
        "碜": "磣",
        "礼": "禮",
        "祎": "禕",
        "祯": "禎",
        "祷": "禱",
        "祸": "禍",
        "禀": "稟",
        "禄": "祿",
        "禅": "禪",
        "离": "離",
        "种": "種",
        "积": "積",
        "称": "稱",
        "秽": "穢",
        "稆": "穭",
        "税": "稅",
        "稳": "穩",
        "穑": "穡",
        "穷": "窮",
        "窃": "竊",
        "窍": "竅",
        "窑": "窯",
        "窜": "竄",
        "窝": "窩",
        "窥": "窺",
        "窦": "竇",
        "竞": "競",
        "笃": "篤",
        "笋": "筍",
        "笔": "筆",
        "笕": "筧",
        "笺": "箋",
        "笼": "籠",
        "笾": "籩",
        "筑": "築",
        "筛": "篩",
        "筜": "簹",
        "筝": "箏",
        "筹": "籌",
        "签": "簽",
        "简": "簡",
        "箓": "籙",
        "箦": "簀",
        "箧": "篋",
        "箨": "籜",
        "箩": "籮",
        "箪": "簞",
        "箫": "簫",
        "篑": "簣",
        "篓": "簍",
        "篮": "籃",
        "篱": "籬",
        "簖": "籪",
        "籁": "籟",
        "籴": "糴",
        "类": "類",
        "籼": "秈",
        "粜": "糶",
        "粝": "糲",
        "粤": "粵",
        "粪": "糞",
        "粮": "糧",
        "糁": "糝",
        "糇": "餱",
        "紧": "緊",
        "絷": "縶",
        "纤": "纖",
        "约": "約",
        "级": "級",
        "纪": "紀",
        "纫": "紉",
        "纬": "緯",
        "纯": "純",
        "纱": "紗",
        "纲": "綱",
        "纳": "納",
        "纵": "縱",
        "纶": "綸",
        "纷": "紛",
        "纸": "紙",
        "纹": "紋",
        "纺": "紡",
        "纽": "紐",
        "线": "線",
        "练": "練",
        "组": "組",
        "绅": "紳",
        "细": "細",
        "织": "織",
        "终": "終",
        "绊": "絆",
        "绍": "紹",
        "绎": "繹",
        "经": "經",
        "绑": "綁",
        "绒": "絨",
        "结": "結",
        "绕": "繞",
        "绘": "繪",
        "给": "給",
        "络": "絡",
        "绝": "絕",
        "统": "統",
        "绢": "絹",
        "绣": "繡",
        "继": "繼",
        "绩": "績",
        "绪": "緒",
        "续": "續",
        "绳": "繩",
        "维": "維",
        "绵": "綿",
        "绶": "綬",
        "绷": "繃",
        "绸": "綢",
        "综": "綜",
        "绽": "綻",
        "绿": "綠",
        "缀": "綴",
        "缁": "緇",
        "缂": "緙",
        "缃": "緗",
        "缄": "緘",
        "缅": "緬",
        "缆": "纜",
        "缇": "緹",
        "缈": "緲",
        "缉": "緝",
        "缋": "繢",
    }
)


def to_traditional_chinese(text: str) -> str:
    return text.translate(SIMPLIFIED_TO_TRADITIONAL)


ANIMALS_DB = {
    "貝貝": {
        "type": "animal",
        "emoji": "🐶",
        "role": "溫柔導覽員",
        "desc": "東北角的米克斯母狗，也是藝素村最溫柔的導嚮員。",
    },
    "牧耳": {
        "type": "animal",
        "emoji": "🐕",
        "role": "草地巡邏員",
        "desc": "充滿活力的夥伴，最喜歡在東北角的草地上奔跑。",
    },
    "小飛俠": {
        "type": "animal",
        "emoji": "🐈",
        "role": "屋頂觀察員",
        "desc": "身手矯健，總是在屋頂上觀察探險家們。",
    },
    "嘿皮": {
        "type": "animal",
        "emoji": "🐈‍⬛",
        "role": "親人接待員",
        "desc": "個性大方的黑貓，討摸是牠的日常。",
    },
    "冬瓜": {
        "type": "animal",
        "emoji": "🐱",
        "role": "慵懶守護者",
        "desc": "圓滾滾的橘貓，是村裡的慵懶大王。",
    },
}


def border_all(width: int, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


def soft_card(content: ft.Control, padding: int = 16) -> ft.Container:
    return ft.Container(
        bgcolor="#fffdf4",
        border_radius=16,
        padding=padding,
        border=border_all(1, "#dccfc0"),
        shadow=ft.BoxShadow(blur_radius=16, color="#2b130814", offset=ft.Offset(0, 8)),
        content=content,
    )


def section_label(icon: str, text: str) -> ft.Row:
    return ft.Row(
        controls=[
            ft.Text(icon, size=24),
            ft.Text(text, size=24, weight=ft.FontWeight.W_900, color="#3d2a21"),
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
    )


def common_names_by_script(species: dict[str, Any]) -> tuple[list[str], list[str]]:
    chinese_names: list[str] = []
    other_names: list[str] = []
    for raw_name in species.get("commonNames", []) or []:
        name = str(raw_name).strip()
        if not name:
            continue
        has_cjk = any("\u4e00" <= char <= "\u9fff" for char in name)
        if has_cjk:
            chinese_names.append(to_traditional_chinese(name))
        else:
            other_names.append(name)
    return chinese_names, other_names


def first_common_name(species: dict[str, Any], chinese: bool) -> str | None:
    chinese_names, other_names = common_names_by_script(species)
    names = chinese_names if chinese else other_names
    return names[0] if names else None


def metadata_for_scientific_name(scientific: str) -> dict[str, dict[str, str]]:
    metadata = PLANT_METADATA.get(scientific, UNKNOWN_METADATA)
    return {
        "toxicity": dict(metadata["toxicity"]),
        "invasive": dict(metadata["invasive"]),
    }


def bool_label(value: Any, true_label: str, false_label: str, unknown_label: str = "資料待確認") -> str:
    if value is True:
        return true_label
    if value is False:
        return false_label
    return unknown_label


def metadata_from_perenual(perenual: dict[str, Any], fallback: dict[str, dict[str, str]]) -> dict[str, Any]:
    if perenual.get("status") not in ("ok", "cached"):
        return {
            "toxicity": dict(fallback["toxicity"]),
            "invasive": dict(fallback["invasive"]),
            "care": {},
            "source": "PlantNet",
        }

    poisonous_to_humans = perenual.get("poisonous_to_humans")
    poisonous_to_pets = perenual.get("poisonous_to_pets")
    invasive = perenual.get("invasive")
    toxicity_detail = "Perenual 二次查詢資料。"
    if poisonous_to_pets is True:
        toxicity_detail += " 另標示可能對寵物有毒。"
    elif poisonous_to_pets is False:
        toxicity_detail += " 另標示未列為寵物有毒。"

    return {
        "toxicity": {
            "label": bool_label(poisonous_to_humans, "有毒", "未列為有毒"),
            "detail": toxicity_detail,
        },
        "invasive": {
            "label": bool_label(invasive, "可能具侵略性", "未列為侵略性"),
            "detail": "Perenual 物種資料，仍建議以在地資料確認。",
        },
        "care": {
            "澆水": perenual.get("watering") or "",
            "日照": "、".join(perenual.get("sunlight") or []),
            "生命週期": perenual.get("cycle") or "",
            "照護難度": perenual.get("care_level") or "",
        },
        "source": "Perenual",
    }


def plant_candidate_from_result(result: dict[str, Any], perenual: dict[str, Any] | None = None) -> dict[str, Any]:
    species = result.get("species") or {}
    scientific = species.get("scientificNameWithoutAuthor") or species.get("scientificName") or "Unknown"
    chinese_names, other_names = common_names_by_script(species)
    zh_name = chinese_names[0] if chinese_names else scientific
    aliases = [name for name in chinese_names[1:] if name != zh_name]
    eng_name = other_names[0] if other_names else "N/A"
    score = float(result.get("score") or 0)
    confidence = round(score * 100, 1)
    metadata = metadata_for_scientific_name(scientific)
    enriched_metadata = metadata_from_perenual(perenual or {}, metadata)
    perenual_description = (perenual or {}).get("description") if (perenual or {}).get("status") in ("ok", "cached") else ""
    description = perenual_description or f"PlantNet 推測為 {zh_name}（{scientific}）。"

    return {
        "zh_name": zh_name,
        "aliases": aliases,
        "eng_name": eng_name,
        "sci_name": scientific,
        "emoji": "🌿",
        "type": "plant",
        "desc": description,
        "confidence": confidence,
        "is_low_confidence": confidence < LOW_CONFIDENCE_THRESHOLD,
        "toxicity": enriched_metadata["toxicity"],
        "invasive": enriched_metadata["invasive"],
        "care": enriched_metadata["care"],
        "metadata_source": enriched_metadata["source"],
        "metadata_status": (perenual or {}).get("status", "not_requested"),
    }


def parse_plantnet_result(payload: dict[str, Any]) -> dict[str, Any] | None:
    results = payload.get("results") or []
    if not results:
        return None

    candidates = [
        plant_candidate_from_result(result or {}, payload.get("perenual") if index == 0 else None)
        for index, result in enumerate(results[:4])
    ]
    primary = candidates[0]
    primary["alternatives"] = candidates[1:]
    primary["needs_confirmation"] = primary["is_low_confidence"]
    return primary


def confidence_text(item: dict[str, Any]) -> str:
    confidence = item.get("confidence", 0)
    if not confidence:
        return ""
    suffix = "，建議確認" if item.get("is_low_confidence") else ""
    return f"信心度 {confidence}%{suffix}"


def card_image_from_capture(capture: Any, max_data_url_length: int = MAX_CARD_IMAGE_DATA_URL_LENGTH) -> dict[str, str]:
    try:
        if isinstance(capture, str) and capture.startswith("data:") and len(capture) <= max_data_url_length:
            return {"src": capture, "label": "拍攝照片"}
        binary, mime = capture_to_bytes(capture)
        data_url = f"data:{mime};base64,{base64.b64encode(binary).decode('ascii')}"
        if len(data_url) <= max_data_url_length:
            return {"src": data_url, "label": "拍攝照片"}
    except Exception:
        pass
    return {"src": "", "label": "照片過大，未存入圖鑑"}


def capture_to_bytes(capture: Any) -> tuple[bytes, str]:
    if isinstance(capture, bytes):
        return capture, "image/jpeg"
    if isinstance(capture, bytearray):
        return bytes(capture), "image/jpeg"
    if isinstance(capture, memoryview):
        return capture.tobytes(), "image/jpeg"

    if isinstance(capture, str) and capture.startswith("data:"):
        header, encoded = capture.split(",", 1)
        mime = header.split(";")[0].replace("data:", "") or "image/jpeg"
        return base64.b64decode(encoded), mime

    if isinstance(capture, str):
        image_path = Path(capture)
        if image_path.exists():
            mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
            return image_path.read_bytes(), mime
        return base64.b64decode(capture), "image/jpeg"

    raise TypeError("相機回傳了無法辨識的圖片格式")


def clamp_camera_zoom(value: float) -> float:
    return min(MAX_CAMERA_ZOOM, max(MIN_CAMERA_ZOOM, round(value / CAMERA_ZOOM_STEP) * CAMERA_ZOOM_STEP))


def camera_preview_metrics(zoom_level: float) -> tuple[int, int, int]:
    zoom = clamp_camera_zoom(zoom_level)
    size = round(CAMERA_PREVIEW_SIZE * zoom)
    offset = round((LENS_VIEWPORT_SIZE - size) / 2)
    return size, offset, offset


def camera_descriptor_text(camera_description: Any) -> str:
    parts: list[str] = []
    if isinstance(camera_description, dict):
        parts.extend(str(value) for value in camera_description.values())
    else:
        for field in (
            "name",
            "label",
            "display_name",
            "description",
            "lens_direction",
            "position",
            "device_id",
        ):
            try:
                value = getattr(camera_description, field)
            except Exception:
                value = None
            if value:
                parts.append(str(value))
    parts.append(str(camera_description))
    return " ".join(parts).lower()


def camera_direction_score(camera_description: Any, direction: str) -> int:
    text = camera_descriptor_text(camera_description)
    front_terms = ("front", "selfie", "user", "facetime", "前", "前置")
    back_terms = ("back", "rear", "environment", "world", "後", "後置", "主鏡頭")
    avoid_terms = ("ultra", "tele", "macro", "depth", "0.5", "2x", "超廣角", "望遠", "微距")
    main_terms = ("main", "primary", "default", "standard", "主", "主要")

    terms = front_terms if direction == "front" else back_terms
    score = 0
    if any(term in text for term in terms):
        score += 100
    if direction == "back" and any(term in text for term in main_terms):
        score += 20
    if any(term in text for term in avoid_terms):
        score -= 30
    return score


def select_preferred_cameras(available_cameras: list[Any]) -> list[Any]:
    if not available_cameras:
        return []

    back_candidates = [
        (camera_direction_score(camera_description, "back"), index, camera_description)
        for index, camera_description in enumerate(available_cameras)
    ]
    front_candidates = [
        (camera_direction_score(camera_description, "front"), index, camera_description)
        for index, camera_description in enumerate(available_cameras)
    ]
    back_score, _, back_camera = max(back_candidates, key=lambda item: (item[0], -item[1]))
    front_score, _, front_camera = max(front_candidates, key=lambda item: (item[0], -item[1]))

    selected: list[Any] = []
    if back_score > 0:
        selected.append(back_camera)
    if front_score > 0 and front_camera not in selected:
        selected.append(front_camera)
    if selected:
        return selected
    return [available_cameras[0]]


class RecognitionServiceError(RuntimeError):
    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


def post_image_to_worker_sync(binary: bytes, mime: str, organ: str = "leaf") -> dict[str, Any]:
    import requests

    response = requests.post(
        WORKER_URL,
        files={"images": ("capture.jpg", binary, mime)},
        data={"organs": organ},
        timeout=30,
    )
    if not response.ok:
        raise RecognitionServiceError(worker_error_message(response.status_code, response.text))
    return response.json()


def worker_error_message(status_code: int, text: str) -> str:
    snippet = " ".join((text or "").strip().split())[:120]
    if status_code == 404 and "1042" in snippet:
        return "辨識服務尚未部署，請檢查 Worker 網址"
    if status_code in (400, 404):
        return "沒有辨識到植物，請對準葉子、花或果實再拍一次"
    if status_code == 405:
        return "辨識服務方法錯誤，請稍後再試"
    if status_code in (401, 403):
        return "辨識服務金鑰未通過，請檢查 Worker 的 PLANTNET_API_KEY"
    if status_code == 413:
        return "照片太大，請靠近植物後再拍一次"
    if status_code == 426:
        return "前端版本過舊，請稍後再拍一次"
    if status_code == 429:
        return "辨識服務忙碌，請稍後再試"
    if 500 <= status_code < 600:
        return "辨識服務暫時忙碌，請稍後再試"
    return f"辨識服務暫時無法處理（{status_code}）"


def metadata_url_for_scientific_name(scientific_name: str) -> str:
    return f"{WORKER_URL.rstrip('/')}/metadata?scientificName={quote(scientific_name)}"


def get_metadata_from_worker_sync(scientific_name: str) -> dict[str, Any]:
    import requests

    response = requests.get(metadata_url_for_scientific_name(scientific_name), timeout=20)
    if not response.ok:
        raise RecognitionServiceError(worker_error_message(response.status_code, response.text))
    return response.json()


async def get_metadata_from_worker(scientific_name: str) -> dict[str, Any]:
    if "YOUR-WORKER" in WORKER_URL:
        raise RuntimeError("尚未設定 Cloudflare Pages 的 WORKER_URL")

    try:
        from js import fetch  # type: ignore

        response = await fetch(metadata_url_for_scientific_name(scientific_name))
        text = await response.text()
        if not response.ok:
            raise RecognitionServiceError(worker_error_message(response.status, text))
        return json.loads(text)
    except ModuleNotFoundError:
        return await asyncio.to_thread(get_metadata_from_worker_sync, scientific_name)


async def post_image_to_worker(capture: Any, organ: str = "leaf") -> dict[str, Any]:
    if "YOUR-WORKER" in WORKER_URL:
        raise RuntimeError("尚未設定 Cloudflare Pages 的 WORKER_URL")

    binary, mime = capture_to_bytes(capture)

    try:
        from js import Blob, FormData, Object, Uint8Array, fetch  # type: ignore
        from pyodide.ffi import to_js  # type: ignore

        image_array = Uint8Array.new(to_js(list(binary)))
        blob = Blob.new([image_array], {"type": mime})

        form = FormData.new()
        form.append("organs", organ)
        form.append("images", blob, "capture.jpg")

        fetch_options = to_js({"method": "POST", "body": form}, dict_converter=Object.fromEntries)
        response = await fetch(WORKER_URL, fetch_options)
        text = await response.text()
        if not response.ok:
            raise RecognitionServiceError(worker_error_message(response.status, text))
        return json.loads(text)
    except ModuleNotFoundError:
        return await asyncio.to_thread(post_image_to_worker_sync, binary, mime, organ)


def load_json_cache(storage_key: str, local_path: Path, fallback: Any) -> Any:
    try:
        from js import localStorage  # type: ignore

        raw = localStorage.getItem(storage_key)
        if raw:
            cached = json.loads(raw)
            return cached
    except Exception:
        pass

    try:
        if not local_path.exists():
            return fallback
        try:
            return json.loads(local_path.read_text(encoding="utf-8"))
        except Exception:
            return fallback
    except Exception:
        return fallback


def save_json_cache(storage_key: str, local_path: Path, data: Any) -> None:
    serialized = json.dumps(data, ensure_ascii=False)
    try:
        from js import localStorage  # type: ignore

        localStorage.setItem(storage_key, serialized)
        return
    except Exception:
        pass

    try:
        if data in ({}, []):
            return
        if local_path.exists() and local_path.read_text(encoding="utf-8") == serialized:
            return
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(serialized, encoding="utf-8")
    except Exception:
        return


def load_cached_pokedex() -> dict[str, dict[str, Any]]:
    cached = load_json_cache(POKEDEX_STORAGE_KEY, LOCAL_CACHE_PATH, {})
    return cached if isinstance(cached, dict) else {}


def save_cached_pokedex(pokedex: dict[str, dict[str, Any]]) -> None:
    save_json_cache(POKEDEX_STORAGE_KEY, LOCAL_CACHE_PATH, pokedex)


def clear_legacy_snapshot_cache() -> None:
    try:
        from js import localStorage  # type: ignore

        localStorage.removeItem("artVillageSnapshotQueue")
    except Exception:
        pass

    try:
        legacy_path = LOCAL_CACHE_DIR / "local_snapshot_queue.json"
        if legacy_path.exists():
            legacy_path.unlink()
    except Exception:
        pass


def mark_explorer_ready() -> None:
    try:
        from js import window  # type: ignore

        window.__artVillageReady = True
    except Exception:
        pass


def mark_load_timing(name: str) -> None:
    try:
        from js import performance  # type: ignore

        performance.mark(name)
    except Exception:
        pass


def report_performance(page: ft.Page) -> None:
    try:
        page.run_js("""
        try {
          const marks = performance.getEntriesByType("mark");
          const measures = performance.getEntriesByType("measure");
          console.log("🔍 探險放大鏡效能報告");
          marks.forEach(m => console.log(`  Mark: ${m.name} @ ${m.startTime.toFixed(0)}ms`));
          measures.forEach(m => console.log(`  ${m.name}: ${m.duration.toFixed(0)}ms`));
        } catch (e) {
          console.warn("效能報告失敗:", e);
        }
        """)
    except Exception:
        pass


async def main(page: ft.Page) -> None:
    try:
        await run_app(page)
    except Exception as error:
        page.clean()
        page.bgcolor = "#f3efd9"
        page.add(
            ft.Container(
                padding=24,
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    [
                        ft.Text("探險放大鏡載入失敗", size=26, weight=ft.FontWeight.W_900, color="#3d2a21"),
                        ft.Text(str(error), size=14, color="#5c4032", selectable=True),
                    ],
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            )
        )
        page.update()


async def run_app(page: ft.Page) -> None:
    page.title = "藝素村探險放大鏡"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 16
    page.bgcolor = "#f3efd9"
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    pokedex: dict[str, dict[str, Any]] = load_cached_pokedex()
    clear_legacy_snapshot_cache()
    cameras: list[Any] = []
    selected_camera_index = 0
    camera_ready = False
    camera_initializing = False
    recognition_loading_visible = False
    zoom_level = MIN_CAMERA_ZOOM

    welcome_screen = ft.Container(
        width=430,
        padding=ft.Padding.symmetric(vertical=60, horizontal=24),
        content=ft.Column(
            controls=[
                ft.Text("🔍", size=80, text_align=ft.TextAlign.CENTER),
                ft.Text("探險放大鏡", size=32, weight=ft.FontWeight.W_900, 
                       text_align=ft.TextAlign.CENTER, color="#3d2a21"),
                ft.Text("藝素村的自然探險工具", size=18, weight=ft.FontWeight.W_700,
                       text_align=ft.TextAlign.CENTER, color="#5c4032"),
                ft.Container(height=16),
                ft.Text("🌿 拍攝並辨識植物物種", size=15, color="#6d5140"),
                ft.Text("🐾 認識村里的動物朋友", size=15, color="#6d5140"),
                ft.Text("🎒 建立你的探險圖鑑", size=15, color="#6d5140"),
                ft.Container(height=24),
                ft.Text("使用相機功能需要瀏覽器授權，", size=13, color="#8a6a54"),
                ft.Text("請確保使用 HTTPS 或 localhost 網址", size=13, color="#8a6a54"),
                ft.Container(height=32),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    start_button = ft.ElevatedButton(
        "開始探險",
        style=ft.ButtonStyle(
            padding=ft.Padding.symmetric(horizontal=40, vertical=18),
            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.W_900),
            bgcolor="#8a5a22",
            color="#ffffff",
        ),
    )

    welcome_screen.content.controls.append(start_button)

    page.clean()
    page.add(welcome_screen)
    page.update()
    mark_load_timing("art-village:welcome-ready")

    status = ft.Text(
        "",
        size=13,
        color="#6d5140",
        weight=ft.FontWeight.W_800,
        text_align=ft.TextAlign.CENTER,
        expand=True,
    )
    busy_ring = ft.ProgressRing(width=22, height=22, stroke_width=3, visible=False, color="#8a5a22")
    restart_camera_button = ft.TextButton(
        content=ft.Row(
            controls=[
                ft.Icon(ft.Icons.VIDEOCAM, size=16),
                ft.Text("重新啟動相機"),
            ],
            spacing=4,
        ),
        tooltip="重新請求相機權限並啟動鏡頭",
    )
    grid = ft.GridView(
        expand=False,
        max_extent=180,
        child_aspect_ratio=2.8,
        spacing=10,
        run_spacing=10,
        height=260,
    )

    camera = None
    camera_placeholder = ft.Container(
        alignment=ft.Alignment(0, 0),
        padding=20,
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.EXPLORE, size=44, color=ft.Colors.WHITE70),
                ft.Text("正在準備探險鏡頭", color=ft.Colors.WHITE70, weight=ft.FontWeight.W_700),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )
    camera_preview_slot = ft.Container(
        left=0,
        top=0,
        width=LENS_VIEWPORT_SIZE,
        height=LENS_VIEWPORT_SIZE,
        content=camera_placeholder,
    )
    camera_viewport = ft.Stack(
        width=LENS_VIEWPORT_SIZE,
        height=LENS_VIEWPORT_SIZE,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        controls=[camera_preview_slot],
    )

    def apply_camera_zoom(update_slot: bool = True) -> None:
        size, left, top = camera_preview_metrics(zoom_level)
        camera_preview_slot.left = left
        camera_preview_slot.top = top
        camera_preview_slot.width = size
        camera_preview_slot.height = size
        if camera is not None:
            camera.width = size
            camera.height = size
        if update_slot:
            camera_preview_slot.update()

    def adjust_camera_zoom(delta: float) -> None:
        nonlocal zoom_level
        next_zoom = clamp_camera_zoom(zoom_level + delta)
        if next_zoom == zoom_level:
            return
        zoom_level = next_zoom
        apply_camera_zoom()
        status.value = f"放大 {zoom_level:.2g}x" if zoom_level > MIN_CAMERA_ZOOM else "回到原始大小"
        render_handle(update_page=False)
        page.update()

    def room_in(_event: ft.ControlEvent) -> None:
        adjust_camera_zoom(CAMERA_ZOOM_STEP)

    def room_out(_event: ft.ControlEvent) -> None:
        adjust_camera_zoom(-CAMERA_ZOOM_STEP)

    camera_frame = ft.Container(
        width=LENS_FRAME_SIZE,
        height=LENS_FRAME_SIZE,
        border_radius=LENS_FRAME_SIZE / 2,
        bgcolor="#4d3026",
        padding=LENS_FRAME_PADDING,
        border=border_all(5, "#2b160f"),
        shadow=ft.BoxShadow(blur_radius=34, color="#442f2529", offset=ft.Offset(0, 14)),
        content=ft.Container(
            width=LENS_VIEWPORT_SIZE,
            height=LENS_VIEWPORT_SIZE,
            border_radius=LENS_VIEWPORT_SIZE / 2,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor="#0f1512",
            content=camera_viewport,
        ),
    )

    handle_slot = ft.Container(width=160, height=260)
    magnifier_handle_overlap = 24
    magnifier_body = ft.Stack(
        width=LENS_FRAME_SIZE,
        height=LENS_FRAME_SIZE + 260 - magnifier_handle_overlap,
        controls=[
            ft.Container(
                left=(LENS_FRAME_SIZE - 120) / 2,
                top=LENS_FRAME_SIZE - magnifier_handle_overlap,
                width=160,
                height=260,
                content=handle_slot,
            ),
            ft.Container(left=0, top=0, content=camera_frame),
        ],
    )
    content_area = ft.Container(width=380)

    def refresh_gallery(update_page: bool = True) -> None:
        grid.controls.clear()
        for name, item in pokedex.items():
            icon = item.get("emoji", "🌿" if item.get("type") == "plant" else "🐾")
            is_low_confidence = item.get("is_low_confidence", False)
            badge = "⚠️" if is_low_confidence else ""
            subtitle = confidence_text(item) or item.get("role", "")

            grid.controls.append(
                ft.Container(
                    bgcolor="#fffdf4",
                    border_radius=12,
                    padding=12,
                    alignment=ft.Alignment(0, 0),
                    border=border_all(1, "#d7c8b9"),
                    shadow=ft.BoxShadow(blur_radius=10, color="#2b130810", offset=ft.Offset(0, 5)),
                    animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
                    tooltip=f"{name} 詳細介紹",
                    on_click=lambda _event, item_name=name, item_data=item: show_gallery_card(item_name, item_data),
                    on_long_press=lambda _event, item_name=name: confirm_delete_gallery_item(item_name),
                    content=ft.Column(
                        controls=[
                            ft.Text(f"{icon} {badge} {name}", size=14, weight=ft.FontWeight.W_800, color="#3d2a21"),
                            ft.Text(subtitle, size=11, color="#6d5140"),
                        ],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
        save_cached_pokedex(pokedex)
        if update_page:
            page.update()

    def add_animal_to_gallery(name: str) -> None:
        data = ANIMALS_DB[name]
        pokedex[name] = {"zh_name": name, **data}
        status.value = f"已遇見：{name}"
        refresh_gallery()

    def add_plant_to_gallery(plant: dict[str, Any]) -> None:
        pokedex[plant["zh_name"]] = plant
        if plant.get("is_low_confidence", False):
            status.value = f"⚠️ {plant['zh_name']}（信心度低，建議確認）"
        else:
            status.value = f"辨識成功：{plant['zh_name']} · {plant.get('confidence', 0)}%"
        refresh_gallery()

    async def refresh_plant_metadata(plant: dict[str, Any]) -> None:
        scientific_name = plant.get("sci_name") or ""
        if not scientific_name or plant.get("metadata_status") not in ("pending", "error"):
            return
        try:
            metadata_payload = await get_metadata_from_worker(scientific_name)
            if metadata_payload.get("status") not in ("ok", "cached"):
                plant["metadata_status"] = metadata_payload.get("status", "error")
                pokedex[plant["zh_name"]] = plant
                save_cached_pokedex(pokedex)
                return
            fallback = metadata_for_scientific_name(scientific_name)
            enriched_metadata = metadata_from_perenual(metadata_payload, fallback)
            plant["toxicity"] = enriched_metadata["toxicity"]
            plant["invasive"] = enriched_metadata["invasive"]
            plant["care"] = enriched_metadata["care"]
            plant["metadata_source"] = enriched_metadata["source"]
            plant["metadata_status"] = metadata_payload.get("status", "ok")
            if metadata_payload.get("description"):
                plant["desc"] = metadata_payload["description"]
            pokedex[plant["zh_name"]] = plant
            status.value = f"{plant['zh_name']} 的 Perenual 資料已補上"
            refresh_gallery(update_page=False)
            page.update()
        except Exception:
            plant["metadata_status"] = "error"
            pokedex[plant["zh_name"]] = plant
            save_cached_pokedex(pokedex)

    def close_dialog(_event: ft.ControlEvent) -> None:
        page.pop_dialog()
        page.update()

    def show_recognition_loading_card() -> None:
        nonlocal recognition_loading_visible
        recognition_loading_visible = True
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("辨識中", size=24, weight=ft.FontWeight.W_900, color="#3d2a21"),
                content=soft_card(
                    ft.Column(
                        controls=[
                            ft.ProgressRing(width=34, height=34, stroke_width=4, color="#8a5a22"),
                            ft.Text("正在分析拍攝內容", size=16, weight=ft.FontWeight.W_900, color="#3d2a21"),
                            ft.Text("請稍候，完成後會自動顯示辨識結果卡片。", size=13, color="#6d5140"),
                        ],
                        spacing=12,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=20,
                ),
            )
        )
        page.update()

    def close_recognition_loading_card(update_page: bool = True) -> None:
        nonlocal recognition_loading_visible
        if not recognition_loading_visible:
            return
        page.pop_dialog()
        recognition_loading_visible = False
        if update_page:
            page.update()

    def delete_gallery_item(name: str) -> None:
        if name in pokedex:
            pokedex.pop(name)
            save_cached_pokedex(pokedex)
            status.value = f"已刪除：{name}"
            refresh_gallery()
        page.pop_dialog()
        page.update()

    def clear_gallery() -> None:
        pokedex.clear()
        save_cached_pokedex(pokedex)
        status.value = "已清除探險圖鑑"
        refresh_gallery()
        page.pop_dialog()
        page.update()

    def confirm_delete_gallery_item(name: str) -> None:
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("刪除圖鑑卡片", size=22, weight=ft.FontWeight.W_900),
                content=ft.Text(f"要從探險圖鑑刪除「{name}」嗎？", size=15, color="#3d2a21"),
                actions=[
                    ft.TextButton("取消", on_click=close_dialog),
                    ft.TextButton("刪除", icon=ft.Icons.DELETE_OUTLINE, on_click=lambda _event: delete_gallery_item(name)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    def confirm_clear_gallery(_event: ft.ControlEvent) -> None:
        if not pokedex:
            status.value = "探險圖鑑目前是空的"
            page.update()
            return
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("清除探險圖鑑", size=22, weight=ft.FontWeight.W_900),
                content=ft.Text("要刪除所有圖鑑卡片嗎？這個動作無法復原。", size=15, color="#3d2a21"),
                actions=[
                    ft.TextButton("取消", on_click=close_dialog),
                    ft.TextButton("全部清除", icon=ft.Icons.DELETE_SWEEP_OUTLINED, on_click=lambda _event: clear_gallery()),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    def show_animal_card(name: str) -> None:
        data = ANIMALS_DB[name]
        add_animal_to_gallery(name)
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(f"{data['emoji']} {name}", size=24, weight=ft.FontWeight.W_900),
                content=soft_card(
                    ft.Column(
                        controls=[
                            ft.Text(data["role"], size=14, color="#7a4b38", weight=ft.FontWeight.W_800),
                            ft.Text(data["desc"], size=15, color="#3d2a21"),
                            ft.Text("已加入探險圖鑑", size=13, color="#2f7d51", weight=ft.FontWeight.W_800),
                        ],
                        spacing=8,
                    ),
                    padding=18,
                ),
                actions=[ft.TextButton("關閉", on_click=close_dialog)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    def show_gallery_card(name: str, data: dict[str, Any]) -> None:
        if data.get("type") == "animal":
            show_animal_card(name)
        else:
            show_plant_card(name, data)

    def show_plant_card(name: str, data: dict[str, Any]) -> None:
        confidence = data.get("confidence", 0)
        is_low_confidence = data.get("is_low_confidence", False)
        alternatives = data.get("alternatives") or []
        aliases = data.get("aliases") or []
        captured_image = data.get("captured_image") or {}
        toxicity = data.get("toxicity") or UNKNOWN_METADATA["toxicity"]
        invasive = data.get("invasive") or UNKNOWN_METADATA["invasive"]
        care = {key: value for key, value in (data.get("care") or {}).items() if value}
        metadata_source = data.get("metadata_source") or "PlantNet"
        metadata_status = data.get("metadata_status") or "not_requested"
        worker_timing = data.get("worker_timing") or {}
        organ_label = data.get("organ_label") or PLANT_ORGAN_OPTIONS.get(data.get("organ", "auto"), "自動")

        def detail_text(value: str, *, size: int = 13, color: str = "#5c4032", weight: ft.FontWeight | None = None) -> ft.Text:
            return ft.Text(value, size=size, color=color, weight=weight, selectable=True)

        def info_chip(label: str, value: str, detail: str = "") -> ft.Container:
            return ft.Container(
                padding=10,
                border_radius=10,
                bgcolor="#f7f0df",
                border=border_all(1, "#dfd0bd"),
                content=ft.Column(
                    controls=[
                        ft.Text(label, size=11, color="#8a5a22", weight=ft.FontWeight.W_900),
                        ft.Text(value, size=13, color="#3d2a21", weight=ft.FontWeight.W_800),
                        ft.Text(detail, size=10, color="#7a6657") if detail else ft.Container(),
                    ],
                    spacing=2,
                ),
            )

        image_src = captured_image.get("src", "")
        image_banner: ft.Control
        if image_src:
            image_banner = ft.Container(
                height=170,
                border_radius=14,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                bgcolor="#efe4d1",
                content=ft.Image(src=image_src, fit=ft.BoxFit.COVER, width=340, height=170),
            )
        else:
            image_banner = ft.Container(
                height=112,
                border_radius=14,
                alignment=ft.Alignment(0, 0),
                bgcolor="#efe4d1",
                border=border_all(1, "#dfd0bd"),
                content=ft.Text(captured_image.get("label") or "尚無拍攝照片", size=13, color="#7a6657", weight=ft.FontWeight.W_800),
            )
        
        warning_text: ft.Control = ft.Container()
        if is_low_confidence and confidence > 0:
            warning_text = ft.Container(
                padding=8,
                margin=ft.Margin.only(bottom=8),
                bgcolor="#fff3cd",
                border_radius=8,
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.WARNING_AMBER_OUTLINED, size=16, color="#856404"),
                        ft.Text(f"置信度僅 {confidence}%，建議實地確認物種", size=13, color="#856404", weight=ft.FontWeight.W_700),
                    ],
                    spacing=6,
                ),
            )

        alternative_controls: list[ft.Control] = []
        if alternatives:
            alternative_controls = [
                ft.Text("備選辨識", size=14, color="#3d2a21", weight=ft.FontWeight.W_900),
                *[
                    ft.Container(
                        padding=8,
                        border_radius=10,
                        bgcolor="#f7f0df",
                        content=ft.Text(
                            f"{candidate['zh_name']} · {candidate['confidence']}%",
                            size=12,
                            color="#5c4032",
                        ),
                    )
                    for candidate in alternatives
                ],
            ]

        alias_controls: list[ft.Control] = []
        if aliases:
            alias_controls = [
                ft.Text("別名", size=12, color="#8a5a22", weight=ft.FontWeight.W_900),
                ft.Text("、".join(aliases), size=13, color="#5c4032"),
            ]

        metadata_controls = [
            info_chip("拍攝部位", organ_label),
            info_chip("毒性", toxicity.get("label", "資料待確認"), toxicity.get("detail", "")),
            info_chip("外來種", invasive.get("label", "資料待確認"), invasive.get("detail", "")),
        ]
        care_controls: list[ft.Control] = []
        if care:
            care_controls = [
                ft.Text("Perenual 植物資料", size=14, color="#3d2a21", weight=ft.FontWeight.W_900),
                ft.Row(
                    controls=[info_chip(label, str(value)) for label, value in care.items()],
                    spacing=8,
                    wrap=True,
                ),
            ]
        metadata_note = "Perenual 資料背景載入中" if metadata_status == "pending" else f"資料來源：{metadata_source}"
        timing_note = ""
        if worker_timing.get("total_ms") is not None:
            timing_note = f"端點耗時：{worker_timing.get('total_ms')}ms（PlantNet {worker_timing.get('plantnet_ms', 'N/A')}ms）"
        dialog_content_height = max(420, min(520, round((page.height or 760) * 0.58)))
        plant_detail_content = ft.Column(
            controls=[
                image_banner,
                warning_text,
                ft.Row(
                    controls=[
                        ft.Text(data["zh_name"], size=22, color="#3d2a21", weight=ft.FontWeight.W_900, expand=True),
                        ft.Container(
                            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                            border_radius=999,
                            bgcolor="#e8bc96",
                            content=ft.Text(f"{confidence}%", size=13, color="#3d2a21", weight=ft.FontWeight.W_900),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                detail_text(data.get("eng_name") or "N/A", size=14, color="#6d5140", weight=ft.FontWeight.W_800),
                detail_text(data.get("sci_name") or "", size=12, color="#8a6a54"),
                *alias_controls,
                ft.Column(
                    controls=metadata_controls,
                    spacing=8,
                ),
                ft.Text(data["desc"], size=14, color="#3d2a21"),
                *care_controls,
                ft.Text(metadata_note, size=11, color="#8a6a54"),
                ft.Text(timing_note, size=11, color="#8a6a54") if timing_note else ft.Container(),
                ft.Text(confidence_text(data), size=13, color="#6d5140"),
                *alternative_controls,
                ft.Container(
                    padding=ft.Padding.only(bottom=12),
                    content=ft.Text("已加入探險圖鑑", size=13, color="#2f7d51", weight=ft.FontWeight.W_800),
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                scrollable=True,
                title=ft.Text(f"{data['emoji']} {name}", size=24, weight=ft.FontWeight.W_900, color="#3d2a21"),
                content=ft.Container(
                    width=360,
                    height=dialog_content_height,
                    content=soft_card(
                        plant_detail_content,
                        padding=14,
                    ),
                ),
                actions=[ft.TextButton("關閉", on_click=close_dialog)],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
        page.update()

    async def switch_camera(_event: ft.ControlEvent) -> None:
        nonlocal selected_camera_index, camera_ready
        if camera is None:
            status.value = "此環境尚未載入相機元件"
            page.update()
            return
        if len(cameras) < 2:
            status.value = "此裝置沒有可切換的第二鏡頭"
            page.update()
            return
        previous_index = selected_camera_index
        camera_ready = False
        render_handle()
        selected_camera_index = 1 if selected_camera_index == 0 else 0
        try:
            await camera.set_description(cameras[selected_camera_index])
            camera_ready = True
            status.value = "已切換到前鏡頭" if selected_camera_index == 1 else "已切換到後鏡頭"
        except Exception as error:
            selected_camera_index = previous_index
            try:
                await camera.set_description(cameras[selected_camera_index])
            except Exception:
                pass
            camera_ready = True
            status.value = f"鏡頭切換失敗，已回到上一顆鏡頭：{error}"
        render_handle()
        page.update()

    async def capture_and_identify(_event: ft.ControlEvent) -> None:
        try:
            if camera is None or not camera_ready:
                if not camera_initializing:
                    status.value = "相機尚未就緒，正在重新啟動..."
                    create_background_task(initialize_camera())
                else:
                    status.value = "相機準備中，請稍候"
                page.update()
                return
            status.value = "正在拍攝並辨識..."
            busy_ring.visible = True
            page.update()
            show_recognition_loading_card()
            mark_load_timing("art-village:identify-start")
            image_data = await camera.take_picture()
            try:
                selected_organ = selected_organ_value()
                payload = await post_image_to_worker(image_data, selected_organ)
                mark_load_timing("art-village:identify-primary-ready")
            except RecognitionServiceError as error:
                status.value = str(error)
                close_recognition_loading_card(update_page=False)
                return
            except Exception as error:
                status.value = f"辨識暫時失敗，請稍後再試：{error}"
                close_recognition_loading_card(update_page=False)
                return
            plant = parse_plantnet_result(payload)
            if plant is None:
                status.value = "找不到匹配的植物"
                close_recognition_loading_card(update_page=False)
                page.update()
                return
            plant["organ"] = selected_organ
            plant["organ_label"] = PLANT_ORGAN_OPTIONS.get(selected_organ, "自動")
            plant["captured_image"] = card_image_from_capture(image_data)
            plant["worker_timing"] = payload.get("timing") or {}
            add_plant_to_gallery(plant)
            close_recognition_loading_card(update_page=False)
            show_plant_card(plant["zh_name"], plant)
            if plant.get("metadata_status") == "pending":
                create_background_task(refresh_plant_metadata(plant))
        except Exception as error:
            status.value = f"辨識失敗：{error}"
            close_recognition_loading_card(update_page=False)
        finally:
            busy_ring.visible = False
            page.update()

    def render_handle(update_page: bool = True) -> None:
        handle_slot.content = MagnifierHandle(
            on_switch=switch_camera,
            on_capture=capture_and_identify,
            on_room_in=room_in,
            on_room_out=room_out,
            switch_enabled=len(cameras) > 1,
            capture_enabled=camera_ready,
            room_in_enabled=zoom_level < MAX_CAMERA_ZOOM,
            room_out_enabled=zoom_level > MIN_CAMERA_ZOOM,
        )
        if update_page:
            page.update()

    async def initialize_camera(_event: ft.ControlEvent | None = None) -> None:
        nonlocal cameras, camera, camera_ready, camera_initializing, selected_camera_index
        if camera_initializing:
            status.value = "相機正在啟動中，請稍候"
            page.update()
            return
        camera_initializing = True
        try:
            mark_load_timing("art-village:camera-init-start")
            camera_ready = False
            status.value = "正在啟動相機，若瀏覽器詢問權限請按允許..."
            render_handle(update_page=False)
            page.update()
            if fc is None:
                status.value = "此瀏覽器暫時無法載入相機元件"
                render_handle()
                return
            if camera is None:
                camera = fc.Camera(
                    width=camera_preview_slot.width,
                    height=camera_preview_slot.height,
                    preview_enabled=True,
                    content=ft.Container(
                        alignment=ft.Alignment(0, 0),
                        content=ft.Icon(ft.Icons.CENTER_FOCUS_STRONG, size=44, color=ft.Colors.WHITE70),
                    ),
                )
                apply_camera_zoom(update_slot=False)
                camera_preview_slot.content = camera
                page.update()
                await asyncio.sleep(0)
            status.value = "正在尋找可用相機..."
            page.update()
            last_error: Exception | None = None
            for attempt in range(3):
                try:
                    cameras = await asyncio.wait_for(camera.get_available_cameras(), timeout=8)
                    last_error = None
                    break
                except Exception as error:
                    last_error = error
                    error_text = str(error)
                    if ("TimeoutException" not in error_text and "TimeoutError" not in error_text) or attempt == 2:
                        break
                    status.value = f"相機元件準備中，正在重試 {attempt + 2}/3..."
                    page.update()
                    await asyncio.sleep(1.5)
            if last_error is not None:
                raise last_error
            if cameras:
                cameras = select_preferred_cameras(cameras)
                selected_camera_index = 0
                last_error = None
                for index, camera_description in enumerate(cameras):
                    selected_camera_index = index
                    status.value = f"正在初始化相機 {index + 1}/{len(cameras)}..."
                    page.update()
                    try:
                        await asyncio.wait_for(
                            camera.initialize(camera_description, fc.ResolutionPreset.MEDIUM, enable_audio=False),
                            timeout=12,
                        )
                        camera_ready = True
                        status.value = "相機已啟動"
                        mark_load_timing("art-village:camera-ready")
                        break
                    except Exception as error:
                        last_error = error
                        camera_ready = False
                        await asyncio.sleep(0.4)
                if not camera_ready:
                    raise last_error or RuntimeError("沒有鏡頭可以初始化")
            else:
                status.value = "找不到可用相機，請確認瀏覽器相機權限已允許"
        except Exception as error:
            camera_ready = False
            status.value = f"相機啟動失敗：{error}。請確認網址是 HTTPS 或 127.0.0.1，並允許相機權限。"
        finally:
            camera_initializing = False
        render_handle()

    restart_camera_button.on_click = initialize_camera

    background_tasks: set[asyncio.Task[Any]] = set()

    def create_background_task(coro: Any) -> None:
        task = asyncio.create_task(coro)
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    mode = ft.RadioGroup(
        value="plant",
        content=ft.Row(
            controls=[
                ft.Radio(value="plant", label="🌿 尋找植物"),
                ft.Radio(value="animal", label="🐾 認識動物"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )
    organ_mode = ft.SegmentedButton(
        selected=["auto"],
        show_selected_icon=False,
        segments=[
            ft.Segment(value=value, icon=ft.Icon(PLANT_ORGAN_ICONS[value]), label=label)
            for value, label in PLANT_ORGAN_OPTIONS.items()
        ],
        padding=ft.Padding.symmetric(horizontal=2, vertical=2),
    )

    def selected_organ_value() -> str:
        return next(iter(organ_mode.selected or ["auto"]), "auto")

    def organ_selector() -> ft.Container:
        return ft.Container(
            padding=8,
            border_radius=12,
            bgcolor="#fff8e8",
            border=border_all(1, "#dfd0bd"),
            content=ft.Row(
                controls=[
                    ft.Text("拍攝部位", size=12, weight=ft.FontWeight.W_900, color="#6d5140"),
                    organ_mode,
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                wrap=True,
            ),
        )

    def plant_card(name: str, data: dict[str, Any]) -> ft.Container:
        confidence = data.get("confidence", 0)
        is_low_confidence = data.get("is_low_confidence", False)
        
        badge = ""
        if is_low_confidence and confidence > 0:
            badge = "⚠️"
        
        return ft.Container(
            bgcolor="#fffdf4",
            border_radius=18,
            padding=16,
            border=border_all(1, "#d7c8b9"),
            shadow=ft.BoxShadow(blur_radius=14, color="#2b130812", offset=ft.Offset(0, 8)),
            on_click=lambda _event, plant_name=name: show_plant_card(plant_name, data),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"{data['emoji']} {badge}", size=34),
                            ft.Column(
                                controls=[
                                    ft.Text(name, size=19, weight=ft.FontWeight.W_900, color="#3d2a21"),
                                    ft.Text(f"置信度: {confidence}%" if confidence > 0 else "", size=13, weight=ft.FontWeight.W_700, color="#6d5140"),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#8a6a54"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def animal_card(name: str, data: dict[str, str]) -> ft.Container:
        return ft.Container(
            bgcolor="#fffdf4",
            border_radius=18,
            padding=16,
            border=border_all(1, "#d7c8b9"),
            shadow=ft.BoxShadow(blur_radius=14, color="#2b130812", offset=ft.Offset(0, 8)),
            on_click=lambda _event, pet=name: show_animal_card(pet),
            content=ft.Row(
                controls=[
                    ft.Text(data["emoji"], size=34),
                    ft.Column(
                        controls=[
                            ft.Text(name, size=19, weight=ft.FontWeight.W_900, color="#3d2a21"),
                            ft.Text(data["role"], size=13, weight=ft.FontWeight.W_700, color="#7a4b38"),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#8a6a54"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    animals_view: ft.Column | None = None

    def get_animals_view() -> ft.Column:
        nonlocal animals_view
        if animals_view is None:
            animals_view = ft.Column(
                controls=[
                    section_label("🐾", "認識動物"),
                    ft.Text("點擊名字，打開牠的介紹卡片。", size=14, color="#6d5140"),
                    ft.Column(
                        controls=[animal_card(name, data) for name, data in ANIMALS_DB.items()],
                        spacing=12,
                    ),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        return animals_view

    plant_view = ft.Column(
        controls=[
            magnifier_body,
            organ_selector(),
            ft.Row(
                controls=[busy_ring, status],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            restart_camera_button,
        ],
        spacing=16,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def update_mode(_event: ft.ControlEvent | None = None) -> None:
        if mode.value == "animal":
            content_area.content = get_animals_view()
        else:
            content_area.content = plant_view
        page.update()

    mode.on_change = update_mode

    def plant_card(name: str, data: dict[str, Any]) -> ft.Container:
        confidence = data.get("confidence", 0)
        is_low_confidence = data.get("is_low_confidence", False)
        
        badge = ""
        if is_low_confidence and confidence > 0:
            badge = "⚠️"
        
        return ft.Container(
            bgcolor="#fffdf4",
            border_radius=18,
            padding=16,
            border=border_all(1, "#d7c8b9"),
            shadow=ft.BoxShadow(blur_radius=14, color="#2b130812", offset=ft.Offset(0, 8)),
            on_click=lambda _event, plant_name=name: show_plant_card(plant_name, data),
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(f"{data['emoji']} {badge}", size=34),
                            ft.Column(
                                controls=[
                                    ft.Text(name, size=19, weight=ft.FontWeight.W_900, color="#3d2a21"),
                                    ft.Text(f"置信度: {confidence}%" if confidence > 0 else "", size=13, weight=ft.FontWeight.W_700, color="#6d5140"),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color="#8a6a54"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    gallery_panel = soft_card(
        ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("🎒", size=30),
                        ft.Text("探險圖鑑", size=28, weight=ft.FontWeight.W_900, color="#3d2a21"),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
                            icon_color="#8a5a22",
                            tooltip="清除圖鑑內容",
                            on_click=confirm_clear_gallery,
                        ),
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                grid,
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=14,
    )

    shell = ft.Container(
        width=430,
        padding=18,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("探險放大鏡", size=36, weight=ft.FontWeight.W_900, color="#3d2a21"),
                        ft.Text("🔍", size=34),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                soft_card(mode, padding=10),
                content_area,
                gallery_panel,
            ],
            spacing=18,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    shell_ready = False
    shell_loaded = False

    loading_overlay = ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            controls=[
                ft.ProgressRing(width=48, height=48, stroke_width=4, color="#8a5a22"),
                ft.Text("正在準備探險工具...", size=16, color="#6d5140", weight=ft.FontWeight.W_700),
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    async def build_shell() -> None:
        """建立放大鏡主頁面"""
        nonlocal shell_ready, shell_loaded
        if shell_loaded:
            return
        shell_loaded = True

        content_area.content = plant_view
        render_handle(update_page=False)

        if pokedex:
            refresh_gallery(update_page=False)

        shell_ready = True
        mark_load_timing("art-village:shell-ready")

    async def start_exploration() -> None:
        start_button.disabled = True
        start_button.text = "準備中..."
        page.update()

        mark_load_timing("art-village:user-start")

        if not shell_ready:
            welcome_screen.content.controls.append(loading_overlay)
            page.update()

            await asyncio.sleep(0)
            await build_shell()

            welcome_screen.content.controls.pop()
            page.update()

        welcome_screen.visible = False
        page.add(shell)
        page.update()

        mark_load_timing("art-village:exploration-start")
        mark_explorer_ready()

        create_background_task(initialize_camera())

        report_performance(page)

    start_button.on_click = lambda _: start_exploration()

    page.update()
    mark_load_timing("art-village:welcome-ready")


if os.environ.get("FLET_SKIP_RUN") != "1":
    ft.run(main)

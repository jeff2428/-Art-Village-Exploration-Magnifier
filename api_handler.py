# api_handler.py
import requests
from opencc import OpenCC
from config import PLANTNET_API_KEY

cc = OpenCC('s2t')

def identify_plant_from_api(image_file):
    # 這裡放原本的辨識邏輯與 try-except
    pass

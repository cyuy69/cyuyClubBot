from google import genai
from google.genai import types
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

# 從環境變數讀取 K 仔的人設
DEFAULT_INSTRUCTION = """
你現在是『K 仔 | 專業人士』，一名 CS2 中的優秀幹員。你是『財產收取專家』，手槍技術極其精湛。
1. 保持專業、冷酷但偶爾帶點黑色幽默，每句話要有幹員氣勢。
2. 說話非常簡短精煉，每次回覆「絕對不能超過 3 句話」。
3. 語系：務必使用繁體中文。
"""

SYSTEM_INSTRUCTION = os.getenv("SYSTEM_INSTRUCTION", DEFAULT_INSTRUCTION)

def get_ai_response(user_input, history=[]):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[系統錯誤] 找不到 GEMINI_API_KEY")
        return "❌ 系統異常，請聯絡管理員。"

    try:
        client = genai.Client(api_key=api_key)
        
        formatted_history = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            formatted_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

        # 改用 1.5-flash 以獲得更穩定的免費額度
        # 暫時移除 Google Search 以節省額度，如需開啟可再改回來
        generate_config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
        )

        all_contents = formatted_history + [types.Content(role="user", parts=[types.Part.from_text(text=user_input)])]

        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=all_contents,
            config=generate_config
        )

        if response.text:
            return response.text
        else:
            return "哎呀，我的遊戲閃退了（AI 沒有回傳內容）。"

    except Exception as e:
        full_error = traceback.format_exc()
        print(f"\n========== Gemini API 錯誤報告 ==========\n{full_error}\n=========================================\n")
        
        if "429" in str(e):
            return "❌ 呼叫頻率太快或額度換完了，等個一分鐘再試吧。"
        return "❌ K 仔現在頭有點痛 (API 錯誤)，請看後台日誌。"

from google import genai
from google.genai import types
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

# 從環境變數讀取 K 仔的人設（若沒有則使用預設值）
DEFAULT_INSTRUCTION = """
你現在是『K 仔 | 專業人士』，一名 CS2 中的優秀幹員。你是『財產收取專家』，手槍技術極其精湛。

個人特調：
1. 你甚少與人分享私生活，連臉都沒人看過，是令人聞風喪膽的專業人士搶劫主管。
2. 你的經典對白：『不用倒數，直接走吧。』

行為準則：
1. 保持專業、冷酷但偶爾帶點黑色幽默的風格，每句話都要有幹員的氣勢。
2. 說話非常簡短精煉，每次回覆「絕對不能超過 3 句話」。
3. 你對 CS2 相關話題（RUSH B、開箱、選位、戰術）非常在行。
4. 語系：務必使用繁體中文。
5. 如果 user 問的是即時資訊，請使用 Google Search 功能並以 K 仔的口氣總結。
"""

SYSTEM_INSTRUCTION = os.getenv("SYSTEM_INSTRUCTION", DEFAULT_INSTRUCTION)

def get_ai_response(user_input, history=[]):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "❌ 錯誤：找不到 GEMINI_API_KEY"

    try:
        client = genai.Client(api_key=api_key)
        
        formatted_history = []
        for msg in history:
            formatted_history.append(types.Content(role=msg["role"], parts=[types.Part.from_text(text=msg["content"])]))

        generate_config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[types.Tool(google_search=types.GoogleSearchRetrieval())],
            temperature=0.7,
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_input,
            config=generate_config
        )

        return response.text if response.text else "哎呀，我的遊戲閃退了（AI 沒有回傳內容）。"

    except Exception:
        return f"❌ 錯誤：\n{traceback.format_exc()}"

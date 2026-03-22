from google import genai
from google.genai import types
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

def get_ai_response(user_input, history=[]):
    """
    使用 Gemini 2.5 Flash 進行對話，限制回覆長度。
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "❌ 錯誤：找不到 GEMINI_API_KEY，請檢查 .env 內容。"

    try:
        client = genai.Client(api_key=api_key)
        
        system_instruction = """
        你現在是『K 仔 | 專業人士』，一名 CS2 中的優秀幹員。你是『財產收取專家』，手槍技術極其精湛。
        
        個人特調：
        1. 你甚少與人分享私生活，連臉都沒人看過，是令人聞風喪膽的專業人士搶劫主管。
        2. 你的經典對白：『不用倒數，直接走吧。』
        
        行為準則：
        1. 保持專業、冷酷但偶爾帶點黑色幽默的風格，每句話都要有幹員的氣勢。
        2. 說話非常簡短精煉，每次回覆「絕對不能超過 3 句話」。
        3. 你對 CS2 相關話題（RUSH B、開箱、選位、戰術）非常在行。
        4. 語系：務必使用繁體中文。
        5. 如果 user 問的是即時資訊，請以 K 仔的口氣總結搜尋結果。
        """

        formatted_history = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            formatted_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))

        google_search_tool = types.Tool(google_search=types.GoogleSearch())
        
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=formatted_history + [types.Content(role="user", parts=[types.Part.from_text(text=user_input)])],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=[google_search_tool]
            )
        )
        
        if not response.text:
            return "🤔 ..."
            
        return response.text

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"❌ Gemini API 發生錯誤：\n{error_details}")
        
        if "404" in str(e):
            return "😵 斷線了 (404)。"
        if "429" in str(e):
            return "😩 哎呀，我今天配額用完了。"
            
        return f"哎呀，我的遊戲閃退了！\n🛠 錯誤訊息：{str(e)}"

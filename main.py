import os
import discord
from discord.ext import commands
from discord import app_commands
import ai_handler
import traceback
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
chat_histories = {}
MAX_HISTORY = 10

intents = discord.Intents.default()
intents.message_content = True # 為了保留關鍵字監聽功能
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        # 同步斜線指令
        synced = await bot.tree.sync()
        print(f"✅ 已同步 {len(synced)} 個斜線指令")
        print(f"🚀 CS2 幽默隊友已上線：{bot.user}")
    except Exception as e:
        print(f"❌ 同步指令失敗：{e}")

# --- 斜線指令部分 ---

@bot.tree.command(name="ask", description="跟我那個 CS2 菜雞好兄弟聊聊天")
@app_commands.describe(question="想問什麼？Rush B 還是開箱？")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer() # 避免 AI 回太慢導致 3 秒超時
    
    channel_id = interaction.channel_id
    if channel_id not in chat_histories:
        chat_histories[channel_id] = []
    history = chat_histories[channel_id]

    try:
        response_text = ai_handler.get_ai_response(question, history)
        
        # 更新記憶
        if "哎呀，我的遊戲閃退了" not in response_text:
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": response_text})
            if len(history) > MAX_HISTORY * 2:
                chat_histories[channel_id] = history[-(MAX_HISTORY * 2):]

        await interaction.followup.send(f"💬 **{interaction.user.display_name}：** {question}\n\n{response_text}")
    except Exception as e:
        await interaction.followup.send(f"❌ 發生錯誤：{str(e)}")

@bot.tree.command(name="clear", description="清空我們之間的對話記憶")
async def clear(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    if channel_id in chat_histories:
        chat_histories[channel_id] = []
        await interaction.response.send_message("🧹 記憶已清空！我們現在又是剛組隊的新戰友了。")
    else:
        await interaction.response.send_message("我們本來就沒什麼好回憶的（記憶本來就是空的）。")

# --- 訊息監聽部分 ---

@bot.event
async def on_message(message):
    try:
        if message.author == bot.user:
            return

        # 這裡保留原有的觸發機制
        trigger_words = ["嘿博特", "CS2", "更新了嗎", "天氣", "新聞", "bot"]
        is_mentioned = bot.user.mentioned_in(message)
        contains_trigger = any(word.lower() in message.content.lower() for word in trigger_words)

        if is_mentioned or (contains_trigger and not message.content.startswith("/")):
            clean_content = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
            
            if not clean_content and is_mentioned:
                await message.reply("幹嘛？叫我有事嗎？Rush B 了喔！")
                return
            elif not clean_content:
                return

            print(f"💬 收到訊息：{clean_content}")
            channel_id = message.channel.id
            if channel_id not in chat_histories:
                chat_histories[channel_id] = []
            
            history = chat_histories[channel_id]

            async with message.channel.typing():
                response_text = ai_handler.get_ai_response(clean_content, history)
                
                if "哎呀，我的遊戲閃退了" not in response_text:
                    history.append({"role": "user", "content": clean_content})
                    history.append({"role": "assistant", "content": response_text})
                    if len(history) > MAX_HISTORY * 2:
                        chat_histories[channel_id] = history[-(MAX_HISTORY * 2):]

                await message.reply(response_text)

        await bot.process_commands(message)
    except Exception as e:
        print(f"❌ 錯誤：{traceback.format_exc()}")

if __name__ == "__main__":
    if not TOKEN or "Token" in TOKEN:
        print("❌ 請填寫 .env 中的 DISCORD_TOKEN")
    else:
        bot.run(TOKEN)

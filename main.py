import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
import ai_handler
import traceback
from dotenv import load_dotenv
import datetime
import pytz

# --- 1. 載入設定檔 ---
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ROLE_ID = os.getenv("ROLE_ID")
UPDATE_BOT_ID = os.getenv("UPDATE_BOT_ID") # 要監聽的机器人 ID

TRIGGER_WORDS_STR = os.getenv("TRIGGER_WORDS", "嘿博特,CS2,bot,K仔")
TRIGGER_WORDS = [word.strip().lower() for word in TRIGGER_WORDS_STR.split(",")]

MAX_HISTORY = int(os.getenv("MAX_HISTORY", 10))
TW_TIMEZONE = pytz.timezone('Asia/Taipei')
NIGHTLY_HOUR = int(os.getenv("NIGHTLY_HOUR", 22))
NIGHTLY_MINUTE = int(os.getenv("NIGHTLY_MINUTE", 0))

# --- 2. 初始化 Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

chat_histories = {}
target_time = datetime.time(hour=NIGHTLY_HOUR, minute=NIGHTLY_MINUTE, second=0, tzinfo=TW_TIMEZONE)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ [系統] 機器人 {bot.user} 已上線")
        print(f"✅ [系統] 已同步 {len(synced)} 個斜線指令")
        if not nightly_call.is_running():
            nightly_call.start()
            print(f"📅 [任務] 定時揪團任務已啟動：每晚 {NIGHTLY_HOUR:02d}:{NIGHTLY_MINUTE:02d}")
    except Exception:
        print(f"❌ 初始化失敗：{traceback.format_exc()}")

# --- 3. 定時任務 ---
@tasks.loop(time=target_time)
async def nightly_call():
    if not CHANNEL_ID: return
    channel = bot.get_channel(int(CHANNEL_ID))
    if channel:
        try:
            prompt = "現在是晚上 10 點，請以 K 仔的口氣，喊大家上線打 CS2。記得標記身分組，3句話以內。"
            call_message = ai_handler.get_ai_response(prompt, [])
            mention_text = f"<@&{ROLE_ID}>" if ROLE_ID else "@everyone"
            await channel.send(f"{mention_text}\n{call_message}")
        except Exception:
            print(f"❌ 定時任務失敗：{traceback.format_exc()}")

# --- 4. 斜線指令 ---
@bot.tree.command(name="ask", description="跟 K 仔聊聊專業的事")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    cid = interaction.channel_id
    if cid not in chat_histories: chat_histories[cid] = []
    try:
        response_text = ai_handler.get_ai_response(question, chat_histories[cid])
        chat_histories[cid].append({"role": "user", "content": question})
        chat_histories[cid].append({"role": "assistant", "content": response_text})
        if len(chat_histories[cid]) > MAX_HISTORY * 2:
            chat_histories[cid] = chat_histories[cid][-(MAX_HISTORY * 2):]
        await interaction.followup.send(f"👤 **{interaction.user.display_name}：** {question}\n\n{response_text}")
    except Exception:
        await interaction.followup.send(f"❌ 錯誤：\n```{traceback.format_exc()[-300:]}```")

@bot.tree.command(name="clear", description="清空 K 仔對你的記憶")
async def clear(interaction: discord.Interaction):
    chat_histories[interaction.channel_id] = []
    await interaction.response.send_message("🧹 記憶已清空！")

# --- 5. 訊息監聽 ---
@bot.event
async def on_message(message):
    try:
        if message.author == bot.user: return

        # 特殊功能：監聽指定機器人更新並總結
        if str(message.author.id) == str(UPDATE_BOT_ID):
            print(f"📢 [更新] 偵測到更新機器人發話：{message.author.id}")
            async with message.channel.typing():
                # 組合 Prompt，要求 K 仔總結
                update_content = message.content
                # 如果有 Embeds (卡片訊息)，也抓取描述文字
                if message.embeds:
                    for embed in message.embeds:
                        if embed.description:
                            update_content += f"\n[內容補充]: {embed.description}"
                
                prompt = f"以下是 CS2 的英文更新消息，請用『K 仔 | 專業人士』的口氣，將其翻譯成繁體中文並總結重點給隊友看。語句要帥氣、簡短，總結後要順便叫大家上線：\n\n{update_content}"
                summary = ai_handler.get_ai_response(prompt, [])
                
                mention_text = f"<@&{ROLE_ID}>" if ROLE_ID else "@everyone"
                await message.reply(f"{mention_text}\n**📦 K 仔更新簡報：**\n{summary}")
            return

        # 一般對話邏輯
        is_mentioned = bot.user.mentioned_in(message)
        contains_trigger = any(word in message.content.lower() for word in TRIGGER_WORDS)

        if is_mentioned or (contains_trigger and not message.content.startswith("/")):
            clean_content = message.content.replace(f"<@{bot.user.id}>", "").strip()
            if not clean_content:
                if is_mentioned: await message.reply("幹嘛？不用倒數，直接走吧。")
                return

            cid = message.channel.id
            if cid not in chat_histories: chat_histories[cid] = []
            async with message.channel.typing():
                response_text = ai_handler.get_ai_response(clean_content, chat_histories[cid])
                chat_histories[cid].append({"role": "user", "content": clean_content})
                chat_histories[cid].append({"role": "assistant", "content": response_text})
                await message.reply(response_text)

        await bot.process_commands(message)
    except Exception:
        print(f"❌ 錯誤：{traceback.format_exc()}")

if __name__ == "__main__":
    bot.run(TOKEN)

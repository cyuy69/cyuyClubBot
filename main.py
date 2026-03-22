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
UPDATE_BOT_ID = os.getenv("UPDATE_BOT_ID")

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

def truncate_content(text, limit=1900):
    """防止超過 Discord 2000 字元限制"""
    if len(text) > limit:
        return text[:limit] + "\n\n...(內容過長已截斷)"
    return text

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ [系統] 機器人 {bot.user} 已上線")
        if not nightly_call.is_running():
            nightly_call.start()
    except Exception:
        print(f"❌ 初始化失敗：{traceback.format_exc()}")

# --- 3. 定時任務 ---
@tasks.loop(time=target_time)
async def nightly_call():
    if not CHANNEL_ID: return
    channel = bot.get_channel(int(CHANNEL_ID))
    if channel:
        try:
            prompt = "現在是晚上 10 點，請以 K 仔的口氣，喊大家上線打 CS2。標記身分組，3句話以內。"
            call_message = ai_handler.get_ai_response(prompt, [])
            mention_text = f"<@&{ROLE_ID}>" if ROLE_ID else "@everyone"
            await channel.send(truncate_content(f"{mention_text}\n{call_message}"))
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
        await interaction.followup.send(truncate_content(f"👤 **{interaction.user.display_name}：** {question}\n\n{response_text}"))
    except Exception:
        await interaction.followup.send(f"❌ 錯誤：\n```{traceback.format_exc()[-300:]}```")

# --- 5. 訊息監聽 ---
@bot.event
async def on_message(message):
    try:
        if message.author == bot.user: return

        # 監聽指定機器人更新
        if str(message.author.id) == str(UPDATE_BOT_ID):
            async with message.channel.typing():
                update_content = message.content
                if message.embeds:
                    for embed in message.embeds:
                        if embed.description:
                            update_content += f"\n[內容補充]: {embed.description}"
                
                # 限制傳給 AI 的長度，避免 AI 回傳也太長
                prompt = f"請總結此 CS2 更新：\n{update_content[:2000]}"
                summary = ai_handler.get_ai_response(prompt, [])
                
                mention_text = f"<@&{ROLE_ID}>" if ROLE_ID else "@everyone"
                await message.reply(truncate_content(f"{mention_text}\n**📦 K 仔更新簡報：**\n{summary}"))
            return

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
                await message.reply(truncate_content(response_text))

        await bot.process_commands(message)
    except Exception:
        print(f"❌ 錯誤：{traceback.format_exc()}")

if __name__ == "__main__":
    bot.run(TOKEN)

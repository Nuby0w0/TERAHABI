import discord
from discord.ext import tasks, commands
import asyncio
from datetime import datetime
import pytz
import json
import os

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===================== 자동 삭제 기능 =====================
@tasks.loop(minutes=1)
async def delete_loop():
    now_kst = datetime.now(pytz.timezone("Asia/Seoul"))
    if now_kst.hour == 0 and now_kst.minute == 0 and delete_loop.started_by_command:
        await run_deletion()

delete_loop.started_by_command = False

async def run_deletion():
    channel_id = 1374600137388720221  # 자동 삭제 채널 ID
    channel = bot.get_channel(channel_id)
    if not channel:
        print("❌ 채널을 찾을 수 없습니다.")
        return

    try:
        async for msg in channel.history(limit=100):
            await msg.delete()
    except Exception as e:
        print(f"⚠️ 메시지 삭제 중 오류: {e}")

@bot.command()
@commands.has_any_role("관리자", "오롯이 완전한 하나의 세상")
async def 자동삭제(ctx):
    if not delete_loop.is_running():
        delete_loop.started_by_command = True
        delete_loop.start()
        await ctx.send("✅ 자동 삭제가 시작되었습니다 (매일 00:00 KST).")
    else:
        await ctx.send("⚠️ 자동 삭제는 이미 실행 중입니다.")

@bot.command()
@commands.has_any_role("관리자", "오롯이 완전한 하나의 세상")
async def 중지(ctx):
    if delete_loop.is_running():
        delete_loop.stop()
        delete_loop.started_by_command = False
        await ctx.send("🛑 자동 삭제가 중지되었습니다.")
    else:
        await ctx.send("⚠️ 자동 삭제는 이미 중지된 상태입니다.")

@bot.command(name="삭제")
@commands.has_any_role("관리자", "오롯이 완전한 하나의 세상")
@commands.has_permissions(manage_messages=True)
async def delete_messages_cmd(ctx, 개수: int):
    if 개수 < 1:
        await ctx.send("1 이상의 숫자를 입력해주세요.", delete_after=5)
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    deleted_total = 0
    while 개수 > 0:
        batch = min(개수, 100)
        deleted = await ctx.channel.purge(limit=batch)
        deleted_total += len(deleted)
        개수 -= batch

    msg = await ctx.send(f"{deleted_total}개의 메시지를 삭제했습니다.")
    await msg.delete(delay=5)

# ===================== 하단 고정 메시지 기능 =====================
BOTTOM_FIXED_FILE = "bottom_fixed.json"
bottom_fixed_content = {}
bottom_fixed_message = {}

def load_bottom_fixed():
    if os.path.exists(BOTTOM_FIXED_FILE):
        try:
            with open(BOTTOM_FIXED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except json.JSONDecodeError:
            pass
    return {}

def save_bottom_fixed():
    with open(BOTTOM_FIXED_FILE, "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in bottom_fixed_content.items()}, f, ensure_ascii=False, indent=2)

async def send_fixed_message(channel, content):
    try:
        return await channel.send(content)
    except Exception as e:
        print(f"고정 메시지 전송 실패: {e}")

async def delete_fixed_message(channel_id):
    msg = bottom_fixed_message.get(channel_id)
    if msg:
        try:
            await msg.delete()
        except discord.NotFound:
            pass
        bottom_fixed_message.pop(channel_id, None)

@bot.event
async def on_ready():
    global bottom_fixed_content
    print(f"✅ 로그인됨: {bot.user}")
    bottom_fixed_content = load_bottom_fixed()

    for channel_id, content in bottom_fixed_content.items():
        channel = bot.get_channel(channel_id)
        if channel:
            msg = await send_fixed_message(channel, content)
            if msg:
                bottom_fixed_message[channel_id] = msg

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot:
        return

    channel_id = message.channel.id
    if channel_id in bottom_fixed_content:
        await delete_fixed_message(channel_id)
        msg = await send_fixed_message(message.channel, bottom_fixed_content[channel_id])
        if msg:
            bottom_fixed_message[channel_id] = msg

@bot.command(name="고정")
@commands.has_permissions(manage_messages=True)
async def 고정(ctx, *, 내용: str):
    channel_id = ctx.channel.id
    bottom_fixed_content[channel_id] = 내용
    save_bottom_fixed()

    await delete_fixed_message(channel_id)
    msg = await send_fixed_message(ctx.channel, 내용)
    if msg:
        bottom_fixed_message[channel_id] = msg

@bot.command(name="고정해제")
@commands.has_permissions(manage_messages=True)
async def 고정해제(ctx):
    channel_id = ctx.channel.id

    await delete_fixed_message(channel_id)

    if channel_id in bottom_fixed_content:
        bottom_fixed_content.pop(channel_id)
        save_bottom_fixed()

    await ctx.send("📌 고정 메시지가 해제되었습니다.", delete_after=5)


bot.run("MTM3NDk0NzE2MTYxMDkxMTc4NA.GoM3HZ.IdWNu3vKVY_9sCKW1cbOeEFHRCpfKld-Z3wuKM")


import discord
from discord import app_commands, Embed, Colour
from discord.ext import commands
import requests
import time
import os
from flask import Flask
from threading import Thread

# Web server giữ bot luôn chạy
app = Flask('')

@app.route('/')
def home():
    return "Bot Đang Chạy"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# Thiết lập bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

API_TOKEN = 'dfce079aa89e7256f53f6f2fe2328c128a584467f5afcbc5f5d451c581879768'
LINK_ORIGINAL = 'https://danvnstore.site/callback.php'
YOUR_SECRET_KEY = 'lizimininbot'  # Đổi thành key bí mật khớp với file PHP

admin_ids = {1364169704943652924}
used_keys = set()

def is_admin(user):
    return user.id in admin_ids

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot đã đăng nhập: {bot.user}")

@tree.command(name="info", description="Giới thiệu các lệnh bot")
async def info(interaction: discord.Interaction):
    description = (
        "/mail /ugphone /redfinger /ldcloud - Nhận tài khoản
"
        "/getkey - Nhận key qua link

"
        "**Admin:** /upmail /upugphone /upredfinger /upldcloud
"
        "/delmail /delugphone /delredfinger /delldcloud
"
        "/setowner /dellowner /listowner"
    )
    embed = Embed(title="Danh sách lệnh bot", description=description, color=Colour.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="getkey", description="Tạo link rút gọn để nhận key")
async def getkey(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    try:
        unique_link = f"{LINK_ORIGINAL}?uid={user_id}&t={int(time.time())}"
        encoded_link = requests.utils.quote(unique_link, safe='')
        api_url = f"https://yeumoney.com/QL_api.php?token={API_TOKEN}&url={encoded_link}&format=json"
        res = requests.get(api_url, timeout=5)
        data = res.json()

        if data.get("status") == "success":
            await interaction.response.send_message(f"**Link nhận key:** {data['shortenedUrl']}")
        else:
            await interaction.response.send_message(f"**Lỗi API:** {data.get('status')}")
    except Exception as e:
        await interaction.response.send_message(f"**Lỗi:** {e}")

async def check_key_valid(interaction, key):
    try:
        res = requests.get("https://danvnstore.site/keys.json", timeout=5)
        key_data = res.json()
    except Exception as e:
        await interaction.response.send_message(f"**Lỗi khi kiểm tra key:** {e}")
        return False

    if key not in key_data:
        await interaction.response.send_message(f"**Key `{key}` không tồn tại hoặc không hợp lệ.**")
        return False

    if key in used_keys:
        await interaction.response.send_message(f"**Key `{key}` đã được dùng.**")
        return False

    return True

async def get_account(interaction, key, label):
    if not await check_key_valid(interaction, key):
        return

    try:
        res = requests.post("https://danvnstore.site/get_account.php", data={
            "label": label,
            "key": YOUR_SECRET_KEY
        })
        data = res.json()
        if data.get("status") != "success":
            await interaction.response.send_message(f"**{data.get('message', 'Lỗi không xác định')}**")
            return

        account = data.get("account", {})
        used_keys.add(key)
        await interaction.response.send_message(f"**Tài khoản {label}:**
Email: `{account.get('email')}`
Password: `{account.get('password')}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"**Lỗi khi lấy tài khoản:** {e}")

@tree.command(name="mail", description="Nhận tài khoản Email")
@app_commands.describe(key="Key hợp lệ")
async def mail(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "mail")

@tree.command(name="ugphone", description="Nhận tài khoản UGPhone")
@app_commands.describe(key="Key hợp lệ")
async def ugphone(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "ugphone")

@tree.command(name="redfinger", description="Nhận tài khoản RedFinger")
@app_commands.describe(key="Key hợp lệ")
async def redfinger(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "redfinger")

@tree.command(name="ldcloud", description="Nhận tài khoản LD Cloud")
@app_commands.describe(key="Key hợp lệ")
async def ldcloud(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "ldcloud")

async def upload_account(interaction, label, email, password):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return

    try:
        res = requests.post("https://danvnstore.site/upload_account.php", data={
            "label": label,
            "email": email,
            "password": password,
            "key": YOUR_SECRET_KEY
        })
        data = res.json()
        if data.get("status") == "success":
            await interaction.response.send_message(f"Đã thêm tài khoản {label}: `{email}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"Lỗi: {data.get('message')}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi khi upload: {e}", ephemeral=True)

@tree.command(name="upmail", description="Thêm tài khoản Email")
@app_commands.describe(email="Email", password="Mật khẩu")
async def upmail(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, "mail", email, password)

@tree.command(name="upugphone", description="Thêm tài khoản UGPhone")
@app_commands.describe(email="Email", password="Mật khẩu")
async def upugphone(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, "ugphone", email, password)

@tree.command(name="upredfinger", description="Thêm tài khoản RedFinger")
@app_commands.describe(email="Email", password="Mật khẩu")
async def upredfinger(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, "redfinger", email, password)

@tree.command(name="upldcloud", description="Thêm tài khoản LD Cloud")
@app_commands.describe(email="Email", password="Mật khẩu")
async def upldcloud(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, "ldcloud", email, password)

async def delete_account(interaction, label, email):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return

    try:
        res = requests.post("https://danvnstore.site/delete_account.php", data={
            "label": label,
            "email": email,
            "key": YOUR_SECRET_KEY
        })
        data = res.json()
        if data.get("status") == "success":
            await interaction.response.send_message(f"Đã xoá tài khoản {label}: `{email}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"Lỗi: {data.get('message')}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi khi xoá: {e}", ephemeral=True)

@tree.command(name="delmail", description="Xoá tài khoản Email")
@app_commands.describe(email="Email tài khoản")
async def delmail(interaction: discord.Interaction, email: str):
    await delete_account(interaction, "mail", email)

@tree.command(name="delugphone", description="Xoá tài khoản UGPhone")
@app_commands.describe(email="Email tài khoản")
async def delugphone(interaction: discord.Interaction, email: str):
    await delete_account(interaction, "ugphone", email)

@tree.command(name="delredfinger", description="Xoá tài khoản RedFinger")
@app_commands.describe(email="Email tài khoản")
async def delredfinger(interaction: discord.Interaction, email: str):
    await delete_account(interaction, "redfinger", email)

@tree.command(name="delldcloud", description="Xoá tài khoản LD Cloud")
@app_commands.describe(email="Email tài khoản")
async def delldcloud(interaction: discord.Interaction, email: str):
    await delete_account(interaction, "ldcloud", email)

@tree.command(name="setowner", description="Thêm admin")
@app_commands.describe(user="Người dùng cần thêm")
async def setowner(interaction: discord.Interaction, user: discord.User):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    admin_ids.add(user.id)
    await interaction.response.send_message(f"Đã thêm admin: {user.mention}", ephemeral=True)

@tree.command(name="dellowner", description="Xóa admin")
@app_commands.describe(user="Người dùng cần xóa")
async def dellowner(interaction: discord.Interaction, user: discord.User):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    admin_ids.discard(user.id)
    await interaction.response.send_message(f"Đã xóa admin: {user.mention}", ephemeral=True)

@tree.command(name="listowner", description="Liệt kê admin")
async def listowner(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    ids = "
".join([str(uid) for uid in admin_ids])
    await interaction.response.send_message("**Danh sách admin:**
" + ids, ephemeral=True)

bot.run(os.environ["DISCORD_TOKEN"])

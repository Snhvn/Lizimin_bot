import discord
from discord import app_commands
from discord.ext import commands
from discord import Embed, Colour
import requests
import time
import os
import json
from flask import Flask
from threading import Thread

# Tạo web server để UptimeRobot ping
app = Flask('')

@app.route('/')
def home():
    return "Bot Đang Chạy Url Trên"

def run():
    app.run(host='0.0.0.0', port=8080)

# Khởi động web server ở luồng riêng
Thread(target=run).start()

# Thiết lập bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

API_TOKEN = 'dfce079aa89e7256f53f6f2fe2328c128a584467f5afcbc5f5d451c581879768'
LINK_ORIGINAL = 'https://danvnstore.site/callback.php'

admin_ids = {1364169704943652924}
used_keys = set()

# Load và lưu file JSON
def load_accounts_from_file(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_accounts_to_file(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Khởi tạo từ file JSON
accounts_mail = load_accounts_from_file("mail_accounts.json")
accounts_ug = load_accounts_from_file("ug_accounts.json")
accounts_red = load_accounts_from_file("red_accounts.json")
accounts_ld = load_accounts_from_file("ld_accounts.json")

def is_admin(user):
    return user.id in admin_ids

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot đã đăng nhập: {bot.user}")

@tree.command(name="info", description="Giới thiệu các lệnh bot")
async def info(interaction: discord.Interaction):
    description = (
        "/mail  - Nhận tài khoản Email\n"
        "/ug  - Nhận tài khoản UGPhone\n"
        "/red  - Nhận tài khoản RedFonger\n"
        "/ld  - Nhận tài khoản LD Cloud\n"
        "/getkey - Lấy link rút gọn để nhận key\n"
        "\n**Lệnh admin:**\n"
        "/upmail  \n/upug  \n/upred  \n/upld  \n"
        "/listmail /listug /listred /listld\n"
        "/delmail \n/delug \n/delred \n/deldl \n"
        "/addadmin <user_id>\n/removeadmin <user_id>\n/listadmin"
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

async def get_account(interaction, key, accounts, label):
    if not await check_key_valid(interaction, key):
        return
    if not accounts:
        await interaction.response.send_message(f"**Hiện không còn tài khoản {label}.**")
        return
    email, password = accounts.popitem()
    used_keys.add(key)
    await interaction.response.send_message(f"**Tài khoản {label}**\nEmail: `{email}`\nPassword: `{password}`", ephemeral=True)

@tree.command(name="mail", description="Nhận tài khoản Email")
@app_commands.describe(key="Key hợp lệ")
async def mail(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_mail, "Email")

@tree.command(name="ug", description="Nhận tài khoản UGPhone")
@app_commands.describe(key="Key hợp lệ")
async def ug(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_ug, "UGPhone")

@tree.command(name="red", description="Nhận tài khoản RedFonger")
@app_commands.describe(key="Key hợp lệ")
async def red(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_red, "RedFonger")

@tree.command(name="ld", description="Nhận tài khoản LD Cloud")
@app_commands.describe(key="Key hợp lệ")
async def ld(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_ld, "LD Cloud")

# Admin: Upload tài khoản
async def upload_account(interaction, accounts, email, password, label, filename):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    accounts[email] = password
    save_accounts_to_file(filename, accounts)
    await interaction.response.send_message(f"Đã thêm tài khoản {label}: `{email}`")

@tree.command(name="upmail")
async def upmail(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, accounts_mail, email, password, "Email", "mail_accounts.json")

@tree.command(name="upug")
async def upug(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, accounts_ug, email, password, "UGPhone", "ug_accounts.json")

@tree.command(name="upred")
async def upred(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, accounts_red, email, password, "RedFonger", "red_accounts.json")

@tree.command(name="upld")
async def upld(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, accounts_ld, email, password, "LD Cloud", "ld_accounts.json")

# Admin: List tài khoản
async def list_accounts(interaction, filename, label):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    accounts = load_accounts_from_file(filename)
    if not accounts:
        await interaction.response.send_message(f"Không còn tài khoản {label}.", ephemeral=True)
    else:
        message = "\n".join([f"{email}: {pw}" for email, pw in accounts.items()])
        await interaction.response.send_message(f"Tài khoản {label}:\n`{message}`", ephemeral=True)

@tree.command(name="listmail")
async def listmail(interaction: discord.Interaction):
    await list_accounts(interaction, "mail_accounts.json", "Email")

@tree.command(name="listug")
async def listug(interaction: discord.Interaction):
    await list_accounts(interaction, "ug_accounts.json", "UGPhone")

@tree.command(name="listred")
async def listred(interaction: discord.Interaction):
    await list_accounts(interaction, "red_accounts.json", "RedFonger")

@tree.command(name="listld")
async def listld(interaction: discord.Interaction):
    await list_accounts(interaction, "ld_accounts.json", "LD Cloud")

# Admin: Xoá tài khoản
async def delete_account(interaction, accounts, email, label, filename):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    if email in accounts:
        del accounts[email]
        save_accounts_to_file(filename, accounts)
        await interaction.response.send_message(f"Đã xóa tài khoản {label}: `{email}`", ephemeral=True)
    else:
        await interaction.response.send_message(f"Tài khoản `{email}` không tồn tại.", ephemeral=True)

@tree.command(name="delmail")
async def delmail(interaction: discord.Interaction, email: str):
    await delete_account(interaction, accounts_mail, email, "Email", "mail_accounts.json")

@tree.command(name="delug")
async def delug(interaction: discord.Interaction, email: str):
    await delete_account(interaction, accounts_ug, email, "UGPhone", "ug_accounts.json")

@tree.command(name="delred")
async def delred(interaction: discord.Interaction, email: str):
    await delete_account(interaction, accounts_red, email, "RedFonger", "red_accounts.json")

@tree.command(name="deldl")
async def deldl(interaction: discord.Interaction, email: str):
    await delete_account(interaction, accounts_ld, email, "LD Cloud", "ld_accounts.json")

# Admin: Quản lý admin
@tree.command(name="addadmin")
async def addadmin(interaction: discord.Interaction, user_id: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    admin_ids.add(user_id)
    await interaction.response.send_message(f"Đã thêm admin: `{user_id}`")

@tree.command(name="removeadmin")
async def removeadmin(interaction: discord.Interaction, user_id: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    admin_ids.discard(user_id)
    await interaction.response.send_message(f"Đã xóa admin: `{user_id}`")

@tree.command(name="listadmin")
async def listadmin(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    ids = "\n".join([str(uid) for uid in admin_ids])
    await interaction.response.send_message(f"Danh sách admin:\n`{ids}`", ephemeral=True)

# Chạy bot
bot.run(os.environ["DISCORD_TOKEN"])

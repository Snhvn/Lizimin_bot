import discord
from discord import app_commands
from discord.ext import commands
from discord import Embed, Colour
import requests
import time
import os

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

accounts_mail = {}
accounts_ug = {}
accounts_red = {}
accounts_ld = {}

def is_admin(user):
    return user.id in admin_ids

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot đã đăng nhập: {bot.user}")

@tree.command(name="info", description="Giới thiệu các lệnh bot")
async def info(interaction: discord.Interaction):
    description = (
        "/mail <key> - Nhận tài khoản Email\n"
        "/ug <key> - Nhận tài khoản UGPhone\n"
        "/red <key> - Nhận tài khoản RedFinger\n"
        "/ld <key> - Nhận tài khoản LD Cloud\n"
        "/getkey - Lấy link rút gọn để nhận key\n"
        "\n**Lệnh admin:**\n"
        "/upmail <email> <password>\n"
        "/upug <email> <password>\n"
        "/upred <email> <password>\n"
        "/upld <email> <password>\n"
        "/listmail /listug /listred /listld\n"
        "/delmail <email>\n/delug <email>\n/delred <email>\n/deldl <email>\n"
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

# Lệnh nhận tài khoản
@tree.command(name="mail", description="Nhận tài khoản Email")
@app_commands.describe(key="Key hợp lệ")
async def mail(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_mail, "Email")

@tree.command(name="ug", description="Nhận tài khoản UGPhone")
@app_commands.describe(key="Key hợp lệ")
async def ug(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_ug, "UGPhone")

@tree.command(name="red", description="Nhận tài khoản RedFinger")
@app_commands.describe(key="Key hợp lệ")
async def red(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_red, "RedFonger")

@tree.command(name="ld", description="Nhận tài khoản LD Cloud")
@app_commands.describe(key="Key hợp lệ")
async def ld(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_ld, "LD Cloud")

# Admin: Upload tài khoản
async def upload_account(interaction, accounts, email, password, label):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    accounts[email] = password
    await interaction.response.send_message(f"Đã thêm tài khoản {label}: `{email}`")

@tree.command(name="upmail", description="(Admin) Thêm tài khoản Email")
async def upmail(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, accounts_mail, email, password, "Email")

@tree.command(name="upug", description="(Admin) Thêm tài khoản UGPhone")
async def upug(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, accounts_ug, email, password, "UGPhone")

@tree.command(name="upred", description="(Admin) Thêm tài khoản RedFonger")
async def upred(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, accounts_red, email, password, "RedFonger")

@tree.command(name="upld", description="(Admin) Thêm tài khoản LD Cloud")
async def upld(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, accounts_ld, email, password, "LD Cloud")

# Admin: List tài khoản
async def list_accounts(interaction, accounts, label):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    if not accounts:
        await interaction.response.send_message(f"Không còn tài khoản {label}.", ephemeral=True)
    else:
        message = "\n".join([f"{email}: {pw}" for email, pw in accounts.items()])
        await interaction.response.send_message(f"Tài khoản {label}:\n```{message}```", ephemeral=True)

@tree.command(name="listmail", description="(Admin) Xem danh sách tài khoản Email")
async def listmail(interaction: discord.Interaction):
    await list_accounts(interaction, accounts_mail, "Email")

@tree.command(name="listug", description="(Admin) Xem danh sách tài khoản UGPhone")
async def listug(interaction: discord.Interaction):
    await list_accounts(interaction, accounts_ug, "UGPhone")

@tree.command(name="listred", description="(Admin) Xem danh sách tài khoản RedFonger")
async def listred(interaction: discord.Interaction):
    await list_accounts(interaction, accounts_red, "RedFonger")

@tree.command(name="listld", description="(Admin) Xem danh sách tài khoản LD Cloud")
async def listld(interaction: discord.Interaction):
    await list_accounts(interaction, accounts_ld, "LD Cloud")

# Admin: Xoá tài khoản
async def delete_account(interaction, accounts, email, label):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    if email in accounts:
        del accounts[email]
        await interaction.response.send_message(f"Đã xóa tài khoản {label}: `{email}`", ephemeral=True)
    else:
        await interaction.response.send_message(f"Tài khoản `{email}` không tồn tại.", ephemeral=True)

@tree.command(name="delmail")
async def delmail(interaction: discord.Interaction, email: str):
    await delete_account(interaction, accounts_mail, email, "Email")

@tree.command(name="delug")
async def delug(interaction: discord.Interaction, email: str):
    await delete_account(interaction, accounts_ug, email, "UGPhone")

@tree.command(name="delred")
async def delred(interaction: discord.Interaction, email: str):
    await delete_account(interaction, accounts_red, email, "RedFonger")

@tree.command(name="deldl")
async def deldl(interaction: discord.Interaction, email: str):
    await delete_account(interaction, accounts_ld, email, "LD Cloud")

# Admin: Quản lý admin
@tree.command(name="addadmin", description="(Admin) Thêm người vào danh sách admin")
async def addadmin(interaction: discord.Interaction, user_id: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    admin_ids.add(user_id)
    try:
        user = await bot.fetch_user(user_id)
        await interaction.response.send_message(f"Đã thêm admin: {user.name} ({user_id})")
    except:
        await interaction.response.send_message(f"Đã thêm admin (ID: `{user_id}`) - Không lấy được tên")

@tree.command(name="removeadmin", description="(Admin) Xoá người khỏi danh sách admin")
async def removeadmin(interaction: discord.Interaction, user_id: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    admin_ids.discard(user_id)
    await interaction.response.send_message(f"Đã xóa admin: `{user_id}`")

@tree.command(name="listadmin", description="(Admin) Xem danh sách admin")
async def listadmin(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return

    result = []
    for uid in admin_ids:
        try:
            user = await bot.fetch_user(uid)
            result.append(f"{user.name} ({uid})")
        except:
            result.append(f"Không lấy được tên ({uid})")
    
    msg = "\n".join(result)
    await interaction.response.send_message(f"Danh sách admin:\n```{msg}```", ephemeral=True)

# Chạy bot
bot.run(os.environ["DISCORD_TOKEN"])

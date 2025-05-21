import discord
from discord import app_commands
from discord.ext import commands
import requests
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

owner_id = 1364169704943652924
admin_ids = {owner_id}
BASE_URL = "https://txziczacroblox.site"

def is_admin(user):
    return user.id in admin_ids

# Get account using key (1-time use)
async def get_account(interaction, key, label):
    try:
        res = requests.post(f"{BASE_URL}/{label}.php", data={"key": key})
        if "Lỗi" in res.text:
            await interaction.response.send_message(res.text, ephemeral=True)
        else:
            await interaction.response.send_message(f"{label}:\n{res.text}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

@tree.command(name="mail")
@app_commands.describe(key="Key nhận tài khoản")
async def mail(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "mail")

@tree.command(name="ugphone")
@app_commands.describe(key="Key nhận tài khoản")
async def ugphone(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "ug")

@tree.command(name="redfinger")
@app_commands.describe(key="Key nhận tài khoản")
async def redfinger(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "red")

@tree.command(name="ldcloud")
@app_commands.describe(key="Key nhận tài khoản")
async def ldcloud(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "ld")

# Upload account
async def upload_account(interaction, label, email, password):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    try:
        res = requests.post(f"{BASE_URL}/{label}.php", data={"email": email, "password": password})
        await interaction.response.send_message(res.text, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

@tree.command(name="upmail")
@app_commands.describe(email="Email", password="Password")
async def upmail(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, "mail", email, password)

@tree.command(name="upugphone")
@app_commands.describe(email="Email", password="Password")
async def upug(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, "ug", email, password)

@tree.command(name="upredfinger")
@app_commands.describe(email="Email", password="Password")
async def upred(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, "red", email, password)

@tree.command(name="upldcloud")
@app_commands.describe(email="Email", password="Password")
async def upld(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, "ld", email, password)

# Delete account
async def delete_account(interaction, label, email):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    try:
        res = requests.get(f"{BASE_URL}/del{label}.php?email={email}")
        await interaction.response.send_message(res.text, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

@tree.command(name="delmail")
@app_commands.describe(email="Email cần xoá")
async def delmail(interaction: discord.Interaction, email: str):
    await delete_account(interaction, "mail", email)

@tree.command(name="delugphone")
@app_commands.describe(email="Email cần xoá")
async def delug(interaction: discord.Interaction, email: str):
    await delete_account(interaction, "ug", email)

@tree.command(name="delredfinger")
@app_commands.describe(email="Email cần xoá")
async def delred(interaction: discord.Interaction, email: str):
    await delete_account(interaction, "red", email)

@tree.command(name="delldcloud")
@app_commands.describe(email="Email cần xoá")
async def delld(interaction: discord.Interaction, email: str):
    await delete_account(interaction, "ld", email)

# List account (Admin only)
async def list_accounts(interaction, label):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    try:
        res = requests.get(f"{BASE_URL}/{label}.json")
        accounts = res.json()
        if not accounts:
            await interaction.response.send_message(f"Danh sách {label} trống.", ephemeral=True)
        else:
            msg = "\n".join([f"{k}:{v}" for k,v in accounts.items()])
            await interaction.response.send_message(f"Danh sách {label}:\n```{msg}```", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

@tree.command(name="listmail")
async def listmail(interaction: discord.Interaction):
    await list_accounts(interaction, "mail")

@tree.command(name="listugphone")
async def listug(interaction: discord.Interaction):
    await list_accounts(interaction, "ug")

@tree.command(name="listredfinger")
async def listred(interaction: discord.Interaction):
    await list_accounts(interaction, "red")

@tree.command(name="listldcloud")
async def listld(interaction: discord.Interaction):
    await list_accounts(interaction, "ld")

# GETKEY - Tạo link rút gọn từ YeuMoney
@tree.command(name="getkey")
async def getkey(interaction: discord.Interaction):
    try:
        link_goc = "https://web-can-rut-gon.com"
        token = "dfce079aa89e7256f53f6f2fe2328c128a584467f5afcbc5f5d451c581879768"
        api_url = f"https://yeumoney.com/QL_api.php?token={token}&url={requests.utils.quote(link_goc)}&format=json"
        res = requests.get(api_url).json()
        if res["status"] == "success":
            await interaction.response.send_message(f"Link nhận key: {res['shortenedUrl']}", ephemeral=True)
        else:
            await interaction.response.send_message("Không tạo được link.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

# ADMIN: Thêm admin (chỉ owner)
@tree.command(name="addowner")
@app_commands.describe(user="Người cần cấp quyền admin")
async def addowner(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != owner_id:
        await interaction.response.send_message("Chỉ owner mới có quyền.", ephemeral=True)
        return
    admin_ids.add(user.id)
    await interaction.response.send_message(f"Đã thêm {user.mention} làm admin.", ephemeral=True)

# ADMIN: Xoá admin (chỉ owner)
@tree.command(name="delowner")
@app_commands.describe(user="Người cần xoá quyền admin")
async def delowner(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != owner_id:
        await interaction.response.send_message("Chỉ owner mới có quyền.", ephemeral=True)
        return
    if user.id == owner_id:
        await interaction.response.send_message("Không thể xoá owner.", ephemeral=True)
        return
    admin_ids.discard(user.id)
    await interaction.response.send_message(f"Đã xoá {user.mention} khỏi admin.", ephemeral=True)

# Giới thiệu bot
@tree.command(name="info")
async def info(interaction: discord.Interaction):
    await interaction.response.send_message("Bot phân phối tài khoản | Dùng key 1 lần | Hỗ trợ: mail, ugphone, redfinger, ldcloud", ephemeral=True)

# Bot ready
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot sẵn sàng: {bot.user}")

# Chạy bot
bot.run(os.environ["DISCORD_TOKEN"])

import discord
from discord import app_commands
from discord.ext import commands
import requests
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Admin IDs
admin_ids = {1364169704943652924}
owner_id = 1364169704943652924  # Admin chính
BASE_URL = "https://txziczacroblox.site"

def is_admin(user):
    return user.id in admin_ids

# Nhận tài khoản
async def get_account(interaction, key, label):
    try:
        res = requests.get(f"{BASE_URL}/{label}.json")
        accounts = res.json()
        if not accounts:
            await interaction.response.send_message(f"Hết tài khoản {label}.")
            return
        email, password = next(iter(accounts.items()))
        await interaction.response.send_message(f"{label}:\nEmail: `{email}`\nPassword: `{password}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}")

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

# Upload tài khoản (admin-only)
async def upload_account(interaction, label, email, password):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.")
        return
    try:
        res = requests.post(f"{BASE_URL}/{label}.php", data={"email": email, "password": password})
        await interaction.response.send_message(f"{res.text}")
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}")

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

# Xoá tài khoản (admin-only)
async def delete_account(interaction, label, email):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.")
        return
    try:
        res = requests.get(f"{BASE_URL}/del{label}.php?email={email}")
        await interaction.response.send_message(f"{res.text}")
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}")

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

# List tài khoản (admin-only)
async def list_accounts(interaction, label):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    try:
        res = requests.get(f"{BASE_URL}/{label}.json")
        accounts = res.json()
        if not accounts:
            await interaction.response.send_message(f"Không có tài khoản {label}.", ephemeral=True)
            return
        msg = "\n".join([f"`{k}` | `{v}`" for k, v in accounts.items()])
        await interaction.response.send_message(f"**Danh sách {label}:**\n{msg}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}", ephemeral=True)

@tree.command(name="listmail")
async def listmail(interaction: discord.Interaction):
    await list_accounts(interaction, "mail")

@tree.command(name="listugphone")
async def listugphone(interaction: discord.Interaction):
    await list_accounts(interaction, "ug")

@tree.command(name="listldcloud")
async def listldcloud(interaction: discord.Interaction):
    await list_accounts(interaction, "ld")

@tree.command(name="listredfinger")
async def listredfinger(interaction: discord.Interaction):
    await list_accounts(interaction, "red")

# Quản lý admin
@tree.command(name="setowner")
@app_commands.describe(id="ID người cần thêm làm admin")
async def setowner(interaction: discord.Interaction, id: int):
    if interaction.user.id != owner_id:
        await interaction.response.send_message("Chỉ admin chính mới được thêm admin.")
        return
    admin_ids.add(id)
    await interaction.response.send_message(f"Đã thêm ID `{id}` vào admin.")

@tree.command(name="delowner")
@app_commands.describe(id="ID admin cần xoá")
async def delowner(interaction: discord.Interaction, id: int):
    if interaction.user.id != owner_id:
        await interaction.response.send_message("Chỉ admin chính mới được xoá admin.")
        return
    if id == owner_id:
        await interaction.response.send_message("Không thể xoá admin chính.")
        return
    if id in admin_ids:
        admin_ids.remove(id)
        await interaction.response.send_message(f"Đã xoá ID `{id}` khỏi admin.")
    else:
        await interaction.response.send_message("ID này không phải admin.")

# Giới thiệu bot
@tree.command(name="info")
async def info(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Bot phân phối tài khoản**\n"
        "- Dùng `/mail`, `/ugphone`, `/ldcloud`, `/redfinger` để nhận tài khoản (có key).\n"
        "- Admin có thể `/up...`, `/list...`, `/del...`\n"
        "- Admin chính dùng `/setowner`, `/delowner` để quản lý admin.",
        ephemeral=True
    )

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot sẵn sàng: {bot.user}")

bot.run(os.environ["DISCORD_TOKEN"])

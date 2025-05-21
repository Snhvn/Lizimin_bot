import discord
from discord import app_commands
import requests

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

MAIL_URL = "https://txziczacroblox.site/mail.json"
MAIL_PHP_URL = "https://txziczacroblox.site/mail.php"
SAVE_MAIL_URL = "https://txziczacroblox.site/save_mail.php"
KEYS_URL = "https://txziczacroblox.site/keys.json"
SAVE_KEYS_URL = "https://txziczacroblox.site/save_keys.php"

ADMIN_IDS = [1364169704943652924]  # Thay bằng user ID của bạn

@client.event
async def on_ready():
    await tree.sync()
    print(f"Bot is ready as {client.user}")

@tree.command(name="info", description="Giới thiệu bot và các lệnh hiện có")
async def info(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Bot Tài Khoản**\n"
        "- `/info`: Giới thiệu bot\n"
        "- `/mail <key>`: Nhận tài khoản mail (1 lần)\n"
        "- `/upmail <email:pass>`: Thêm tài khoản (chỉ admin)\n"
        "- `/delmail <email:pass>`: Xóa tài khoản (chỉ admin)"
    )

@tree.command(name="mail", description="Lấy tài khoản từ key")
@app_commands.describe(key="Nhập key được cấp")
async def mail(interaction: discord.Interaction, key: str):
    try:
        keys = requests.get(KEYS_URL).json()
        if key not in keys or not keys[key]:
            await interaction.response.send_message("Key không hợp lệ hoặc đã dùng.")
            return
        keys[key] = False
        requests.post(SAVE_KEYS_URL, json=keys)
        mails = requests.get(MAIL_URL).json()
        if not mails:
            await interaction.response.send_message("Không còn tài khoản.")
            return
        account = mails.pop(0)
        requests.post(SAVE_MAIL_URL, json=mails)
        await interaction.response.send_message(f"Tài khoản của bạn: `{account}`")
    except:
        await interaction.response.send_message("Lỗi khi xử lý yêu cầu.")

@tree.command(name="upmail", description="Upload tài khoản mail (chỉ admin)")
@app_commands.describe(account="Tài khoản định dạng email:pass")
async def upmail(interaction: discord.Interaction, account: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    try:
        res = requests.post(MAIL_PHP_URL, data={"account": account})
        if res.status_code == 200:
            await interaction.response.send_message("Tài khoản đã được upload.")
        else:
            await interaction.response.send_message("Upload thất bại.")
    except:
        await interaction.response.send_message("Lỗi kết nối máy chủ.")

@tree.command(name="delmail", description="Xóa tài khoản mail (chỉ admin)")
@app_commands.describe(account="Tài khoản email:pass cần xóa")
async def delmail(interaction: discord.Interaction, account: str):
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message("Bạn không có quyền.", ephemeral=True)
        return
    try:
        mails = requests.get(MAIL_URL).json()
        if account not in mails:
            await interaction.response.send_message("Tài khoản không tồn tại.")
            return
        mails.remove(account)
        requests.post(SAVE_MAIL_URL, json=mails)
        await interaction.response.send_message(f"Đã xóa: `{account}`")
    except:
        await interaction.response.send_message("Lỗi khi xử lý.")

# Chạy bot với token từ biến môi trường
import os
client.run(os.environ["DISCORD_TOKEN"])

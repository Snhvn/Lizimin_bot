import discord
from discord import app_commands, Embed, Colour
from discord.ext import commands
import requests
import time
import os
import json
from flask import Flask
from threading import Thread

# === UPTIME SERVER (Flask) ===
app = Flask('')

@app.route('/')
def home():
    return "Bot đang chạy!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# === DISCORD BOT SETUP ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

API_TOKEN = 'dfce079aa89e7256f53f6f2fe2328c128a584467f5afcbc5f5d451c581879768'
LINK_ORIGINAL = 'https://danvnstore.site/callback.php'
admin_ids = {1364169704943652924}
used_keys = set()

# === ACCOUNT DATA ===
def load_accounts(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_accounts(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

accounts = {
    "mail": load_accounts("mail_accounts.json"),
    "ug": load_accounts("ug_accounts.json"),
    "red": load_accounts("red_accounts.json"),
    "ld": load_accounts("ld_accounts.json")
}

# === UTILITIES ===
def is_admin(user):
    return user.id in admin_ids

async def check_key_valid(interaction, key):
    try:
        res = requests.get("https://danvnstore.site/keys.json", timeout=5)
        key_data = res.json()
    except Exception as e:
        await interaction.response.send_message(f"Lỗi kiểm tra key: {e}")
        return False

    if key not in key_data:
        await interaction.response.send_message(f"Key `{key}` không hợp lệ.")
        return False
    if key in used_keys:
        await interaction.response.send_message(f"Key `{key}` đã được sử dụng.")
        return False
    return True

async def get_account(interaction, key, acc_type, label):
    if not await check_key_valid(interaction, key):
        return
    accs = accounts[acc_type]
    if not accs:
        await interaction.response.send_message(f"Hết tài khoản {label}.")
        return
    email, password = accs.popitem()
    used_keys.add(key)
    save_accounts(f"{acc_type}_accounts.json", accs)
    await interaction.response.send_message(f"**Tài khoản {label}**\nEmail: `{email}`\nPassword: `{password}`", ephemeral=True)

# === BOT EVENTS ===
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot đã đăng nhập: {bot.user}")

# === USER COMMANDS ===
@tree.command(name="info", description="Xem lệnh bot")
async def info(interaction: discord.Interaction):
    desc = (
        "/mail /ug /red /ld - Nhận tài khoản\n"
        "/getkey - Lấy link nhận key\n\n"
        "**Lệnh admin:**\n"
        "/upmail /upug /upred /upld\n"
        "/listmail /listug /listred /listld\n"
        "/delmail /delug /delred /deldl\n"
        "/addadmin /removeadmin /listadmin"
    )
    embed = Embed(title="Lệnh Bot", description=desc, color=Colour.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="getkey", description="Tạo link rút gọn nhận key")
async def getkey(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    try:
        link = f"{LINK_ORIGINAL}?uid={user_id}&t={int(time.time())}"
        encoded = requests.utils.quote(link, safe='')
        api_url = f"https://yeumoney.com/QL_api.php?token={API_TOKEN}&url={encoded}&format=json"
        res = requests.get(api_url, timeout=5)
        data = res.json()
        if data.get("status") == "success":
            await interaction.response.send_message(f"Link nhận key: {data['shortenedUrl']}")
        else:
            await interaction.response.send_message(f"Lỗi API: {data.get('status')}")
    except Exception as e:
        await interaction.response.send_message(f"Lỗi: {e}")

@tree.command(name="mail")
@app_commands.describe(key="Key hợp lệ")
async def mail(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "mail", "Email")

@tree.command(name="ug")
@app_commands.describe(key="Key hợp lệ")
async def ug(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "ug", "UGPhone")

@tree.command(name="red")
@app_commands.describe(key="Key hợp lệ")
async def red(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "red", "RedFonger")

@tree.command(name="ld")
@app_commands.describe(key="Key hợp lệ")
async def ld(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, "ld", "LD Cloud")

# === ADMIN COMMANDS ===
async def upload_account(interaction, acc_type, email, password, label):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Không có quyền.", ephemeral=True)
        return
    accs = accounts[acc_type]
    accs[email] = password
    save_accounts(f"{acc_type}_accounts.json", accs)
    await interaction.response.send_message(f"Đã thêm {label}: `{email}`")

@tree.command(name="upmail") async def upmail(i, email: str, password: str): await upload_account(i, "mail", email, password, "Email")
@tree.command(name="upug") async def upug(i, email: str, password: str): await upload_account(i, "ug", email, password, "UGPhone")
@tree.command(name="upred") async def upred(i, email: str, password: str): await upload_account(i, "red", email, password, "RedFonger")
@tree.command(name="upld") async def upld(i, email: str, password: str): await upload_account(i, "ld", email, password, "LD Cloud")

async def list_accounts(interaction, acc_type, label):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Không có quyền.", ephemeral=True)
        return
    accs = accounts[acc_type]
    if not accs:
        await interaction.response.send_message(f"Không còn {label}.", ephemeral=True)
    else:
        msg = "\n".join([f"{e}: {p}" for e, p in accs.items()])
        await interaction.response.send_message(f"{label}:\n```{msg}```", ephemeral=True)

@tree.command(name="listmail") async def listmail(i): await list_accounts(i, "mail", "Email")
@tree.command(name="listug") async def listug(i): await list_accounts(i, "ug", "UGPhone")
@tree.command(name="listred") async def listred(i): await list_accounts(i, "red", "RedFonger")
@tree.command(name="listld") async def listld(i): await list_accounts(i, "ld", "LD Cloud")

async def delete_account(interaction, acc_type, email, label):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Không có quyền.", ephemeral=True)
        return
    accs = accounts[acc_type]
    if email in accs:
        del accs[email]
        save_accounts(f"{acc_type}_accounts.json", accs)
        await interaction.response.send_message(f"Đã xóa {label}: `{email}`", ephemeral=True)
    else:
        await interaction.response.send_message(f"Tài khoản `{email}` không tồn tại.", ephemeral=True)

@tree.command(name="delmail") async def delmail(i, email: str): await delete_account(i, "mail", email, "Email")
@tree.command(name="delug") async def delug(i, email: str): await delete_account(i, "ug", email, "UGPhone")
@tree.command(name="delred") async def delred(i, email: str): await delete_account(i, "red", email, "RedFonger")
@tree.command(name="deldl") async def deldl(i, email: str): await delete_account(i, "ld", email, "LD Cloud")

# === ADMIN LIST ===
@tree.command(name="addadmin")
async def addadmin(i, user_id: int):
    if not is_admin(i.user): await i.response.send_message("Không có quyền.", ephemeral=True); return
    admin_ids.add(user_id)
    await i.response.send_message(f"Đã thêm admin: `{user_id}`")

@tree.command(name="removeadmin")
async def removeadmin(i, user_id: int):
    if not is_admin(i.user): await i.response.send_message("Không có quyền.", ephemeral=True); return
    if user_id == 1364169704943652924:
        await i.response.send_message("Không thể xóa admin gốc.", ephemeral=True)
        return
    admin_ids.discard(user_id)
    await i.response.send_message(f"Đã xóa admin: `{user_id}`")

@tree.command(name="listadmin")
async def listadmin(i):
    if not is_admin(i.user): await i.response.send_message("Không có quyền.", ephemeral=True); return
    ids = "\n".join([str(uid) for uid in admin_ids])
    await i.response.send_message(f"Admin hiện tại:\n```{ids}```", ephemeral=True)

# === RUN BOT ===
bot.run(os.environ["DISCORD_TOKEN"])

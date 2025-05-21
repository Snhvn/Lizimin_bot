import discord
from discord import app_commands
from discord.ext import commands
from discord import Embed, Colour
import requests
import time
import os
import json
import threading
from flask import Flask

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
# Web server đơn giản để giữ bot hoạt động
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

# Chạy web server trong thread riêng
threading.Thread(target=run_web).start()

API_TOKEN = 'dfce079aa89e7256f53f6f2fe2328c128a584467f5afcbc5f5d451c581879768'
LINK_ORIGINAL = 'http://txziczacroblox.site/callback.php'

# Định nghĩa các URL API trên hosting của bạn
HOSTING_BASE_URL = 'http://txziczacroblox.site/' # Thay bằng base URL hosting của bạn

# URLs cho Mail accounts
READ_MAIL_URL = HOSTING_BASE_URL + 'read_mail.php'
WRITE_MAIL_URL = HOSTING_BASE_URL + 'write_mail.php'
# URLs cho UG accounts
READ_UG_URL = HOSTING_BASE_URL + 'read_ug.php'
WRITE_UG_URL = HOSTING_BASE_URL + 'write_ug.php'
# URLs cho Red accounts
READ_RED_URL = HOSTING_BASE_URL + 'read_red.php'
WRITE_RED_URL = HOSTING_BASE_URL + 'write_red.php'
# URLs cho LD accounts
READ_LD_URL = HOSTING_BASE_URL + 'read_ld.php'
WRITE_LD_URL = HOSTING_BASE_URL + 'write_ld.php'
# URLs cho Admin IDs
READ_ADMINS_URL = HOSTING_BASE_URL + 'read_admins.php'
WRITE_ADMINS_URL = HOSTING_BASE_URL + 'write_admins.php'
# URLs cho Used Keys
READ_USED_KEYS_URL = HOSTING_BASE_URL + 'read_used_keys.php'
WRITE_USED_KEYS_URL = HOSTING_BASE_URL + 'write_used_keys.php'


def load_accounts(read_url):
    """Tải tài khoản từ URL API."""
    try:
        response = requests.get(read_url, timeout=5)
        response.raise_for_status() # Ném lỗi cho các mã trạng thái HTTP xấu (4xx, 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi tải tài khoản từ {read_url}: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Lỗi giải mã JSON từ {read_url}: {e}")
        return {}

def save_accounts(write_url, accounts):
    """Lưu tài khoản vào URL API."""
    try:
        response = requests.post(write_url, json=accounts, timeout=5)
        response.raise_for_status()
        result = response.json()
        if result.get('status') != 'success':
            print(f"Lỗi khi lưu tài khoản vào {write_url}: {result.get('message', 'Lỗi không xác định')}")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi lưu tài khoản vào {write_url}: {e}")

def load_ids(read_url):
    """Tải ID (admins, used_keys) từ URL API."""
    try:
        response = requests.get(read_url, timeout=5)
        response.raise_for_status()
        return set(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi tải ID từ {read_url}: {e}")
        return set()
    except json.JSONDecodeError as e:
        print(f"Lỗi giải mã JSON từ {read_url}: {e}")
        return set()

def save_ids(write_url, ids):
    """Lưu ID (admins, used_keys) vào URL API."""
    try:
        response = requests.post(write_url, json=list(ids), timeout=5)
        response.raise_for_status()
        result = response.json()
        if result.get('status') != 'success':
            print(f"Lỗi khi lưu ID vào {write_url}: {result.get('message', 'Lỗi không xác định')}")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi lưu ID vào {write_url}: {e}")

# Khởi tạo dữ liệu từ các URL API trên hosting
accounts_mail = load_accounts(READ_MAIL_URL)
accounts_ug = load_accounts(READ_UG_URL)
accounts_red = load_accounts(READ_RED_URL)
accounts_ld = load_accounts(READ_LD_URL)
admin_ids = load_ids(READ_ADMINS_URL)
used_keys = load_ids(READ_USED_KEYS_URL)

# Đảm bảo admin chính luôn có trong danh sách và lưu lại nếu cần
if 1364169704943652924 not in admin_ids:
    admin_ids.add(1364169704943652924)
    save_ids(WRITE_ADMINS_URL, admin_ids)


def is_admin(user):
    return user.id in admin_ids

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot đã đăng nhập: {bot.user}")


## Lệnh Thông tin

@tree.command(name="info", description="Giới thiệu các lệnh bot")
async def info(interaction: discord.Interaction):
    is_admin_user = interaction.user.id in admin_ids

    description = (
        "``/mail <key> - Lấy tài khoản Email``\n"
        "``/ug <key> - Lấy tài khoản UGPhone``\n"
        "``/red <key> - Lấy tài khoản RedFonger``\n"
        "``/ld <key> - Lấy tài khoản LD Cloud``\n"
    )
    if is_admin_user:
        description += (
            "``/upmail <email> <password> - (Admin) Thêm tài khoản Email``\n"
            "``/upug <email> <password> - (Admin) Thêm tài khoản UGPhone``\n"
            "``/upred <email> <password> - (Admin) Thêm tài khoản RedFonger``\n"
            "``/upld <email> <password> - (Admin) Thêm tài khoản LD Cloud``\n"
            "``/listmail - (Admin) Xem danh sách tài khoản Email còn lại``\n"
            "``/listug - (Admin) Xem danh sách tài khoản UGPhone còn lại``\n"
            "``/listred - (Admin) Xem danh sách tài khoản RedFonger còn lại``\n"
            "``/listld - (Admin) Xem danh sách tài khoản LD Cloud còn lại``\n"
            "``/delmail <email> - (Admin) Xóa tài khoản Email``\n"
            "``/delug <email> - (Admin) Xóa tài khoản UGPhone``\n"
            "``/delred <email> - (Admin) Xóa tài khoản RedFonger``\n"
            "``/deldl <email> - (Admin) Xóa tài khoản LD Cloud``\n"
            "``/addadmin <user_id> - (Admin) Thêm admin mới``\n"
            "``/removeadmin <user_id> - (Admin) Gỡ admin``\n"
            "``/listadmin - (Admin) Danh sách admin``"
        )

    embed = Embed(
        title="Các lệnh bot",
        description=description,
        color=Colour(0xAA00FF)
    )
    embed.set_image(url="https://i.imgur.com/WFeKMG6.gif")

    await interaction.response.send_message(embed=embed, ephemeral=True)


## Lấy Link Key Rút Gọn

@tree.command(name="getkey", description="Lấy link key rút gọn.")
async def getkey(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    try:
        unique_link = f"{LINK_ORIGINAL}?uid={user_id}&t={int(time.time())}"
        encoded_link = requests.utils.quote(unique_link, safe='')
        api_url = f"https://yeumoney.com/QL_api.php?token={API_TOKEN}&url={encoded_link}&format=json"
        res = requests.get(api_url, timeout=5)
        data = res.json()

        if data.get("status") == "success":
            short_url = data["shortenedUrl"]
            await interaction.response.send_message(
                f"**Link key rút gọn:** {short_url}"
            )
        else:
            await interaction.response.send_message(f"**Lỗi API:** {data.get('status')}")
    except Exception as e:
        await interaction.response.send_message(f"**Lỗi hệ thống:** {e}")


## Kiểm Tra Key Hợp Lệ

async def check_key_valid(interaction, key):
    try:
        # Đây là URL cho keys.json, giả định vẫn nằm trên hosting và có thể truy cập
        res = requests.get("http://txziczacroblox.site/keys.json", timeout=5)
        res.raise_for_status() # Ném lỗi nếu có vấn đề về HTTP
        key_data = res.json()
    except requests.exceptions.RequestException as e:
        await interaction.response.send_message(f"**Lỗi khi kiểm tra key từ hosting:** {e}", ephemeral=True)
        return False
    except json.JSONDecodeError as e:
        await interaction.response.send_message(f"**Lỗi giải mã JSON từ keys.json:** {e}", ephemeral=True)
        return False

    if key not in key_data:
        await interaction.response.send_message(f"**Key `{key}` không hợp lệ hoặc không tồn tại.**")
        return False

    if key in used_keys:
        await interaction.response.send_message(f"**Key `{key}` đã được sử dụng để lấy tài khoản.**")
        return False

    return True


## Lấy Tài Khoản (Người dùng)

async def get_account(interaction, key, accounts_dict, account_type, write_url):
    if not await check_key_valid(interaction, key):
        return

    if not accounts_dict:
        await interaction.response.send_message(f"**Không còn tài khoản {account_type} để cấp.**")
        return

    try:
        # Lấy một item ngẫu nhiên và xóa nó
        email, password = accounts_dict.popitem()
        used_keys.add(key)
        save_ids(WRITE_USED_KEYS_URL, used_keys) # Lưu key đã sử dụng
        save_accounts(write_url, accounts_dict) # Lưu lại danh sách tài khoản sau khi cấp

        await interaction.response.send_message(
            f"**Tài khoản cho key `{key}`:**\nEmail: `{email}`\nMật khẩu: `{password}`",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.response.send_message(f"**Lỗi khi cấp tài khoản {account_type}:** {e}", ephemeral=True)


@tree.command(name="mail", description="Nhận tài khoản (email/mật khẩu) bằng key duy nhất.")
@app_commands.describe(key="Key dùng để nhận tài khoản")
async def mail(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_mail, "Email", WRITE_MAIL_URL)

@tree.command(name="ug", description="Nhận tài khoản UGPhone bằng key duy nhất.")
@app_commands.describe(key="Key dùng để nhận tài khoản")
async def ug(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_ug, "UGPhone", WRITE_UG_URL)

@tree.command(name="red", description="Nhận tài khoản RedFonger Cloud bằng key duy nhất.")
@app_commands.describe(key="Key dùng để nhận tài khoản")
async def red(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_red, "RedFonger", WRITE_RED_URL)

@tree.command(name="ld", description="Nhận tài khoản LD Cloud bằng key duy nhất.")
@app_commands.describe(key="Key dùng để nhận tài khoản")
async def ld(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_ld, "LD Cloud", WRITE_LD_URL)


## Upload Tài Khoản (Admin)

async def upload_account(interaction, email, password, accounts_dict, account_type, write_url):
    if not is_admin(interaction.user):
        await interaction.response.send_message("**Bạn không có quyền dùng lệnh này.**", ephemeral=True)
        return

    if email in accounts_dict:
        await interaction.response.send_message(f"**Email `{email}` đã tồn tại trong {account_type}.**", ephemeral=True)
        return

    accounts_dict[email] = password
    save_accounts(write_url, accounts_dict) # Lưu lại sau khi thêm
    await interaction.response.send_message(f"**Đã thêm tài khoản {account_type}:**\nEmail: `{email}`\nMật khẩu: `{password}`", ephemeral=True)

@tree.command(name="upmail", description="(Admin) Thêm tài khoản Email mới.")
@app_commands.describe(email="Email tài khoản", password="Mật khẩu")
async def upmail(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, email, password, accounts_mail, "Email", WRITE_MAIL_URL)

@tree.command(name="upug", description="(Admin) Thêm tài khoản UGPhone mới.")
@app_commands.describe(email="Email tài khoản", password="Mật khẩu")
async def upug(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, email, password, accounts_ug, "UGPhone", WRITE_UG_URL)

@tree.command(name="upred", description="(Admin) Thêm tài khoản RedFonger mới.")
@app_commands.describe(email="Email tài khoản", password="Mật khẩu")
async def upred(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, email, password, accounts_red, "RedFonger", WRITE_RED_URL)

@tree.command(name="upld", description="(Admin) Thêm tài khoản LD Cloud mới.")
@app_commands.describe(email="Email tài khoản", password="Mật khẩu")
async def upld(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, email, password, accounts_ld, "LD Cloud", WRITE_LD_URL)


## List Tài Khoản (Admin)

async def list_accounts(interaction, accounts_dict, account_type):
    if not is_admin(interaction.user):
        await interaction.response.send_message("**Bạn không có quyền sử dụng lệnh này.**", ephemeral=True)
        return

    if not accounts_dict:
        await interaction.response.send_message(f"**Không còn tài khoản {account_type} nào.**", ephemeral=True)
        return

    message = f"**Danh sách tài khoản {account_type} còn lại:**\n"
    for email in accounts_dict:
        message += f"- `{email}`\n"
    await interaction.response.send_message(message, ephemeral=True)

@tree.command(name="listmail", description="(Admin) Xem danh sách tài khoản Email còn lại.")
async def listmail(interaction: discord.Interaction):
    await list_accounts(interaction, accounts_mail, "Email")

@tree.command(name="listug", description="(Admin) Xem danh sách tài khoản UGPhone còn lại.")
async def listug(interaction: discord.Interaction):
    await list_accounts(interaction, accounts_ug, "UGPhone")

@tree.command(name="listred", description="(Admin) Xem danh sách tài khoản RedFonger còn lại.")
async def listred(interaction: discord.Interaction):
    await list_accounts(interaction, accounts_red, "RedFonger")

@tree.command(name="listld", description="(Admin) Xem danh sách tài khoản LD Cloud còn lại.")
async def listld(interaction: discord.Interaction):
    await list_accounts(interaction, accounts_ld, "LD Cloud")


## Xóa Tài Khoản (Admin)

async def delete_account(interaction, email, accounts_dict, account_type, write_url):
    if not is_admin(interaction.user):
        await interaction.response.send_message("**Bạn không có quyền dùng lệnh này.**", ephemeral=True)
        return

    if email not in accounts_dict:
        await interaction.response.send_message(f"**Email `{email}` không tồn tại trong {account_type}.**", ephemeral=True)
        return

    del accounts_dict[email]
    save_accounts(write_url, accounts_dict) # Lưu lại sau khi xóa
    await interaction.response.send_message(f"**Đã xóa tài khoản {account_type} với email `{email}`.**", ephemeral=True)

@tree.command(name="delmail", description="(Admin) Xóa tài khoản Email.")
@app_commands.describe(email="Email tài khoản cần xóa")
async def delmail(interaction: discord.Interaction, email: str):
    await delete_account(interaction, email, accounts_mail, "Email", WRITE_MAIL_URL)

@tree.command(name="delug", description="(Admin) Xóa tài khoản UGPhone.")
@app_commands.describe(email="Email tài khoản cần xóa")
async def delug(interaction: discord.Interaction, email: str):
    await delete_account(interaction, email, accounts_ug, "UGPhone", WRITE_UG_URL)

@tree.command(name="delred", description="(Admin) Xóa tài khoản RedFonger.")
@app_commands.describe(email="Email tài khoản cần xóa")
async def delred(interaction: discord.Interaction, email: str):
    await delete_account(interaction, email, accounts_red, "RedFonger", WRITE_RED_URL)

@tree.command(name="deldl", description="(Admin) Xóa tài khoản LD Cloud.")
@app_commands.describe(email="Email tài khoản cần xóa")
async def deldl(interaction: discord.Interaction, email: str):
    await delete_account(interaction, email, accounts_ld, "LD Cloud", WRITE_LD_URL)


## Quản Lý Admin

@tree.command(name="addadmin", description="Thêm admin mới.")
async def addadmin(interaction: discord.Interaction, user_id: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("**Bạn không có quyền thực hiện thao tác này.**", ephemeral=True)
        return
    if user_id in admin_ids:
        await interaction.response.send_message("**Người này đã là admin rồi.**", ephemeral=True)
        return

    admin_ids.add(user_id)
    save_ids(WRITE_ADMINS_URL, admin_ids)
    await interaction.response.send_message(f"**Đã thêm admin với ID `{user_id}`.**", ephemeral=True)

@tree.command(name="removeadmin", description="Gỡ admin.")
async def removeadmin(interaction: discord.Interaction, user_id: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("**Bạn không có quyền thực hiện thao tác này.**", ephemeral=True)
        return
    if user_id == 1364169704943652924: # ID admin chính (bảo vệ)
        await interaction.response.send_message("**Không thể gỡ admin chính.**", ephemeral=True)
        return
    if user_id == interaction.user.id:
        await interaction.response.send_message("**Bạn không thể tự gỡ chính mình.**", ephemeral=True)
        return
    if user_id in admin_ids:
        admin_ids.remove(user_id)
        save_ids(WRITE_ADMINS_URL, admin_ids)
        await interaction.response.send_message(f"**Đã gỡ admin với ID `{user_id}`.**", ephemeral=True)
    else:
        await interaction.response.send_message("**ID này không phải là admin.**", ephemeral=True)

@tree.command(name="listadmin", description="Danh sách admin hiện tại.")
async def listadmin(interaction: discord.Interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("**Bạn không có quyền sử dụng lệnh này.**", ephemeral=True)
        return
    admins_list = "\n".join(f"- `{admin_id}`" for admin_id in admin_ids)
    await interaction.response.send_message(f"**Danh sách admin:**\n{admins_list}", ephemeral=True)


bot.run(os.environ["DISCORD_TOKEN"])

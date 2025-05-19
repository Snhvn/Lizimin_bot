import discord
from discord import app_commands
from discord.ext import commands
from discord import Embed, Colour
import requests
import time

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

API_TOKEN = 'dfce079aa89e7256f53f6f2fe2328c128a584467f5afcbc5f5d451c581879768'
LINK_ORIGINAL = 'https://danvnstore.site/callback.php'

# Danh sách admin khởi tạo với admin chính được bảo vệ
admin_ids = {1364169704943652924}

used_keys = set()

# Các dict lưu tài khoản từng loại
accounts_mail = {
    "user1@example.com": "pass1",
    "user2@example.com": "pass2",
}
accounts_ug = {
    "ug1@example.com": "ugpass1",
    "ug2@example.com": "ugpass2",
}
accounts_red = {
    "red1@example.com": "redpass1",
    "red2@example.com": "redpass2",
}
accounts_ld = {
    "ld1@example.com": "ldpass1",
    "ld2@example.com": "ldpass2",
}

def is_admin(user):
    return user.id in admin_ids

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot đã đăng nhập: {bot.user}")

# ====================== Lệnh thông tin ===========================
@tree.command(name="info", description="Giới thiệu các lệnh bot")
async def info(interaction: discord.Interaction):
    is_admin = interaction.user.id in admin_ids

    description = (
        "``/mail <key> - Lấy tài khoản Email``\n"
        "``/ug <key> - Lấy tài khoản UGPhone``\n"
        "``/red <key> - Lấy tài khoản RedFonger``\n"
        "``/ld <key> - Lấy tài khoản LD Cloud``\n"
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
# ===================== Lấy link key rút gọn =====================
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

# ====================== Kiểm tra key hợp lệ ======================
async def check_key_valid(interaction, key):
    try:
        res = requests.get("https://danvnstore.site/keys.json", timeout=5)
        key_data = res.json()
    except Exception as e:
        await interaction.response.send_message(f"**Lỗi khi kiểm tra key:** {e}")
        return False

    if key not in key_data:
        await interaction.response.send_message(f"**Key `{key}` không hợp lệ hoặc không tồn tại.**")
        return False

    if key in used_keys:
        await interaction.response.send_message(f"**Key `{key}` đã được sử dụng để lấy tài khoản.**")
        return False

    return True

# ==================== Lấy tài khoản cho từng loại =================
async def get_account(interaction, key, accounts_dict, account_type):
    if not await check_key_valid(interaction, key):
        return

    if not accounts_dict:
        await interaction.response.send_message(f"**Không còn tài khoản {account_type} để cấp.**")
        return

    email, password = accounts_dict.popitem()
    used_keys.add(key)

    await interaction.response.send_message(
        f"**Tài khoản cho key `{key}`:**\nEmail: `{email}`\nMật khẩu: `{password}`",
        ephemeral=True,
    )

@tree.command(name="mail", description="Nhận tài khoản (email/mật khẩu) bằng key duy nhất.")
@app_commands.describe(key="Key dùng để nhận tài khoản")
async def mail(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_mail, "Email")

@tree.command(name="ug", description="Nhận tài khoản UGPhone bằng key duy nhất.")
@app_commands.describe(key="Key dùng để nhận tài khoản")
async def ug(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_ug, "UGPhone")

@tree.command(name="red", description="Nhận tài khoản RedFonger Cloud bằng key duy nhất.")
@app_commands.describe(key="Key dùng để nhận tài khoản")
async def red(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_red, "RedFonger")

@tree.command(name="ld", description="Nhận tài khoản LD Cloud bằng key duy nhất.")
@app_commands.describe(key="Key dùng để nhận tài khoản")
async def ld(interaction: discord.Interaction, key: str):
    await get_account(interaction, key, accounts_ld, "LD Cloud")

# ===================== Upload tài khoản (admin only) =================
async def upload_account(interaction, email, password, accounts_dict, account_type):
    if not is_admin(interaction.user):
        await interaction.response.send_message("**Bạn không có quyền dùng lệnh này.**", ephemeral=True)
        return

    if email in accounts_dict:
        await interaction.response.send_message(f"**Email `{email}` đã tồn tại trong {account_type}.**", ephemeral=True)
        return

    accounts_dict[email] = password
    await interaction.response.send_message(f"**Đã thêm tài khoản {account_type}:**\nEmail: `{email}`\nMật khẩu: `{password}`", ephemeral=True)

@tree.command(name="upmail", description="(Admin) Thêm tài khoản Email mới.")
@app_commands.describe(email="Email tài khoản", password="Mật khẩu")
async def upmail(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, email, password, accounts_mail, "Email")

@tree.command(name="upug", description="(Admin) Thêm tài khoản UGPhone mới.")
@app_commands.describe(email="Email tài khoản", password="Mật khẩu")
async def upug(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, email, password, accounts_ug, "UGPhone")

@tree.command(name="upred", description="(Admin) Thêm tài khoản RedFonger mới.")
@app_commands.describe(email="Email tài khoản", password="Mật khẩu")
async def upred(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, email, password, accounts_red, "RedFonger")

@tree.command(name="upld", description="(Admin) Thêm tài khoản LD Cloud mới.")
@app_commands.describe(email="Email tài khoản", password="Mật khẩu")
async def upld(interaction: discord.Interaction, email: str, password: str):
    await upload_account(interaction, email, password, accounts_ld, "LD Cloud")

# ====================== List tài khoản (admin only) ===================
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

# ===================== Xóa tài khoản (admin only) =======================
async def delete_account(interaction, email, accounts_dict, account_type):
    if not is_admin(interaction.user):
        await interaction.response.send_message("**Bạn không có quyền dùng lệnh này.**", ephemeral=True)
        return

    if email not in accounts_dict:
        await interaction.response.send_message(f"**Email `{email}` không tồn tại trong {account_type}.**", ephemeral=True)
        return

    del accounts_dict[email]
    await interaction.response.send_message(f"**Đã xóa tài khoản {account_type} với email `{email}`.**", ephemeral=True)

@tree.command(name="delmail", description="(Admin) Xóa tài khoản Email.")
@app_commands.describe(email="Email tài khoản cần xóa")
async def delmail(interaction: discord.Interaction, email: str):
    await delete_account(interaction, email, accounts_mail, "Email")

@tree.command(name="delug", description="(Admin) Xóa tài khoản UGPhone.")
@app_commands.describe(email="Email tài khoản cần xóa")
async def delug(interaction: discord.Interaction, email: str):
    await delete_account(interaction, email, accounts_ug, "UGPhone")

@tree.command(name="delred", description="(Admin) Xóa tài khoản RedFonger.")
@app_commands.describe(email="Email tài khoản cần xóa")
async def delred(interaction: discord.Interaction, email: str):
    await delete_account(interaction, email, accounts_red, "RedFonger")

@tree.command(name="deldl", description="(Admin) Xóa tài khoản LD Cloud.")
@app_commands.describe(email="Email tài khoản cần xóa")
async def deldl(interaction: discord.Interaction, email: str):
    await delete_account(interaction, email, accounts_ld, "LD Cloud")

# =================== Quản lý admin =====================
@tree.command(name="addadmin", description="Thêm admin mới.")
async def addadmin(interaction: discord.Interaction, user_id: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("**Bạn không có quyền thực hiện thao tác này.**", ephemeral=True)
        return
    if user_id in admin_ids:
        await interaction.response.send_message("**Người này đã là admin rồi.**", ephemeral=True)
        return

    admin_ids.add(user_id)
    await interaction.response.send_message(f"**Đã thêm admin với ID `{user_id}`.**", ephemeral=True)

@tree.command(name="removeadmin", description="Gỡ admin.")
async def removeadmin(interaction: discord.Interaction, user_id: int):
    if not is_admin(interaction.user):
        await interaction.response.send_message("**Bạn không có quyền thực hiện thao tác này.**", ephemeral=True)
        return
    if user_id == 1364169704943652924:
        await interaction.response.send_message("**Không thể gỡ admin chính.**", ephemeral=True)
        return
    if user_id == interaction.user.id:
        await interaction.response.send_message("**Bạn không thể tự gỡ chính mình.**", ephemeral=True)
        return
    if user_id in admin_ids:
        admin_ids.remove(user_id)
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


bot.run("MTM3Mzk3NTM4OTg0NzgxODM4Mw.G9A2Mv.9N_1lWFpRN1fX5VXNG0uV1H_ETz0f891ynAXEc")  # Thay bằng token
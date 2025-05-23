import discord
from discord.ext import commands
from discord import Embed, Colour
import requests
import time
import os
import json
import threading
from flask import Flask

# --- Cấu hình Bot Discord ---
intents = discord.Intents.default()
intents.message_content = True # Rất quan trọng cho Prefix Commands
bot = commands.Bot(command_prefix="!", intents=intents) # Đặt prefix mong muốn

# --- Web Server để giữ Bot hoạt động ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_web_server():
    """Chạy web server trong một thread riêng."""
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False, use_reloader=False)

# Chạy web server trong thread riêng
threading.Thread(target=run_web_server).start()

# --- Cấu hình API và URLs ---
API_TOKEN = os.environ.get('YEUMONEY_API_TOKEN', 'dfce079aa89e7256f53f6f2fe2328c128a584467f5afcbc5f5d451c581879768')
LINK_ORIGINAL = 'https://xumivnstore.site/callback.php'
HOSTING_BASE_URL = 'https://xumivnstore.site/'

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

# --- Hàm Tải/Lưu Dữ liệu từ API ---
def load_data_from_api(url, default_value_type):
    """Tải dữ liệu (tài khoản hoặc ID) từ URL API."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if default_value_type == dict:
            return data if isinstance(data, dict) else {}
        elif default_value_type == set:
            return set(data) if isinstance(data, list) else set()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi tải dữ liệu từ {url}: {e}")
    except json.JSONDecodeError as e:
        print(f"Lỗi giải mã JSON từ {url}: {e}")
    return default_value_type()

def save_data_to_api(url, data):
    """Lưu dữ liệu (tài khoản hoặc ID) vào URL API."""
    try:
        json_data = list(data) if isinstance(data, set) else data
        response = requests.post(url, json=json_data, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get('status') != 'success':
            print(f"Lỗi khi lưu dữ liệu vào {url}: {result.get('message', 'Lỗi không xác định')}")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi lưu dữ liệu vào {url}: {e}")
    except json.JSONDecodeError as e:
        print(f"Lỗi giải mã JSON khi lưu vào {url}: {e}")

# --- Khởi tạo Dữ liệu Toàn cục ---
accounts_mail = load_data_from_api(READ_MAIL_URL, dict)
accounts_ug = load_data_from_api(READ_UG_URL, dict)
accounts_red = load_data_from_api(READ_RED_URL, dict)
accounts_ld = load_data_from_api(READ_LD_URL, dict)
admin_ids = load_data_from_api(READ_ADMINS_URL, set)
used_keys = load_data_from_api(READ_USED_KEYS_URL, set)

MAIN_ADMIN_ID = 1364169704943652924
if MAIN_ADMIN_ID not in admin_ids:
    admin_ids.add(MAIN_ADMIN_ID)
    save_data_from_api(WRITE_ADMINS_URL, admin_ids)

def is_admin(user_id):
    return user_id in admin_ids

# --- Sự kiện Bot Sẵn sàng ---
@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập: {bot.user}")
    # Không cần tree.sync() cho prefix commands
    await bot.change_presence(activity=discord.Game(name="Phục vụ cộng đồng"))

# --- Lệnh `!info` (Giới thiệu bot và các lệnh) ---
@bot.command(name="info", help="Giới thiệu về bot và các lệnh khả dụng.")
async def info(ctx: commands.Context):
    is_admin_user = is_admin(ctx.author.id)

    description = (
        "**Lệnh dành cho người dùng:**\n"
        "``!getkey`` - Lấy link key rút gọn để nhận tài khoản.\n"
        "``!gmail <key>`` - Lấy tài khoản Email.\n"
        "``!ugphone <key>`` - Lấy tài khoản UGPhone.\n"
        "``!redfinger <key>`` - Lấy tài khoản RedFinger.\n"
        "``!ldcloud <key>`` - Lấy tài khoản LD Cloud.\n"
    )
    if is_admin_user:
        description += (
            "\n**Lệnh dành cho Admin:**\n"
            "``!upgmail <email> <password>`` - Thêm tài khoản Email.\n"
            "``!upugphone <email> <password>`` - Thêm tài khoản UGPhone.\n"
            "``!upredfinger <email> <password>`` - Thêm tài khoản RedFinger.\n"
            "``!upldcloud <email> <password>`` - Thêm tài khoản LD Cloud.\n"
            "``!listgmail`` - Xem danh sách tài khoản Email còn lại.\n"
            "``!listugphone`` - Xem danh sách tài khoản UGPhone còn lại.\n"
            "``!listredfinger`` - Xem danh sách tài khoản RedFinger còn lại.\n"
            "``!listldcloud`` - Xem danh sách tài khoản LD Cloud còn lại.\n"
            "``!dellgmail <email>`` - Xóa tài khoản Email.\n"
            "``!dellugphone <email>`` - Xóa tài khoản UGPhone.\n"
            "``!dellredfinger <email>`` - Xóa tài khoản RedFinger.\n"
            "``!delldcloud <email>`` - Xóa tài khoản LD Cloud.\n"
            "``!setowner <user_mention_or_id>`` - Thêm admin mới.\n"
            "``!delowner <user_mention_or_id>`` - Gỡ admin.\n"
            "``!listadmin`` - Xem danh sách admin.\n"
        )
    embed = Embed(
        title="🤖 Thông tin Bot và Các Lệnh",
        description=description,
        color=Colour(0xAA00FF)
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.set_image(url="https://i.imgur.com/WFeKMG6.gif")

    view = discord.ui.View()
    join_server_button = discord.ui.Button(
        label="Tham gia Server Hỗ Trợ",
        style=discord.ButtonStyle.link,
        url="https://discord.gg/Rgr7vCXwu2"
    )
    view.add_item(join_server_button)

    await ctx.send(embed=embed, view=view)

# --- Lệnh `!getkey` (Lấy link key) ---
@bot.command(name="getkey", help="Lấy link key rút gọn để sử dụng các lệnh khác.")
async def getkey(ctx: commands.Context):
    user_id = str(ctx.author.id)
    try:
        unique_link = f"{LINK_ORIGINAL}?uid={user_id}&t={int(time.time())}"
        encoded_link = requests.utils.quote(unique_link, safe='')
        api_url = f"https://yeumoney.com/QL_api.php?token={API_TOKEN}&url={encoded_link}&format=json"
        
        res = requests.get(api_url, timeout=10)
        res.raise_for_status()
        data = res.json()

        if data.get("status") == "success":
            short_url = data.get("shortenedUrl")
            if short_url:
                await ctx.send(
                    f"**🔗 Link key rút gọn của bạn:**\n{short_url}\n"
                    f"Vui lòng truy cập link này để lấy key và sử dụng các lệnh khác."
                )
            else:
                await ctx.send(f"**Lỗi API:** Không nhận được shortened URL.")
        else:
            await ctx.send(f"**Lỗi API:** {data.get('message', 'Lỗi không xác định từ API rút gọn.')}")
    except requests.exceptions.RequestException as e:
        await ctx.send(f"**Lỗi kết nối API rút gọn:** Vui lòng thử lại sau. ({e})")
    except json.JSONDecodeError:
        await ctx.send(f"**Lỗi giải mã dữ liệu từ API rút gọn.**")
    except Exception as e:
        await ctx.send(f"**Lỗi hệ thống không mong muốn:** {e}")

# --- Kiểm tra Key Hợp Lệ ---
async def check_key_valid(ctx: commands.Context, key: str) -> bool:
    """Kiểm tra xem key có hợp lệ và chưa được sử dụng không."""
    try:
        res = requests.get("https://xumivnstore.site/keys.json", timeout=10)
        res.raise_for_status()
        key_data = res.json()
    except requests.exceptions.RequestException as e:
        await ctx.send(f"Lỗi khi kiểm tra key từ máy chủ: {e}")
        return False
    except json.JSONDecodeError as e:
        await ctx.send(f"Lỗi giải mã JSON từ keys.json: {e}. Vui lòng kiểm tra file keys.json trên hosting.")
        return False

    if key not in key_data:
        await ctx.send(f"**Key `{key}` không hợp lệ hoặc không tồn tại.**")
        return False
    if key in used_keys:
        await ctx.send(f"**Key `{key}` đã được sử dụng để lấy tài khoản khác.**")
        return False
    return True

# --- Hàm Cấp Tài Khoản Chung (Dành cho Người dùng) ---
async def give_account(ctx: commands.Context, key: str, accounts_dict: dict, account_type: str, write_url: str):
    """Cấp một tài khoản cho người dùng nếu key hợp lệ và tài khoản còn."""
    if not await check_key_valid(ctx, key):
        return

    if not accounts_dict:
        await ctx.send(f"**Không còn tài khoản {account_type} để cấp.**")
        return
    
    try:
        email, password = accounts_dict.popitem()
        
        used_keys.add(key)
        save_data_from_api(WRITE_USED_KEYS_URL, used_keys)

        save_data_from_api(write_url, accounts_dict)
        
        await ctx.send(
            f"**✅ Tài khoản {account_type} cho key `{key}` của bạn:**\n"
            f"Email: ``{email}``\nMật khẩu: ``{password}``\n"
            f"Hãy đổi mật khẩu ngay sau khi nhận được tài khoản để bảo mật!"
        )
    except Exception as e:
        await ctx.send(f"**Lỗi khi cấp tài khoản {account_type}:** {e}")

# --- Định nghĩa các Prefix Command để lấy tài khoản ---
@bot.command(name="gmail", help="Nhận tài khoản Email bằng key duy nhất.")
async def gmail(ctx: commands.Context, key: str):
    await give_account(ctx, key, accounts_mail, "Email", WRITE_MAIL_URL)

@bot.command(name="ugphone", help="Nhận tài khoản UGPhone bằng key duy nhất.")
async def ugphone(ctx: commands.Context, key: str):
    await give_account(ctx, key, accounts_ug, "UGPhone", WRITE_UG_URL)

@bot.command(name="redfinger", help="Nhận tài khoản RedFinger Cloud bằng key duy nhất.")
async def redfinger(ctx: commands.Context, key: str):
    await give_account(ctx, key, accounts_red, "RedFinger", WRITE_RED_URL)

@bot.command(name="ldcloud", help="Nhận tài khoản LD Cloud bằng key duy nhất.")
async def ldcloud(ctx: commands.Context, key: str):
    await give_account(ctx, key, accounts_ld, "LD Cloud", WRITE_LD_URL)

# --- Hàm Upload Tài Khoản Chung (Dành cho Admin) ---
async def admin_upload_account(ctx: commands.Context, email: str, password: str, accounts_dict: dict, account_type: str, write_url: str):
    """Thêm tài khoản mới vào danh sách."""
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền dùng lệnh này.")
        return

    if email in accounts_dict:
        await ctx.send(f"**Email `{email}` đã tồn tại trong {account_type}.**")
        return
    
    accounts_dict[email] = password
    save_data_from_api(write_url, accounts_dict)
    await ctx.send(
        f"**✅ Đã thêm tài khoản {account_type}:**\nEmail: ``{email}``\nMật khẩu: ``{password}``"
    )

# --- Định nghĩa các Prefix Command để upload tài khoản (Admin) ---
@bot.command(name="upgmail", help="(Admin) Thêm tài khoản Email mới.")
async def upgmail(ctx: commands.Context, email: str, password: str):
    await admin_upload_account(ctx, email, password, accounts_mail, "Email", WRITE_MAIL_URL)

@bot.command(name="upugphone", help="(Admin) Thêm tài khoản UGPhone mới.")
async def upugphone(ctx: commands.Context, email: str, password: str):
    await admin_upload_account(ctx, email, password, accounts_ug, "UGPhone", WRITE_UG_URL)

@bot.command(name="upredfinger", help="(Admin) Thêm tài khoản RedFinger mới.")
async def upredfinger(ctx: commands.Context, email: str, password: str):
    await admin_upload_account(ctx, email, password, accounts_red, "RedFinger", WRITE_RED_URL)

@bot.command(name="upldcloud", help="(Admin) Thêm tài khoản LD Cloud mới.")
async def upldcloud(ctx: commands.Context, email: str, password: str):
    await admin_upload_account(ctx, email, password, accounts_ld, "LD Cloud", WRITE_LD_URL)

# --- Hàm List Tài Khoản Chung (Dành cho Admin) ---
async def admin_list_accounts(ctx: commands.Context, accounts_dict: dict, account_type: str):
    """Liệt kê tất cả các tài khoản còn lại trong một loại cụ thể."""
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền sử dụng lệnh này.")
        return

    if not accounts_dict:
        await ctx.send(f"**Không còn tài khoản {account_type} nào.**")
        return
    
    message = f"**Danh sách tài khoản {account_type} còn lại ({len(accounts_dict)} tài khoản):**\n"
    current_length = len(message)
    max_length = 1900

    for email in accounts_dict:
        line = f"- ``{email}``\n"
        if current_length + len(line) > max_length:
            await ctx.send(message)
            message = line
            current_length = len(line)
        else:
            message += line
            current_length += len(line)
    
    if message:
        await ctx.send(message)

# --- Định nghĩa các Prefix Command để list tài khoản (Admin) ---
@bot.command(name="listgmail", help="(Admin) Xem danh sách tài khoản Email còn lại.")
async def listgmail(ctx: commands.Context):
    await admin_list_accounts(ctx, accounts_mail, "Email")

@bot.command(name="listugphone", help="(Admin) Xem danh sách tài khoản UGPhone còn lại.")
async def listugphone(ctx: commands.Context):
    await admin_list_accounts(ctx, accounts_ug, "UGPhone")

@bot.command(name="listredfinger", help="(Admin) Xem danh sách tài khoản RedFinger còn lại.")
async def listredfinger(ctx: commands.Context):
    await admin_list_accounts(ctx, accounts_red, "RedFinger")

@bot.command(name="listldcloud", help="(Admin) Xem danh sách tài khoản LD Cloud còn lại.")
async def listldcloud(ctx: commands.Context):
    await admin_list_accounts(ctx, accounts_ld, "LD Cloud")

# --- Hàm Xóa Tài Khoản Chung (Dành cho Admin) ---
async def admin_delete_account(ctx: commands.Context, email: str, accounts_dict: dict, account_type: str, write_url: str):
    """Xóa một tài khoản khỏi danh sách."""
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền dùng lệnh này.")
        return

    if email not in accounts_dict:
        await ctx.send(f"**Email `{email}` không tồn tại trong {account_type}.**")
        return
    
    del accounts_dict[email]
    save_data_from_api(write_url, accounts_dict)
    await ctx.send(
        f"**✅ Đã xóa tài khoản {account_type} với email ``{email}``.**"
    )

# --- Định nghĩa các Prefix Command để xóa tài khoản (Admin) ---
@bot.command(name="dellgmail", help="(Admin) Xóa tài khoản Gmail.")
async def dellgmail(ctx: commands.Context, email: str):
    await admin_delete_account(ctx, email, accounts_mail, "Email", WRITE_MAIL_URL)

@bot.command(name="dellugphone", help="(Admin) Xóa tài khoản UGPhone.")
async def dellugphone(ctx: commands.Context, email: str):
    await admin_delete_account(ctx, email, accounts_ug, "UGPhone", WRITE_UG_URL)

@bot.command(name="dellredfinger", help="(Admin) Xóa tài khoản RedFinger.")
async def dellredfinger(ctx: commands.Context, email: str):
    await admin_delete_account(ctx, email, accounts_red, "RedFinger", WRITE_RED_URL)

@bot.command(name="delldcloud", help="(Admin) Xóa tài khoản LD Cloud.")
async def delldcloud(ctx: commands.Context, email: str):
    await admin_delete_account(ctx, email, accounts_ld, "LD Cloud", WRITE_LD_URL)

# --- Quản Lý Admin ---
@bot.command(name="setowner", help="(Admin) Thêm một người dùng làm admin mới.")
async def setowner(ctx: commands.Context, user: discord.Member): # discord.Member tự động phân giải từ mention/ID
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền thực hiện thao tác này.")
        return
    
    user_id = user.id
    if user_id in admin_ids:
        await ctx.send(f"**{user.display_name}** đã là admin rồi.")
        return

    admin_ids.add(user_id)
    save_data_from_api(WRITE_ADMINS_URL, admin_ids)
    await ctx.send(f"**✅ Đã thêm {user.display_name} ({user_id}) làm admin.**")

@bot.command(name="delowner", help="(Admin) Gỡ một người dùng khỏi danh sách admin.")
async def delowner(ctx: commands.Context, user: discord.Member):
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền thực hiện thao tác này.")
        return
    
    user_id = user.id
    if user_id == MAIN_ADMIN_ID:
        await ctx.send("Không thể gỡ admin chính.")
        return
    if user_id == ctx.author.id:
        await ctx.send("Bạn không thể tự gỡ chính mình.")
        return
    
    if user_id in admin_ids:
        admin_ids.remove(user_id)
        save_data_from_api(WRITE_ADMINS_URL, admin_ids)
        await ctx.send(f"**✅ Đã gỡ {user.display_name} ({user_id}) khỏi danh sách admin.**")
    else:
        await ctx.send(f"**{user.display_name}** không phải là admin.")

@bot.command(name="listadmin", help="(Admin) Xem danh sách admin hiện tại.")
async def listadmin(ctx: commands.Context):
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền sử dụng lệnh này.")
        return
    
    if not admin_ids:
        await ctx.send("Hiện không có admin nào được thêm (chỉ có admin chính).")
        return

    admin_names = []
    for admin_id in admin_ids:
        try:
            member = ctx.guild.get_member(admin_id) if ctx.guild else None
            if member is None:
                member = await bot.fetch_user(admin_id)
            admin_names.append(f"- ``{member.display_name}`` (ID: ``{admin_id}``)")
        except discord.NotFound:
            admin_names.append(f"- Người dùng không tìm thấy (ID: ``{admin_id}``)")
        except Exception as e:
            admin_names.append(f"- Lỗi khi lấy tên (ID: ``{admin_id}``): {e}")

    admins_list = "\n".join(admin_names)
    await ctx.send(f"**📝 Danh sách admin:**\n{admins_list}")

# --- Chạy Bot ---
bot.run(os.environ["DISCORD_TOKEN"])

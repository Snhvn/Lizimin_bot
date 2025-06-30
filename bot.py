import discord
from discord.ext import commands
from discord import Embed, Colour
import time
import os
import json
import requests # Cần import requests để tương tác với URL website

TOKEN= '' # Dán token của bạn vào giữa hai dấu '

# --- Cấu hình Bot Discord ---
intents = discord.Intents.default()
intents.message_content = True # Rất quan trọng cho Prefix Commands
bot = commands.Bot(command_prefix="!", intents=intents) # Đặt prefix mong muốn

# --- Cấu hình File Dữ liệu Cục bộ ---
# Các tên file JSON sẽ được lưu trữ cục bộ trên hosting của bot
MAIL_ACCOUNTS_FILE = 'mail_accounts.json'
RED_ACCOUNTS_FILE = 'red_accounts.json'
LD_ACCOUNTS_FILE = 'ld_accounts.json'
UGPHONE_ACCOUNTS_FILE = 'ugphone_accounts.json'
ADMIN_IDS_FILE = 'admin_ids.json'
USED_KEYS_FILE = 'used_keys.json'

# File lưu trữ ID kênh được chỉ định cho MỖI GUILD
DESIGNATED_CHANNELS_FILE = 'designated_channels_by_guild.json'

# --- Cấu hình URL cho Valid Keys ---
# Đây là URL file JSON trên website riêng của bạn để lấy key hợp lệ
VALID_KEYS_URL = 'https://xumivnstore.site/keys.json' # Đảm bảo file này trả về một LIST các chuỗi key


# --- Hàm Tải/Lưu Dữ liệu từ File Cục bộ ---
def load_data_from_local_file(file_path, default_value_type):
    """Tải dữ liệu từ một file JSON cục bộ."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if default_value_type == dict:
                    return data if isinstance(data, dict) else {}
                elif default_value_type == set:
                    return set(data) if isinstance(data, list) else set()
            except json.JSONDecodeError as e:
                print(f"Lỗi giải mã JSON từ {file_path}: {e}")
    return default_value_type() # Trả về giá trị mặc định nếu file không tồn tại hoặc lỗi

def save_data_to_local_file(file_path, data):
    """Lưu dữ liệu vào một file JSON cục bộ."""
    try:
        json_data = list(data) if isinstance(data, set) else data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False) # indent để dễ đọc, ensure_ascii=False để hỗ trợ tiếng Việt
    except IOError as e:
        print(f"Lỗi khi ghi dữ liệu vào {file_path}: {e}")


# --- Hàm Tải Dữ liệu từ URL (chỉ dùng cho Valid Keys) ---
def load_data_from_url(url, default_value_type):
    """Tải dữ liệu từ một URL API (dùng cho keys.json)."""
    try:
        response = requests.get(url)
        response.raise_for_status() # Ném lỗi cho phản hồi trạng thái HTTP xấu (4xx hoặc 5xx)
        data = response.json()
        if default_value_type == dict:
            return data if isinstance(data, dict) else {}
        elif default_value_type == set:
            # keys.json thường là một list các key, nên chuyển nó thành set
            return set(data) if isinstance(data, list) else set()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi tải dữ liệu từ {url}: {e}")
    except json.JSONDecodeError as e:
        print(f"Lỗi giải mã JSON từ {url}: {e}")
    return default_value_type() # Trả về giá trị mặc định nếu có lỗi


# --- Hàm Tải/Lưu Designated Channel IDs theo Guild ---
def load_designated_channels_by_guild():
    """Tải ID kênh được chỉ định cho từng guild từ file."""
    if os.path.exists(DESIGNATED_CHANNELS_FILE):
        with open(DESIGNATED_CHANNELS_FILE, 'r') as f:
            try:
                data = json.load(f)
                return {int(k): v for k, v in data.items()} # Đảm bảo keys là int (guild_id)
            except json.JSONDecodeError:
                return {}
    return {}

def save_designated_channels_by_guild(channels_dict):
    """Lưu ID kênh được chỉ định cho từng guild vào file."""
    with open(DESIGNATED_CHANNELS_FILE, 'w') as f:
        json.dump(channels_dict, f, indent=4) # indent để dễ đọc


# --- Khởi tạo Dữ liệu Toàn cục ---
# Khởi tạo các biến toàn cục bằng cách tải dữ liệu từ các file cục bộ VÀ URL
accounts_mail = load_data_from_local_file(MAIL_ACCOUNTS_FILE, dict)
accounts_red = load_data_from_local_file(RED_ACCOUNTS_FILE, dict)
accounts_ld = load_data_from_local_file(LD_ACCOUNTS_FILE, dict)
accounts_uglocal = load_data_from_local_file(UGPHONE_ACCOUNTS_FILE, set) # UGLocal dùng set
admin_ids = load_data_from_local_file(ADMIN_IDS_FILE, set) # Admin IDs dùng set
used_keys_counts = load_data_from_local_file(USED_KEYS_FILE, dict) # used_keys_counts dùng dict

# valid_keys SẼ ĐƯỢC TẢI TỪ URL CỦA BẠN
valid_keys = load_data_from_url(VALID_KEYS_URL, set)


# ĐẶT ID DISCORD CỦA BẠN VÀO ĐÂY ĐỂ LÀM ADMIN CHÍNH
MAIN_ADMIN_ID = 882844895902040104 # Thay thế bằng ID của bạn
if MAIN_ADMIN_ID not in admin_ids:
    admin_ids.add(MAIN_ADMIN_ID)
    # Lưu lại admin_ids sau khi thêm admin chính nếu nó chưa có
    save_data_to_local_file(ADMIN_IDS_FILE, admin_ids)

# Load Designated Channel IDs for each guild
designated_channels_by_guild = load_designated_channels_by_guild()


def is_admin(user_id):
    return user_id in admin_ids

# --- Kiểm tra kênh hợp lệ ---
async def check_channel(ctx: commands.Context):
    # Luôn cho phép trong tin nhắn riêng tư (DM)
    if ctx.guild is None:
        return True

    # Lấy kênh được chỉ định cho guild hiện tại
    guild_id = ctx.guild.id
    current_designated_channel_id = designated_channels_by_guild.get(guild_id)

    # Nếu chưa có kênh nào được chỉ định cho guild này, cho phép ở bất kỳ kênh nào
    if current_designated_channel_id is None:
        return True
    
    # Nếu có kênh được chỉ định, chỉ cho phép ở kênh đó
    return ctx.channel.id == current_designated_channel_id

# --- Sự kiện Bot Sẵn sàng ---
@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="Phục vụ tại sever Xumi"))

# --- Xử lý trước khi lệnh được gọi ---
@bot.before_invoke
async def before_any_command(ctx):
    # Luôn cho phép các lệnh quản lý admin (do bot admin) và setchannel/huychannel (do server admin)
    # để tránh bị khóa nếu kênh được chỉ định bị xóa hoặc bot bị lỗi
    # Các lệnh quản lý key không bị chặn vì chúng tương tác với URL
    if ctx.command.name in ['setchannel', 'huychannel', 'setadm', 'delladm', 'listadm', 'addkey', 'delkey', 'listkey']:
        pass
    elif not await check_channel(ctx):
        if ctx.guild: # Chỉ gửi cảnh báo nếu không phải là DM
            current_designated_channel_id = designated_channels_by_guild.get(ctx.guild.id)
            if current_designated_channel_id:
                channel_mention = f"<#{current_designated_channel_id}>"
                description_message = f"Vui lòng sử dụng lệnh này ở kênh đã được chỉ định trong server này: {channel_mention}"
            else:
                description_message = "Không có kênh nào được chỉ định cho server này. Vui lòng sử dụng `!setchannel` để đặt kênh."

            embed_wrong_channel = Embed(
                title="⚠️ Lệnh Chỉ Sử Dụng Được Ở Kênh Khác",
                description=description_message,
                color=Colour.orange()
            )
            embed_wrong_channel.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
            await ctx.send(embed=embed_wrong_channel, delete_after=10)
        raise commands.CommandInvokeError("Lệnh bị từ chối do không đúng kênh.")


# --- Xử lý lỗi Cooldown ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        remaining_time = round(error.retry_after, 1)
        await ctx.send(f"**⏰ Vui lòng chờ {remaining_time} giây trước khi sử dụng lệnh này lần nữa.**", delete_after=5)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"**Vui lòng nhập đầy đủ đối số cho lệnh này.** (Lỗi: {error})")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Đối số bạn cung cấp không hợp lệ. Vui lòng kiểm tra lại. (Lỗi: {error})")
    elif isinstance(error, commands.CommandInvokeError) and "Lệnh bị từ chối do không đúng kênh." in str(error):
        pass
    elif isinstance(error, commands.MissingPermissions):
        embed_no_perms = Embed(
            title="❌ Thiếu Quyền Hạn",
            description="Bạn không có đủ quyền để sử dụng lệnh này. Bạn cần có quyền **Quản lý Kênh** hoặc **Quản trị viên** trong server.",
            color=Colour.red()
        )
        embed_no_perms.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_no_perms)
    else:
        print(f"Lỗi không mong muốn xảy ra: {error}")

# --- Lệnh `!setchannel` (Admin Server) ---
@bot.command(name="setchannel", help="(Admin Server) Chỉ định kênh bot sẽ nhận lệnh trong server này. Chỉ dành cho admin server (có quyền Quản lý Kênh/Quản trị viên).")
@commands.has_permissions(manage_channels=True)
async def setchannel(ctx: commands.Context):
    global designated_channels_by_guild

    if ctx.guild is None:
        await ctx.send("Lệnh này chỉ có thể được sử dụng trong một kênh trên máy chủ (server).")
        return

    guild_id = ctx.guild.id
    channel_id = ctx.channel.id

    designated_channels_by_guild[guild_id] = channel_id
    save_designated_channels_by_guild(designated_channels_by_guild)

    embed_success = Embed(
        title="✅ Kênh Đặt Lệnh Đã Được Cập Nhật",
        description=f"Bot từ giờ sẽ chỉ nhận lệnh ở kênh này: **<#{channel_id}>** trong server **{ctx.guild.name}**.",
        color=Colour.green()
    )
    embed_success.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
    await ctx.send(embed=embed_success)

# --- Lệnh `!huychannel` (Admin Server) ---
@bot.command(name="huychannel", aliases=["clearchannel"], help="(Admin Server) Xóa kênh đã chỉ định cho bot trong server này. Bot sẽ nhận lệnh ở bất kỳ kênh nào.")
@commands.has_permissions(manage_channels=True)
async def huychannel(ctx: commands.Context):
    global designated_channels_by_guild

    if ctx.guild is None:
        await ctx.send("Lệnh này chỉ có thể được sử dụng trong một kênh trên máy chủ (server).")
        return

    guild_id = ctx.guild.id

    if guild_id in designated_channels_by_guild:
        del designated_channels_by_guild[guild_id]
        save_designated_channels_by_guild(designated_channels_by_guild)
        
        embed_success = Embed(
            title="✅ Đã Hủy Kênh Đặt Lệnh",
            description=f"Bot từ giờ sẽ nhận lệnh ở **bất kỳ kênh nào** trong server **{ctx.guild.name}**.",
            color=Colour.green()
        )
        embed_success.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_success)
    else:
        embed_not_set = Embed(
            title="ℹ️ Chưa Có Kênh Nào Được Đặt",
            description=f"Không có kênh nào được chỉ định cho server **{ctx.guild.name}** để hủy.",
            color=Colour.blue()
        )
        embed_not_set.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_not_set)

# --- Lệnh `!info` (Giới thiệu bot và các lệnh) ---
@bot.command(name="info", help="Giới thiệu về bot và các lệnh khả dụng.")
@commands.cooldown(1, 10, commands.BucketType.user)
async def info(ctx: commands.Context):
    is_admin_user = is_admin(ctx.author.id)

    user_commands_description = (
        "**Lệnh dành cho người dùng:**\n"
        "• `!getkey` - Lấy link trực tiếp để nhận tài khoản .\n"
        "• `!mail <key>` - Lấy tài khoản Email.\n"
        "• `!redfinger <key>` - Lấy tài khoản RedFinger.\n"
        "• `!ldcloud <key>` - Lấy tài khoản LD Cloud.\n"
        "• `!ugphone <key>` - Lấy 2 đoạn code/tài khoản UGPhone cùng lúc.\n"
    )

    admin_commands_description = ""
    if is_admin_user:
        admin_commands_description = (
            "\n**Lệnh dành cho Admin Bot:**\n"
            "• `!lmail <email> <password>` - Thêm tài khoản Email (có thể thêm nhiều tài khoản).\n"
            "• `!lredfinger <email> <password>` - Thêm tài khoản RedFinger (có thể thêm nhiều tài khoản).\n"
            "• `!lldcloud <email> <password>` - Thêm tài khoản LD Cloud (có thể thêm nhiều tài khoản).\n"
            "• `!lugphone <code_string>` - Thêm đoạn code/tài khoản UGLocal (chỉ tài khoản/code, không mật khẩu).\n"
            "• `!listmail` - Xem danh sách tài khoản Email còn lại.\n"
            "• `!listredfinger` - Xem danh sách tài khoản RedFinger còn lại.\n"
            "• `!listldcloud` - Xem danh sách tài khoản LD Cloud còn lại.\n"
            "• `!listugphone` - Xem danh sách code/tài khoản UGLocal còn lại.\n"
            "• `!dellgmail <email>` - Xóa tài khoản Email.\n"
            "• `!dellredfinger <email>` - Xóa tài khoản RedFinger.\n"
            "• `!delldcloud <email>` - Xóa tài khoản LD Cloud.\n"
            "• `!dellugphone <code_string>` - Xóa đoạn code/tài khoản UGLocal.\n"
            "• `!setadm <user_mention_or_id>` - Thêm admin bot mới.\n"
            "• `!delladm <user_mention_or_id>` - Gỡ admin bot.\n"
            "• `!listadm` - Xem danh sách admin bot.\n"
            "• `!addkey` - Thông báo cách thêm key mới (cần cập nhật file keys.json trên web).\n"
            "• `!delkey` - Thông báo cách xóa key (cần cập nhật file keys.json trên web).\n"
            "• `!listkey` - Cập nhật và liệt kê tất cả các key hợp lệ từ website và số lượt đã dùng.\n"
        )
    
    server_admin_command_description = (
        "\n**Lệnh dành cho Admin Server (có quyền Quản lý Kênh/Quản trị viên):**\n"
        "• `!setchannel` - Chỉ định kênh mà bot sẽ nhận các lệnh khác.\n"
        "• `!huychannel` - Xóa kênh đã được chỉ định.\n"
    )

    description = (
        "**Chào mừng bạn đến với XumiVN Store Bot!**\n"
        "Mình là bot hỗ trợ tự động cấp tài khoản cho người dùng tại XumiVN Store. "
        "Sử dụng các lệnh dưới đây để tương tác với mình nhé!\n\n"
        f"{user_commands_description}"
        f"{admin_commands_description}"
        f"{server_admin_command_description}"
    )

    embed = Embed(
        title="🤖 Thông tin Bot và Các Lệnh",
        description=description,
        color=Colour(0xAA00FF)
    )
    
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.set_image(url="https://i.imgur.com/WFeKMG6.gif")

    embed.set_footer(text="© XumiVN Store | Tham gia Discord: discord.gg/Rgr7vCXwu2")

    view = discord.ui.View()
    join_server_button = discord.ui.Button(
        label="Tham gia XumiVN Store",
        style=discord.ButtonStyle.primary,
        url="https://discord.gg/Rgr7vCXwu2"
    )
    view.add_item(join_server_button)

    await ctx.send(embed=embed, view=view)

# --- Lệnh `!getkey` (Lấy link key) ---
@bot.command(name="getkey", help="Lấy link trực tiếp để nhận tài khoản.")
@commands.cooldown(1, 10, commands.BucketType.user)
async def getkey(ctx: commands.Context):
    link_to_send = "https://xumivnstore.site"

    embed_dm = Embed(
        title="🔗 Link Key Của Bạn",
        description=(
            f"Vui lòng truy cập link này để lấy key và sử dụng các lệnh khác.\n\n"
            f"Link: **{link_to_send}**\n\n"
            f"Link này được gửi riêng tư cho bạn."
        ),
        color=Colour.blue()
    )
    if bot.user.avatar:
        embed_dm.set_thumbnail(url=bot.user.avatar.url)
    embed_dm.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
    
    try:
        await ctx.author.send(embed=embed_dm)
        await ctx.send(f"**{ctx.author.mention}**, link key của bạn đã được gửi qua tin nhắn riêng tư (DM)! Vui lòng kiểm tra DM của bạn.")
    except discord.Forbidden:
        await ctx.send(f"**{ctx.author.mention}**, tôi không thể gửi tin nhắn riêng tư cho bạn. Vui lòng kiểm tra cài đặt quyền riêng tư của bạn (cho phép tin nhắn từ thành viên máy chủ) hoặc mở DM của bạn để nhận key.")


# --- Kiểm tra Key Hợp Lệ (từ URL website) ---
async def check_key_valid(ctx: commands.Context, key: str) -> bool:
    """Kiểm tra xem key có hợp lệ không bằng cách truy vấn VALID_KEYS_URL."""
    global valid_keys
    valid_keys = load_data_from_url(VALID_KEYS_URL, set) # Luôn tải lại danh sách key từ URL để đảm bảo dữ liệu mới nhất

    if key not in valid_keys:
        await ctx.send(f"**Key `{key}` không hợp lệ hoặc không tồn tại.**")
        return False
    
    return True

# --- Hàm Cấp Tài Khoản Chung (Dành cho Người dùng) ---
async def give_account(ctx: commands.Context, key: str, accounts_dict: dict, account_type: str, file_path: str):
    """Cấp một tài khoản (email:password) cho người dùng nếu key hợp lệ và tài khoản còn."""
    global used_keys_counts

    if not await check_key_valid(ctx, key):
        return

    if key in used_keys_counts and used_keys_counts.get(key, 0) > 0:
        await ctx.send(f"**Key `{key}` đã được sử dụng để lấy tài khoản khác hoặc đã hết lượt sử dụng cho {account_type}.**")
        return

    if not accounts_dict:
        await ctx.send(f"**Đã Hết Tài Khoản Tồn Kho {account_type} để cấp.**")
        return
    
    email = None
    password = None
    try:
        email, password = next(iter(accounts_dict.items())) 
        del accounts_dict[email]

        used_keys_counts[key] = 1 

        save_data_to_local_file(file_path, accounts_dict)
        save_data_to_local_file(USED_KEYS_FILE, used_keys_counts)
        
        embed_dm = Embed(
            title=f"✅ Tài Khoản {account_type} Của Bạn",
            description=f"Dưới đây là tài khoản {account_type} mà bạn yêu cầu với key ``{key}``.",
            color=Colour.green()
        )
        embed_dm.add_field(name="Email", value=f"```{email}```", inline=False)
        embed_dm.add_field(name="Mật khẩu", value=f"```{password}```", inline=False)
        embed_dm.set_footer(text="Hãy đổi mật khẩu ngay sau khi nhận được tài khoản để bảo mật!")
        if bot.user.avatar:
            embed_dm.set_thumbnail(url=bot.user.avatar.url)
        embed_dm.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")

        await ctx.author.send(embed=embed_dm)
        await ctx.send(f"**{ctx.author.mention}**, **tài khoản {account_type} của bạn đã được gửi qua tin nhắn riêng tư (DM)! Vui lòng kiểm tra DM của bạn.**")

    except Exception as e:
        if key in used_keys_counts:
            if used_keys_counts.get(key, 0) > 0:
                used_keys_counts[key] -= 1 
            if used_keys_counts[key] <= 0:
                del used_keys_counts[key]
            save_data_to_local_file(USED_KEYS_FILE, used_keys_counts)
            print(f"Hoàn tác trạng thái key {key} do lỗi: {e}")

        if email and password:
            accounts_dict[email] = password
        save_data_to_local_file(file_path, accounts_dict)

        embed_error_dm = Embed(
            title=f"❌ Lỗi Khi Cấp Tài Khoản {account_type}",
            description=f"Đã xảy ra lỗi không mong muốn: {e}",
            color=Colour.red()
        )
        embed_error_dm.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.author.send(embed=embed_error_dm)
        await ctx.send(f"**{ctx.author.mention}**, đã xảy ra lỗi khi cấp tài khoản, vui lòng kiểm tra DM của bạn để biết chi tiết.")


# --- Hàm Cấp Code/Tài Khoản Chỉ Tài Khoản (Dành cho Người dùng) ---
async def give_single_account(ctx: commands.Context, key: str, accounts_set: set, account_type: str, file_path: str):
    """Cấp một đoạn code/tài khoản (chỉ tài khoản/email, không mật khẩu) cho người dùng nếu key hợp lệ và tài khoản còn."""
    global used_keys_counts

    if not await check_key_valid(ctx, key):
        return

    if key in used_keys_counts and used_keys_counts.get(key, 0) >= 2:
        await ctx.send(f"**Key `{key}` đã được sử dụng để lấy tài khoản khác hoặc đã hết lượt sử dụng cho {account_type}.**")
        return

    num_available = len(accounts_set)
    accounts_to_give = []
    
    accounts_list_temp = list(accounts_set)
    
    count_to_take = min(num_available, 2 - used_keys_counts.get(key, 0))

    for _ in range(count_to_take):
        if accounts_list_temp:
            account_data = accounts_list_temp.pop(0)
            accounts_to_give.append(account_data)
        else:
            break

    if not accounts_to_give:
        if num_available == 0:
            await ctx.send(f"**Đã Hết Tài Khoản Tồn Kho {account_type} để cấp.**")
        else:
            await ctx.send(f"**Không còn đủ tài khoản {account_type} để cấp thêm với key ``{key}``. Key này còn {2 - used_keys_counts.get(key, 0)} lượt sử dụng.**")
        return
    
    try:
        for acc in accounts_to_give:
            accounts_set.discard(acc)

        used_keys_counts[key] = used_keys_counts.get(key, 0) + len(accounts_to_give)

        save_data_to_local_file(file_path, accounts_set) 
        save_data_to_local_file(USED_KEYS_FILE, used_keys_counts)
        
        # --- BẮT ĐẦU SỬA ĐỔI CHO LỖI EMBED QUÁ DÀI ---
        # Tổng hợp nội dung tài khoản để kiểm tra độ dài và gửi file nếu cần
        all_accounts_content = "\n".join(accounts_to_give)
        
        embed_dm = Embed(
            title=f"✅ {len(accounts_to_give)} Đoạn Code/Tài Khoản {account_type} Của Bạn",
            description=f"Dưới đây là các đoạn code/tài khoản {account_type} mà bạn yêu cầu với key ``{key}``.",
            color=Colour.green()
        )

        # Nếu tổng nội dung quá dài, gửi file đính kèm
        if len(all_accounts_content) > 1000: # Đặt ngưỡng an toàn, ví dụ 1000 ký tự
            file_name = f"{account_type}_accounts_{ctx.author.id}.txt"
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(all_accounts_content)
            
            embed_dm.description = f"Các đoạn code/tài khoản {account_type} của bạn quá dài để hiển thị trực tiếp. Vui lòng kiểm tra file đính kèm bên dưới."
            discord_file = discord.File(file_name, filename=file_name)
            
            if used_keys_counts.get(key, 0) >= 2:
                embed_dm.set_footer(text="Key này đã được sử dụng hết lượt.")
            else:
                embed_dm.set_footer(text=f"Key này còn {2 - used_keys_counts.get(key, 0)} lượt sử dụng.")

            if bot.user.avatar:
                embed_dm.set_thumbnail(url=bot.user.avatar.url)
            embed_dm.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")

            await ctx.author.send(embed=embed_dm, file=discord_file)
            await ctx.send(f"**{ctx.author.mention}**, {len(accounts_to_give)} đoạn code/tài khoản {account_type} của bạn đã được gửi qua tin nhắn riêng tư (DM)! Vui lòng kiểm tra DM của bạn và file đính kèm.")
            
            os.remove(file_name) # Xóa file sau khi gửi
            return # Thoát hàm sau khi gửi file
        else:
            # Nếu không quá dài, thêm vào embed như bình thường
            for i, account_data in enumerate(accounts_to_give):
                embed_dm.add_field(name=f"Code/Tài khoản {i+1}", value=f"```\n{account_data}\n```", inline=False)
            
            if used_keys_counts.get(key, 0) >= 2:
                embed_dm.set_footer(text="Key này đã được sử dụng hết lượt.")
            else:
                embed_dm.set_footer(text=f"Key này còn {2 - used_keys_counts.get(key, 0)} lượt sử dụng.")

            if bot.user.avatar:
                embed_dm.set_thumbnail(url=bot.user.avatar.url)
            embed_dm.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")

            await ctx.author.send(embed=embed_dm)
            await ctx.send(f"**{ctx.author.mention}**, {len(accounts_to_give)} đoạn code/tài khoản {account_type} của bạn đã được gửi qua tin nhắn riêng tư (DM)! Vui lòng kiểm tra DM của bạn.")
        # --- KẾT THÚC SỬA ĐỔI CHO LỖI EMBED QUÁ DÀI ---


    except Exception as e:
        if key in used_keys_counts:
            used_keys_counts[key] = used_keys_counts.get(key, 0) - len(accounts_to_give)
            if used_keys_counts[key] <= 0:
                del used_keys_counts[key]
            save_data_to_local_file(USED_KEYS_FILE, used_keys_counts)
            print(f"Hoàn tác trạng thái key {key} do lỗi: {e}")

        for acc in accounts_to_give:
            accounts_set.add(acc)
        save_data_to_local_file(file_path, accounts_set)

        embed_error_dm = Embed(
            title=f"❌ Lỗi Khi Cấp Đoạn Code/Tài Khoản {account_type}",
            description=f"Đã xảy ra lỗi không mong muốn: {e}",
            color=Colour.red()
        )
        embed_error_dm.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.author.send(embed=embed_error_dm)
        await ctx.send(f"**{ctx.author.mention}**, đã xảy ra lỗi khi cấp đoạn code/tài khoản, vui lòng kiểm tra DM của bạn để biết chi tiết.")

# --- Định nghĩa các Prefix Command để lấy tài khoản ---
@bot.command(name="mail", help="Nhận tài khoản Email bằng key duy nhất.")
@commands.cooldown(1, 10, commands.BucketType.user)
async def mail(ctx: commands.Context, key: str):
    await give_account(ctx, key, accounts_mail, "Email", MAIL_ACCOUNTS_FILE)

@bot.command(name="redfinger", help="Nhận tài khoản RedFinger Cloud bằng key duy nhất.")
@commands.cooldown(1, 10, commands.BucketType.user)
async def redfinger(ctx: commands.Context, key: str):
    await give_account(ctx, key, accounts_red, "RedFinger", RED_ACCOUNTS_FILE)

@bot.command(name="ldcloud", help="Nhận tài khoản LD Cloud bằng key duy nhất.")
@commands.cooldown(1, 10, commands.BucketType.user)
async def ldcloud(ctx: commands.Context, key: str):
    await give_account(ctx, key, accounts_ld, "LD Cloud", LD_ACCOUNTS_FILE)

@bot.command(name="ugphone", help="Nhận 2 đoạn code/tài khoản UGLocal cùng lúc.")
@commands.cooldown(1, 10, commands.BucketType.user)
async def ugphone(ctx: commands.Context, key: str):
    await give_single_account(ctx, key, accounts_uglocal, "UGPHONE", UGPHONE_ACCOUNTS_FILE)


# --- Hàm Upload Tài Khoản Chung (Dành cho Admin) ---
async def admin_upload_multiple_accounts(ctx: commands.Context, raw_input: str, accounts_dict: dict, account_type: str, file_path: str):
    """Thêm nhiều tài khoản (email:password) mới vào danh sách từ input nhiều dòng."""
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền dùng lệnh này.")
        return

    added_accounts = []
    skipped_accounts = []

    lines = raw_input.strip().split('\n')
    for line in lines:
        parts = line.strip().split(' ', 1)
        if len(parts) == 2:
            email = parts[0].strip()
            password = parts[1].strip()
            if email and password:
                if email in accounts_dict:
                    skipped_accounts.append(email)
                else:
                    accounts_dict[email] = password
                    added_accounts.append(email)
            else:
                skipped_accounts.append(line.strip())
        else:
            skipped_accounts.append(line.strip())

    if added_accounts:
        save_data_to_local_file(file_path, accounts_dict)
        
        embed_success_desc = f"Đã thêm **{len(added_accounts)}** tài khoản {account_type} mới vào hệ thống."
        if added_accounts:
            embed_success_desc += "\n**Các tài khoản đã thêm:**\n" + "\n".join([f"``{acc}``" for acc in added_accounts[:10]])
            if len(added_accounts) > 10:
                embed_success_desc += "\n*(và nhiều tài khoản khác...)*"

        embed_success = Embed(
            title=f"✅ Thêm Tài Khoản {account_type} Thành Công",
            description=embed_success_desc,
            color=Colour.green()
        )
        embed_success.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_success)
    else:
        embed_no_add = Embed(
            title=f"ℹ️ Không có Tài Khoản {account_type} nào được thêm",
            description="Không có tài khoản hợp lệ nào để thêm hoặc tất cả đã tồn tại.",
            color=Colour.blue()
        )
        embed_no_add.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_no_add)

    if skipped_accounts:
        embed_skipped_desc = f"Có **{len(skipped_accounts)}** tài khoản không được thêm (đã tồn tại hoặc định dạng sai):\n"
        embed_skipped_desc += "\n".join([f"``{acc}``" for acc in skipped_accounts[:10]])
        if len(skipped_accounts) > 10:
            embed_skipped_desc += "\n*(và nhiều tài khoản khác...)*"
        
        embed_skipped = Embed(
            title=f"⚠️ Tài Khoản {account_type} Bị Bỏ Qua",
            description=embed_skipped_desc,
            color=Colour.orange()
        )
        embed_skipped.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_skipped)


# --- Hàm Upload Code/Tài Khoản Chỉ Tài Khoản (Dành cho Admin) ---
async def admin_upload_single_account(ctx: commands.Context, account_string: str, accounts_set: set, account_type: str, file_path: str):
    """Thêm một đoạn code/tài khoản (chỉ tài khoản/email, không mật khẩu) mới vào danh sách."""
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền dùng lệnh này.")
        return

    added_count = 0
    skipped_count = 0
    added_accounts_list = []
    skipped_accounts_list = []

    lines = account_string.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line:
            if line in accounts_set:
                skipped_count += 1
                skipped_accounts_list.append(line)
            else:
                accounts_set.add(line)
                added_count += 1
                added_accounts_list.append(line)
    
    if added_count > 0:
        save_data_to_local_file(file_path, accounts_set)
        
        embed_success_desc = f"Đã thêm **{added_count}** đoạn code/tài khoản {account_type} mới vào hệ thống."
        if added_accounts_list:
            embed_success_desc += "\n**Các đoạn code/tài khoản đã thêm:**\n" + "\n".join([f"``{acc}``" for acc in added_accounts_list[:10]])
            if len(added_accounts_list) > 10:
                embed_success_desc += "\n*(và nhiều tài khoản khác...)*"

        embed_success = Embed(
            title=f"✅ Thêm Đoạn Code/Tài Khoản {account_type} Thành Công",
            description=embed_success_desc,
            color=Colour.green()
        )
        embed_success.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_success)
    else:
        embed_no_add = Embed(
            title=f"ℹ️ Không có Đoạn Code/Tài Khoản {account_type} nào được thêm",
            description="Không có đoạn code/tài khoản hợp lệ nào để thêm hoặc tất cả đã tồn tại.",
            color=Colour.blue()
        )
        embed_no_add.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_no_add)

    if skipped_count > 0:
        embed_skipped_desc = f"Có **{skipped_count}** đoạn code/tài khoản không được thêm (đã tồn tại hoặc trống):\n"
        embed_skipped_desc += "\n".join([f"``{acc}``" for acc in skipped_accounts_list[:10]])
        if len(skipped_accounts_list) > 10:
            embed_skipped_desc += "\n*(và nhiều tài khoản khác...)*"
            
        embed_skipped = Embed(
            title=f"⚠️ Đoạn Code/Tài Khoản {account_type} Bị Bỏ Qua",
            description=embed_skipped_desc,
            color=Colour.orange()
        )
        embed_skipped.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_skipped)


# --- Định nghĩa các Prefix Command để upload tài khoản (Admin) ---
@bot.command(name="lmail", help="(Admin) Thêm tài khoản Email mới. Ví dụ: !lmail\nemail1@gmail.com pass1\nemail2@gmail.com pass2")
async def lmail(ctx: commands.Context, *, raw_input: str):
    await admin_upload_multiple_accounts(ctx, raw_input, accounts_mail, "Email", MAIL_ACCOUNTS_FILE)

@bot.command(name="lredfinger", help="(Admin) Thêm tài khoản RedFinger mới. Ví dụ: !lredfinger\nemail1@gmail.com pass1\nemail2@gmail.com pass2")
async def lredfinger(ctx: commands.Context, *, raw_input: str):
    await admin_upload_multiple_accounts(ctx, raw_input, accounts_red, "RedFinger", RED_ACCOUNTS_FILE)

@bot.command(name="lldcloud", help="(Admin) Thêm tài khoản LD Cloud mới. Ví dụ: !lldcloud\nemail1@gmail.com pass1\nemail2@gmail.com pass2")
async def lldcloud(ctx: commands.Context, *, raw_input: str):
    await admin_upload_multiple_accounts(ctx, raw_input, accounts_ld, "LD Cloud", LD_ACCOUNTS_FILE)

@bot.command(name="lugphone", help="(Admin) Thêm đoạn code/tài khoản UGLocal mới. (Hỗ trợ nhiều dòng, mỗi dòng một code)")
async def lugphone(ctx: commands.Context, *, account_string: str):
    await admin_upload_single_account(ctx, account_string, accounts_uglocal, "UGPHONE", UGPHONE_ACCOUNTS_FILE)


# --- Hàm List Tài Khoản Chung (Dành cho Admin) ---
async def admin_list_accounts(ctx: commands.Context, accounts_dict: dict, account_type: str):
    """Liệt kê tất cả các tài khoản còn lại trong một loại cụ thể."""
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền sử dụng lệnh này.")
        return

    if not accounts_dict:
        embed_no_accounts = Embed(
            title=f"⚠️ Danh Sách {account_type} Trống",
            description=f"**Hiện không có tài khoản {account_type} nào trong kho.**",
            color=Colour.orange()
        )
        embed_no_accounts.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_no_accounts)
        return
    
    embed_list = Embed(
        title=f"📝 Danh Sách Tài Khoản {account_type} Còn Lại",
        description=f"**Tổng cộng: {len(accounts_dict)} tài khoản**",
        color=Colour.blue()
    )
    embed_list.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
    
    current_chunk = ""
    field_count = 0
    max_field_length = 1024

    sorted_emails = sorted(accounts_dict.keys())

    for email in sorted_emails:
        line = f"- ``{email}``\n"
        if len(current_chunk) + len(line) > max_field_length:
            if field_count < 25:
                embed_list.add_field(name=f"Tài khoản {field_count + 1}", value=current_chunk, inline=False)
                field_count += 1
                current_chunk = line
            else:
                await ctx.send(embed=embed_list)
                embed_list = Embed(
                    title=f"📝 (Tiếp theo) Danh Sách Tài Khoản {account_type}",
                    color=Colour.blue()
                )
                embed_list.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
                field_count = 0
                current_chunk = line
        else:
            current_chunk += line
    
    if current_chunk and field_count < 25:
        embed_list.add_field(name=f"Tài khoản {field_count + 1}", value=current_chunk, inline=False)
    
    await ctx.send(embed=embed_list)


# --- Hàm List Code/Tài Khoản Chỉ Tài Khoản (Dành cho Admin) ---
async def admin_list_single_accounts(ctx: commands.Context, accounts_set: set, account_type: str):
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền sử dụng lệnh này.")
        return

    if not accounts_set:
        embed_no_accounts = Embed(
            title=f"⚠️ Danh Sách {account_type} Trống",
            description=f"**Hiện không có đoạn code/tài khoản {account_type} nào trong kho.**",
            color=Colour.orange()
        )
        embed_no_accounts.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_no_accounts)
        return
    
    embed_list = Embed(
        title=f"📝 Danh Sách Đoạn Code/Tài Khoản {account_type} Còn Lại",
        description=f"**Tổng cộng: {len(accounts_set)} Tài Khoản**",
        color=Colour.blue()
    )
    embed_list.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")

    current_chunk = ""
    field_count = 0
    max_field_length = 1024

    sorted_accounts = sorted(list(accounts_set))

    for account_data in sorted_accounts:
        display_data = account_data if len(account_data) <= 50 else f"{account_data[:47]}..."
        line = f"- ```{display_data}```\n"
        
        if len(current_chunk) + len(line) > max_field_length:
            if field_count < 25:
                embed_list.add_field(name=f"Tài Khoản {account_type} {field_count + 1}", value=current_chunk, inline=False)
                field_count += 1
                current_chunk = line
            else:
                await ctx.send(embed=embed_list)
                embed_list = Embed(
                    title=f"📝 (Tiếp theo) Danh Sách Đoạn Code/Tài Khoản {account_type}",
                    color=Colour.blue()
                )
                embed_list.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
                field_count = 0
                current_chunk = line
        else:
            current_chunk += line
    
    if current_chunk and field_count < 25:
        embed_list.add_field(name=f"Tài Khoản {account_type} {field_count + 1}", value=current_chunk, inline=False)
    
    await ctx.send(embed=embed_list)


# --- Định nghĩa các Prefix Command để list tài khoản (Admin) ---
@bot.command(name="listmail", help="(Admin) Xem danh sách tài khoản Email còn lại.")
async def listmail(ctx: commands.Context):
    await admin_list_accounts(ctx, accounts_mail, "Email")

@bot.command(name="listredfinger", help="(Admin) Xem danh sách tài khoản RedFinger còn lại.")
async def listredfinger(ctx: commands.Context):
    await admin_list_accounts(ctx, accounts_red, "RedFinger")

@bot.command(name="listldcloud", help="(Admin) Xem danh sách tài khoản LD Cloud còn lại.")
async def listldcloud(ctx: commands.Context):
    await admin_list_accounts(ctx, accounts_ld, "LD Cloud")

@bot.command(name="listugphone", help="(Admin) Xem danh sách đoạn code/tài khoản UGLocal còn lại.")
async def listugphone(ctx: commands.Context):
    await admin_list_single_accounts(ctx, accounts_uglocal, "UGPHONE")

# --- Hàm Xóa Tài Khoản Chung (Dành cho Admin) ---
async def admin_delete_account(ctx: commands.Context, email: str, accounts_dict: dict, account_type: str, file_path: str):
    """Xóa một tài khoản (email:password) khỏi danh sách."""
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền dùng lệnh này.")
        return

    if email not in accounts_dict:
        embed_not_found = Embed(
            title=f"⚠️ Lỗi Xóa Tài Khoản {account_type}",
            description=f"**Email ``{email}`` không tồn tại trong danh sách {account_type}.**",
            color=Colour.orange()
        )
        embed_not_found.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_not_found)
        return
    
    del accounts_dict[email]
    save_data_to_local_file(file_path, accounts_dict)
    
    embed_success = Embed(
        title=f"✅ Xóa Tài Khoản {account_type} Thành Công",
        description=f"Đã xóa tài khoản {account_type} với email ``{email}`` khỏi hệ thống.",
        color=Colour.green()
    )
    embed_success.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
    await ctx.send(embed=embed_success)


# --- Hàm Xóa Code/Tài Khoản Chỉ Tài Khoản (Dành cho Admin) ---
async def admin_delete_single_account(ctx: commands.Context, account_string: str, accounts_set: set, account_type: str, file_path: str):
    """Xóa một đoạn code/tài khoản (chỉ tài khoản) khỏi danh sách."""
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền dùng lệnh này.")
        return

    if account_string not in accounts_set:
        embed_not_found = Embed(
            title=f"⚠️ Lỗi Xóa Đoạn Code/Tài Khoản {account_type}",
            description=f"**Đoạn code/tài khoản ``{account_string}`` không tồn tại trong danh sách {account_type}.**",
            color=Colour.orange()
        )
        embed_not_found.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_not_found)
        return
    
    accounts_set.remove(account_string)
    save_data_to_local_file(file_path, accounts_set)
    
    embed_success = Embed(
        title=f"✅ Xóa Đoạn Code/Tài Khoản {account_type} Thành Công",
        description=f"Đã xóa đoạn code/tài khoản {account_type} sau khỏi hệ thống:",
        color=Colour.green()
    )
    embed_success.add_field(name="Nội dung", value=f"```\n{account_string}\n```", inline=False)
    embed_success.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
    await ctx.send(embed=embed_success)

# --- Định nghĩa các Prefix Command để xóa tài khoản (Admin) ---
@bot.command(name="dellmail", help="(Admin) Xóa tài khoản Gmail.")
async def dellmail(ctx: commands.Context, email: str):
    await admin_delete_account(ctx, email, accounts_mail, "Email", MAIL_ACCOUNTS_FILE)

@bot.command(name="dellredfinger", help="(Admin) Xóa tài khoản RedFonger.")
async def dellredfinger(ctx: commands.Context, email: str):
    await admin_delete_account(ctx, email, accounts_red, "RedFinger", RED_ACCOUNTS_FILE)

@bot.command(name="delldcloud", help="(Admin) Xóa tài khoản LD Cloud.")
async def delldcloud(ctx: commands.Context, email: str):
    await admin_delete_account(ctx, email, accounts_ld, "LD Cloud", LD_ACCOUNTS_FILE)

@bot.command(name="dellugphone", help="(Admin) Xóa đoạn code/tài khoản UGLocal.")
async def dellugphone(ctx: commands.Context, *, account_string: str):
    await admin_delete_single_account(ctx, account_string, accounts_uglocal, "UGPHONE", UGPHONE_ACCOUNTS_FILE)

# --- Quản Lý Key Hợp lệ (Admin) ---
@bot.command(name="addkey", help="(Admin) Thông báo cách thêm key mới. Key được quản lý trên website riêng của bạn.")
async def addkey(ctx: commands.Context):
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền dùng lệnh này.")
        return
    
    embed_info = Embed(
        title="ℹ️ Cách Thêm Key Mới",
        description=(
            "Để thêm key mới, bạn cần **cập nhật file `keys.json` trên website riêng của bạn** (`https://xumivnstore.site/keys.json`).\n\n"
            "File `keys.json` phải là một mảng JSON (list) chứa các chuỗi key, ví dụ:\n"
            "```json\n[\"key123\", \"keyabc\", \"keyxyz\"]\n```\n"
            "Sau khi cập nhật trên website, bot sẽ tự động đọc key mới khi người dùng sử dụng lệnh lấy tài khoản."
        ),
        color=Colour.blue()
    )
    embed_info.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
    await ctx.send(embed=embed_info)

@bot.command(name="delkey", help="(Admin) Thông báo cách xóa key. Key được quản lý trên website riêng của bạn.")
async def delkey(ctx: commands.Context):
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền dùng lệnh này.")
        return
    
    embed_info = Embed(
        title="ℹ️ Cách Xóa Key",
        description=(
            "Để xóa key, bạn cần **cập nhật file `keys.json` trên website riêng của bạn** (`https://xumivnstore.site/keys.json`) bằng cách loại bỏ key đó khỏi mảng JSON.\n\n"
            "Sau khi key bị xóa khỏi file `keys.json` trên website, bot sẽ không còn chấp nhận key đó nữa."
        ),
        color=Colour.blue()
    )
    embed_info.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
    await ctx.send(embed=embed_info)


@bot.command(name="listkey", help="(Admin) Cập nhật và liệt kê tất cả các key hợp lệ từ website và số lượt đã dùng của mỗi key.")
async def listkey(ctx: commands.Context):
    global valid_keys, used_keys_counts
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền sử dụng lệnh này.")
        return
    
    valid_keys = load_data_from_url(VALID_KEYS_URL, set) # Luôn tải lại danh sách key từ URL để đảm bảo dữ liệu mới nhất
    
    if not valid_keys:
        embed_no_keys = Embed(
            title="⚠️ Danh Sách Key Trống",
            description="**Hiện không có key hợp lệ nào được tải từ website của bạn.** Vui lòng kiểm tra file `keys.json` trên `https://xumivnstore.site/keys.json`.",
            color=Colour.orange()
        )
        embed_no_keys.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_no_keys)
        return

    embed_list = Embed(
        title="📝 Danh Sách Key Hợp Lệ Hiện Tại (Từ Website)",
        description=f"**Tổng cộng: {len(valid_keys)} key.** (Hiển thị số lượt dùng nếu có)",
        color=Colour.blue()
    )
    embed_list.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")

    current_chunk = ""
    field_count = 0
    max_field_length = 1024

    sorted_keys = sorted(list(valid_keys))

    for key in sorted_keys:
        used_count = used_keys_counts.get(key, 0)
        status_text = f"Đã dùng: {used_count} lượt"
        if key.startswith('UG'):
             status_text = f"Đã dùng: {used_count}/2 lượt"

        line = f"- ``{key}`` ({status_text})\n"
        
        if len(current_chunk) + len(line) > max_field_length:
            if field_count < 25:
                embed_list.add_field(name=f"Key {field_count + 1}", value=current_chunk, inline=False)
                field_count += 1
                current_chunk = line
            else:
                await ctx.send(embed=embed_list)
                embed_list = Embed(
                    title=f"📝 (Tiếp theo) Danh Sách Key Hợp Lệ",
                    color=Colour.blue()
                )
                embed_list.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
                field_count = 0
                current_chunk = line
        else:
            current_chunk += line
    
    if current_chunk and field_count < 25:
        embed_list.add_field(name=f"Key {field_count + 1}", value=current_chunk, inline=False)
    
    await ctx.send(embed=embed_list)


# --- Quản Lý Admin ---
@bot.command(name="setadm", help="(Admin) Thêm một người dùng làm admin mới.")
async def setadm(ctx: commands.Context, user: discord.Member):
    global admin_ids
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền thực hiện thao tác này.")
        return
    
    user_id = user.id
    if user_id in admin_ids:
        embed_exist = Embed(
            title="⚠️ Lỗi Thêm Admin",
            description=f"**{user.display_name}** đã là admin rồi.",
            color=Colour.orange()
        )
        embed_exist.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_exist)
        return

    admin_ids.add(user_id)
    save_data_to_local_file(ADMIN_IDS_FILE, admin_ids)
    
    embed_success = Embed(
        title="✅ Thêm Admin Thành Công",
        description=f"Đã thêm **{user.display_name}** (ID: ``{user_id}``) làm admin.",
        color=Colour.green()
    )
    embed_success.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
    await ctx.send(embed=embed_success)

@bot.command(name="delladm", help="(Admin) Gỡ một người dùng khỏi danh sách admin.")
async def delladm(ctx: commands.Context, user: discord.Member):
    global admin_ids
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền thực hiện thao tác này.")
        return
    
    user_id = user.id
    if user_id == MAIN_ADMIN_ID:
        embed_error = Embed(
            title="❌ Lỗi Gỡ Admin",
            description="Không thể gỡ admin chính.",
            color=Colour.red()
        )
        embed_error.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_error)
        return
    if user_id == ctx.author.id:
        embed_error = Embed(
            title="❌ Lỗi Gỡ Admin",
            description="Bạn không thể tự gỡ chính mình.",
            color=Colour.red()
        )
        embed_error.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_error)
        return
    
    if user_id in admin_ids:
        admin_ids.remove(user_id)
        save_data_to_local_file(ADMIN_IDS_FILE, admin_ids)
        embed_success = Embed(
            title="✅ Gỡ Admin Thành Công",
            description=f"Đã gỡ **{user.display_name}** (ID: ``{user_id}``) khỏi danh sách admin.",
            color=Colour.green()
        )
        embed_success.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_success)
    else:
        embed_not_found = Embed(
            title="⚠️ Lỗi Gỡ Admin",
            description=f"**{user.display_name}** không phải là admin.",
            color=Colour.orange()
        )
        embed_not_found.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_not_found)

@bot.command(name="listadm", help="(Admin) Xem danh sách admin hiện tại.")
async def listadm(ctx: commands.Context):
    if not is_admin(ctx.author.id):
        await ctx.send("Bạn không có quyền sử dụng lệnh này.")
        return
    
    if not admin_ids:
        embed_no_admins = Embed(
            title="⚠️ Danh Sách Admin Trống",
            description="Hiện không có admin nào được thêm (chỉ có admin chính).",
            color=Colour.orange()
        )
        embed_no_admins.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
        await ctx.send(embed=embed_no_admins)
        return

    embed_list = Embed(
        title="📝 Danh Sách Admin Hiện Tại",
        description="Dưới đây là danh sách các admin của bot:",
        color=Colour.blue()
    )
    embed_list.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")

    admin_names_list = []
    sorted_admin_ids = sorted(list(admin_ids))

    for admin_id in sorted_admin_ids:
        try:
            member = ctx.guild.get_member(admin_id) if ctx.guild else None
            if member is None:
                member = await bot.fetch_user(admin_id)
            admin_names_list.append(f"- ``{member.display_name}`` (ID: ``{admin_id}``)")
        except discord.NotFound:
            admin_names_list.append(f"- Người dùng không tìm thấy (ID: ``{admin_id}``)")
        except Exception as e:
            admin_names_list.append(f"- Lỗi khi lấy tên (ID: ``{admin_id}``): {e}")

    current_chunk = ""
    field_count = 0
    max_field_length = 1024

    for line in admin_names_list:
        if len(current_chunk) + len(line) + 1 > max_field_length:
            if field_count < 25:
                embed_list.add_field(name=f"Admin {field_count + 1}", value=current_chunk, inline=False)
                field_count += 1
                current_chunk = line + "\n"
            else:
                await ctx.send(embed=embed_list)
                embed_list = Embed(
                    title=f"📝 (Tiếp theo) Danh Sách Admin Hiện Tại",
                    color=Colour.blue()
                )
                embed_list.set_footer(text="© Xumi - https://discord.gg/DPUbDVAazj")
                field_count = 0
                current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    
    if current_chunk and field_count < 25:
        embed_list.add_field(name=f"Admin {field_count + 1}", value=current_chunk, inline=False)
    
    await ctx.send(embed=embed_list)

# CHẠY BOT
bot.run(TOKEN)

import re
import aiohttp
import asyncio
from datetime import datetime, timedelta
import motor.motor_asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *

# ==================== Mongo Setup ====================
mongo = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = mongo["guardian_bot"]
sudo_col = db["sudo_users"]
badword_col = db["badwords"]
settings_col = db["chat_settings"]
stats_col = db["stats"]
chats_col = db["known_chats"]
blocked_packs_col = db["blocked_sticker_packs"]
# =====================================================

bot = Client("guardian_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
PARSE_MODE = enums.ParseMode.MARKDOWN

# ==================== Helper Functions ====================
async def is_sudo(user_id: int):
    return user_id == OWNER_ID or await sudo_col.find_one({"user_id": user_id})

async def add_sudo(uid: int):
    await sudo_col.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)

async def rm_sudo(uid: int):
    await sudo_col.delete_one({"user_id": uid})

async def get_sudo_list():
    docs = await sudo_col.find().to_list(100)
    return [d["user_id"] for d in docs]

async def get_badwords():
    words = [doc["word"] for doc in await badword_col.find().to_list(length=1000)]
    try:
        with open("slang_words.txt", "r") as f:
            words += [w.strip().lower() for w in f if w.strip()]
    except:
        pass
    return list(set(words))

def is_bad_match(word, text):
    """Detect disguised versions: d*m, d/m, d.m, etc."""
    word = re.escape(word)
    pattern = "".join(f"[{c}]" + r"[\W_]*" if c.isalpha() else c for c in word)
    return re.search(pattern, text, re.IGNORECASE) is not None

async def send_log(text):
    """Send logs to log chat."""
    chat_id_doc = await settings_col.find_one({"setting": "log_chat"})
    if chat_id_doc:
        try:
            await bot.send_message(chat_id_doc["chat_id"], text)
        except:
            pass

async def update_stats(reason):
    """Update deletion stats."""
    await stats_col.update_one(
        {"_id": "global"},
        {"$inc": {f"{reason}_count": 1, "total": 1}},
        upsert=True
    )

async def get_stats():
    s = await stats_col.find_one({"_id": "global"}) or {}
    chat_count = await chats_col.count_documents({})
    return {
        "Total": s.get("total", 0),
        "AI Flags": s.get("ai_count", 0),
        "DB Flags": s.get("db_count", 0),
        "Edits": s.get("edit_count", 0),
        "Chats": chat_count,
    }

async def track_chat(message):
    try:
        if message.chat:
            await chats_col.update_one(
                {"chat_id": message.chat.id},
                {"$set": {"chat_id": message.chat.id, "title": message.chat.title or message.chat.first_name or "Private", "type": str(message.chat.type)}},
                upsert=True,
            )
    except Exception:
        pass

# ==================== AI Filter for TEXT ====================
async def ai_check_safe(text):
    """Ask AI if text is truly abusive in context."""
    global OPENROUTER_KEY
    if not OPENROUTER_KEY:
        await send_log("⚠️ Missing OpenRouter API key.")
        return False

    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You detect *real* abusive, sexual, or hateful messages.\n"
                    "If text just coincidentally matches slang letters (like 'mc' in 'Mausam chal'), return OK.\n"
                    "Return ONLY 'BAD' or 'OK'."
                )
            },
            {"role": "user", "content": text}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OPENROUTER_URL, json=payload, headers=headers, timeout=10) as resp:
                data = await resp.json()
                reply = data["choices"][0]["message"]["content"].strip().upper()
                return reply == "BAD"
    except Exception as e:
        await send_log(f"⚠️ AI error: {e}")
        return False

# ==================== AI Media NSFW (placeholder) ====================
async def ai_media_check(file_bytes: bytes, mime: str) -> bool:
    """
    Placeholder for media NSFW detection.
    Returns True if media is considered NSFW (should be deleted).
    Implement your preferred image/video moderation API here.
    """
    # Simple placeholder: always return False (not NSFW)
    # Replace with real API calls (e.g., OpenAI moderation, Sightengine, or other).
    return False

# ==================== Warn User ====================
async def warn_user(bot_obj, message, reason):
    user = message.from_user
    kb = InlineKeyboardMarkup([
         [
            InlineKeyboardButton("˹ 𝐔ᴘᴅᴧᴛєs ˼", url="https://t.me/team_rdx_network"),
            InlineKeyboardButton("˹ 𝐒υᴘᴘσʀᴛ ˼", url="https://t.me/team_rdx_point")
        ],
        [
            InlineKeyboardButton("✙ 𝐀ᴅᴅ 𝐌є 𝐈η 𝐘συʀ 𝐆ʀσυᴘ ✙",
            url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true&admin=delete_messages+invite_users")
        ]
    ])
    try:
        warn = await message.reply_text(f"⚠️ {user.mention} — {reason}", reply_markup=kb)
        await asyncio.sleep(WARN_DELETE_DELAY)
        await warn.delete()
    except:
        pass
    await send_log(f"⚠️ {user.mention} triggered warning: {reason}")

# ==================== Log Formatter ====================
async def format_and_send_deletion_log(chat_id, message, reason_type, matched_word):
    try:
        time_str = (
            message.date.strftime("%Y-%m-%d %H:%M:%S UTC")
            if isinstance(message.date, datetime)
            else datetime.utcfromtimestamp(message.date).strftime("%Y-%m-%d %H:%M:%S UTC")
        )
        text = (
            f"🧹 **Message Deleted Logged**\n"
            f"👤 **User:** {message.from_user.mention if message.from_user else 'Unknown'}\n"
            f"💬 **Chat:** {message.chat.title or chat_id}\n"
            f"🕒 **Time:** {time_str}\n"
            f"🚫 **Reason:** {reason_type.upper()}\n"
            f"🔤 **Matched Word:** `{matched_word}`\n\n"
            f"📝 **Content:**\n{message.text or 'N/A'}"
        )
        await send_log(text)
    except Exception as e:
        print(f"Log error: {e}")

# ==================== Commands ====================
@bot.on_message(filters.command("start"))
async def start_cmd(_, m):
    photo_url = "https://files.catbox.moe/8z8qgr.jfif"
    short_caption = "🛡️ **ABUSE GUARDIAN BOT ** — online and active ⚡"

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("˹ 𝐇єʟᴘ 𝐀ηᴅ 𝐂ᴏᴍᴍᴧηᴅs ˼", callback_data="help")],
        [
            InlineKeyboardButton("˹ 𝐔ᴘᴅᴧᴛєs ˼", url="https://t.me/TheAceUpdates"),
            InlineKeyboardButton("˹ 𝐒υᴘᴘσʀᴛ ˼", url="https://t.me/hellbotsupport")
        ],
        [InlineKeyboardButton("˹ 𝐃єᴠєʟσᴘєʀ ˼", url="https://t.me/TrueNakshu")],
        [InlineKeyboardButton("⌯ 𝐀ᴅᴅ 𝐌є ⌯", url=f"https://t.me/@AbuseGuardianBot?startgroup=true")]
    ])

    full_text = (
        "```"
        "+--------------------------------------------+\n"
        "|  ⚡  ABUSE GUARDIAN TERMINAL INITIATED...  |\n"
        "+--------------------------------------------+\n"
        "```"
        "\n"
        "👾 **AI-Powered Guardian Online**\n"
        "Scanning chats for abuse, hate & NSFW in real-time.\n\n"
        "⚙️ **Quick Commands:**\n"
        "• /help — View control panel\n"
        "• /stats — Live moderation data\n\n"
        "💀 **Protocol:** Zero Mercy | Neural Verified | Fast Purge\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🕶️ **Status:** ACTIVE ✅\n"
        "🌐 **Mode:** Silent | Secure | Relentless\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⌯ _Welcome, Operator._\n"
        "⌯ ADD : @abuseGuardianBot ⌯ "
    )

    # Send image with short caption
    try:
        await m.reply_photo(photo=photo_url, caption=short_caption)
    except:
        await m.reply_text(short_caption)

    # Send long styled info message
    await m.reply_text(full_text, reply_markup=btn, parse_mode=PARSE_MODE)

@bot.on_callback_query(filters.regex("help"))
async def help_btn(_, q):
    txt = (
        "+--------------------------------------------------------+\n" "| 🛡️ ABUSE GUARDIAN — COMMANDS (SUDO ONLY) |\n" "+--------------------------------------------------------+\n" "| ⚙️ BASIC CONTROLS |\n" "| /add <word> — Add badword |\n" "| /rm <word> — Remove badword |\n" "| /list — Show all badwords |\n" "+--------------------------------------------------------+\n" "| 🧠 AI & CONFIGS |\n" "| /setlog <chat_id> — Set log channel [SUDO] |\n" "| /api <key> — Set OpenRouter API [SUDO] |\n" "+--------------------------------------------------------+\n" "| 👑 SUDO MANAGEMENT |\n" "| /addsudo <id/reply> — Add sudo user [SUDO] |\n" "| /rmsudo <id/reply> — Remove sudo user [SUDO] |\n" "| /sudolist — List sudo users [SUDO] |\n" "+--------------------------------------------------------+\n" "| 📢 BROADCAST & CLEANUP |\n" "| /broadcast <text> — Broadcast to all chats |\n" "| (sudo only) [SUDO] |\n" "+--------------------------------------------------------+\n" "| 🚫 STICKER FIREWALL |\n" "| /blockpack (reply sticker) — Block sticker pack [SUDO] |\n" "| /unblockpack (reply sticker)— Unblock pack [SUDO] |\n" "+--------------------------------------------------------+\n" "| 📊 STATS & INFO |\n" "| /stats — Show live moderation stats |\n" "+--------------------------------------------------------+\n" "| ℹ️ NOTE: Commands marked [SUDO] require owner/sudo |\n" "+--------------------------------------------------------+\n"
    )
    await q.message.edit_text(txt, parse_mode=PARSE_MODE)

# ----- Sudo Commands -----
@bot.on_message(filters.command("addsudo"))
async def addsudo_cmd(_, m):
    if not await is_sudo(m.from_user.id):
        return await m.reply("❌ Only owner/sudo can use this.")
    uid = m.reply_to_message.from_user.id if m.reply_to_message else (int(m.command[1]) if len(m.command) > 1 else None)
    if not uid:
        return await m.reply("Usage: /addsudo <id> or reply to user")
    await add_sudo(uid)
    await m.reply(f"✅ Added sudo user `{uid}`")

@bot.on_message(filters.command("rmsudo"))
async def rmsudo_cmd(_, m):
    if not await is_sudo(m.from_user.id):
        return await m.reply("❌ Only owner/sudo can use this.")
    uid = m.reply_to_message.from_user.id if m.reply_to_message else (int(m.command[1]) if len(m.command) > 1 else None)
    if not uid:
        return await m.reply("Usage: /rmsudo <id> or reply to user")
    await rm_sudo(uid)
    await m.reply(f"🗑️ Removed sudo user `{uid}`")

@bot.on_message(filters.command("sudolist"))
async def sudolist_cmd(_, m):
    sudos = await get_sudo_list()
    if not sudos:
        return await m.reply("No sudo users added yet.")
    txt = "**👑 Sudo Users:**\n" + "\n".join([f"• `{i}`" for i in sudos])
    await m.reply(txt)

# ----- Badword Commands -----
@bot.on_message(filters.command("add"))
async def add_word(_, m):
    if not await is_sudo(m.from_user.id):
        return await m.reply("❌ Not allowed.")
    word = m.command[1].lower() if len(m.command) > 1 else (m.reply_to_message.text.strip().lower() if m.reply_to_message and m.reply_to_message.text else None)
    if not word:
        return await m.reply("Usage: /add <word> or reply")
    await badword_col.update_one({"word": word}, {"$set": {"word": word}}, upsert=True)
    await m.reply(f"✅ Added badword: `{word}`")

@bot.on_message(filters.command("rm"))
async def rm_word(_, m):
    if not await is_sudo(m.from_user.id):
        return await m.reply("❌ Not allowed.")
    word = m.command[1].lower() if len(m.command) > 1 else (m.reply_to_message.text.strip().lower() if m.reply_to_message and m.reply_to_message.text else None)
    if not word:
        return await m.reply("Usage: /rm <word> or reply")
    await badword_col.delete_one({"word": word})
    await m.reply(f"🗑️ Removed badword: `{word}`")

@bot.on_message(filters.command("list"))
async def list_words(_, m):
    words = await get_badwords()
    if not words:
        return await m.reply("No badwords added yet.")
    txt = "**🧾 Badword List:**\n" + ", ".join(words)
    await m.reply(txt[:4000])

# ----- Log & API -----
@bot.on_message(filters.command("setlog"))
async def set_log(_, m):
    if not await is_sudo(m.from_user.id):
        return await m.reply("❌ Not allowed.")
    if len(m.command) < 2:
        return await m.reply("Usage: /setlog <chat_id>")
    cid = int(m.command[1])
    await settings_col.update_one({"setting": "log_chat"}, {"$set": {"chat_id": cid, "setting": "log_chat"}}, upsert=True)
    await m.reply(f"✅ Log chat set to `{cid}`")

@bot.on_message(filters.command("api"))
async def set_api(_, m):
    global OPENROUTER_KEY
    if not await is_sudo(m.from_user.id):
        return await m.reply("❌ Not allowed.")
    if len(m.command) < 2:
        return await m.reply("Usage: /api <key>")
    OPENROUTER_KEY = m.command[1]
    await m.reply("✅ API key set successfully.")

@bot.on_message(filters.command("stats"))
async def stats_cmd(_, m):
    s = await get_stats()
    # also show a few chats (last 10)
    chats = await chats_col.find().sort("chat_id", -1).to_list(10)
    chat_lines = "\n".join([f"• {c.get('title','-')} (`{c['chat_id']}`)" for c in chats]) or "None"
    txt = (
        "📊 **Guardian Stats**\n\n"
        f"🧹 Total Deletions: `{s['Total']}`\n"
        f"🧠 AI Flags: `{s['AI Flags']}`\n"
        f"💾 DB Matches: `{s['DB Flags']}`\n"
        f"✏️ Edits Caught: `{s['Edits']}`\n"
        f"💬 Known Chats: `{s['Chats']}`\n\n"
    )
    await m.reply(txt)

# ----- Broadcast -----
@bot.on_message(filters.command("broadcast"))
async def broadcast_cmd(_, m):
    if not await is_sudo(m.from_user.id):
        return await m.reply("❌ Only owner/sudo can use this.")
    if len(m.command) < 2 and not m.reply_to_message:
        return await m.reply("Usage: /broadcast <text> or reply to a message to broadcast")
    text = " ".join(m.command[1:]) if len(m.command) > 1 else None
    if m.reply_to_message and not text:
        # broadcast the replied-to message (media or text)
        docs = await chats_col.find().to_list(None)
        sent = 0
        failed = 0
        for c in docs:
            try:
                await m.reply_to_message.copy(chat_id=c["chat_id"])
                   sent += 1
        except Exception:
            failed += 1
    await m.reply(f"Broadcast finished — sent: {sent}, failed: {failed}")

# ----- Sticker pack block/unblock -----
@bot.on_message(filters.command("blockpack"))
async def blockpack_cmd(_, m):
    if not await is_sudo(m.from_user.id):
        return await m.reply("❌ Only owner/sudo can use this.")
    if not m.reply_to_message or not m.reply_to_message.sticker:
        return await m.reply("Reply to a sticker from the pack you want to block.")
    pack = m.reply_to_message.sticker.set_name or m.reply_to_message.sticker.set_name
    if not pack:
        return await m.reply("Could not determine sticker pack name.")
    await blocked_packs_col.update_one({"pack": pack}, {"$set": {"pack": pack}}, upsert=True)
    await m.reply(f"🚫 Blocked sticker pack: `{pack}`")

@bot.on_message(filters.command("unblockpack"))
async def unblockpack_cmd(_, m):
    if not await is_sudo(m.from_user.id):
        return await m.reply("❌ Only owner/sudo can use this.")
    if not m.reply_to_message or not m.reply_to_message.sticker:
        return await m.reply("Reply to a sticker from the pack you want to unblock.")
    pack = m.reply_to_message.sticker.set_name or m.reply_to_message.sticker.set_name
    await blocked_packs_col.delete_one({"pack": pack})
    await m.reply(f"✅ Unblocked sticker pack: `{pack}`")

# ----- Media Cleaner (simple) -----
@bot.on_message(filters.command("cleanmedia"))
async def clean_media_cmd(_, m):
    if not await is_sudo(m.from_user.id):
        return await m.reply("❌ Only owner/sudo can use this.")
    days = int(m.command[1]) if len(m.command) > 1 else 30
    threshold = datetime.utcnow() - timedelta(days=days)
    # This is a best-effort placeholder: Telegram bots cannot search chat history globally.
    await m.reply("🔎 Media cleaner is a best-effort tool. Run it as bot admin in a group to delete old media messages. This command is a placeholder.")

# ==================== Message Watchers ====================
IGNORE_CMDS = [
    "start", "help", "stats", "add", "rm", "list", "setlog",
    "api", "addsudo", "rmsudo", "sudolist", "broadcast", "blockpack", "unblockpack",
]

@bot.on_message((filters.group | filters.private) & ~filters.command(IGNORE_CMDS))
async def scan_message(_, m):
    # Track chat for broadcast/stats
    await track_chat(m)

    # If sticker from blocked pack -> delete
    if m.sticker and m.sticker.set_name:
        blocked = await blocked_packs_col.find_one({"pack": m.sticker.set_name})
        if blocked:
            try:
                await m.delete()
                await send_log(f"Deleted sticker from blocked pack `{m.sticker.set_name}` in chat `{m.chat.id}` by {m.from_user.mention}")
            except:
                pass
            return

    # Prepare text for matching but skip parts coming from user's name/username
    raw_text = (m.text or "")
    if not raw_text:
        # check media NSFW: download and check
        if m.media and (m.photo or m.video or m.document):
            try:
                f = await m.download(as_bytes=True)
                is_nsfw = await ai_media_check(f, m.media.value)
                if is_nsfw:
                    await m.delete()
                    await warn_user(bot, m, "NSFW media removed")
                    await format_and_send_deletion_log(m.chat.id, m, "ai_media", "<media>")
                    await update_stats("ai")
                return
            except Exception:
                return
        return

    text = raw_text.lower()
    # remove occurrences of user's visible names to avoid false flags
    uname = (m.from_user.username or "").lower()
    fname = (m.from_user.first_name or "").lower()
    lname = (m.from_user.last_name or "").lower()
    # create a version without names
    text_no_names = text
    for n in {uname, fname, lname}:
        if n:
            # replace whole-word occurrences and simple substrings to reduce false positives
            text_no_names = re.sub(re.escape(n), "", text_no_names, flags=re.IGNORECASE)

    words = await get_badwords()
    for w in words:
        if w in text_no_names or is_bad_match(w, text_no_names):
            # If AI says this is BAD -> delete and log
            if await ai_check_safe(text):
                await m.delete()
                # Auto-add this word to DB for faster blocking in future
                try:
                    await badword_col.update_one({"word": w}, {"$set": {"word": w}}, upsert=True)
                except:
                    pass
                await warn_user(bot, m, "Bad word detected")
                await format_and_send_deletion_log(m.chat.id, m, "ai", w)
                await update_stats("ai")
            else:
                # AI judged it OK (false positive) -> log safe usage
                await send_log(f"✅ Safe usage ignored: `{raw_text}`")
            return

    # If we reached here no deletion

@bot.on_edited_message(filters.group)
async def edit_scan(_, m):
    # Track chat
    await track_chat(m)

    raw_text = (m.text or "")
    if not raw_text:
        return
    text = raw_text.lower()
    uname = (m.from_user.username or "").lower()
    fname = (m.from_user.first_name or "").lower()
    lname = (m.from_user.last_name or "").lower()
    text_no_names = text
    for n in {uname, fname, lname}:
        if n:
            text_no_names = re.sub(re.escape(n), "", text_no_names, flags=re.IGNORECASE)

    words = await get_badwords()
    for w in words:
        if w in text_no_names or is_bad_match(w, text_no_names):
            if await ai_check_safe(text):
                await m.delete()
                await warn_user(bot, m, "Edited abusive message")
                await format_and_send_deletion_log(m.chat.id, m, "edit", w)
                await update_stats("edit")
            else:
                await send_log(f"✅ Safe edited text ignored: `{raw_text}`")
            return

print("✅ Guardian Bot v3.3 running with extra features...")
bot.run()


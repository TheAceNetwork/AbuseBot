🛡️ Abuse Guardian Bot — Powerful AI Anti-Abuse Telegram Bot

Abuse Guardian Bot ek advanced AI-powered Telegram moderation bot hai jo abusive, sexual, hateful, or NSFW content ko automatically detect karke delete karta hai.
Ye bot hybrid system use karta hai: Custom badword database + AI contextual verification, jisse false positives almost zero ho jaate hain.

🚀 Features
🔥 AI-Powered Message Filtering

GPT-based AI model se text ka deep contextual analysis.

Sirf real abusive messages delete — normal slang/normal words ignore.

📌 Smart Badword System

Database me custom badwords add/remove.

Auto-learning feature: AI detect kare to word DB me auto-add ho sakta hai.

🛑 Advanced Pattern Detection

Detects disguised words like:
m*ch, m.c, m/c, m c, m..c, etc.

🎨 NSFW Media Detection (placeholder ready)

Image/video/document NSFW detection function present.

Easily add OpenAI, SightEngine, etc.

🤖 Sudo System

Unlimited sudo users add/remove.

Owner + sudos = full control.

🗑️ Message Edit Protection

User ne edit karke badword use kiya → instant delete + log.

🔥 Sticker Pack Blocking System

Entire sticker packs block/unblock.

Blocked pack ka koi sticker aaya → auto delete.

📊 Live Stats Dashboard

Total deletions

AI flags

DB matches

Edited message violations

Known chats list

🔗 Broadcast System

All chats/groups me DM-like broadcast.

📥 Custom Logging System

Har violation ka log ek dedicated log chat me send.

🛡 Chat Tracker

Bot jaha bhi message dekhta hai, us chat ko auto-save karta hai (for broadcast & stats).

⚙️ Commands
👑 Owner / Sudo Commands
Command	Description
/addsudo <id/reply>	Add sudo user
/rmsudo <id/reply>	Remove sudo
/sudolist	Show sudo users
/setlog <chat_id>	Set log chat
/api <key>	Set OpenRouter API Key
/broadcast <text>	Broadcast to all chats
/blockpack (reply sticker)	Block sticker pack
/unblockpack (reply sticker)	Unblock pack
📝 Badword Control
Command	Description
/add <word>	Add badword
/rm <word>	Remove badword
/list	Show badword list
ℹ️ General
Command	Description
/start	Start message
/help	Help menu
/stats	Show moderation stats
/cleanmedia <days>	Placeholder — clean old media
🛠️ Setup & Installation
1️⃣ Requirements

Python 3.9+

MongoDB Database

Telegram Bot Token (BotFather se)

API_ID + API_HASH (my.telegram.org)

Optional: OpenRouter API key (AI moderation)

2️⃣ Install Libraries
pip install -r requirements.txt

3️⃣ Fill config.py

Example:

API_ID = 12345
API_HASH = "your_api_hash"
BOT_TOKEN = "12345:ABCDEF"
MONGO_URI = "mongodb+srv://..."
OWNER_ID = 123456
OPENROUTER_KEY = ""
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
WARN_DELETE_DELAY = 7

4️⃣ Run Bot
python3 bot.py

🧠 AI Logic (How It Works)

User sends message → bot cleans username/first/last names for accuracy.

Bot checks against badword DB.

If match milta hai → AI se verify:

AI returns BAD → delete + warn + log

AI returns OK → ignore (normal usage)

Editing system & sticker blocking background me continuously run hote hain.

📡 Logging System

Har delete event ka log automatically send hota hai:

User

Chat

Time

Reason

Matched word

Full message content

🧑‍💻 Developer Notes

Media NSFW detection placeholder hai — easily upgradeable.

Auto-DB learning enabled.

Highly modular and customizable architecture.

Real-time group protection with minimum false positives.

⭐ Credits

Built with ❤️ by @TrueNakshu
Support: https://t.me/hellbotsupport

Updates: https://t.me/TheAceUpdates

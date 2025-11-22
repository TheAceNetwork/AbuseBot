# 🛡️ **Abuse Guardian Bot**
### **AI-Powered Telegram Moderation Bot for Real-Time Abuse Protection**

A next-gen AI moderation bot jo Telegram groups ko **abusive, hateful, sexual, toxic** messages se real-time protect karta hai.  
Hybrid system: **Badword DB + AI Context Analyzer = Almost Zero False Positives ⚡**

---

## 🚀 **Key Features**

### 🔥 **AI-Powered Message Filtering**
- GPT-based contextual analysis  
- Real abusive message → auto delete  
- Normal slang → ignored  

### 📌 **Smart Badword Engine**
- Custom badword DB (add/remove anytime)  
- Pattern detection like: `m*ch`, `m.c`, `m..c`, `m c`  
- Auto-learning mode (optional)

### 🛑 **Advanced Protection**
- Edited message scanning  
- Sticker pack blocking  
- Media NSFW placeholder (ready for integration)

### 📊 **Live Stats Dashboard**
- Total deletions  
- AI flags  
- DB matches  
- Edited violations  
- Known chats  

### 🤖 **Full Sudo System**
- Unlimited sudo users  
- Owner & sudo users have full control  

---

## ⚙️ **Commands Overview**

### 👑 **Owner / Sudo Commands**
| Command | Description |
|--------|-------------|
| `/addsudo <id/reply>` | Add sudo user |
| `/rmsudo <id/reply>` | Remove sudo user |
| `/sudolist` | Show sudo list |
| `/setlog <chat_id>` | Set log channel |
| `/api <key>` | Set OpenRouter API key |
| `/broadcast <text>` | Send message to all chats |
| `/blockpack` | Block sticker pack |
| `/unblockpack` | Unblock sticker pack |

### 📝 **Badword Control**
| Command | Description |
|--------|-------------|
| `/add <word>` | Add badword |
| `/rm <word>` | Remove badword |
| `/list` | Show all badwords |

### ℹ️ **General Commands**
| Command | Description |
|--------|-------------|
| `/start` | Start message |
| `/help` | Help menu |
| `/stats` | Moderation stats |
| `/cleanmedia` | Clean old media (placeholder) |

---

## 🛠️ **Setup & Installation**

### **1️⃣ Install Requirements**
```bash
pip install -r requirements.txt
2️⃣ Fill config.py
python
Copy code
API_ID = 12345
API_HASH = "your_api_hash"
BOT_TOKEN = "12345:ABCDEF"
MONGO_URI = "mongodb+srv://..."
OWNER_ID = 123456
OPENROUTER_KEY = ""
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
WARN_DELETE_DELAY = 7
3️⃣ Run the Bot
python3 bot.py ```
🧠 AI Logic Flow
text
Copy code
User message → clean text
      ↓
DB match check
      ↓
If match → AI verification
      ↓
AI says BAD → delete + warn + log
AI says OK → ignore
      ↓
Edited messages + sticker violations also scanned (background)
📡 Logging System
text
Copy code
Each deletion log includes:

• User
• Chat
• Time
• Reason
• Matched word
• Full message
🧑‍💻 Developer Notes
text
Copy code
• NSFW media detection module (placeholder-ready)
• Highly modular architecture
• Auto-learning badword DB
• Fully customizable moderation system
⭐ Credits
text
Copy code
Built with ❤️ by @TrueNakshu
Support: https://t.me/hellbotsupport
Updates: https://t.me/TheAceUpdates

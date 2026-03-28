# Claude API - Phone Access Setup

Use Claude from your phone via web interface running on your Mac mini, powered by API credits instead of your usage limit account.

## 🎯 What This Does

- Runs Claude backend on your Mac mini (never sleeps)
- Access from phone on same network or remotely via ngrok
- Uses your $25 API credit balance (no usage limits!)
- Clean web interface optimized for mobile
- Optional iMessage remote control integration

## 📋 Prerequisites

1. **Claude API Key** - Get from [Anthropic Console](https://console.anthropic.com/)
2. **Python 3.8+** - Already installed on Mac
3. **Mac mini** (always on, or at least when you need it)
4. **Phone on same WiFi** - Or use ngrok for remote access

## 🚀 Quick Start (5 minutes)

### 1. Install Backend Dependencies

```bash
cd /Users/genesisai/portfolio/claude-api-phone-access/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Go to parent directory
cd ..

# Copy example env file
cp .env.example .env

# Edit .env and add your Claude API key
# CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx
nano .env
```

Get your API key from: https://console.anthropic.com/account/keys

### 3. Start the Server

```bash
cd backend
source venv/bin/activate
python app.py
```

You'll see:
```
Starting Claude API server on port 5000
Access from phone at: http://<your-mac-ip>:5000
```

### 4. Access from Phone

#### Same Network:
1. Find your Mac's IP: Open Terminal, run `ifconfig | grep "inet "`
2. Look for IP on your local network (like `192.168.x.x` or `10.0.x.x`)
3. On phone browser, go to: `http://<that-ip>:5000`

#### Remote Access (Using ngrok):
```bash
# Install ngrok from https://ngrok.com
brew install ngrok

# In a new terminal, run:
ngrok http 5000

# You'll get a URL like: https://xxxx-xx-xxx-xxx-xxx.ngrok.io
# Use this on your phone from anywhere!
```

## 💬 How to Use

1. Open web UI from phone
2. Type your question
3. Claude responds using your API credits
4. Conversation history saved auto matically

## 📱 Features

✅ **Mobile-optimized** - Works great on phone  
✅ **Multiple conversations** - Keep different chats separate  
✅ **Auto-save history** - All conversations saved locally  
✅ **Real-time typing** - Shows typing indicator  
✅ **Error handling** - Clear error messages  
✅ **Health check** - Auto-detects disconnections  

## 🎮 Optional: iMessage Remote Control

Send commands via iMessage from your phone:

```bash
python imessage-integration/imessage_controller.py \
  "+1234567890" \
  "@claude chat What is Claude?"
```

Available commands:
- `@claude chat [question]` - Ask Claude something
- `@claude status` - Check if server is running
- `@claude clear` - Clear conversation history

## 🔒 Security Notes

- Keep `.env` file private (contains API key)
- ngrok URL is semi-public - treat like password
- Only run on trusted networks
- Consider adding auth if needed

## 💰 Cost Tracking

Each API call uses your $25 credit:
- Short responses ~$0.01-0.05
- With $25, you get thousands of interactions
- Monitor at: https://console.anthropic.com/account/usage

## 🛟 Troubleshooting

### "Connection refused" on phone
- [ ] Check Mac IP address matches (run `ifconfig`)
- [ ] Make sure backend is running
- [ ] Phone on same WiFi network

### "API key not found" error
- [ ] Check `.env` file exists
- [ ] Verify `CLAUDE_API_KEY=sk-ant-...` is set
- [ ] Restart backend after saving `.env`

### Server won't start
- [ ] Check port 5000 not in use: `lsof -i :5000`
- [ ] Python 3.8+ required: `python3 --version`
- [ ] Try different port: `PORT=8000 python app.py`

### ngrok not working
- [ ] Check internet connection
- [ ] Restart ngrok
- [ ] Free tier may require re-auth after 2 hours

## 🏗️ Project Structure

```
claude-api-phone-access/
├── backend/
│   ├── app.py              # Main Flask server
│   ├── requirements.txt    # Python dependencies
│   ├── venv/              # Virtual environment
│   └── conversation_history.json  # Auto-saved chats
├── frontend/
│   └── index.html         # Mobile web UI
├── imessage-integration/
│   └── imessage_controller.py     # iMessage commands
├── .env                   # Your API key (gitignored)
├── .env.example          # Template
└── README.md             # This file
```

## 🎓 Next Steps

1. **Test locally first** - Use same Mac before trying phone
2. **Keep Mac mini on** - Set to never sleep in System Preferences
3. **Bookmark the URL** - For quick access on phone
4. **Try ngrok** - For true remote access from anywhere

## 📚 API Reference

### Chat Endpoint
```bash
POST /api/chat
{
  "message": "Your question",
  "conversation_id": "default"
}
```

### Get History
```bash
GET /api/conversation/default
```

### Clear All
```bash
POST /api/clear
```

---

**Ready?** Start the backend and open http://your-mac-ip:5000 on your phone!

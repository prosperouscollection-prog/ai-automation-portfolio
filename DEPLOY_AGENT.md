# Deploy Claude API Phone Access - Automated Setup

Use the automated deployment agent to set up your Claude API phone access in one command!

## 🚀 Quick Start (90 seconds)

### Option 1: Bash Script (Recommended for Mac)

```bash
cd /Users/genesisai/portfolio
bash deploy.sh
```

### Option 2: Python Script (More Detailed)

```bash
cd /Users/genesisai/portfolio
python3 deploy.py
```

Both scripts do the same thing - choose based on your preference!

## 📋 What the Deployment Agent Does

1. ✅ Checks Python 3.8+ is installed
2. ✅ Creates virtual environment
3. ✅ Installs dependencies (Flask, Anthropic, etc.)
4. ✅ Prompts for Claude API key securely
5. ✅ Verifies API key works
6. ✅ Creates `.env` file with your key
7. ✅ Guides Mac setup (never sleep settings)
8. ✅ Shows how to access from phone
9. ✅ Offers to start server immediately

## 🎯 Step-by-Step

### Step 1: Open Terminal
```bash
cd /Users/genesisai/portfolio
```

### Step 2: Run Deployment
```bash
bash deploy.sh
# or
python3 deploy.py
```

### Step 3: Answer Prompts
- Confirm you want to deploy
- Enter your Claude API key (won't be displayed)
- Confirm Mac sleep settings
- Decide if you want to start server now

### Step 4: Get Your Mac IP
The script will show you where to find it, or run:
```bash
ifconfig | grep -E "inet " | grep -v 127.0.0.1
```

### Step 5: Access from Phone
On your phone browser, visit:
```
http://192.168.x.x:5000
```
(Replace with your actual Mac IP from Step 4)

## 🛠️ Comparing the Two Scripts

| Feature | `deploy.sh` | `deploy.py` |
|---------|-----------|-----------|
| Speed | ⚡ Fast | ⏳ Slightly slower |
| Output | 🎨 Colorful | 📊 Detailed |
| API Key Test | Basic | ✅ Tests connection |
| Mac guidance | Simple | ✅ Detailed |
| Error handling | Good | ✅ Better |
| Platform | macOS best | ✅ Cross-platform |
| Complexity | Simple | More features |

**Recommendation**: Use `deploy.sh` for quick setup. Use `deploy.py` if you want more detailed checks.

## 🔄 After Deployment

### Start server again later:
```bash
cd /Users/genesisai/portfolio/claude-api-phone-access/backend
source venv/bin/activate
python app.py
```

### Change port:
```bash
PORT=8000 python app.py
```

### Reconfigure API key:
```bash
# Edit the file
nano /Users/genesisai/portfolio/claude-api-phone-access/.env

# Update CLAUDE_API_KEY value
```

## 💰 Monitor Your Credit

After deployment, track your API usage at:
https://console.anthropic.com/account/usage

Estimated costs:
- Short response: $0.01
- Medium response: $0.05  
- Long response: $0.10
- With $25 credit: ~250 conversations

## 🎯 First Test

1. Open browser on phone
2. Type: "What is an AI agent?"
3. Send
4. You should get a response in 1-3 seconds
5. ✅ Everything is working!

## 🌍 Remote Access (Anywhere)

Want to use from outside your WiFi?

### Option 1: ngrok (Easiest)
```bash
# Install (one time)
brew install ngrok

# In new terminal
ngrok http 5000

# You'll get URL like: https://abc123.ngrok.io
# Use that on phone from anywhere!
```

### Option 2: Cloud VPS
Deploy backend to cloud (Heroku, Replit, etc.)

### Option 3: VPN
Set up VPN on Mac and phone

## ⚙️ Mac Settings (Important)

After deployment, configure Mac to never sleep:

1. Apple menu → System Settings
2. Energy Saver or Battery
3. "Turn display off after" → Never
4. "Put computer to sleep" → Never
5. ✅ Check "Prevent computer from sleeping when plugged in"

Without these settings, the server stops when Mac sleeps!

## 🐛 Troubleshooting

### "Python 3 not found"
```bash
# Install Python
brew install python3

# Then run deploy script again
```

### "Permission denied" on deploy.sh
```bash
# Make it executable
chmod +x /Users/genesisai/portfolio/deploy.sh

# Then run
bash deploy.sh
```

### "API key not valid" error
1. Go to https://console.anthropic.com/account/keys
2. Create a new key if needed
3. Make sure key starts with `sk-ant-`
4. Verify you have API credit balance
5. Run deployment again

### "Port 5000 in use"
```bash
# Find what's using it
lsof -i :5000

# Kill it
kill -9 <PID>

# Or use different port
PORT=8000 python app.py
```

### "Can't reach from phone"
- ✓ Phone on same WiFi as Mac?
- ✓ Mac IP address correct?
- ✓ Server running? (Check terminal)
- ✓ Firewall blocking 5000?
  - System Settings → Security & Privacy
  - Check firewall status

### "Mac going to sleep"
- System Settings → Energy Saver
- Disable "Put computer to sleep"
- Check "Prevent computer from sleeping when plugged in"

## 📚 What Gets Installed

The deployment agent installs these packages:

```
Flask==3.0.0           # Web framework
Flask-CORS==4.0.0      # Cross-origin requests
anthropic==0.25.0      # Claude API client
python-dotenv==1.0.0   # Environment variables
```

Total size: ~50-100 MB in virtual environment

## 🎓 After First Deployment

1. ✅ Set Mac to never sleep
2. ✅ Test from phone once
3. ✅ (Optional) Set up ngrok for remote
4. ✅ (Optional) Import chat history
5. ✅ Start building!

## 📖 Documentation

Full documentation available:
- [README.md](claude-api-phone-access/README.md) - Complete overview
- [SETUP_STEPS.md](claude-api-phone-access/SETUP_STEPS.md) - Manual setup
- [IMPORT_GUIDE.md](../IMPORT_GUIDE.md) - Import chat history

## ❓ Common Questions

**Q: Does my Mac need to stay on?**
A: Yes! For 24/7 access. Set it to never sleep.

**Q: Is my API key safe?**
A: Yes! Stored in `.env` with 600 permissions (only you can read).

**Q: How much does this cost?**
A: Uses your $25 API credit. Roughly $0.01 per response.

**Q: Can I use from outside my WiFi?**
A: Yes! Use ngrok tunnel or deploy to cloud.

**Q: Can I import old conversations?**
A: Yes! See [IMPORT_GUIDE.md](../IMPORT_GUIDE.md)

**Q: What if API key fails?**
A: Get new key from console.anthropic.com and redeploy.

---

**Ready?** Run `bash deploy.sh` and you'll be chatting with Claude on your phone in 2 minutes! 🚀

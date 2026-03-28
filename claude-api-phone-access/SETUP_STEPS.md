# Complete Setup Steps - Claude API Phone Access

## Step 1: Get Your API Key ✅

1. Go to https://console.anthropic.com/account/keys
2. Click "Create Key"
3. Copy the key (starts with `sk-ant-`)
4. Keep it safe - don't share this!

**Status**: You said you already have an API key, so skip this if you already have one.

## Step 2: Prepare Your Mac Mini 🖥️

**Make sure your Mac mini:**
- [ ] Is powered on and connected to WiFi
- [ ] Won't sleep unexpectedly
  - System Preferences → Energy Saver → Never put display to sleep / Prevent computer from sleeping
- [ ] Has Python 3.8+ installed (should already have it)
- [ ] Can be reached from your phone's WiFi network

Check Python version:
```bash
python3 --version
```

Should show `Python 3.x.x`

## Step 3: Install Backend (5 minutes) 🚀

Open Terminal on your Mac:

```bash
# Navigate to backend folder
cd /Users/genesisai/portfolio/claude-api-phone-access/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

You should see it installing Flask, Anthropic, etc.

## Step 4: Set Your API Key 🔑

```bash
# Go back to main folder
cd ..

# Create .env file from example
cp .env.example .env

# Open it in editor
nano .env
```

You'll see:
```
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx
```

Replace `sk-ant-xxxxxxxxxxxxx` with your actual key. Then:
- Press `Ctrl + X`
- Press `Y` (yes)
- Press `Enter` (save)

## Step 5: Start the Server 🎯

```bash
cd backend
source venv/bin/activate
python app.py
```

You should see:
```
Starting Claude API server on port 5000
Access from phone at: http://<your-mac-ip>:5000
```

**Keep this Terminal window open!**

## Step 6: Find Your Mac's IP Address 🌐

In a **new Terminal window**:

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Look for something like:
- `192.168.1.x`
- `10.0.0.x`

This is your Mac's local IP. Let's call it `YOUR_MAC_IP`.

## Step 7: Access From Phone 📱

### Option A: Same WiFi Network (Easiest)

1. Make sure phone is on **same WiFi** as Mac
2. Open phone browser
3. Go to: `http://YOUR_MAC_IP:5000`
   - Replace `YOUR_MAC_IP` with actual IP (e.g., `http://192.168.1.100:5000`)
4. You should see the Claude chat interface!

### Option B: Remote Access with ngrok

For access from anywhere (not just your WiFi):

```bash
# Install ngrok (one time)
brew install ngrok

# In a NEW terminal window, run:
ngrok http 5000
```

You'll see something like:
```
Forwarding                    https://abc123-def456.ngrok.io -> http://localhost:5000
```

Copy that URL and use it on your phone from anywhere!

## Step 8: Test It! 🧪

1. Open the webpage on your phone
2. Type a simple question: "Hello, who are you?"
3. Click Send
4. Claude should respond!

If it works, you're done! 🎉

## Step 9 (Optional): Set Up as Auto-Start 🔄

So server starts automatically when Mac restarts:

1. Create `start-claude.command` file on Desktop:
```bash
#!/bin/bash
cd /Users/genesisai/portfolio/claude-api-phone-access/backend
source venv/bin/activate
python app.py
```

2. Make it executable:
```bash
chmod +x ~/Desktop/start-claude.command
```

3. System Preferences → General → Login Items → + button → Select `start-claude.command`

## Step 10 (Optional): Phone Bookmark 🔖

On your phone:
1. Open the Claude URL in Safari
2. Tap Share button
3. Add to Home Screen
4. Now it looks like an app!

## Monitoring Your Credit Usage 💰

Track how much of your $25 you're using:
1. Go to https://console.anthropic.com/account/usage
2. Each message costs small amount (~$0.01-0.10)
3. At current rate, you'll get many conversations

## Troubleshooting Checklists

### Not loading on phone?
- [ ] Phone and Mac on same WiFi? (Check WiFi settings)
- [ ] Server still running on Mac? (Check first Terminal window)
- [ ] Correct IP address used?
- [ ] Firewall blocking port 5000? Try: `System Pref → Security & Privacy`

### "API key not valid" error?
- [ ] Copy entire key from console.anthropic.com?
- [ ] Pasted into `.env` file correctly?
- [ ] Restarted backend after editing `.env`?

### Server is slow?
- [ ] Check internet connection
- [ ] Claude takes ~1-3 seconds to respond (normal)
- [ ] Try shorter questions first

### Can't find Mac IP?
```bash
# Try this command
hostname -I
# or
_mdns-sd browse _http._tcp . | grep mac
```

## Already Have ngrok? 🌍

If you want remote access and want to set it up properly:

```bash
# Sign up free at ngrok.com
# Download and authenticate
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Then just run:
ngrok http 5000

# Share the URL with yourself and use from phone
```

---

**You're all set!** The server is running on your $25 API credit and you can chat with Claude from your phone. 🎉

Need help? Check README.md or see Troubleshooting section above.

# Telegram Bot Diagnostic & Fix

## Status Check

### ✅ Completed
- [x] Webhook is set: `setWebhook` returned `ok:true`
- [x] Demo server is running on Render
- [x] Telegram endpoint exists: `/telegram/webhook`
- [x] Bot token is syntactically valid

### ⚠️ To Verify
- [ ] TELEGRAM_BOT_TOKEN on Render (check if set)
- [ ] TELEGRAM_CHAT_ID on Render (check if set)
- [ ] Bot can send test message to your chat

## Root Cause: Environment Variables on Render

1. Secrets in GitHub ≠ Environment vars on Render
2. You must explicitly link or add secrets to Render
3. Without `TELEGRAM_CHAT_ID`, webhook receives messages but rejects them (security check at line 974 of server.js)

## Fix Steps

### Step 1: Get Your Chat ID
```bash
# If you don't have it, open Telegram and:
# 1. Search for @userinfobot
# 2. Send any message
# 3. Reply will show your User ID (this is TELEGRAM_CHAT_ID)
```

### Step 2: Verify GitHub Secrets
```bash
gh secret list | grep TELEGRAM
```
You should see:
- `TELEGRAM_BOT_TOKEN` 
- `TELEGRAM_CHAT_ID`

### Step 3: Add to Render Dashboard
1. Go to https://dashboard.render.com
2. Find your app: `genesis-ai-systems-demo`
3. Go to **Environment** tab
4. Add these manual environment variables:
   - Key: `TELEGRAM_BOT_TOKEN` → Value: `8785951790:AAH6EpabJeUnig5w8XyQayn-J5vldvFZ9Fg`
   - Key: `TELEGRAM_CHAT_ID` → Value: `<YOUR_CHAT_ID>`
5. Click "Deploy" to apply changes

### Step 4: Test the Bot
1. Open Telegram
2. Find `@GenesisAISystemsBot`
3. Send `/start`
4. Wait for the command menu to appear

## Command Reference

| Command | What it does |
|---------|-------------|
| `/start` | Show main menu |
| `/status` | Check all systems |
| `/leads` | See today's leads |
| `/deploy` | Deploy the website |
| `/agents` | Check running agents |
| `/report` | Weekly summary |
| `/help` | Show all commands |

## Still Not Working?

Check the Render logs:
```bash
# View Render logs for errors
# Go to https://dashboard.render.com and click your app's "View logs" button
```

Look for messages like:
- `Telegram token not configured` → TELEGRAM_BOT_TOKEN is missing
- `Rejected Telegram from XXXX` → TELEGRAM_CHAT_ID doesn't match
- `Telegram webhook error` → See error details in logs

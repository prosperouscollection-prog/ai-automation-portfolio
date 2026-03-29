# Telegram Bot Setup — Genesis AI Systems

## Step 1: Create the bot

1. Open Telegram
2. Search for `@BotFather`
3. Send `/newbot`
4. Name it `Genesis AI Systems`
5. Pick a username like `GenesisAISystemsBot`
6. Copy the bot token right away

## Step 2: Get your Chat ID

1. Search for `@userinfobot`
2. Send any message
3. Copy your ID number

## Step 3: Add to GitHub secrets

```bash
gh secret set TELEGRAM_BOT_TOKEN --body "your_bot_token"
gh secret set TELEGRAM_CHAT_ID --body "your_chat_id"
```

## Step 4: Add to Render

- `TELEGRAM_BOT_TOKEN=your_token`
- `TELEGRAM_CHAT_ID=your_chat_id`

## Step 5: Set the webhook

```bash
curl -X POST "https://api.telegram.org/bot[YOUR_TOKEN]/setWebhook" \
  -d "url=https://genesis-ai-systems-demo.onrender.com/telegram/webhook"
```

## Step 6: Test it

Open Telegram.  
Find your bot.  
Send `/start`.

You should see the Genesis AI Systems menu.

## What you can do from Telegram

- See all leads with one tap
- Deploy the site with one tap
- Trigger any agent instantly
- Get weekly reports
- Find new prospects
- Run sales follow-ups
- Check system health

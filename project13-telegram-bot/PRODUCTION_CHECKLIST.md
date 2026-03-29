# Production Checklist — A Private Chat App for Your Business

## Setup
- [ ] Bot created via @BotFather
- [ ] Bot token saved (`TELEGRAM_BOT_TOKEN`)
- [ ] Your chat ID obtained from @userinfobot (`TELEGRAM_CHAT_ID`)
- [ ] Secrets added to GitHub (`gh secret set`)
- [ ] **Environment variables added to Render dashboard** ⚠️ IMPORTANT
  - [ ] `TELEGRAM_BOT_TOKEN` set on Render
  - [ ] `TELEGRAM_CHAT_ID` set on Render
- [ ] Webhook URL set (with single quotes):
  ```bash
  curl -X POST 'https://api.telegram.org/bot<TOKEN>/setWebhook' \
    -d 'url=https://genesis-ai-systems-demo.onrender.com/telegram/webhook'
  ```

## Testing
- [ ] Bot responds to `/start` command
- [ ] Command menu appears with all buttons
- [ ] `/status` shows system health
- [ ] `/leads` shows today's leads
- [ ] `/deploy` button triggers deployment
- [ ] Buttons send correct callback data
- [ ] Messages appear within 2 seconds
- [ ] Error messages appear in Render logs

## Commands Verified
- [ ] `/start` - Main menu
- [ ] `/status` - System health  
- [ ] `/leads` - Today's leads
- [ ] `/deploy` - Deploy site
- [ ] `/agents` - Running agents
- [ ] `/report` - Weekly report
- [ ] `/prospects` - New prospects
- [ ] `/content` - Content ideas
- [ ] `/revenue` - Revenue summary
- [ ] `/clients` - All clients
- [ ] `/followup` - Follow-up tasks
- [ ] `/help` - Show all commands

## Troubleshooting
- [ ] Check Render env vars via dashboard
- [ ] Review Render logs for errors
- [ ] Use TELEGRAM_DIAGNOSTIC.md for issues
- [ ] Use correct chat ID (not user ID prefix)

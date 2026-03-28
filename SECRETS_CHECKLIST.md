# Genesis AI Systems — SECRETS & OPERATIONS CHECKLIST

> This checklist ensures all secrets are configured and all notification, demo, email, SMS, and agent systems are operational. Designed for **Genesis AI Systems** ([genesisai.systems](https://genesisai.systems)).
> 
> _Founder: Trendell Fordham_

---

## 1. REQUIRED SECRETS

- [ ] `ANTHROPIC_API_KEY`           
- [ ] `OPENAI_API_KEY`              
- [ ] `TWILIO_ACCOUNT_SID`          
- [ ] `TWILIO_AUTH_TOKEN`           
- [ ] `TWILIO_FROM_NUMBER`          
- [ ] `ALERT_PHONE_NUMBER`          
- [ ] `SENDGRID_API_KEY`            
- [ ] `SENDGRID_FROM_EMAIL`         
- [ ] `SENDGRID_FROM_NAME`          
- [ ] `SITE_URL`                    
- [ ] `NOTIFICATION_EMAIL`          
- [ ] `CALENDLY_URL`                
- [ ] `N8N_WEBHOOK_BASE_URL`        
- [ ] `DEMO_SERVER_URL`             
- [ ] `VAPI_PUBLIC_KEY`             
- [ ] `RAILWAY_TOKEN`               

## 2. OPTIONAL SECRETS

- [ ] `SLACK_WEBHOOK_URL`            

## 3. VERIFICATION & TESTS

- [ ] Test SMS delivery to **(313) 400-2575** using test script
- [ ] Test email delivery to **info@genesisai.systems** using test script
- [ ] Test Slack notification (if webhook exists)
- [ ] Security agent passing: ![Security](https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/security_agent.yml/badge.svg)
- [ ] QA agent passing: ![QA](https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/qa_agent.yml/badge.svg)
- [ ] Evolution agent daily completion
- [ ] Deploy agent passes on latest deployment
- [ ] All 8 live demos working and accessible
- [ ] `genesisai.systems` loads with status `200 OK`
- [ ] System health badge present in README
- [ ] All action scripts tested (see SETUP_GUIDE.md Section 9)

## 4. GITHUB REPO SECRETS LOCATION

> Add/update all secrets here:  
> [github.com/prosperouscollection-prog/ai-automation-portfolio/settings/secrets/actions](https://github.com/prosperouscollection-prog/ai-automation-portfolio/settings/secrets/actions)

---

## 5. DOCUMENTATION & RESOURCES

- [SETUP_GUIDE.md](./SETUP_GUIDE.md) — Full secrets, integration, and testing walkthrough.
- [README.md](./README.md) — Status badges, agent summary, and system health.
- [scripts/notify.py](.github/workflows/scripts/notify.py) — Notification logic (testable with `--test-sms`, `--test-email`, `--test-slack`).
- [scripts/test_notifications.py](.github/workflows/scripts/test_notifications.py) — Test all notification channels and confirm operational status.

---

## 6. TROUBLESHOOTING

- Double-check all values for typos in GitHub Secrets
- Use `.env` file for local CLI tests
- Confirm verified email and phone in Twilio/SendGrid
- Check workflow run logs for agent errors: [Actions workflow results](https://github.com/prosperouscollection-prog/ai-automation-portfolio/actions)

---

#### Genesis AI Systems | Detroit, MI  
**Founder:** Trendell Fordham  
info@genesisai.systems • (313) 400-2575

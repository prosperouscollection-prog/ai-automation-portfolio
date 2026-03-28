#!/bin/bash

# Genesis AI Systems — Interactive Setup Script
# https://genesisai.systems
# Trendell Fordham, Founder
# Last updated: 2024-06

RESET='\033[0m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
BOLD='\033[1m'

STEP=1
TOTAL=10

function print_success() {
    echo -e "${GREEN}$1${RESET}"
}

function print_error() {
    echo -e "${RED}$1${RESET}"
}

function print_info() {
    echo -e "${BLUE}$1${RESET}"
}

function prompt_continue() {
    read -p "Press Enter to continue..."
}

function check_command() {
    command -v "$1" >/dev/null 2>&1
}

function step_complete() {
    echo -e "${GREEN}Step $STEP of $TOTAL complete${RESET}\n"
    ((STEP++))
}

function open_url() {
    # Cross-platform: macOS (open), Linux (xdg-open)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$1" >/dev/null 2>&1
    else
        xdg-open "$1" >/dev/null 2>&1
    fi
}

######################
# 1. Check Dependencies
######################
print_info "\n--- Step 1: Checking system dependencies ---"
missing=0
for CMD in python3 pip3 git node; do
    if check_command "$CMD"; then
        print_success "[OK] $CMD found"
    else
        print_error "[ERROR] $CMD is missing. Please install it before continuing."
        missing=1
    fi
done

if [[ $missing -ne 0 ]]; then
    print_error "Please install all missing dependencies and rerun setup.sh."
    exit 1
fi
step_complete

##############################
# 2. Install Python Packages
##############################
print_info "--- Step 2: Installing Python dependencies ---"
REQ_FILE=".github/workflows/scripts/requirements.txt"
if [[ ! -f "$REQ_FILE" ]]; then
    print_error "requirements.txt not found at $REQ_FILE!"
    exit 1
fi
pip3 install --upgrade pip >/dev/null
pip3 install -r "$REQ_FILE"
if [[ $? -ne 0 ]]; then
    print_error "Failed to install Python dependencies. Check error messages above."
    exit 1
fi
print_success "Python dependencies installed."
step_complete

#######################################
# 3. Create .env Template (if missing)
#######################################
print_info "--- Step 3: Creating .env template ---"
ENV_FILE=".env"
if [[ -f "$ENV_FILE" ]]; then
    print_info ".env already exists. Skipping template creation."
else
    cat > "$ENV_FILE" <<EOL
# --- Genesis AI Systems Project ---
# All sensitive credentials go here. See SETUP_GUIDE.md

ANTHROPIC_API_KEY=
OPENAI_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
ALERT_PHONE_NUMBER=+13134002575
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=info@genesisai.systems
SENDGRID_FROM_NAME=Genesis AI Systems
SITE_URL=https://genesisai.systems
NOTIFICATION_EMAIL=info@genesisai.systems
CALENDLY_URL=https://calendly.com/genesisai-info-ptmt/free-ai-demo-call
N8N_WEBHOOK_BASE_URL=https://n8n.genesisai.systems
DEMO_SERVER_URL=
VAPI_PUBLIC_KEY=
RAILWAY_TOKEN=
SLACK_WEBHOOK_URL=
EOL
    print_success ".env template created. Please fill in your environment variables after setup."
fi
step_complete

############################################
# 4. Guide: Twilio Account Setup
############################################
print_info "--- Step 4: Twilio Setup ---"
echo "A Twilio account is required for SMS alerts."
echo "Signup: https://www.twilio.com/try-twilio"
open_url "https://www.twilio.com/try-twilio"
echo "- Verify phone: (313) 400-2575"
echo "- Get a Twilio phone number"
echo "- Find SID/Auth Token in the dashboard"
echo "- Record: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, ALERT_PHONE_NUMBER"
prompt_continue
step_complete

############################################
# 5. Guide: SendGrid Account Setup
############################################
print_info "--- Step 5: SendGrid Setup ---"
echo "A SendGrid account is required for email notifications."
echo "Signup: https://signup.sendgrid.com/"
open_url "https://signup.sendgrid.com/"
echo "- Verify: info@genesisai.systems"
echo "- Create API key with 'Mail Send' scope"
echo "- Add DNS validation via Cloudflare if needed"
echo "- Record: SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME"
prompt_continue
step_complete

############################################
# 6. Guide: (Optional) Slack Setup
############################################
print_info "--- Step 6: Slack Setup (optional) ---"
echo "Configure a Slack channel for system alerts (optional)"
echo "- Create workspace: Genesis AI Systems"
echo "- Channel: #system-alerts"
echo "- Create Slack App: https://api.slack.com/apps"
echo "- Enable Incoming Webhooks, add to channel"
open_url "https://api.slack.com/apps"
echo "- Record: SLACK_WEBHOOK_URL (optional)"
prompt_continue
step_complete

############################################
# 7. Anthropic & OpenAI API Keys
############################################
print_info "--- Step 7: API Credentials ---"
echo "Register and obtain your AI API keys:"
echo "- Anthropic: https://console.anthropic.com/settings/keys"
echo "- OpenAI: https://platform.openai.com/api-keys"
open_url "https://console.anthropic.com/settings/keys"
open_url "https://platform.openai.com/api-keys"
echo "- Record: ANTHROPIC_API_KEY, OPENAI_API_KEY"
prompt_continue
step_complete

############################################
# 8. Test Notification Channels
############################################
print_info "--- Step 8: Testing notification channels ---"
echo "We'll now test your notification setup."
python3 .github/workflows/scripts/notify.py --test-sms
SMS_STATUS=$?
python3 .github/workflows/scripts/notify.py --test-email
EMAIL_STATUS=$?
python3 .github/workflows/scripts/notify.py --test-slack
SLACK_STATUS=$?

if [[ $SMS_STATUS -eq 0 ]]; then
  print_success "SMS test: Success"
else
  print_error "SMS test: Failure"
fi
if [[ $EMAIL_STATUS -eq 0 ]]; then
  print_success "Email test: Success"
else
  print_error "Email test: Failure"
fi
if [[ $SLACK_STATUS -eq 0 ]]; then
  print_success "Slack test: Success"
else
  print_info "Slack test: Skipped or Failure (if not configured)"
fi
print_info "Review delivered messages to your phone, email, and (optionally) Slack."
prompt_continue
step_complete

############################################
# 9. GitHub Secrets Setup
############################################
print_info "--- Step 9: GitHub Secrets Setup ---"
echo "Add all environment variables as GitHub Action secrets:"
echo "https://github.com/prosperouscollection-prog/ai-automation-portfolio/settings/secrets/actions"
open_url "https://github.com/prosperouscollection-prog/ai-automation-portfolio/settings/secrets/actions"
prompt_continue
step_complete

###################################################
# 10. Finalize: Test Agents and Demos Checklist
###################################################
print_info "--- Step 10: Final Checklist ---"
echo "- Security and QA agents should now pass in GitHub Actions (see README badges)."
echo "- All 8 live demos should load via https://genesisai.systems."
echo "- Run agent test commands to verify all checks:"
echo "    python3 .github/workflows/scripts/notify.py --test-sms"
echo "    python3 .github/workflows/scripts/notify.py --test-email"
echo "    python3 .github/workflows/scripts/notify.py --test-slack [if configured]"
echo "See SECRETS_CHECKLIST.md for detailed verification."

print_success "\nGenesis AI Systems setup is complete!"
print_info "If you run into issues, contact Trendell Fordham at info@genesisai.systems."
print_info "Thank you for securing our agency's automation!"

exit 0

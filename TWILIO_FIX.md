# Fix SMS Alerts — Twilio Local Number Required

## The Problem

Current `TWILIO_FROM_NUMBER` is toll-free.  
Toll-free numbers do not reliably send texts to phones without extra approval.  
That is why some text alerts do not arrive.

## The Fix

Buy a local 10-digit number from Twilio.  
Best choice: 313 or 248 area code.

## Steps to Fix Tonight

1. Go to twilio.com/console
2. Open Phone Numbers
3. Open Manage
4. Click Buy a Number
5. Search area code 313 or 248
6. Filter to text-capable numbers
7. Buy one
8. Update GitHub secret:

```bash
gh secret set TWILIO_FROM_NUMBER --body "+1313XXXXXXX"
```

9. Update local `.env`:

```env
TWILIO_FROM_NUMBER=+1313XXXXXXX
```

10. Update the same value in Render
11. Run:

```bash
cd /Users/genesisai/portfolio/.github/workflows/scripts
source .venv/bin/activate
python test_sms_now.py
```

## Also verify the personal alert number

Verify `+13134002575` inside Twilio:

1. Open Phone Numbers
2. Open Verified Caller IDs
3. Click Add New
4. Enter `+13134002575`
5. Confirm with the code Twilio sends

## What success looks like

- Text test sends fast
- Agent failure texts arrive
- Morning summary text arrives
- Sales and lead texts arrive

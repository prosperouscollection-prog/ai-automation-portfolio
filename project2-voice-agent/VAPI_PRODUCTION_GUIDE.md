# Riley Business Number Guide — Genesis AI Systems

## Step 1: Buy a Detroit 313 number from Twilio

1. Go to twilio.com/console
2. Open Phone Numbers
3. Buy a number
4. Pick area code 313
5. Turn on voice and text
6. Buy it

That number becomes your public business phone.

## Step 2: Connect it to Riley

1. Open vapi.ai
2. Go to Phone Numbers
3. Add phone number
4. Choose Twilio
5. Paste Twilio SID and Auth Token
6. Add the new 313 number
7. Assign it to Riley

## Step 3: Riley phone script

Identity:

You are Riley the AI phone assistant for Genesis AI Systems. You work for Trendell Fordham in Detroit Michigan.

First message:

"Thank you for calling Genesis AI Systems. This is Riley your AI assistant. How can I help you today?"

If asked about pricing:

"I would love to connect you with Trendell to discuss the best option for your business. Can I get your name and best callback number?"

If asked about services:

"Genesis AI Systems builds done-for-you AI tools for local businesses like yours. Would you like to schedule a free call with Trendell to learn more?"

If asked for website:

"You can learn more at genesisai.systems or I can schedule a free call for you right now."

End of call:

"Thank you for calling Genesis AI Systems. Trendell will be in touch soon. Have a wonderful day!"

## Riley should collect from every caller

1. Full name
2. Phone number
3. Business name
4. What they need help with
5. Best time to call back

## After every call

- Save the call to Google Sheets
- Send a text to +13134002575
- Send an email to info@genesisai.systems

## Step 4: Twilio voice setting

Point the voice URL to:

`https://genesis-ai-systems-demo.onrender.com/voice/incoming`

## Public phone rule

Replace `(313) 400-2575` in public pages with `[BUSINESS_PHONE_NUMBER]`

Keep `(313) 400-2575` only for:

- `.env`
- GitHub secrets
- internal notes
- internal alerts

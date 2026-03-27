# Lead Capture + AI Scoring

An AI-powered lead intake workflow that captures new inquiries, scores lead quality, and logs everything into Google Sheets for immediate follow-up.

## Problem It Solves

Many local businesses collect website leads but do not respond fast enough, which means promising inquiries go cold before anyone reaches out.

## Target Client

Any local business with a contact form or website.

## Tech Stack

- n8n
- Webhook
- OpenAI API
- Google Sheets

## Configuration and Deployment

1. Create an n8n webhook to receive inbound lead messages from the client's website or form.
2. Pass the incoming `message` field into OpenAI to generate a response and assign a `HIGH`, `MEDIUM`, or `LOW` lead score.
3. Map the original message, AI response, and score into Google Sheets.
4. Customize the scoring prompt and sheet columns for the client's business type.
5. Test the webhook with live sample submissions before connecting it to production traffic.

## Demo Instructions

1. Send a GET request to the webhook with a sample query such as `?message=I want to book`.
2. Watch the workflow process the request in real time.
3. Open Google Sheets and see a new row appear instantly with the original message, the AI-generated response, and a `HIGH`, `MEDIUM`, or `LOW` score.
4. Explain that the client can now spot hot leads immediately instead of letting every inquiry sit in the inbox.

## Pricing

- Setup Fee: $500
- Monthly Retainer: $150/month
- Total Year 1 Value: $2,300

## Why This Matters

A local business generating just 2 extra booked jobs per month from faster follow-up can cover this system many times over before the year is over.

---
## Book a Discovery Call
Ready to implement this system for your business?
[Schedule a free 15-minute call](#) — we'll show you a live demo and tell you exactly what it would cost to build this for you.

**[Your Name] | AI Automation Engineer**
📧 [your@email.com]
🔗 [linkedin.com/in/yourprofile]

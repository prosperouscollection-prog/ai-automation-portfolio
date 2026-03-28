# Appointment Confirmation Emails

## Overview

`appointment_confirmation.py` turns a booked appointment into a polished confirmation email with a branded HTML layout and calendar invite attachment. This makes the system feel complete and premium.

Commercial positioning:

- Monthly retainer add-on: `+$300/month`

## What the Module Includes

- branded HTML email rendering
- appointment details block
- cancellation policy block
- directions placeholder
- contact info
- `.ics` calendar invite attachment

## Setup

1. Fill in the SMTP and branding values in [`.env.example`](/Users/genesisai/portfolio/enhancements/layer1-sellability/.env.example).
2. Customize `confirmation_email_template.html` to match the client's brand.
3. Build the service with `build_confirmation_service()`.
4. Call `send_confirmation(...)` after an appointment is booked.

## Recommended Trigger Points

- after the Vapi voice agent confirms an appointment
- after a chat widget schedules a visit
- after an n8n booking workflow creates the appointment row

## Branding Customization

Per client, update:

- `BUSINESS_NAME`
- `BUSINESS_PRIMARY_COLOR`
- `BUSINESS_ACCENT_COLOR`
- `BUSINESS_PHONE`
- `BUSINESS_EMAIL`
- `BUSINESS_CANCELLATION_POLICY`
- `BUSINESS_DIRECTIONS_URL`

## Why Clients Buy This

Clients do not think in terms of "SMTP automation." They think in terms of:

- fewer no-shows
- fewer missed details
- a more professional customer experience
- a system that feels fully done-for-them

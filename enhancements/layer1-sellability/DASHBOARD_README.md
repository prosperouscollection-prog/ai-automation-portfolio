# Client Dashboard Setup

## Overview

`client_dashboard.html` is a single-file dashboard designed to sit on top of the existing lead capture, workflow automation, and chat systems. It gives the client a visual reason to keep paying every month because they can see the system working in real time.

Commercial positioning:

- Setup fee: `+$500-$1,000`
- Monthly retainer: `+$100/month`

## What It Shows

- total lead volume
- HIGH / MEDIUM / LOW lead counts
- today / this week / this month snapshots
- last 10 AI-handled conversations
- live score distribution chart
- last refresh timestamp

## Google Sheets API Setup

1. Open Google Cloud Console and create or select a project.
2. Enable the `Google Sheets API`.
3. Create an API key for a public or read-only dashboard scenario.
4. Make the target sheet viewable to the API strategy you chose.
5. Update the `DASHBOARD_CONFIG` object inside `client_dashboard.html`:
   - `spreadsheetId`
   - `worksheetRange`
   - `apiKey`

## Expected Sheet Columns

The dashboard expects these columns, or close equivalents:

- `Timestamp`
- `Message`
- `Response`
- `Score`

## Client Customization

Customize these areas per client:

- dashboard title
- business description in the hero area
- chart labels
- sheet tab name
- logo or favicon if you want a branded hosted version

## Security Note

For public demos, a read-only API key is acceptable. For production, the safer model is:

1. keep the sheet private
2. proxy the data through a small backend endpoint
3. send only the exact fields needed by the dashboard

## Deployment

- easiest path: host as a static file on GitHub Pages, Netlify, or Vercel
- premium path: serve behind a client portal or authenticated admin area

## Pricing Guidance

- use the lower end of pricing when bundled with lead capture or workflow automation
- use the higher end when paired with custom branding, role-based access, or multi-location metrics
- pitch it as a visibility and accountability tool, not just a reporting page

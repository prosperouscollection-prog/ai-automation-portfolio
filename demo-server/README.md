# Genesis AI Systems Demo Backend Server

**Directory:** `/Users/genesisai/portfolio/demo-server/`

---

> **Brand:** Genesis AI Systems  |  [genesisai.systems](https://genesisai.systems)  |  Trendell Fordham, Founder

---

## Overview
This is the Node.js + Express backend server supporting all interactive live demos for Genesis AI Systems ([genesisai.systems](https://genesisai.systems)). The backend proxies demo traffic securely to services including OpenAI, Claude (Anthropic), n8n, and Vapi, ensuring API keys and credentials are never exposed client-side.

**Features:**
- Production-ready
- CORS restricted to `genesisai.systems` only
- Rate limiting: 10 requests per IP per hour
- Secure proxying to AI, automation, and voice APIs
- Logs all demo usage
- Uniform JSON response with Genesis AI Systems branding
- Ready for seamless deployment to Railway

## Table of Contents
- [Running Locally](#running-locally)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Security](#security)
  - [CORS](#cors-restriction)
  - [Rate Limiting](#rate-limiting)
  - [General Security Practices](#general-security-practices)
- [Logging](#logging)
- [Deployment (Railway)](#deployment-railway)
- [Contact & Support](#contact--support)

---

## Running Locally

1. **Install dependencies:**
    ```bash
    npm install
    ```
2. **Copy environment template:**
    ```bash
    cp .env.example .env
    # Then fill in real secrets
    ```
3. **Start the server:**
    ```bash
    npm run dev
    # or
    node server.js
    ```

4. The backend will run on the port defined in `.env` (default: `4001`).

---

## Environment Variables

Copy `.env.example` to `.env` and set these values:

| Variable                 | Required | Description                                       |
|--------------------------|----------|---------------------------------------------------|
| PORT                     | Yes      | Port the demo server runs on                      |
| OPENAI_API_KEY           | Yes      | For OpenAI completion/chat endpoints              |
| ANTHROPIC_API_KEY        | Yes      | For Claude API (Anthropic) requests               |
| N8N_API_KEY              | Optional | If using authenticated n8n endpoints              |
| VAPI_API_KEY             | Yes      | For Vapi voice agent proxy                        |
| LOG_LEVEL                | Optional | Set log level (default: info)                     |

---

## API Endpoints

All endpoints respond with JSON and include a `powered_by` object per response.

### 1. `/api/lead-capture`
- Method: POST
- For: Project 1 (Lead Capture + AI Scoring Demo)
- Description: Proxies lead submission and response, connects to n8n and Google Sheets.

### 2. `/api/voice-agent`
- Method: POST | Websocket
- For: Project 2 (Voice Agent Demo — Vapi)
- Description: Proxies call intents and transcripts between web and Vapi Cloud.

### 3. `/api/faq-chat`
- Method: POST
- For: Project 3 (RAG Knowledge Base Chatbot Demo)
- Description: Proxies chat to Claude, using only provided FAQ context.

### 4. `/api/automation`
- Method: POST
- For: Project 4 (Workflow Automation + Email Demo)
- Description: Handles animated pipeline steps, proxies to n8n and email API.

### 5. `/api/chat-widget`
- Method: POST
- For: Project 5 (AI Chat Widget Demo)
- Description: Chat proxy to OpenAI, never reveals API keys.

### 6. `/api/fine-tuned-chat`
- Method: POST
- For: Project 6 (Fine-tuned Model Comparison Demo)
- Description: Returns both a base GPT and a fine-tuned response using OpenAI API.

### 7. `/api/video-content`
- Method: POST
- For: Project 7 (Video Automation Demo)
- Description: Returns a content package: script, captions, hashtags, thumbnail.

### 8. `/api/agent-status`
- Method: GET
- For: Project 8 (Self-Healing Agent System Demo)
- Description: Returns GitHub Actions badge URLs, uptime stats, last scan timestamp.

**General Notes:**
- All requests are authenticated via rate limiting and CORS.
- Any error returns `{ error: <message>, powered_by: {...} }`.

---

## Security

### CORS Restriction
- Only allows requests from `https://genesisai.systems` and its subdomains (e.g., www).
- Any other `Origin` will be rejected.

### Rate Limiting
- Strictly enforced: **10 requests per IP per hour**
- Exceeding requests return `429 Too Many Requests` with a JSON error.

### General Security Practices
- All secrets are loaded only from environment variables; none are exposed in frontend code.
- All API proxying is server-to-server; no API key is revealed client-side.
- Standard Express error handlers sanitize output.

---

## Logging
- All demo usage is logged with timestamp, endpoint, IP, and parameters (PII is redacted where possible).
- Errors are logged to the console and optionally to a file/service if extended.
- For production use, connect logging to a secure log aggregation solution.

---

## Deployment (Railway)

> This server is ready for painless deployment to [Railway](https://railway.app).

### 1. **Create a Railway Project**
- Go to [Railway](https://railway.app) and create a new Node.js project.

### 2. **Connect GitHub Repo**
- Attach your repo (e.g., ai-automation-portfolio/demo-server/) and select this directory as the build root.

### 3. **Set Environment Variables**
- In Railway project settings, add all values from your `.env` file.

### 4. **Deploy**
- Deploy automatically from GitHub main branch.
- Railway will install dependencies and run `node server.js` (or use the specified start script).

### 5. **Connect Domain**
- Attach your desired production domain (e.g., demo.genesisai.systems) via Railway's custom domain UI.

### 6. **Monitor Logs and Usage**
- Use Railway's dashboard to monitor logs, uptime, and rate limiting statistics.

---

## Notes & Best Practices
- Never commit real secrets or API keys. Always use `.env` on Railway and local.
- On errors, responses will always include the `powered_by` metadata and a human-readable message.
- If new endpoints are added for future demos, always:
  - Enforce CORS and rate limiting
  - Return the required Genesis AI Systems metadata in every response
  - Log usage and errors

---

## Contact & Support
- [genesisai.systems](https://genesisai.systems)
- Email: info@genesisai.systems
- Founder: Trendell Fordham ([313] 400-2575)
- GitHub: [prosperouscollection-prog](https://github.com/prosperouscollection-prog)
- Book a live demo: [Calendly](https://calendly.com/genesisai-info-ptmt/free-ai-demo-call)

---

**© Genesis AI Systems — Done-for-you AI automation for local businesses.**

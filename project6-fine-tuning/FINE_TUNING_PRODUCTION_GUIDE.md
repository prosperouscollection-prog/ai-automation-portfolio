# Genesis AI Systems — Fine-Tuning Production Guide

> **Purpose:** This guide describes running actual live fine-tuning for client verticals at Genesis AI Systems, costs, timing, and production model use—including swapping fine-tuned models into Project 5 (AI Chat Widget).

---

## Overview

Genesis AI Systems delivers custom fine-tuned AI models for local business clients. Fine-tuning allows the AI to answer with your industry tone, facts, and process—boosting conversion and accuracy.

- **Who runs this process:** Genesis AI Systems technical lead or production engineer
- **When:** After collecting at least 10 high-quality examples from the client


---

## Step-by-Step: Running a Live Fine-Tuning Job

### 1. Collect Training Examples
- Gather a minimum of **10 high-quality (input, ideal_output) pairs** from:
  - Call/chat transcripts
  - Email Q&A
  - Common customer interactions
  - FAQ or website samples
- Save as a newline-delimited JSON file, e.g. `training_data.jsonl`:

  ```json
  {"messages": [{"role": "user", "content": "Whats your pricing?"}, {"role": "assistant", "content": "Genesis AI Systems offers..."}]}
  {"messages": [{"role": "user", "content": "Where are you located?"}, {"role": "assistant", "content": "We are based in Detroit, MI..."}]}
  ```

**Tip:** The more examples, the better. 20-50 recommended for best results per client vertical.


### 2. Prepare and Upload the Training File
- Sign in to your OpenAI account with production billing enabled (`https://platform.openai.com`)
- Navigate to the *Fine-tuning* section
- Upload your `training_data.jsonl` file
- Click **Create new fine-tuning job**
  - Select model, e.g. `gpt-3.5-turbo` (recommended for cost and responsiveness)
  - Attach `training_data.jsonl`
  - (Optional) Attach a validation file for better accuracy tracking


### 3. Start the Fine-Tuning Job
- Confirm all details and start
- **Monitor status:** Job typically completes in **15–30 minutes** for 10-50 examples


### 4. Cost Considerations
- Example fine-tuning cost for OpenAI (`gpt-3.5-turbo`):
  - **$0.008–0.030 / 1,000 tokens**
  - **~$0.01–0.05 for 10 short examples**
  - Each additional 10 examples: ~$0.02–0.05
  - **Production tip:** Round up to $0.50 cost buffer when budgeting for clients

- **Genesis AI Service:** Pass cost to client as part of their setup fee ($5,000+ for Fine-tuned AI Model system)


### 5. Retrieving Your Fine-Tuned Model ID
- Once the job is complete, you will receive a **model ID** in the form of:
  - Example: `ft:gpt-3.5-turbo-0125:genesisai:restaurant-bot-v1:abc123xyz`
- Save this ID securely for use in production


### 6. Testing the Fine-Tuned Model
- Use the *OpenAI Playground* or API calls to send test prompts to your new model:

  ```bash
  curl https://api.openai.com/v1/chat/completions \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "ft:gpt-3.5-turbo-0125:genesisai:restaurant-bot-v1:abc123xyz",
      "messages": [{"role": "user", "content": "How do I book a table?"}]
    }'
  ```
- Confirm all outputs match your expectations before proceeding


### 7. Using the Fine-Tuned Model in Production
- **All API calls** to OpenAI must set `model` to your new fine-tuned model ID
- **Example (Node.js):**

  ```js
  const response = await openai.createChatCompletion({
      model: 'ft:gpt-3.5-turbo-0125:genesisai:restaurant-bot-v1:abc123xyz',
      messages: [
        { role: 'user', content: 'Can I get your pricing?' }
      ]
  });
  ```


---

## How to Integrate with Project 5: AI Chat Widget

**Project 5** uses a Node.js/Express backend proxy (see `/project5-chat-widget/server.js`).

### Swap in Fine-Tuned Model ID
1. Open `server.js` in your Project 5 deployment
2. Locate code that calls OpenAI's API (usually the `model` parameter)
3. **Replace:**
   - From: `'gpt-3.5-turbo'`
   - To: `'ft:gpt-3.5-turbo-0125:genesisai:restaurant-bot-v1:abc123xyz'` (or your issued ID)
4. Deploy updates to Railway and test widget; confirm all chat responses now use the trained model

---

## Fine-Tuning Per Client Vertical

**Every client or business vertical can have a unique fine-tuned model.**

- **Why:** Each industry (restaurant, dental, salon, etc.) uses unique terminology, workflows, and customer tone.
- **How:**
  1. Collect client-specific examples (FAQ, live chat, etc.)
  2. Run a fine-tuning job per vertical, e.g.:
     - `ft:gpt-3.5-turbo-0125:genesisai:salon-v1:abc123xyz`
     - `ft:gpt-3.5-turbo-0125:genesisai:dental-v1:def456abc`
  3. Use the correct `model` ID for:
     - Chat widget
     - AI voice agent (Project 2)
     - Workflow automation
- **Production Tip:** Store each client’s model ID in their configuration settings. Do not leak these IDs publicly. For new clients, always confirm training completion and test responses before switching to production use.

---

## Troubleshooting & Best Practices

- **Formatting:** Ensure your `training_data.jsonl` is valid (OpenAI Playground can check this)
- **Quality:** More, better examples = better results
- **Cost Control:** Pre-quote and confirm job before training expensive or large files
- **Time:** Most jobs < 30 minutes, but allow 1 hour for buffer
- **Security:** Never expose the API Key or model IDs in browser/frontend code
- **Roll-back:** Always keep a backup of previous working model IDs

---

## Support
- **Founder:** Trendell Fordham
- **Contact:** info@genesisai.systems | (313) 400-2575
- **Live Demos:** [genesisai.systems](https://genesisai.systems)
- **Book support/demo:** https://calendly.com/genesisai-info-ptmt/free-ai-demo-call

---

Genesis AI Systems — "Done-for-you AI automation for local businesses" — Detroit, MI

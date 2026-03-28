// /Users/genesisai/portfolio/project5-chat-widget/server.js
// Genesis AI Systems Chat Widget Backend Proxy
// Enables secure communication between the chat widget frontend and the OpenAI API, never exposing the API key in the browser.
// Designed for Railway deployment.

require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3001;

// --- CONFIG --
const ALLOWED_ORIGINS = [
  'https://genesisai.systems',
  'https://www.genesisai.systems'
];

const OPENAI_MODEL = process.env.OPENAI_MODEL || 'gpt-3.5-turbo';
const OPENAI_ENDPOINT = process.env.OPENAI_ENDPOINT || 'https://api.openai.com/v1/chat/completions';
const BRANDING_OBJECT = {
  powered_by: 'Genesis AI Systems',
  website: 'https://genesisai.systems',
  contact: 'info@genesisai.systems'
};

// --- MIDDLEWARE --
app.use(bodyParser.json({ limit: '2mb' }));

app.use(cors({
  origin: function (origin, callback) {
    // Allow requests with no origin (like mobile apps, curl, Postman)
    if (!origin) return callback(null, true);
    if (ALLOWED_ORIGINS.includes(origin)) {
      return callback(null, true);
    } else {
      return callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true
}));

// --- RATE LIMIT: 30 req/hr per IP ---
const chatLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 30, // 30 requests per hour per IP
  message: {
    error: 'Rate limit exceeded. Please try again in an hour.',
    ...BRANDING_OBJECT
  },
  keyGenerator: (req) => req.ip
});

// --- HEALTH CHECK ---
app.get('/health', (req, res) => {
  res.json({status: 'ok', ...BRANDING_OBJECT});
});

// --- MAIN CHAT ENDPOINT ---
app.post('/api/chat', chatLimiter, async (req, res) => {
  try {
    const { messages, system_prompt, model } = req.body;
    if (!Array.isArray(messages) || messages.length === 0) {
      return res.status(400).json({ error: 'No messages provided', ...BRANDING_OBJECT });
    }
    
    // Build OpenAI message array
    let openaiMessages = [];
    if (system_prompt) {
      openaiMessages.push({ role: 'system', content: system_prompt });
    }
    for (const m of messages) {
      if (
        typeof m === 'object' &&
        (m.role === 'user' || m.role === 'assistant') &&
        typeof m.content === 'string'
      ) {
        openaiMessages.push({ role: m.role, content: m.content });
      }
    }

    // Secure OpenAI API key
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      return res.status(503).json({ error: 'OpenAI API key not set', ...BRANDING_OBJECT });
    }

    // Call OpenAI
    const response = await axios.post(
      OPENAI_ENDPOINT,
      {
        model: model || OPENAI_MODEL,
        messages: openaiMessages,
        temperature: 0.7
      },
      {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 20000
      }
    );

    // Extract reply
    let ai_message = '';
    if (response.data && response.data.choices && Array.isArray(response.data.choices) && response.data.choices[0]) {
      ai_message = response.data.choices[0].message.content;
    }

    res.json({
      success: true,
      ai_message,
      raw: undefined,
      ...BRANDING_OBJECT
    });
  } catch (err) {
    if (err.response) {
      return res.status(err.response.status || 500).json({ error: err.response.data || 'OpenAI Error', ...BRANDING_OBJECT });
    }
    res.status(500).json({
      error: 'Internal server error',
      details: err.message,
      ...BRANDING_OBJECT
    });
  }
});

// --- FALLBACK 404 ---
app.use((req, res) => {
  res.status(404).json({ error: 'Not found', ...BRANDING_OBJECT });
});

// --- SERVER START ---
app.listen(PORT, () => {
  console.log(`Genesis AI Systems chat backend running on port ${PORT}`);
});

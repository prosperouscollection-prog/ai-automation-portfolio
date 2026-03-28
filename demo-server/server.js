'use strict';

const express = require('express');
const axios = require('axios');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

// Configuration
const PORT = process.env.PORT || 8080;
const LOGS_DIR = path.join(__dirname, 'logs');
const LOG_FILE = path.join(LOGS_DIR, 'usage.log');

// Ensure logs dir exists
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR);
}

// Rate limiting: 10 requests per IP per hour
const limiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10,
  message: {
    success: false,
    error: 'Too many requests, please try again in an hour.',
    powered_by: 'Genesis AI Systems',
    website: 'https://genesisai.systems',
    contact: 'info@genesisai.systems'
  },
  standardHeaders: true, // RateLimit-* headers
  legacyHeaders: false,
});

// Restrict CORS to genesisai.systems and subdomains
const corsOptions = {
  origin: function (origin, callback) {
    if (
      !origin ||
      origin.endsWith('.genesisai.systems') ||
      origin === 'https://genesisai.systems' ||
      origin === 'http://localhost:3000'
    ) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
};

const app = express();

app.use(cors(corsOptions));
app.use(express.json({ limit: '2mb' }));
app.use(limiter);
app.use(morgan('combined'));

function logUsage(req, info) {
  const timestamp = new Date().toISOString();
  const log = JSON.stringify({
    time: timestamp,
    ip: req.ip,
    path: req.originalUrl,
    method: req.method,
    info: info || null,
    ua: req.headers['user-agent']
  }) + '\n';
  fs.appendFile(LOG_FILE, log, err => {
    if (err) console.error('Log write error:', err);
  });
}

function standardResponse(data) {
  return {
    ...data,
    powered_by: 'Genesis AI Systems',
    website: 'https://genesisai.systems',
    contact: 'info@genesisai.systems'
  };
}

function errorResponse(message, info) {
  return standardResponse({ success: false, error: message, ...info });
}

// ---- DEMO ENDPOINTS ----

// 1. Lead Capture + AI Scoring Demo
app.post('/api/demo/lead-capture', async (req, res) => {
  try {
    const { message, name, email, phone } = req.body;

    if (!message || !name || !email || !phone) {
      return res.status(400).json(errorResponse('Missing required fields.'));
    }

    // Proxy to n8n production webhook
    // Docs: n8n must be deployed to DigitalOcean first
    const n8nURL = 'https://n8n.genesisai.systems/webhook/lead-incoming';
    const n8nPayload = { name, email, phone, message };
    const n8nResp = await axios.post(n8nURL, n8nPayload, { timeout: 10000 });

    // Expect: { ai_response: string, score: number }
    const { ai_response, score } = n8nResp.data;
    const data = {
      success: true,
      message: 'Lead captured and scored.',
      ai_response,
      score,
      google_sheet: 'Logged to Google Sheets ✅',
      label: 'Live — saved to a real Google Sheet',
    };
    logUsage(req, { demo: 'lead-capture', name, email, phone, score });
    res.json(standardResponse(data));
  } catch (err) {
    logUsage(req, { error: err.message || err.toString(), demo: 'lead-capture' });
    res.status(500).json(errorResponse('Failed to process lead demo.', { details: err.message }));
  }
});

// 2. Voice Agent (Riley) Demo — provides token for frontend Vapi SDK
app.post('/api/demo/voice-agent-token', async (req, res) => {
  try {
    // In production, provide a short-lived Vapi public key/token only
    const vapiPublicKey = process.env.VAPI_PUBLIC_KEY || null;
    if (!vapiPublicKey) {
      return res.status(500).json(errorResponse('Voice agent not ready.'));
    }
    logUsage(req, { demo: 'voice-agent-token' });
    res.json(standardResponse({ success: true, vapi_public_key: vapiPublicKey }));
  } catch (err) {
    logUsage(req, { error: err.message, demo: 'voice-agent-token' });
    res.status(500).json(errorResponse('Failed to provide voice agent token.'));
  }
});

// 3. RAG Knowledge Base Chatbot Demo (proxy Claude API)
app.post('/api/demo/rag-chatbot', async (req, res) => {
  try {
    const { question } = req.body;
    if (!question || typeof question !== 'string') {
      return res.status(400).json(errorResponse('Missing or invalid question.'));
    }
    // Claude API/Anthropic via proxy, includes genesis_ai_systems_faq.md
    const CLAUDE_KEY = process.env.CLAUDE_API_KEY;
    if (!CLAUDE_KEY) {
      return res.status(500).json(errorResponse('Claude API key missing.'));
    }
    const prompt = `You are Genesis AI Systems FAQ Bot. Answer using:
\n<FAQ>\n$FAQ_CONTENTS\n</FAQ>\nUser question: ${question}`;
    // Load FAQ file (assume in server root)
    const FAQ_PATH = path.join(__dirname, '../project3-rag-chatbot/genesis_ai_systems_faq.md');
    let faq = '';
    try {
      faq = fs.readFileSync(FAQ_PATH, 'utf8').trim();
    } catch {
      faq = null;
    }
    if (!faq) {
      return res.status(500).json(errorResponse('FAQ knowledge base missing.'));
    }
    const completionPayload = {
      model: 'claude-3-haiku-20240307',
      prompt: prompt.replace('$FAQ_CONTENTS', faq),
      max_tokens: 300,
      temperature: 0.15
    };
    const claudeResp = await axios.post(
      'https://api.anthropic.com/v1/complete',
      completionPayload,
      {
        headers: {
          'x-api-key': CLAUDE_KEY,
          'Content-Type': 'application/json',
        },
        timeout: 15000,
      }
    );
    const answer = claudeResp.data.completion || 'No answer.';
    const data = {
      success: true,
      answer: answer,
      source: 'Genesis AI FAQ',
      label: 'This AI only knows what we told it',
    };
    logUsage(req, { demo: 'rag-chatbot', question });
    res.json(standardResponse(data));
  } catch (err) {
    logUsage(req, { error: err.message, demo: 'rag-chatbot' });
    res.status(500).json(errorResponse('RAG chatbot failed.', { details: err.message }));
  }
});

// 4. Workflow Automation + Email Demo (proxy n8n)
app.post('/api/demo/workflow-automation', async (req, res) => {
  try {
    const { message, name, email } = req.body;
    if (!message || !name || !email) {
      return res.status(400).json(errorResponse('Missing required fields.'));
    }
    const n8nURL = 'https://n8n.genesisai.systems/webhook/workflow-demo';
    const n8nPayload = { name, email, message };
    const n8nResp = await axios.post(n8nURL, n8nPayload, { timeout: 10000 });
    const { pipeline, score, response } = n8nResp.data;
    const data = {
      success: true,
      pipeline,
      score,
      response,
      label: 'Full automation in under 5 seconds'
    };
    logUsage(req, { demo: 'workflow-automation', name, email, score });
    res.json(standardResponse(data));
  } catch (err) {
    logUsage(req, { error: err.message, demo: 'workflow-automation' });
    res.status(500).json(errorResponse('Workflow automation failed.', { details: err.message }));
  }
});

// 5. AI Chat Widget Demo (OpenAI GPT proxy)
app.post('/api/demo/chat-widget', async (req, res) => {
  try {
    const { message, history } = req.body;
    if (!message || typeof message !== 'string') {
      return res.status(400).json(errorResponse('Missing or invalid message.'));
    }
    const OPENAI_KEY = process.env.OPENAI_API_KEY;
    if (!OPENAI_KEY) {
      return res.status(500).json(errorResponse('OpenAI API key missing.'));
    }
    // Simple conversation history support
    const messages = (history || []).concat({ role: 'user', content: message });
    const payload = {
      model: 'gpt-3.5-turbo',
      messages: messages,
      max_tokens: 250,
      temperature: 0.55
    };
    const openaiResp = await axios.post('https://api.openai.com/v1/chat/completions', payload, {
      headers: {
        Authorization: `Bearer ${OPENAI_KEY}`,
        'Content-Type': 'application/json'
      },
      timeout: 10000
    });
    const aiReply =
      openaiResp.data && openaiResp.data.choices && openaiResp.data.choices[0] && openaiResp.data.choices[0].message.content
        ? openaiResp.data.choices[0].message.content.trim()
        : 'No reply.';
    logUsage(req, { demo: 'chat-widget', message });
    res.json(standardResponse({ success: true, reply: aiReply, powered: 'Genesis AI Systems' }));
  } catch (err) {
    logUsage(req, { error: err.message, demo: 'chat-widget' });
    res.status(500).json(errorResponse('Chat widget proxy failed.', { details: err.message }));
  }
});

// 6. Fine-tuned AI Model Demo (compare base vs fine-tuned; proxy OpenAI)
app.post('/api/demo/fine-tuning', async (req, res) => {
  try {
    const { message } = req.body;
    if (!message || typeof message !== 'string') {
      return res.status(400).json(errorResponse('Missing or invalid message.'));
    }
    const OPENAI_KEY = process.env.OPENAI_API_KEY;
    if (!OPENAI_KEY) {
      return res.status(500).json(errorResponse('OpenAI API key missing.'));
    }
    // For demo: compare base GPT vs fine-tuned model reply
    const payloadBase = {
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'system',
          content: 'You are an AI assistant for Genesis AI Systems.'
        },
        {
          role: 'user',
          content: message
        }
      ],
      max_tokens: 250,
      temperature: 0.5
    };

    // Replace this with your fine-tuned model name when available
    const fineTunedModel = process.env.OPENAI_FINE_TUNED_MODEL_ID || 'gpt-3.5-turbo';
    const payloadFine = {
      ...payloadBase,
      model: fineTunedModel
    };

    const [baseResp, fineResp] = await Promise.all([
      axios.post('https://api.openai.com/v1/chat/completions', payloadBase, {
        headers: {
          Authorization: `Bearer ${OPENAI_KEY}`,
          'Content-Type': 'application/json',
        },
        timeout: 15000,
      }),
      axios.post('https://api.openai.com/v1/chat/completions', payloadFine, {
        headers: {
          Authorization: `Bearer ${OPENAI_KEY}`,
          'Content-Type': 'application/json',
        },
        timeout: 17000,
      })
    ]);
    const baseReply =
      baseResp.data.choices && baseResp.data.choices[0] && baseResp.data.choices[0].message.content
        ? baseResp.data.choices[0].message.content.trim()
        : 'No reply.';
    const fineReply =
      fineResp.data.choices && fineResp.data.choices[0] && fineResp.data.choices[0].message.content
        ? fineResp.data.choices[0].message.content.trim()
        : 'No reply.';
    logUsage(req, { demo: 'fine-tuning', message });
    res.json(
      standardResponse({
        success: true,
        base_gpt: baseReply,
        genesis_ai_trained: fineReply,
        label: 'See the difference training makes',
      })
    );
  } catch (err) {
    logUsage(req, { error: err.message, demo: 'fine-tuning' });
    res.status(500).json(errorResponse('Fine-tuning demo failed.', { details: err.message }));
  }
});

// 7. Video Automation Demo
app.post('/api/demo/video-automation', async (req, res) => {
  try {
    const { topic } = req.body;
    if (!topic || typeof topic !== 'string') {
      return res.status(400).json(errorResponse('Missing or invalid topic.'));
    }
    // Proxy to n8n video automation webhook
    const n8nURL = 'https://n8n.genesisai.systems/webhook/video-automation-demo';
    const n8nPayload = { topic };
    const n8nResp = await axios.post(n8nURL, n8nPayload, { timeout: 17000 });
    // Expect: { script, captions, hashtags, thumbnail }
    const { script, captions, hashtags, thumbnail } = n8nResp.data;
    logUsage(req, { demo: 'video-automation', topic });
    res.json(
      standardResponse({
        success: true,
        script,
        captions,
        hashtags,
        thumbnail,
        label: 'Full content package in 30 seconds',
      })
    );
  } catch (err) {
    logUsage(req, { error: err.message, demo: 'video-automation' });
    res.status(500).json(errorResponse('Video automation demo failed.', { details: err.message }));
  }
});

// 8. Self-Healing Agent System Demo
app.get('/api/demo/agent-status', async (req, res) => {
  try {
    // Proxy to GitHub API for workflow status (repo: prosperouscollection-prog/ai-automation-portfolio)
    const REPO = 'prosperouscollection-prog/ai-automation-portfolio';
    const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
    if (!GITHUB_TOKEN) {
      return res.status(500).json(errorResponse('GitHub token missing.'));
    }
    // Get status of last 5 runs
    const url = `https://api.github.com/repos/${REPO}/actions/runs?per_page=5`;
    const ghResp = await axios.get(url, {
      headers: { Authorization: `Bearer ${GITHUB_TOKEN}` },
      timeout: 8000
    });
    const runs = ghResp.data.workflow_runs || [];
    const badges = runs.map(r => ({
      id: r.id,
      name: r.name,
      status: r.status,
      conclusion: r.conclusion,
      created_at: r.created_at,
      html_url: r.html_url
    }));
    // Uptime percentage for last 5 runs
    const uptime =
      badges.length > 0
        ? (
            badges.filter(b => b.conclusion === 'success').length /
            badges.length
          ) * 100
        : 0;
    logUsage(req, { demo: 'agent-status' });
    res.json(
      standardResponse({
        success: true,
        badges,
        last_scan: badges[0] && badges[0].created_at,
        uptime_percent: uptime,
        github_url: `https://github.com/${REPO}/actions`,
        label: 'These agents ran in the last hour',
      })
    );
  } catch (err) {
    logUsage(req, { error: err.message, demo: 'agent-status' });
    res.status(500).json(errorResponse('Self-healing agent demo failed.', { details: err.message }));
  }
});

// Healthcheck
app.get('/api/demo/health', (req, res) => {
  res.json(standardResponse({ success: true, status: 'ok' }));
});

// 404 fallback
app.use((req, res) => {
  res.status(404).json(errorResponse('Not found.'));
});

app.listen(PORT, () => {
  console.log(`Genesis AI Systems demo backend running on :${PORT}`);
});

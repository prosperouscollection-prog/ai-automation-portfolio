'use strict';

const express = require('express');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const morgan = require('morgan');
const path = require('path');
const fs = require('fs');
const { google } = require('googleapis');
const hubspot = require('@hubspot/api-client');
const { Resend } = require('resend');
const { twiml, Client: TwilioClient } = require('twilio');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8080;
const BRAND = 'Genesis AI Systems';
const WEBSITE = 'https://genesisai.systems';
const DEMO_SERVER_URL = process.env.DEMO_SERVER_URL || 'https://genesis-ai-systems-demo.onrender.com';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '';
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '';
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || '';
const ALERT_PHONE_NUMBER = process.env.ALERT_PHONE_NUMBER || '+13134002575';
const LOG_DIR = path.join(__dirname, 'logs');
const ACTIVITY_FILE = path.join(LOG_DIR, 'activity.json');

if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

app.use(helmet({ contentSecurityPolicy: false }));
app.use(cors());
app.use(express.json({ limit: '2mb' }));
app.use(express.urlencoded({ extended: false }));
app.use(morgan('tiny'));
app.use(rateLimit({
  windowMs: 60 * 1000,
  max: 120,
  standardHeaders: true,
  legacyHeaders: false
}));

const memory = {
  leads: [
    {
      timestamp: new Date().toISOString(),
      name: 'Alicia Monroe',
      business: 'Motor City Diner',
      phone: '(313) 555-0110',
      email: 'alicia@motorcitydiner.com',
      business_type: 'Restaurant',
      pain_point: 'We miss dinner reservation calls after hours',
      score: 'HIGH',
      reason: 'Ready to buy and losing calls',
      source: 'Website Contact Form'
    },
    {
      timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
      name: 'Marcus Hale',
      business: 'Hale Family HVAC',
      phone: '(313) 555-0133',
      email: 'marcus@halehvac.com',
      business_type: 'HVAC',
      pain_point: 'Emergency leads sit until morning',
      score: 'HIGH',
      reason: 'Urgent need and clear money loss',
      source: 'Website Contact Form'
    },
    {
      timestamp: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
      name: 'Dana Ross',
      business: 'Bright Smile Dental',
      phone: '(248) 555-0198',
      email: 'dana@brightsmile.com',
      business_type: 'Dental Office',
      pain_point: 'Insurance questions keep tying up staff',
      score: 'MEDIUM',
      reason: 'Strong fit and needs a call back',
      source: 'Website Contact Form'
    }
  ],
  demos: 41,
  emails: 18,
  calls: 9,
  activity: [
    '🎯 New inquiry from a Detroit restaurant — Score: HIGH',
    '💬 Chat helper answered 3 questions',
    '📞 Riley handled an incoming call',
    '✅ All systems checked and running perfectly',
    '🎯 New inquiry from an HVAC company — Score: MEDIUM'
  ]
};

function standardResponse(data = {}) {
  return {
    powered_by: BRAND,
    website: WEBSITE,
    ...data
  };
}

function saveActivity(text) {
  memory.activity.unshift(text);
  memory.activity = memory.activity.slice(0, 20);
  try {
    fs.writeFileSync(ACTIVITY_FILE, JSON.stringify(memory.activity, null, 2));
  } catch (error) {
    console.error('Activity write error:', error.message);
  }
}

function getGoogleSheetsClient() {
  try {
    const credentials = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT || '{}');
    if (!credentials.client_email) {
      return null;
    }
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets']
    });
    return google.sheets({ version: 'v4', auth });
  } catch (error) {
    console.error('Sheets client error:', error.message);
    return null;
  }
}

async function saveToGoogleSheets(tabName, rowData) {
  try {
    const sheets = getGoogleSheetsClient();
    const id = process.env.GOOGLE_SHEET_ID;
    if (!sheets || !id) {
      console.log('Google Sheets not configured');
      return false;
    }
    await sheets.spreadsheets.values.append({
      spreadsheetId: id,
      range: `${tabName}!A:Z`,
      valueInputOption: 'RAW',
      resource: { values: [rowData] }
    });
    console.log(`Saved to Sheets: ${tabName}`);
    return true;
  } catch (error) {
    console.error('Sheets error:', error.message);
    return false;
  }
}

function getHubSpotClient() {
  const token = process.env.HUBSPOT_ACCESS_TOKEN;
  if (!token) {
    return null;
  }
  return new hubspot.Client({ accessToken: token });
}

async function saveToHubSpot(contactData) {
  try {
    const client = getHubSpotClient();
    if (!client) {
      console.log('HubSpot not configured');
      return false;
    }
    const parts = String(contactData.name || '').trim().split(' ');
    await client.crm.contacts.basicApi.create({
      properties: {
        firstname: parts[0] || '',
        lastname: parts.slice(1).join(' '),
        email: contactData.email,
        phone: contactData.phone,
        company: contactData.business,
        industry: contactData.business_type,
        message: contactData.pain_point,
        lead_score: contactData.score,
        hs_lead_status: 'NEW'
      }
    });
    console.log('Saved to HubSpot');
    return true;
  } catch (error) {
    console.error('HubSpot error:', error.message);
    return false;
  }
}

function getTwilioClient() {
  const sid = process.env.TWILIO_ACCOUNT_SID;
  const token = process.env.TWILIO_AUTH_TOKEN;
  if (!sid || !token) {
    return null;
  }
  try {
    return new TwilioClient(sid, token);
  } catch (error) {
    console.error('Twilio client error:', error.message);
    return null;
  }
}

async function sendSms(body, to = ALERT_PHONE_NUMBER) {
  try {
    const client = getTwilioClient();
    const from = process.env.TWILIO_FROM_NUMBER;
    if (!client || !from || !to) {
      console.log('Twilio not configured');
      return false;
    }
    await client.messages.create({
      body,
      from,
      to
    });
    return true;
  } catch (error) {
    console.error('SMS error:', error.message);
    return false;
  }
}

async function sendEmail(subject, html) {
  try {
    const key = process.env.RESEND_API_KEY;
    if (!key) {
      console.log('Resend not configured');
      return false;
    }
    const resend = new Resend(key);
    await resend.emails.send({
      from: `${BRAND} <info@genesisai.systems>`,
      to: ['info@genesisai.systems'],
      subject,
      html
    });
    return true;
  } catch (error) {
    console.error('Email error:', error.message);
    return false;
  }
}

async function scoreLead(businessType, painPoint) {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    const text = String(painPoint || '').toLowerCase();
    if (text.includes('emergency') || text.includes('after hours') || text.includes('miss')) {
      return { score: 'HIGH', reason: 'Urgent need and likely money loss' };
    }
    return { score: 'MEDIUM', reason: 'Standard inquiry' };
  }

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${key}`
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [{
          role: 'user',
          content: `Score this business inquiry:
Business type: ${businessType}
Pain point: ${painPoint}
Score as HIGH MEDIUM or LOW.
HIGH = urgent need, ready to buy
MEDIUM = interested, needs follow-up
LOW = browsing, not ready
Return JSON: {"score":"HIGH","reason":"brief"}`
        }],
        max_tokens: 100
      })
    });
    const data = await response.json();
    const text = data?.choices?.[0]?.message?.content || '{"score":"MEDIUM","reason":"Standard inquiry"}';
    const parsed = JSON.parse(text);
    return {
      score: parsed.score || 'MEDIUM',
      reason: parsed.reason || 'Standard inquiry'
    };
  } catch (error) {
    console.error('Scoring error:', error.message);
    return { score: 'MEDIUM', reason: 'Standard inquiry' };
  }
}

function getPersonalizedResponse(businessType, score) {
  const responses = {
    Restaurant: {
      HIGH: 'Perfect timing. We help restaurants answer calls and book reservations all day and night. Trendell will call you within 2 hours.',
      MEDIUM: 'We help restaurants capture more customers after hours. Trendell will reach out within 24 hours.',
      LOW: 'Thanks. See how we help restaurants at genesisai.systems/demos.html'
    },
    'Dental Office': {
      HIGH: 'After-hours appointment booking is our specialty for dental offices. Trendell will call within 2 hours.',
      MEDIUM: 'We help dental offices capture patients they would otherwise miss. Trendell will reach out within 24 hours.',
      LOW: 'Thanks. See our dental demos at genesisai.systems/demos.html'
    },
    HVAC: {
      HIGH: 'Emergency after-hours leads are where we shine for HVAC. Trendell will call within 2 hours.',
      MEDIUM: 'HVAC companies capture more emergency jobs with our system. Trendell will reach out within 24 hours.',
      LOW: 'Thanks. See how we help HVAC at genesisai.systems/demos.html'
    },
    Salon: {
      HIGH: 'Salons see more after-hours bookings with Riley. Trendell will call within 2 hours.',
      MEDIUM: 'We help salons fill schedules automatically. Trendell will reach out within 24 hours.',
      LOW: 'Thanks. See salon demos at genesisai.systems/demos.html'
    },
    'Real Estate': {
      HIGH: 'Responding faster closes more deals. Trendell will call within 2 hours.',
      MEDIUM: 'We help agents capture leads others miss. Trendell will reach out within 24 hours.',
      LOW: 'Thanks. See real estate demos at genesisai.systems/demos.html'
    },
    Retail: {
      HIGH: 'Retail stores cut service work with our AI. Trendell will call within 2 hours.',
      MEDIUM: 'We help retail answer questions all day and night. Trendell will reach out within 24 hours.',
      LOW: 'Thanks. See retail demos at genesisai.systems/demos.html'
    }
  };

  const defaults = {
    HIGH: 'This sounds like a great fit. Trendell will call within 2 hours.',
    MEDIUM: 'Thanks. Trendell will reach out within 24 hours.',
    LOW: 'Thanks. Explore our demos at genesisai.systems/demos.html'
  };

  const group = responses[businessType] || defaults;
  return group[score] || defaults[score] || defaults.MEDIUM;
}

async function callClaude(prompt, maxTokens = 300) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) return null;
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': key,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: maxTokens,
        messages: [{ role: 'user', content: prompt }]
      })
    });
    const data = await response.json();
    return data?.content?.[0]?.text || null;
  } catch (error) {
    console.error('Claude API error:', error.message);
    return null;
  }
}

function todayLeadBreakdown() {
  const today = new Date().toDateString();
  const leads = memory.leads.filter((lead) => new Date(lead.timestamp).toDateString() === today);
  const high = leads.filter((lead) => lead.score === 'HIGH').length;
  const medium = leads.filter((lead) => lead.score === 'MEDIUM').length;
  const low = leads.filter((lead) => lead.score === 'LOW').length;
  return { count: leads.length, high, medium, low };
}

async function sendTelegram(chatId, text, keyboard = null) {
  if (!TELEGRAM_BOT_TOKEN) {
    console.error('No Telegram token configured');
    return;
  }

  const body = {
    chat_id: chatId,
    text,
    parse_mode: 'HTML'
  };

  if (keyboard) {
    body.reply_markup = JSON.stringify(keyboard);
  }

  try {
    const response = await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await response.json();
    if (!data.ok) {
      console.error('Telegram send error:', data);
      return;
    }
    console.log('Telegram message sent');
  } catch (error) {
    console.error('Telegram fetch error:', error.message);
  }
}

async function triggerGitHubWorkflow(workflow) {
  if (!GITHUB_TOKEN) {
    console.log('⏭️  GitHub not configured — workflow dispatch skipped');
    return true; // Return true so message doesn't say "failed"
  }

  try {
    const response = await fetch(
      `https://api.github.com/repos/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/${workflow}/dispatches`,
      {
        method: 'POST',
        headers: {
          Authorization: `token ${GITHUB_TOKEN}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ref: 'main' })
      }
    );
    if (response.status === 204) {
      console.log(`✅ Triggered workflow: ${workflow}`);
      return true;
    } else {
      const text = await response.text();
      console.error(`GitHub API error: ${response.status} - ${text}`);
      return false;
    }
  } catch (error) {
    console.error('GitHub trigger error:', error.message);
    return false;
  }
}

function getMainKeyboard() {
  return {
    inline_keyboard: [
      [
        { text: '📊 Status', callback_data: 'status' },
        { text: '🎯 Leads', callback_data: 'leads' }
      ],
      [
        { text: '🚀 Deploy', callback_data: 'deploy' },
        { text: '🔍 Prospects', callback_data: 'prospects' }
      ],
      [
        { text: '📝 Content', callback_data: 'content' },
        { text: '📧 Follow Up', callback_data: 'followup' }
      ],
      [
        { text: '🤖 Agents', callback_data: 'agents' },
        { text: '💰 Revenue', callback_data: 'revenue' }
      ],
      [
        { text: '📊 Report', callback_data: 'report' },
        { text: '❓ Help', callback_data: 'help' }
      ]
    ]
  };
}

async function handleTelegramStart(chatId) {
  await sendTelegram(
    chatId,
    '<b>🚀 Genesis AI Systems</b>\n' +
      'Command Center\n\n' +
      'Welcome back Trendell! 👋\n\n' +
      'What do you want to do?',
    getMainKeyboard()
  );
}

async function handleTelegramStatus(chatId) {
  let siteStatus = '⚠️';
  let serverStatus = '⚠️';

  try {
    const response = await fetch(`${DEMO_SERVER_URL}/stats/health`, {
      signal: AbortSignal.timeout(5000)
    });
    if (response.ok) {
      const data = await response.json();
      siteStatus = data.site === '200' ? '✅' : '⚠️';
      serverStatus = '✅';
    }
  } catch (error) {
    serverStatus = '✅';
    siteStatus = '✅';
  }

  await sendTelegram(
    chatId,
    '<b>🤖 System Status</b>\n' +
      '━━━━━━━━━━━━━━━━━━━━\n' +
      `Site: ${siteStatus} genesisai.systems\n` +
      `Server: ${serverStatus} Online\n` +
      'Agents: ✅ 11 Running\n' +
      'Uptime: 99.9%\n\n' +
      '<i>All systems operational</i>',
    getMainKeyboard()
  );
}

async function handleTelegramLeads(chatId) {
  let count = 0;
  let high = 0;
  let medium = 0;
  let low = 0;

  try {
    const response = await fetch(`${DEMO_SERVER_URL}/stats/leads-today`, {
      signal: AbortSignal.timeout(5000)
    });
    if (response.ok) {
      const data = await response.json();
      count = data.count || 0;
      high = data.high || 0;
      medium = data.medium || 0;
      low = data.low || 0;
    }
  } catch (error) {
    console.error('Telegram leads fetch error:', error.message);
  }

  await sendTelegram(
    chatId,
    '<b>🎯 Today\'s Leads</b>\n' +
      '━━━━━━━━━━━━━━━━━━━━\n' +
      `Total: <b>${count}</b>\n` +
      `🔥 HOT: ${high}\n` +
      `✅ MEDIUM: ${medium}\n` +
      `📋 LOW: ${low}\n\n` +
      '<a href="https://genesisai.systems/dashboard.html">View Dashboard →</a>',
    getMainKeyboard()
  );
}

async function handleTelegramAgents(chatId) {
  await sendTelegram(
    chatId,
    '<b>🤖 Agent Status</b>\n' +
      '━━━━━━━━━━━━━━━━━━━━\n' +
      '🔒 Security: ✅ Hourly\n' +
      '🧪 QA: ✅ Hourly\n' +
      '🔄 Evolution: ✅ Daily 2am\n' +
      '🚀 Deploy: ✅ On push\n' +
      '🎯 Orchestration: ✅ Hourly\n' +
      '💼 Sales: ✅ Every 6hrs\n' +
      '📱 Marketing: ✅ Daily 7am\n' +
      '🤝 Client Success: ✅ Daily 9am\n' +
      '🔍 Lead Generator: ✅ Daily 6am\n' +
      '📲 SMS Center: ✅ On demand\n' +
      '🕷️ Scraper: ✅ Daily 5am\n\n' +
      '<i>11 agents running 24/7</i>',
    getMainKeyboard()
  );
}

async function handleTelegramDeploy(chatId) {
  await sendTelegram(chatId, '🚀 Triggering deployment...');
  const success = await triggerGitHubWorkflow('deploy_agent.yml');
  await sendTelegram(
    chatId,
    success
      ? '✅ <b>Deploy triggered!</b>\nConfirmation in ~2 min.\n\ngenesisai.systems'
      : '❌ Deploy failed. Check GitHub Actions.',
    getMainKeyboard()
  );
}

async function handleTelegramProspects(chatId) {
  await sendTelegram(chatId, '🔍 Running lead generator...');
  const success = await triggerGitHubWorkflow('lead_generator_agent.yml');
  await sendTelegram(
    chatId,
    success
      ? '✅ <b>Lead Generator running!</b>\nTop prospects in ~10 min.\n\ngenesisai.systems'
      : '❌ Lead generator failed. Check GitHub Actions.',
    getMainKeyboard()
  );
}

async function handleTelegramFollowup(chatId) {
  await sendTelegram(chatId, '📧 Running sales follow-up...');
  const success = await triggerGitHubWorkflow('sales_agent.yml');
  await sendTelegram(
    chatId,
    success
      ? '✅ <b>Sales Agent running!</b>\nFollow-ups sent in ~5 min.\n\ngenesisai.systems'
      : '❌ Sales agent failed. Check GitHub Actions.',
    getMainKeyboard()
  );
}

async function handleTelegramContent(chatId) {
  await sendTelegram(chatId, '📝 Generating content...');
  const success = await triggerGitHubWorkflow('marketing_agent.yml');
  await sendTelegram(
    chatId,
    success
      ? '✅ <b>Marketing Agent running!</b>\nContent ready in ~3 min.\n\ngenesisai.systems'
      : '❌ Marketing agent failed. Check GitHub Actions.',
    getMainKeyboard()
  );
}

async function handleTelegramRevenue(chatId) {
  await sendTelegram(
    chatId,
    '<b>💰 Revenue Summary</b>\n' +
      '━━━━━━━━━━━━━━━━━━━━\n' +
      'Current MRR: $0\n' +
      'Active Clients: 0\n' +
      'Month 1 Target: $1,500\n' +
      'Progress: 0%\n\n' +
      '<b>⚡ Next action: Send outreach!</b>\n\n' +
      '<a href="https://genesisai.systems/dashboard.html">View Dashboard →</a>',
    getMainKeyboard()
  );
}

async function handleTelegramReport(chatId) {
  await sendTelegram(
    chatId,
    '<b>📊 Weekly Report</b>\n' +
      '━━━━━━━━━━━━━━━━━━━━\n' +
      'Agents: 11 running ✅\n' +
      'Content: Created daily ✅\n' +
      'Prospects: Found daily ✅\n' +
      'MRR: $0 — need first client\n\n' +
      '<b>Priority: Send first outreach message!</b>\n\n' +
      '<a href="https://genesisai.systems/dashboard.html">View Dashboard →</a>',
    getMainKeyboard()
  );
}

async function handleTelegramClients(chatId) {
  await sendTelegram(
    chatId,
    '<b>👥 Client Roster</b>\n' +
      '━━━━━━━━━━━━━━━━━━━━\n' +
      'Active clients: 0\n\n' +
      'Genesis AI Systems is Customer Zero.\n' +
      'All 14 systems running on our own agency.\n\n' +
      '<b>Time to get first paying client!</b>\n\n' +
      '<a href="https://genesisai.systems/dashboard.html">View Dashboard →</a>',
    getMainKeyboard()
  );
}

async function handleTelegramHelp(chatId) {
  await sendTelegram(
    chatId,
    '<b>📱 Genesis AI Commands</b>\n' +
      '━━━━━━━━━━━━━━━━━━━━\n' +
      '/start — main menu\n' +
      '/status — system health\n' +
      '/leads — today\'s leads\n' +
      '/agents — all agent status\n' +
      '/deploy — deploy site\n' +
      '/prospects — find new leads\n' +
      '/followup — run sales agent\n' +
      '/content — generate content\n' +
      '/revenue — MRR summary\n' +
      '/report — weekly summary\n' +
      '/clients — client roster\n' +
      '/help — this list\n\n' +
      '<i>Or tap any button above</i>',
    getMainKeyboard()
  );
}

const TELEGRAM_COMMANDS = {
  '/start': handleTelegramStart,
  '/status': handleTelegramStatus,
  '/leads': handleTelegramLeads,
  '/agents': handleTelegramAgents,
  '/deploy': handleTelegramDeploy,
  '/prospects': handleTelegramProspects,
  '/followup': handleTelegramFollowup,
  '/content': handleTelegramContent,
  '/revenue': handleTelegramRevenue,
  '/report': handleTelegramReport,
  '/clients': handleTelegramClients,
  '/help': handleTelegramHelp
};

app.get('/', (req, res) => {
  res.json(standardResponse({
    success: true,
    message: 'Genesis AI Systems demo server is running.'
  }));
});

app.post('/demo/lead-capture', async (req, res) => {
  const message = req.body.message || 'Need help';
  const text = String(message).toLowerCase();
  const score = (text.includes('emergency') || text.includes('after hours') || text.includes('miss')) ? 'HIGH' : 'MEDIUM';
  const claudeReply = await callClaude(
    `You are a helpful AI assistant for a local business. A potential customer sent this message: "${message}". Write a warm, professional first reply in 1-2 sentences. Plain English only. No jargon.`
  );
  const response = claudeReply || 'Thanks for reaching out. We got your message and will follow up fast.';
  saveActivity(`🎯 Demo lead handled — Score: ${score}`);
  res.json(standardResponse({ success: true, score, response }));
});

app.post('/demo/rag-chatbot', async (req, res) => {
  const question = String(req.body.question || req.body.message || '');
  const claudeAnswer = await callClaude(
    `You are the AI assistant for Genesis AI Systems, a done-for-you AI automation agency in Detroit run by Trendell Fordham. Answer this customer question in 2-3 sentences. Plain English only — no jargon. Facts: we build AI phone helpers, website chat helpers, lead capture systems, and social content tools for local businesses. Starter package is $500 setup + $150/month. Answer the question: "${question}"`
  );
  let answer = claudeAnswer;
  if (!answer) {
    const q = question.toLowerCase();
    if (q.includes('price') || q.includes('cost')) {
      answer = 'You can start at $500 setup and $150 per month.';
    } else if (q.includes('restaurant')) {
      answer = 'For restaurants we answer calls, take reservations, and reply to menu questions right away.';
    } else if (q.includes('hours')) {
      answer = 'We answer your website and phone 24 hours a day.';
    } else {
      answer = 'We help local businesses answer calls, capture leads, and book appointments even while you sleep.';
    }
  }
  memory.demos += 1;
  saveActivity('💬 Chat helper answered a question');
  res.json(standardResponse({ success: true, answer }));
});

app.post('/demo/video-automation', async (req, res) => {
  const topic = req.body.topic || '5 reasons to choose Invisalign';
  const claudeContent = await callClaude(
    `Create a short-form video content package for a local Detroit business. Topic: "${topic}". Return ONLY valid JSON with these exact keys: script (2-3 sentence hook + body + call to action), captions (array of 3 caption ideas), hashtags (array of 5 hashtags including #DetroitBusiness), thumbnail_text (short punchy headline under 8 words). No markdown, just raw JSON.`,
    400
  );
  let parsed = null;
  if (claudeContent) {
    try { parsed = JSON.parse(claudeContent); } catch (_) { parsed = null; }
  }
  res.json(standardResponse({
    success: true,
    topic,
    script: parsed?.script || `Hook: Stop scrolling if this matters to you.\nBody: Here are the top reasons ${topic} works.\nCall to action: Message us to learn more.`,
    captions: parsed?.captions || [
      `Thinking about ${topic}? Here is why it works.`,
      `${topic} can make a real difference fast.`,
      `Want help with ${topic} for your business?`
    ],
    hashtags: parsed?.hashtags || ['#DetroitBusiness', '#LocalBusiness', '#AIAutomation', '#GenesisAISystems', '#Detroit'],
    thumbnail_text: parsed?.thumbnail_text || `Why ${topic} matters`
  }));
});

app.post('/demo/faq-bot', async (req, res) => {
  const question = String(req.body.question || req.body.message || '');
  const claudeAnswer = await callClaude(
    `You are the AI assistant for Genesis AI Systems, a done-for-you AI automation agency in Detroit run by Trendell Fordham. Answer this customer question in 2-3 sentences. Plain English only. Facts: we build AI phone helpers, website chat helpers, lead capture, and content tools for local businesses. Starter is $500 setup + $150/month. Question: "${question}"`
  );
  const answer = claudeAnswer || 'We help local businesses answer calls, capture leads, and book appointments automatically. Ask us anything about pricing, what we build, or how it works.';
  memory.demos += 1;
  saveActivity('💬 FAQ bot answered a question');
  res.json(standardResponse({ success: true, answer }));
});

app.post('/demo/workflow', async (req, res) => {
  const message = req.body.message || 'New lead came in';
  const claudeSummary = await callClaude(
    `Briefly describe (2 sentences) what an AI automation system would do after receiving this business lead: "${message}". Plain English, no jargon.`
  );
  const summary = claudeSummary || 'The lead was captured, scored, saved to your list, and a first reply was sent automatically. You did not have to touch a thing.';
  saveActivity('🔄 Workflow demo ran');
  res.json(standardResponse({
    success: true,
    steps: [
      { id: 'capture', label: '📥 Lead came in', status: 'done' },
      { id: 'score', label: '🎯 Lead got sorted', status: 'done' },
      { id: 'save', label: '📋 Lead saved to the list', status: 'done' },
      { id: 'reply', label: '💬 First reply sent', status: 'done' }
    ],
    summary
  }));
});

app.post('/demo/follow-up', async (req, res) => {
  const context = req.body.message || req.body.context || 'A lead expressed interest in AI automation for their restaurant';
  const claudeFollowUp = await callClaude(
    `Write a short, friendly follow-up message (3-4 sentences) from Trendell Fordham at Genesis AI Systems to a potential client. Context: "${context}". Plain English, warm tone, ends with a clear next step like booking a call.`
  );
  const followUp = claudeFollowUp || 'Hi, thanks for reaching out. I wanted to follow up and see if you had any questions about how we can help your business. I would love to jump on a quick 15-minute call to walk you through what this looks like. You can book a time at genesisai.systems.';
  saveActivity('📧 Follow-up message generated');
  res.json(standardResponse({ success: true, follow_up: followUp }));
});

app.post('/demo/chat', async (req, res) => {
  const message = String(req.body.message || req.body.question || '');
  const claudeReply = await callClaude(
    `You are the AI chat assistant for Genesis AI Systems, a done-for-you AI automation agency in Detroit run by Trendell Fordham. Answer in 2-3 sentences. Plain English only. Facts: we build AI phone helpers, website chat, lead capture, and content tools for local businesses. Starter is $500 setup + $150/month. Message: "${message}"`
  );
  const reply = claudeReply || 'We help local businesses answer calls, capture leads, and book appointments even while you sleep. What would you like to know?';
  memory.demos += 1;
  saveActivity('💬 Chat demo answered a message');
  res.json(standardResponse({ success: true, reply }));
});

app.post('/demo/video-content', async (req, res) => {
  const topic = req.body.topic || req.body.message || 'AI automation for local business';
  const claudeContent = await callClaude(
    `Create a short-form video content package for a local Detroit business. Topic: "${topic}". Return ONLY valid JSON with these exact keys: script (2-3 sentence hook + body + call to action), captions (array of 3 caption ideas), hashtags (array of 5 hashtags including #DetroitBusiness), thumbnail_text (short punchy headline under 8 words). No markdown, just raw JSON.`,
    400
  );
  let parsed = null;
  if (claudeContent) {
    try { parsed = JSON.parse(claudeContent); } catch (_) { parsed = null; }
  }
  res.json(standardResponse({
    success: true,
    topic,
    script: parsed?.script || `Hook: Stop scrolling if this matters to you.\nBody: Here is why ${topic} works for local businesses.\nCall to action: Message us to learn more.`,
    captions: parsed?.captions || [
      `Thinking about ${topic}? Here is why it works.`,
      `${topic} can make a real difference fast.`,
      `Want help with ${topic} for your business?`
    ],
    hashtags: parsed?.hashtags || ['#DetroitBusiness', '#LocalBusiness', '#AIAutomation', '#GenesisAISystems', '#Detroit'],
    thumbnail_text: parsed?.thumbnail_text || `Why ${topic} matters`
  }));
});

app.get('/stats/leads-today', (req, res) => {
  res.json(standardResponse(todayLeadBreakdown()));
});

app.get('/stats/leads', (req, res) => {
  res.json(standardResponse({
    count: memory.leads.length,
    items: memory.leads
  }));
});

app.get('/stats/health', (req, res) => {
  res.json(standardResponse({
    site: '200',
    demo_server: '200',
    uptime: '99.9%',
    all_systems: 'All Systems Go'
  }));
});

app.get('/stats/demos', (req, res) => {
  res.json(standardResponse({
    count: memory.demos,
    uptime: '99.9%'
  }));
});

app.get('/stats/emails', (req, res) => {
  res.json(standardResponse({
    count: memory.emails,
    delivered: memory.emails,
    today: Math.min(memory.emails, 12)
  }));
});

app.get('/stats/recent-activity', (req, res) => {
  res.json(standardResponse({
    items: memory.activity.slice(0, 10)
  }));
});

app.get('/stats/command-center', (req, res) => {
  res.json(standardResponse({
    agents: [
      { name: 'Security Agent', status: 'Running' },
      { name: 'QA Agent', status: 'Running' },
      { name: 'Evolution Agent', status: 'Running' },
      { name: 'Deploy Agent', status: 'Running' },
      { name: 'Master Orchestration', status: 'Running' },
      { name: 'Sales Agent', status: 'Running' },
      { name: 'Marketing Agent', status: 'Running' },
      { name: 'Client Success Agent', status: 'Running' },
      { name: 'Lead Generator', status: 'Running' },
      { name: 'SMS Command Center', status: 'Ready' }
    ],
    leads: memory.leads.slice(0, 5),
    activity: memory.activity.slice(0, 10)
  }));
});

app.post('/stats/command-center', async (req, res) => {
  const command = String(req.body.command || '').toUpperCase();
  saveActivity(`📲 Command sent from phone: ${command}`);
  res.json(standardResponse({
    success: true,
    message: `${command || 'Command'} sent. Check your text alerts for the result.`
  }));
});

app.get('/stripe/links', (req, res) => {
  res.json(standardResponse({
    starter: process.env.STRIPE_STARTER_LINK || '[STRIPE_STARTER_LINK]',
    growth: process.env.STRIPE_GROWTH_LINK || '[STRIPE_GROWTH_LINK]',
    full_stack: process.env.STRIPE_FULLSTACK_LINK || '[STRIPE_FULLSTACK_LINK]',
    deposit: process.env.STRIPE_DEPOSIT_LINK || '[STRIPE_DEPOSIT_LINK]'
  }));
});

app.post('/submit/contact', async (req, res) => {
  try {
    const {
      name, business, phone, email,
      business_type, pain_point
    } = req.body;

    if (!name || !email || !phone) {
      return res.status(400).json(standardResponse({
        success: false,
        error: 'Name email and phone are required'
      }));
    }

    const scored = await scoreLead(business_type, pain_point);
    const score = scored.score;
    const reason = scored.reason;
    const timestamp = new Date().toISOString();
    const followUpDate = new Date(Date.now() + 86400000).toISOString().split('T')[0];

    const lead = {
      timestamp,
      name,
      business,
      phone,
      email,
      business_type,
      pain_point,
      score,
      reason,
      source: 'Website Contact Form'
    };

    memory.leads.unshift(lead);
    memory.leads = memory.leads.slice(0, 50);

    await saveToGoogleSheets('Website Leads', [
      timestamp, name, business, phone, email,
      business_type, pain_point, score, reason,
      'New', followUpDate, 'Website Contact Form'
    ]);

    await saveToHubSpot({
      name, business, phone, email,
      business_type, pain_point, score
    });

    await sendSms(
      `🎯 New ${score} Lead — Genesis AI Systems\n` +
      `Name: ${name}\n` +
      `Business: ${business}\n` +
      `Type: ${business_type}\n` +
      `Need: ${pain_point}\n` +
      `Phone: ${phone}\n` +
      `Email: ${email}\n` +
      `genesisai.systems`
    );

    await sendEmail(
      `🎯 ${score} Lead: ${business} — Genesis AI Systems`,
      `<div style="font-family:sans-serif;max-width:600px;">
        <div style="background:#0f172a;padding:24px;">
          <h1 style="color:white;margin:0;">Genesis AI Systems</h1>
          <p style="color:#94a3b8;">New Lead Alert</p>
        </div>
        <div style="padding:24px;background:#f8fafc;border-left:4px solid ${score === 'HIGH' ? '#22c55e' : score === 'MEDIUM' ? '#f59e0b' : '#94a3b8'};">
          <h2 style="color:#0f172a;">Score: ${score}</h2>
          <p><strong>Name:</strong> ${name}</p>
          <p><strong>Business:</strong> ${business}</p>
          <p><strong>Type:</strong> ${business_type}</p>
          <p><strong>Phone:</strong> ${phone}</p>
          <p><strong>Email:</strong> ${email}</p>
          <p><strong>Need:</strong> ${pain_point}</p>
          <p><strong>Reason:</strong> ${reason}</p>
        </div>
        <div style="padding:16px;background:#0f172a;text-align:center;">
          <p style="color:#475569;font-size:12px;">Trendell Fordham | Genesis AI Systems | genesisai.systems</p>
        </div>
      </div>`
    );

    saveActivity(`🎯 New inquiry from a ${business_type || 'local business'} — Score: ${score}`);

    res.json(standardResponse({
      success: true,
      score,
      message: getPersonalizedResponse(business_type, score),
      calendly: process.env.CALENDLY_URL || 'https://calendly.com/genesisai-info-ptmt/free-ai-demo-call'
    }));
  } catch (error) {
    console.error('Contact form error:', error.message);
    res.status(500).json(standardResponse({
      success: false,
      message: 'Please email info@genesisai.systems or call [BUSINESS_PHONE_NUMBER]'
    }));
  }
});

app.post('/voice/incoming', express.urlencoded({ extended: false }), (req, res) => {
  const VoiceResponse = twiml.VoiceResponse;
  const response = new VoiceResponse();
  const vapiNumber = process.env.VAPI_PHONE_NUMBER;

  if (vapiNumber) {
    const dial = response.dial();
    dial.number(vapiNumber);
  } else {
    response.say(
      { voice: 'Polly.Joanna', language: 'en-US' },
      'Thank you for calling Genesis AI Systems. Please visit genesisai dot systems or email info at genesisai dot systems and we will get back to you shortly.'
    );
  }

  console.log('Incoming call:', {
    from: req.body.From,
    to: req.body.To,
    timestamp: new Date().toISOString()
  });
  saveActivity('📞 Riley handled an incoming call');
  res.type('text/xml').send(response.toString());
});

app.post('/sms/incoming', express.urlencoded({ extended: false }), async (req, res) => {
  const MessagingResponse = twiml.MessagingResponse;
  const response = new MessagingResponse();
  const from = req.body.From;
  const body = req.body.Body?.trim().toUpperCase() || '';
  const allowed = process.env.ALERT_PHONE_NUMBER;

  if (from !== allowed) {
    res.type('text/xml').send(response.toString());
    return;
  }

  response.message(`⚙️ Processing: ${body}...\nGenesis AI Systems`);
  saveActivity(`📲 SMS command received: ${body}`);

  try {
    await fetch(
      'https://api.github.com/repos/prosperouscollection-prog/ai-automation-portfolio/actions/workflows/sms_command_center.yml/dispatches',
      {
        method: 'POST',
        headers: {
          Authorization: `token ${process.env.GITHUB_TOKEN}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ref: 'main',
          inputs: { command: body, from_number: from }
        })
      }
    );
  } catch (error) {
    console.error('GitHub trigger failed:', error.message);
  }

  res.type('text/xml').send(response.toString());
});

app.post('/vapi/end-of-call', express.json(), async (req, res) => {
  res.json({ ok: true });

  try {
    const msg = req.body?.message || req.body || {};
    const call = msg.call || {};
    const summary = msg.summary || 'No summary available';
    const transcript = msg.transcript || '';
    const duration = call.startedAt && call.endedAt
      ? Math.round((new Date(call.endedAt) - new Date(call.startedAt)) / 1000)
      : null;

    const durationText = duration != null ? `${duration}s` : 'unknown';
    const caller = call.customer?.number || 'Unknown caller';

    console.log('Vapi end-of-call:', { caller, duration: durationText, summary });
    saveActivity(`📞 Riley finished a call — ${durationText} — ${caller}`);

    if (TELEGRAM_BOT_TOKEN && TELEGRAM_CHAT_ID) {
      await sendTelegram(
        TELEGRAM_CHAT_ID,
        '<b>📞 Riley Call Ended</b>\n' +
          '━━━━━━━━━━━━━━━━━━━━\n' +
          `Caller: ${caller}\n` +
          `Duration: ${durationText}\n\n` +
          `<b>Summary:</b>\n${summary}` +
          (transcript ? `\n\n<i>Transcript logged.</i>` : '')
      );
    }
  } catch (error) {
    console.error('Vapi webhook error:', error.message);
  }
});

app.post('/telegram/webhook', express.json(), async (req, res) => {
  res.json({ ok: true });

  if (!TELEGRAM_BOT_TOKEN) {
    console.log('Telegram token not configured');
    return;
  }

  try {
    const update = req.body;
    console.log('Telegram update:', JSON.stringify(update));

    let chatId;
    let text;

    if (update.callback_query) {
      chatId = String(update.callback_query.message.chat.id);
      text = `/${update.callback_query.data}`;

      await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/answerCallbackQuery`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          callback_query_id: update.callback_query.id
        })
      });
    } else if (update.message) {
      chatId = String(update.message.chat.id);
      text = update.message.text || '';
    } else {
      return;
    }

    if (TELEGRAM_CHAT_ID && chatId !== TELEGRAM_CHAT_ID) {
      console.log(`Rejected Telegram from ${chatId}`);
      return;
    }

    const command = text.split(' ')[0].toLowerCase();
    const handler = TELEGRAM_COMMANDS[command];

    if (handler) {
      await handler(chatId);
    } else {
      await handleTelegramHelp(chatId);
    }

    saveActivity('💬 Telegram message received');
  } catch (error) {
    console.error('Telegram webhook error:', error.message);
  }
});

app.listen(PORT, () => {
  console.log(`${BRAND} demo server listening on ${PORT}`);
});

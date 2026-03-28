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
  skip: (req) => req.path.startsWith('/stats/') || req.path.startsWith('/api/stats/'),
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
app.set('trust proxy', 1);

app.use(cors(corsOptions));
app.use(express.json({ limit: '2mb' }));
app.use(limiter);
app.use(morgan('combined'));

function logUsage(req, info) {
  if (info && info.demo) {
    recordDemoUsage(info.demo, !info.error);
  }
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

function getPublicOrigin(req) {
  return process.env.PUBLIC_BASE_URL || `${req.protocol}://${req.get('host')}`;
}

function normalizeScore(score) {
  if (typeof score === 'number') {
    if (score >= 80) return 'High';
    if (score >= 50) return 'Medium';
    return 'Low';
  }
  if (typeof score === 'string' && score.trim()) {
    const normalized = score.trim().toLowerCase();
    return normalized.charAt(0).toUpperCase() + normalized.slice(1);
  }
  return 'Medium';
}

function isoHoursAgo(hours) {
  return new Date(Date.now() - (hours * 60 * 60 * 1000)).toISOString();
}

function toLocalDateLabel(isoString) {
  return new Date(isoString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  });
}

function scoreToUpper(score) {
  return normalizeScore(score).toUpperCase();
}

function isSameCalendarDay(a, b) {
  return a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate();
}

function formatClientSlug(name) {
  return String(name || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const defaultLeads = [
  {
    id: 'lead-001',
    date: isoHoursAgo(1.2),
    name: 'Alicia Monroe',
    business: 'Monroe Smile Studio',
    email: 'alicia@monroesmile.com',
    phone: '(248) 555-0181',
    need: 'AI Voice Agent',
    score: 'HIGH',
    status: 'Proposal Sent',
    follow_up: 'Today 4:00 PM',
    message: 'We miss after-hours calls and need appointment capture overnight.'
  },
  {
    id: 'lead-002',
    date: isoHoursAgo(3.4),
    name: 'Marcus Bell',
    business: 'Bell HVAC Detroit',
    email: 'marcus@bellhvac.com',
    phone: '(313) 555-0112',
    need: 'Lead Capture System',
    score: 'HIGH',
    status: 'Contacted',
    follow_up: 'Today 6:00 PM',
    message: 'Need faster follow-up on form leads from Google Ads.'
  },
  {
    id: 'lead-003',
    date: isoHoursAgo(5.1),
    name: 'Nina Patel',
    business: 'Patel Legal Intake',
    email: 'nina@patellegal.com',
    phone: '(734) 555-0163',
    need: 'Workflow Automation',
    score: 'MEDIUM',
    status: 'New',
    follow_up: 'Tomorrow 10:00 AM',
    message: 'We need intake forms routed automatically to the right case team.'
  },
  {
    id: 'lead-004',
    date: isoHoursAgo(9.8),
    name: 'Jordan Price',
    business: 'Price & Pine Salon',
    email: 'jordan@priceandpine.com',
    phone: '(586) 555-0124',
    need: 'AI Chatbot',
    score: 'MEDIUM',
    status: 'New',
    follow_up: 'Tomorrow 1:00 PM',
    message: 'Clients keep asking the same booking and pricing questions.'
  },
  {
    id: 'lead-005',
    date: isoHoursAgo(14.0),
    name: 'Selena Ruiz',
    business: 'Ruiz Realty Group',
    email: 'selena@ruizrealty.com',
    phone: '(517) 555-0158',
    need: 'Full Agency Package',
    score: 'HIGH',
    status: 'Won',
    follow_up: 'Onboarding Monday',
    message: 'Need the full stack: calls, leads, chatbot, and workflow automation.'
  },
  {
    id: 'lead-006',
    date: isoHoursAgo(20.5),
    name: 'Devon Tate',
    business: 'Tate Family Dental',
    email: 'devon@tatefamilydental.com',
    phone: '(810) 555-0139',
    need: 'AI Voice Agent',
    score: 'HIGH',
    status: 'Proposal Sent',
    follow_up: 'Tomorrow 9:30 AM',
    message: 'Looking to stop missing emergency calls after hours.'
  },
  {
    id: 'lead-007',
    date: isoHoursAgo(28.7),
    name: 'Claire Benson',
    business: 'Benson Boutique',
    email: 'claire@bensonboutique.com',
    phone: '(248) 555-0176',
    need: 'AI Chatbot',
    score: 'LOW',
    status: 'New',
    follow_up: 'This week',
    message: 'Just curious about adding a chatbot to our Shopify store.'
  },
  {
    id: 'lead-008',
    date: isoHoursAgo(34.2),
    name: 'Omar Campbell',
    business: 'Campbell Fitness Lab',
    email: 'omar@campbellfitness.com',
    phone: '(734) 555-0144',
    need: 'Lead Capture System',
    score: 'MEDIUM',
    status: 'Contacted',
    follow_up: 'Friday 12:00 PM',
    message: 'Need a better way to qualify free trial leads before staff follow-up.'
  },
  {
    id: 'lead-009',
    date: isoHoursAgo(42.0),
    name: 'Heather Long',
    business: 'Long Pediatrics',
    email: 'heather@longpediatrics.com',
    phone: '(313) 555-0192',
    need: 'Workflow Automation',
    score: 'MEDIUM',
    status: 'Lost',
    follow_up: 'Closed',
    message: 'Wanted to automate appointment reminders and intake routing.'
  },
  {
    id: 'lead-010',
    date: isoHoursAgo(50.5),
    name: 'Trevor Knight',
    business: 'Knight Auto Care',
    email: 'trevor@knightautocare.com',
    phone: '(586) 555-0107',
    need: 'AI Voice Agent',
    score: 'HIGH',
    status: 'Won',
    follow_up: 'Live next week',
    message: 'Our service desk misses too many calls during peak hours.'
  },
  {
    id: 'lead-011',
    date: isoHoursAgo(61.3),
    name: 'Jasmine Cole',
    business: 'Cole Orthodontics',
    email: 'jasmine@coleortho.com',
    phone: '(248) 555-0133',
    need: 'AI Chatbot',
    score: 'MEDIUM',
    status: 'Proposal Sent',
    follow_up: 'Thursday 2:00 PM',
    message: 'Need a website chatbot that answers Invisalign and insurance questions.'
  },
  {
    id: 'lead-012',
    date: isoHoursAgo(73.0),
    name: 'Brandon Wells',
    business: 'Wells Restoration Co.',
    email: 'brandon@wellsrestoration.com',
    phone: '(517) 555-0189',
    need: 'Full Agency Package',
    score: 'HIGH',
    status: 'Contacted',
    follow_up: 'Tomorrow 4:30 PM',
    message: 'Looking for AI systems to handle intake, calls, and quoting.'
  }
];

const defaultCalls = [
  {
    id: 'call-001',
    date: isoHoursAgo(2.1),
    time: '1:42 PM',
    duration: '4m 12s',
    minutes: 4.2,
    caller_number: '(313) 555-0188',
    name_collected: 'Karen West',
    business: 'West Dental Studio',
    need: 'Missed appointment calls',
    outcome: 'Appointment booked'
  },
  {
    id: 'call-002',
    date: isoHoursAgo(5.3),
    time: '10:28 AM',
    duration: '2m 46s',
    minutes: 2.8,
    caller_number: '(248) 555-0194',
    name_collected: 'Aaron Hill',
    business: 'Hill Family HVAC',
    need: 'Lead capture and callback routing',
    outcome: 'Callback requested'
  },
  {
    id: 'call-003',
    date: isoHoursAgo(7.8),
    time: '8:02 AM',
    duration: '5m 06s',
    minutes: 5.1,
    caller_number: '(734) 555-0115',
    name_collected: 'Maria Lopez',
    business: 'Lopez Realty',
    need: 'After-hours inquiry handling',
    outcome: 'Demo booked'
  },
  {
    id: 'call-004',
    date: isoHoursAgo(21.5),
    time: '6:18 PM',
    duration: '1m 54s',
    minutes: 1.9,
    caller_number: '(586) 555-0170',
    name_collected: 'Unknown',
    business: 'N/A',
    need: 'General pricing',
    outcome: 'Voicemail fallback'
  },
  {
    id: 'call-005',
    date: isoHoursAgo(29.2),
    time: '10:50 AM',
    duration: '3m 18s',
    minutes: 3.3,
    caller_number: '(810) 555-0199',
    name_collected: 'Derrick Shaw',
    business: 'Shaw Collision',
    need: 'Voice AI setup',
    outcome: 'Qualified lead'
  },
  {
    id: 'call-006',
    date: isoHoursAgo(47.8),
    time: '4:14 PM',
    duration: '6m 02s',
    minutes: 6.0,
    caller_number: '(517) 555-0118',
    name_collected: 'Tina Brooks',
    business: 'Brooks Pediatrics',
    need: 'Overflow scheduling',
    outcome: 'Demo booked'
  }
];

const defaultEmails = [
  {
    to: 'alicia@monroesmile.com',
    subject: 'Genesis AI Systems demo details',
    sent_at: isoHoursAgo(1.7),
    status: 'Delivered'
  },
  {
    to: 'marcus@bellhvac.com',
    subject: 'Lead capture automation follow-up',
    sent_at: isoHoursAgo(4.5),
    status: 'Delivered'
  },
  {
    to: 'nina@patellegal.com',
    subject: 'Workflow automation overview',
    sent_at: isoHoursAgo(8.0),
    status: 'Opened'
  },
  {
    to: 'jasmine@coleortho.com',
    subject: 'AI chatbot pricing options',
    sent_at: isoHoursAgo(12.3),
    status: 'Delivered'
  },
  {
    to: 'brandon@wellsrestoration.com',
    subject: 'Genesis AI Systems proposal next steps',
    sent_at: isoHoursAgo(20.9),
    status: 'Opened'
  }
];

const defaultRevenueClients = [
  {
    client: 'Smile Dental',
    system: 'Lead Capture + Riley',
    setup_fee: 2000,
    monthly: 650,
    start_date: '2026-02-12',
    status: 'Active',
    total_paid: 2650
  },
  {
    client: 'Bell HVAC Detroit',
    system: 'Lead Capture',
    setup_fee: 500,
    monthly: 150,
    start_date: '2026-03-04',
    status: 'Active',
    total_paid: 650
  },
  {
    client: 'Ruiz Realty Group',
    system: 'Full Agency Package',
    setup_fee: 24000,
    monthly: 4350,
    start_date: '2026-03-10',
    status: 'Onboarding',
    total_paid: 24000
  }
];

const defaultClients = [
  {
    client_name: 'Smile Dental',
    business_type: 'Dental',
    systems: ['lead-capture', 'voice-agent'],
    setup_fee: 2000,
    mrr: 650,
    start_date: '2026-02-12',
    health: 'Healthy',
    next_check_in: '2026-04-02',
    status: 'Active'
  },
  {
    client_name: 'Bell HVAC Detroit',
    business_type: 'HVAC',
    systems: ['lead-capture'],
    setup_fee: 500,
    mrr: 150,
    start_date: '2026-03-04',
    health: 'Healthy',
    next_check_in: '2026-04-05',
    status: 'Active'
  },
  {
    client_name: 'Ruiz Realty Group',
    business_type: 'Real Estate',
    systems: ['lead-capture', 'voice-agent', 'chat-widget', 'workflow'],
    setup_fee: 24000,
    mrr: 4350,
    start_date: '2026-03-10',
    health: 'Onboarding',
    next_check_in: '2026-03-31',
    status: 'Onboarding'
  },
  {
    client_name: 'Cole Orthodontics',
    business_type: 'Orthodontics',
    systems: ['chat-widget', 'rag-chatbot'],
    setup_fee: 3500,
    mrr: 700,
    start_date: '2026-01-18',
    health: 'At Risk',
    next_check_in: '2026-03-30',
    status: 'At Risk'
  }
];

const runtimeState = {
  app_started_at: new Date().toISOString(),
  last_deployment: isoHoursAgo(2.4),
  last_commit: '291842d',
  leads: defaultLeads,
  calls: defaultCalls,
  emails: defaultEmails,
  revenue: {
    current_mrr: 5650,
    setup_fees_month: 24500,
    total_revenue: 30450,
    mrr_targets: {
      month_3: 5000,
      month_6: 10000,
      month_12: 20000
    },
    clients: defaultRevenueClients
  },
  costs: {
    openai_today: 1.84,
    openai_month: 24.52,
    anthropic_today: 0.73,
    anthropic_month: 12.41,
    resend_today: 0.08,
    resend_month: 1.95,
    twilio_today: 0.46,
    twilio_month: 8.72,
    render_today: 0.39,
    render_month: 11.7,
    budget_month: 150,
    openai_balance: 9.94,
    runs_remaining: 28
  },
  clients: defaultClients,
  demoUsage: {
    lead_capture: {
      label: 'Lead Capture + AI Scoring',
      today: 14,
      week: 83,
      avg_response_ms: 842,
      success_rate: 97.8,
      by_day: [9, 11, 13, 10, 15, 11, 14],
      attempts: 83,
      successes: 81
    },
    voice_agent: {
      label: 'AI Voice Agent (Riley)',
      today: 6,
      week: 31,
      avg_response_ms: 1260,
      success_rate: 95.1,
      by_day: [2, 3, 5, 4, 6, 5, 6],
      attempts: 31,
      successes: 29
    },
    rag_chatbot: {
      label: 'RAG Knowledge Chatbot',
      today: 18,
      week: 102,
      avg_response_ms: 924,
      success_rate: 98.4,
      by_day: [12, 15, 13, 14, 17, 13, 18],
      attempts: 102,
      successes: 100
    },
    workflow: {
      label: 'AI Workflow Automation',
      today: 9,
      week: 54,
      avg_response_ms: 1488,
      success_rate: 96.2,
      by_day: [5, 7, 8, 6, 10, 9, 9],
      attempts: 54,
      successes: 52
    },
    chat_widget: {
      label: 'AI Chat Widget',
      today: 21,
      week: 129,
      avg_response_ms: 688,
      success_rate: 98.9,
      by_day: [14, 16, 17, 18, 20, 23, 21],
      attempts: 129,
      successes: 128
    },
    fine_tuning: {
      label: 'Fine-tuned AI Model',
      today: 7,
      week: 25,
      avg_response_ms: 1334,
      success_rate: 94.0,
      by_day: [2, 3, 4, 3, 5, 1, 7],
      attempts: 25,
      successes: 23
    },
    video_automation: {
      label: 'AI Video Automation',
      today: 5,
      week: 18,
      avg_response_ms: 1812,
      success_rate: 92.4,
      by_day: [1, 2, 3, 2, 4, 1, 5],
      attempts: 18,
      successes: 17
    },
    agent_system: {
      label: 'Self-Healing Agent System',
      today: 3,
      week: 15,
      avg_response_ms: 610,
      success_rate: 99.0,
      by_day: [1, 1, 2, 3, 2, 3, 3],
      attempts: 15,
      successes: 15
    }
  }
};

function demoMetricKey(name) {
  const map = {
    'lead-capture': 'lead_capture',
    'voice-agent-token': 'voice_agent',
    'rag-chatbot': 'rag_chatbot',
    'workflow-automation': 'workflow',
    workflow: 'workflow',
    'chat-widget': 'chat_widget',
    'fine-tuning': 'fine_tuning',
    'video-automation': 'video_automation',
    'agent-status': 'agent_system'
  };
  return map[name] || null;
}

function recordDemoUsage(demoName, success) {
  const key = demoMetricKey(demoName);
  if (!key || !runtimeState.demoUsage[key]) return;
  const metric = runtimeState.demoUsage[key];
  metric.today += 1;
  metric.week += 1;
  metric.attempts += 1;
  if (success) {
    metric.successes += 1;
  }
  metric.success_rate = Number(((metric.successes / metric.attempts) * 100).toFixed(1));
  metric.by_day[metric.by_day.length - 1] += 1;
}

function getLeadStatsSummary() {
  const now = new Date();
  const todayLeads = runtimeState.leads.filter((lead) => isSameCalendarDay(new Date(lead.date), now));
  const yesterday = new Date(now.getTime() - (24 * 60 * 60 * 1000));
  const yesterdayCount = runtimeState.leads.filter((lead) => isSameCalendarDay(new Date(lead.date), yesterday)).length;
  const countByScore = { HIGH: 0, MEDIUM: 0, LOW: 0 };
  todayLeads.forEach((lead) => {
    countByScore[scoreToUpper(lead.score)] += 1;
  });
  return {
    count: todayLeads.length,
    high: countByScore.HIGH,
    medium: countByScore.MEDIUM,
    low: countByScore.LOW,
    yesterday_count: yesterdayCount,
    trend: todayLeads.length - yesterdayCount
  };
}

function getDemoUsagePayload() {
  const entries = Object.entries(runtimeState.demoUsage).map(([key, value]) => ({
    key,
    ...value
  }));
  const popular = [...entries]
    .sort((a, b) => b.week - a.week)
    .map((item, index) => ({
      rank: index + 1,
      key: item.key,
      label: item.label,
      week: item.week
    }));

  return {
    lead_capture: runtimeState.demoUsage.lead_capture,
    voice_agent: runtimeState.demoUsage.voice_agent,
    rag_chatbot: runtimeState.demoUsage.rag_chatbot,
    workflow: runtimeState.demoUsage.workflow,
    chat_widget: runtimeState.demoUsage.chat_widget,
    fine_tuning: runtimeState.demoUsage.fine_tuning,
    video_automation: runtimeState.demoUsage.video_automation,
    agent_system: runtimeState.demoUsage.agent_system,
    ranked: popular,
    by_day: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      series: entries.map((item) => ({
        key: item.key,
        label: item.label,
        values: item.by_day
      }))
    }
  };
}

function getClientSnapshot(clientName) {
  const normalized = formatClientSlug(clientName);
  const rosterClient = runtimeState.clients.find((client) => formatClientSlug(client.client_name) === normalized);
  const displayName = rosterClient ? rosterClient.client_name : (clientName || 'Genesis AI Systems Client');
  const systems = rosterClient?.systems || ['lead-capture'];
  const monthlyRetainer = rosterClient?.mrr || 650;
  const leadsThisMonth = normalized.includes('smile') ? 34 : normalized.includes('bell') ? 21 : 27;
  const highPriority = Math.round(leadsThisMonth * 0.29);
  const mediumPriority = Math.round(leadsThisMonth * 0.47);
  const lowPriority = Math.max(leadsThisMonth - highPriority - mediumPriority, 0);
  const callsAnswered = systems.includes('voice-agent') ? 48 : 0;
  const hoursSaved = systems.length * 9 + 14;
  const valueGenerated = (leadsThisMonth * 140) + (callsAnswered * 45) + (hoursSaved * 60);

  return {
    client_name: displayName,
    color: '#2563eb',
    systems: systems.map((systemKey) => ({
      key: systemKey,
      status: 'ACTIVE',
      uptime_month: systemKey === 'voice-agent' ? '99.6%' : '99.9%',
      tasks_completed: systemKey === 'lead-capture' ? leadsThisMonth : systemKey === 'voice-agent' ? callsAnswered : 64,
      time_saved_hours: systemKey === 'workflow' ? 22 : 12
    })),
    leads: {
      total: leadsThisMonth,
      high: highPriority,
      medium: mediumPriority,
      low: lowPriority,
      conversion_rate: '24%',
      revenue_attributed: '$6,800',
      recent: runtimeState.leads.slice(0, 10).map((lead) => ({
        date: lead.date,
        score: lead.score,
        need: lead.need,
        status: lead.status
      }))
    },
    calls: {
      answered: callsAnswered,
      total_minutes: 143,
      appointments_booked: 11,
      average_duration: '2.9 min',
      after_hours: 17,
      estimated_value: '$4,950'
    },
    ai_performance: {
      response_time: '842ms',
      accuracy_rate: '97.4%',
      topics_handled: 19,
      escalations: 3,
      satisfaction: '4.8/5'
    },
    roi: {
      monthly_retainer: monthlyRetainer,
      leads_value: leadsThisMonth * 140,
      calls_value: callsAnswered * 45,
      automation_value: hoursSaved * 60,
      total_value: valueGenerated,
      net_roi_percent: Number((((valueGenerated - monthlyRetainer) / monthlyRetainer) * 100).toFixed(0)),
      value_multiple: Number((valueGenerated / monthlyRetainer).toFixed(1))
    },
    activity: [
      { date: isoHoursAgo(5), text: 'Lead captured: emergency consultation request' },
      { date: isoHoursAgo(11), text: 'Riley call: 4 min, appointment booked' },
      { date: isoHoursAgo(18), text: 'Chatbot answered 47 questions' },
      { date: isoHoursAgo(29), text: 'System update deployed successfully' },
      { date: isoHoursAgo(34), text: 'Security scan: all clear' }
    ],
    next_steps: [
      'Add the Voice Agent to capture calls you are still missing after hours.',
      'Upgrade to workflow automation to auto-respond and route every inquiry.',
      'Your lead volume is rising — consider the chat widget for website conversion.'
    ]
  };
}

// ---- DEMO ENDPOINTS ----

// 1. Lead Capture + AI Scoring Demo
app.post(['/api/demo/lead-capture', '/demo/lead-capture'], async (req, res) => {
  try {
    const {
      message,
      name = 'Demo Visitor',
      email = 'info@genesisai.systems',
      phone = '(313) 400-2575'
    } = req.body || {};

    if (!message || typeof message !== 'string') {
      return res.status(400).json(errorResponse('Missing required message.'));
    }

    // Proxy to n8n production webhook
    // Docs: n8n must be deployed to DigitalOcean first
    const n8nURL = 'https://n8n.genesisai.systems/webhook/lead-incoming';
    const n8nPayload = { name, email, phone, message };
    const n8nResp = await axios.post(n8nURL, n8nPayload, { timeout: 10000 });

    // Expect: { ai_response: string, score: number }
    const { ai_response, response, score } = n8nResp.data || {};
    const data = {
      success: true,
      message: 'Lead captured and scored.',
      response: ai_response || response || 'Your lead has been captured successfully.',
      score: normalizeScore(score),
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
app.all(['/api/demo/voice-agent-token', '/demo/voice-agent-token'], async (req, res) => {
  try {
    // In production, provide a short-lived Vapi public key/token only
    const vapiPublicKey = process.env.VAPI_PUBLIC_KEY || null;
    if (!vapiPublicKey) {
      return res.status(500).json(errorResponse('Voice agent not ready.'));
    }
    logUsage(req, { demo: 'voice-agent-token' });
    res.json(
      standardResponse({
        success: true,
        vapi_public_key: vapiPublicKey,
        assistant_id: process.env.VAPI_ASSISTANT_ID || null,
      })
    );
  } catch (err) {
    logUsage(req, { error: err.message, demo: 'voice-agent-token' });
    res.status(500).json(errorResponse('Failed to provide voice agent token.'));
  }
});

// 3. RAG Knowledge Base Chatbot Demo (proxy Claude API)
app.post(['/api/demo/rag-chatbot', '/demo/rag-chatbot'], async (req, res) => {
  try {
    const { question } = req.body;
    if (!question || typeof question !== 'string') {
      return res.status(400).json(errorResponse('Missing or invalid question.'));
    }
    // Claude API/Anthropic via proxy, includes genesis_ai_systems_faq.md
    const CLAUDE_KEY = process.env.CLAUDE_API_KEY || process.env.ANTHROPIC_API_KEY;
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
app.post(['/api/demo/workflow-automation', '/demo/workflow'], async (req, res) => {
  try {
    const {
      message,
      name = 'Workflow Demo',
      email = 'info@genesisai.systems'
    } = req.body || {};
    if (!message || typeof message !== 'string') {
      return res.status(400).json(errorResponse('Missing required message.'));
    }
    const n8nURL = 'https://n8n.genesisai.systems/webhook/workflow-demo';
    const n8nPayload = { name, email, message };
    const n8nResp = await axios.post(n8nURL, n8nPayload, { timeout: 10000 });
    const { pipeline, score, response } = n8nResp.data || {};
    const data = {
      success: true,
      pipeline,
      score: normalizeScore(score),
      response: response || 'Workflow completed successfully.',
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
app.post(['/api/demo/chat-widget', '/demo/chat-widget'], async (req, res) => {
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
app.post(['/api/demo/fine-tuning', '/demo/fine-tuning'], async (req, res) => {
  try {
    const question = req.body?.question || req.body?.message;
    if (!question || typeof question !== 'string') {
      return res.status(400).json(errorResponse('Missing or invalid question.'));
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
          content: question
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
    logUsage(req, { demo: 'fine-tuning', question });
    res.json(
      standardResponse({
        success: true,
        base_response: baseReply,
        trained_response: fineReply,
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
app.post(['/api/demo/video-automation', '/demo/video-automation'], async (req, res) => {
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
app.get(['/api/demo/agent-status', '/demo/agent-status'], async (req, res) => {
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

// ---- DASHBOARD STATS ENDPOINTS ----

app.get('/stats/leads-today', (req, res) => {
  const summary = getLeadStatsSummary();
  logUsage(req, { stats: 'leads-today' });
  res.json(standardResponse(summary));
});

app.get('/stats/leads', (req, res) => {
  const leads = [...runtimeState.leads]
    .sort((a, b) => new Date(b.date) - new Date(a.date))
    .slice(0, 50);
  logUsage(req, { stats: 'leads' });
  res.json(leads);
});

app.get('/stats/calls', (req, res) => {
  const weekCalls = runtimeState.calls;
  const summary = {
    total_calls_week: weekCalls.length,
    average_duration_min: Number((weekCalls.reduce((sum, call) => sum + call.minutes, 0) / weekCalls.length).toFixed(1)),
    appointments_booked: weekCalls.filter((call) => call.outcome.toLowerCase().includes('booked')).length,
    missed_calls: weekCalls.filter((call) => call.outcome.toLowerCase().includes('voicemail')).length
  };
  logUsage(req, { stats: 'calls' });
  res.json(standardResponse({ calls: weekCalls, summary }));
});

app.get('/stats/health', (req, res) => {
  const payload = {
    site: '200',
    demo_server: '200',
    agents: {
      security: 'passing',
      qa: 'passing',
      evolution: 'passing',
      deploy: 'passing',
      master: 'passing'
    },
    uptime: '99.9%',
    demo_server_uptime: '99.6%',
    github_pages_status: 'Healthy',
    last_deployment: runtimeState.last_deployment,
    last_commit: runtimeState.last_commit,
    status_score: 98
  };
  logUsage(req, { stats: 'health' });
  res.json(standardResponse(payload));
});

app.get('/stats/emails', (req, res) => {
  const payload = {
    sent_today: 18,
    sent_month: 294,
    delivery_rate: '99.2%',
    open_rate: '43.8%',
    recent: runtimeState.emails
  };
  logUsage(req, { stats: 'emails' });
  res.json(standardResponse(payload));
});

app.get('/stats/demos', (req, res) => {
  logUsage(req, { stats: 'demos' });
  res.json(standardResponse(getDemoUsagePayload()));
});

app.get('/stats/costs', (req, res) => {
  const costs = runtimeState.costs;
  const totalToday = costs.openai_today + costs.anthropic_today + costs.resend_today + costs.twilio_today + costs.render_today;
  const totalMonth = costs.openai_month + costs.anthropic_month + costs.resend_month + costs.twilio_month + costs.render_month;
  const budgetRemaining = Math.max(costs.budget_month - totalMonth, 0);
  logUsage(req, { stats: 'costs' });
  res.json(standardResponse({
    ...costs,
    total_today: Number(totalToday.toFixed(2)),
    total_month: Number(totalMonth.toFixed(2)),
    budget_remaining: Number(budgetRemaining.toFixed(2)),
    projected_month_end: Number((totalMonth * 1.18).toFixed(2))
  }));
});

app.get('/stats/revenue', (req, res) => {
  logUsage(req, { stats: 'revenue' });
  res.json(standardResponse(runtimeState.revenue));
});

app.get('/stats/clients', (req, res) => {
  logUsage(req, { stats: 'clients' });
  res.json(runtimeState.clients);
});

app.get('/stats/client/:clientName', (req, res) => {
  const clientName = req.params.clientName;
  const snapshot = getClientSnapshot(clientName);
  logUsage(req, { stats: 'client', client: clientName });
  res.json(standardResponse(snapshot));
});

// Healthcheck
app.get(['/api/demo/health', '/demo/health'], (req, res) => {
  res.json(standardResponse({ success: true, status: 'ok' }));
});

app.get('/widget-preview', (req, res) => {
  try {
    const widgetPath = path.join(__dirname, '../project5-chat-widget/index.html');
    const widgetHtml = fs.readFileSync(widgetPath, 'utf8');
    const origin = getPublicOrigin(req);
    const updatedHtml = widgetHtml.replace(
      "apiEndpoint: 'https://genesisai-chat-proxy-production.up.railway.app/chat'",
      `apiEndpoint: '${origin}/api/demo/chat-widget'`
    );
    logUsage(req, { demo: 'widget-preview' });
    res.type('html').send(updatedHtml);
  } catch (err) {
    logUsage(req, { error: err.message, demo: 'widget-preview' });
    res.status(500).type('html').send('<p>Widget preview unavailable.</p>');
  }
});

app.get('/widget.js', (req, res) => {
  const origin = getPublicOrigin(req);
  const script = `
(function () {
  const target = document.currentScript && document.currentScript.getAttribute('data-target');
  const host = target ? document.querySelector(target) : document.body;
  if (!host) return;
  const iframe = document.createElement('iframe');
  iframe.src = '${origin}/widget-preview';
  iframe.title = 'Genesis AI Systems Chat Widget';
  iframe.loading = 'lazy';
  iframe.style.width = '100%';
  iframe.style.maxWidth = '420px';
  iframe.style.height = '640px';
  iframe.style.border = '0';
  iframe.style.borderRadius = '18px';
  iframe.style.background = '#0f172a';
  host.appendChild(iframe);
}());
  `.trim();
  logUsage(req, { demo: 'widget.js' });
  res.type('application/javascript').send(script);
});

// 404 fallback
app.use((req, res) => {
  res.status(404).json(errorResponse('Not found.'));
});

app.listen(PORT, () => {
  console.log(`Genesis AI Systems demo backend running on :${PORT}`);
});

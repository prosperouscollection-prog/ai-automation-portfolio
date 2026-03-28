# Case Studies

These are portfolio demo case studies built around a realistic demo client: **Smile Dental**. They are written as projected before-and-after business scenarios to help prospects understand the likely ROI of each system.

## Case Study 1: Lead Capture + AI Scoring

### Client Type And Size

Independent dental office, 2 locations, 8 staff

### The Problem

Smile Dental was receiving an estimated **25 website inquiries per week**, but the office manager estimated that **8 to 10 leads per week** were not being followed up quickly enough. Average response time was around **4 hours**, and by then many prospects had already booked elsewhere or stopped replying.

### The Solution

We built **Lead Capture + AI Scoring** using an n8n webhook, OpenAI scoring logic, Google Sheets logging, and automated Gmail follow-up.

### How It Works

- A lead comes in through a form or webhook and is captured instantly.
- AI scores the inquiry as `HIGH`, `MEDIUM`, or `LOW` based on urgency and booking intent.
- The lead is logged to Google Sheets and an immediate follow-up email is sent.

### The Results

- Estimated **8 to 10 delayed leads per week** now prioritized correctly
- Estimated response time reduced from **4 hours to under 10 seconds**
- Estimated **2 to 4 additional appointments booked per week**
- Front-desk team saves an estimated **3 to 5 hours per week** in manual triage

### Tech Stack Used

- n8n
- OpenAI API
- Google Sheets
- Gmail

### Timeline To Deliver

2 to 3 business days

### Investment

- Setup Fee: $500
- Monthly Retainer: $150/month

### Client Quote

> We finally had a way to see which leads needed immediate attention instead of treating every inquiry the same. Even as a demo, this felt like something our front desk would use daily.

---

## Case Study 2: AI Voice Agent

### Client Type And Size

Independent dental office, 2 locations, 8 staff

### The Problem

Smile Dental estimated they were missing **12 to 15 inbound calls per week** after hours, during lunch, or while the front desk was tied up with patients. A portion of those missed calls were emergency or high-intent new-patient calls.

### The Solution

We built an **AI Voice Agent** in Vapi with an assistant named Riley that answers inbound calls, handles common questions, collects caller details, and routes urgent inquiries appropriately.

### How It Works

- A caller reaches the dental office and Riley answers instantly.
- Riley gathers key details, answers common questions, and identifies urgent situations.
- The office receives the captured caller information for follow-up or scheduling.

### The Results

- Estimated **12 to 15 missed calls per week** now covered
- Estimated **3 to 5 emergency or high-intent calls per week** recovered
- Front-desk interruptions reduced during busy periods
- After-hours call coverage extended from business hours only to **24/7 availability**

### Tech Stack Used

- Vapi
- OpenAI GPT-4
- ElevenLabs

### Timeline To Deliver

3 to 5 business days

### Investment

- Setup Fee: $1,500
- Monthly Retainer: $300/month

### Client Quote

> The most impressive part was hearing the caller get a real response even after hours. It felt like we had added another front-desk layer without hiring another person.

---

## Case Study 3: RAG Knowledge Base Chatbot

### Client Type And Size

Independent dental office, 2 locations, 8 staff

### The Problem

Smile Dental’s team was answering the same questions repeatedly about insurance, hours, emergency care, payment plans, and Invisalign. The office estimated that staff spent **30 to 45 minutes per day** answering repetitive questions across phone, website, and message channels.

### The Solution

We built a **RAG Knowledge Base Chatbot** using a Smile Dental FAQ document inside Claude Projects so the system answered from approved business information and escalated unknown questions safely.

### How It Works

- The chatbot reads from Smile Dental’s FAQ and knowledge document.
- Known questions get fast, grounded answers based on business-approved information.
- Unknown questions are escalated professionally instead of guessed.

### The Results

- Estimated **3.5 to 5 staff hours per week** saved on repetitive questions
- More consistent answers across common topics like insurance and office hours
- Reduced risk of hallucinated answers on unsupported questions
- Better after-hours support coverage for website visitors

### Tech Stack Used

- Claude Projects
- Custom FAQ document
- Prompt design and escalation rules

### Timeline To Deliver

2 to 4 business days

### Investment

- Setup Fee: $1,000
- Monthly Retainer: $200/month

### Client Quote

> The real value was consistency. The chatbot sounded informed, stayed within our approved information, and knew when to hand things off instead of improvising.

---

## Case Study 4: AI Workflow Automation + Email

### Client Type And Size

Independent dental office, 2 locations, 8 staff

### The Problem

Smile Dental had good lead volume but inconsistent speed to lead. New inquiries would sometimes sit in an inbox for **2 to 4 hours**, especially on busy days, reducing conversion on price-sensitive and appointment-ready prospects.

### The Solution

We built **AI Workflow Automation + Email** in n8n so new leads were captured, scored, logged, and emailed automatically within seconds.

### How It Works

- A new lead triggers the workflow through a webhook.
- AI generates a fast, context-aware response and logs the lead in Google Sheets.
- Gmail sends an immediate first-touch reply so the lead is not left waiting.

### The Results

- Lead response time reduced from **2 to 4 hours** to **under 15 seconds**
- Estimated **20 to 25 leads per week** now receive instant acknowledgment
- Estimated **2 to 3 additional consultations per week** from faster follow-up
- Staff time spent on repetitive first responses reduced significantly

### Tech Stack Used

- n8n
- OpenAI API
- Gmail
- Google Sheets

### Timeline To Deliver

3 to 4 business days

### Investment

- Setup Fee: $2,000
- Monthly Retainer: $400/month

### Client Quote

> The biggest improvement was speed. Instead of leads waiting hours, they heard back almost instantly, which made the office feel much more responsive.

---

## Case Study 5: AI Customer Service Chat Widget

### Client Type And Size

Independent dental office, 2 locations, 8 staff

### The Problem

Smile Dental’s website was getting traffic after hours, but visitors with questions about insurance, Invisalign, pricing, and hours were leaving without taking action. The team estimated that **10 to 15 website chats or question-driven visits per week** were likely being lost.

### The Solution

We built an **AI Customer Service Chat Widget** that could be embedded on the website to answer common questions instantly and route prospects toward booking or calling.

### How It Works

- A website visitor opens the chat widget and asks a question.
- The assistant answers in Smile Dental’s tone using configured business details.
- The visitor gets immediate guidance instead of waiting until the office opens.

### The Results

- Estimated **10 to 15 after-hours website conversations per week** now covered
- Website response time reduced from “next business day” to **instant**
- Estimated **2 to 4 additional consultation inquiries per week**
- Better visitor experience for high-intent prospects researching Invisalign or emergency care

### Tech Stack Used

- HTML
- CSS
- JavaScript
- OpenAI GPT-4o-mini API

### Timeline To Deliver

3 to 5 business days

### Investment

- Setup Fee: $2,500
- Monthly Retainer: $500/month

### Client Quote

> The widget made the site feel alive. Instead of visitors bouncing with unanswered questions, they could get help immediately, even outside office hours.

---

## Case Study 6: Fine-Tuned AI Model

### Client Type And Size

Independent dental office, 2 locations, 8 staff

### The Problem

Smile Dental wanted AI responses to sound warmer and more consistent with the office’s actual brand voice. Generic AI responses were accurate enough, but they did not always sound like the friendly, reassuring tone patients expected.

### The Solution

We built a **Fine-Tuned AI Model** using a curated set of Smile Dental training examples so the assistant responded more like the business itself.

### How It Works

- We prepare real business Q&A examples in Smile Dental’s preferred tone.
- The model is fine-tuned to follow that tone and phrasing more consistently.
- The final model can be used inside chat, support, or workflow tools.

### The Results

- More consistent tone across repeated customer interactions
- Estimated reduction in manual editing of AI-written responses by **60% to 80%**
- Stronger brand alignment on common patient questions
- Better customer experience for sensitive topics like emergencies, cancellations, and payment questions

### Tech Stack Used

- Python
- OpenAI fine-tuning API
- JSONL training data

### Timeline To Deliver

5 to 7 business days

### Investment

- Setup Fee: $5,000
- Monthly Retainer: $500/month

### Client Quote

> This felt less like a generic assistant and more like a digital version of our front desk. The tone was the biggest difference.

---

## Case Study 7: AI Video Automation Pipeline

### Client Type And Size

Independent dental office, 2 locations, 8 staff

### The Problem

Smile Dental knew video content could help attract new cosmetic and Invisalign patients, but no one on staff had time to consistently turn topics into scripts, captions, and post-ready content. Content ideas often sat unused for weeks.

### The Solution

We built an **AI Video Automation Pipeline** that accepts a topic and generates a short-form video script, captions, hashtags, thumbnail text, and a logged content record in Google Sheets.

### How It Works

- A topic is submitted through a webhook, such as “5 reasons to choose Invisalign.”
- AI generates the script, captions, hashtags, and thumbnail text automatically.
- Everything is logged to Google Sheets so the team can review and publish faster.

### The Results

- Content prep time reduced from **45 to 60 minutes per topic** to **under 3 minutes**
- Estimated **4 to 8 additional short-form posts per month** possible with the same staff
- Marketing bottleneck reduced for social and Invisalign campaigns
- Easier handoff between content planning and posting

### Tech Stack Used

- n8n
- OpenAI API
- Google Sheets

### Timeline To Deliver

2 to 3 business days

### Investment

- Setup Fee: $1,500
- Monthly Retainer: $300/month

### Client Quote

> Instead of staring at a blank page trying to make content, we could start with a full draft in minutes and focus on publishing.

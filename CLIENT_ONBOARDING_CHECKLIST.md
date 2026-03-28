# Client Onboarding Checklist

This checklist covers everything from signed contract to project delivery and retainer handoff.

Use it as your operating system for every new client.

## Pre-Kickoff

Do not begin implementation until every required item below is complete.

### Contract Signed Checklist

- [ ] Proposal approved
- [ ] Contract sent
- [ ] Contract signed by client
- [ ] Contract signed by you
- [ ] Scope confirmed in writing
- [ ] Payment terms confirmed

### Payment Received Confirmation

- [ ] 50% upfront deposit invoice sent
- [ ] Payment received
- [ ] Payment confirmed in accounting system
- [ ] Client marked as active

### Tools And Access Needed From Client

- [ ] Primary point of contact confirmed
- [ ] Business hours confirmed
- [ ] Services list confirmed
- [ ] FAQs / scripts / policies collected
- [ ] Website access provided if needed
- [ ] Domain / hosting access provided if needed
- [ ] Gmail / Google Workspace access or delegated access provided if needed
- [ ] Google Sheets access provided if needed
- [ ] Vapi / telephony access provided if needed
- [ ] Social platform context provided if needed
- [ ] Branding assets collected
- [ ] Compliance / privacy concerns discussed

### Kickoff Call Scheduled

- [ ] Kickoff meeting booked
- [ ] Calendar invite sent
- [ ] Agenda sent to client
- [ ] Access checklist sent before kickoff

## Kickoff Call Agenda

### 30 Minute Kickoff Structure

#### 0 to 5 Minutes: Confirm Goal

- confirm the business problem
- confirm the exact project scope
- confirm the desired outcome

#### 5 to 10 Minutes: Confirm Inputs

- confirm access
- confirm content / scripts / FAQs
- confirm business rules and escalation cases

#### 10 to 20 Minutes: Confirm Workflow

- walk through how the system will work
- explain what you will build first
- explain what the client should expect during build

#### 20 to 25 Minutes: Confirm Timeline

- confirm review date
- confirm delivery target
- confirm communication cadence

#### 25 to 30 Minutes: Confirm Next Steps

- confirm what the client owes you next
- confirm what you will deliver next
- confirm when you will check in again

### Questions To Ask On Kickoff

- What does success look like for this project?
- Are there any edge cases we should plan for?
- What should the AI never say or do?
- When should the system escalate to a human?
- Who should be notified if something breaks?
- Is there any sensitive data we should avoid sending through third-party tools?

### What To Deliver By End Of Call

- clear scope summary
- confirmed timeline
- confirmed access list
- confirmed communication process
- confirmed next milestone

## Build Phase Checklist

### Project 1: Lead Capture + AI Scoring

- [ ] Confirm webhook input format
- [ ] Confirm lead source
- [ ] Build n8n webhook trigger
- [ ] Connect OpenAI scoring step
- [ ] Define HIGH / MEDIUM / LOW criteria
- [ ] Connect Google Sheets logging
- [ ] Connect Gmail auto-response if included
- [ ] Test with high-intent lead
- [ ] Test with low-intent lead
- [ ] Confirm row logging format
- [ ] Confirm email output formatting

### Project 2: AI Voice Agent

- [ ] Confirm call goals
- [ ] Confirm business hours and fallback behavior
- [ ] Confirm FAQs and booking flow
- [ ] Configure Vapi assistant
- [ ] Set assistant name and tone
- [ ] Connect LLM model
- [ ] Connect voice provider
- [ ] Configure lead capture fields
- [ ] Configure emergency / urgent call handling
- [ ] Test inbound calls
- [ ] Test after-hours scenario
- [ ] Test escalation / fallback routing

### Project 3: RAG Chatbot

- [ ] Collect FAQ document
- [ ] Clean and organize knowledge base
- [ ] Configure Claude Project or selected RAG workflow
- [ ] Set answer style and escalation behavior
- [ ] Test known question
- [ ] Test unknown question
- [ ] Confirm no hallucination on unsupported questions
- [ ] Document how client updates the knowledge base

### Project 4: Workflow Automation + Email

- [ ] Map trigger event
- [ ] Build webhook input
- [ ] Connect AI response generation
- [ ] Connect lead scoring if included
- [ ] Connect Google Sheets logging
- [ ] Connect Gmail sending
- [ ] Test full flow from webhook to inbox
- [ ] Confirm response timing
- [ ] Confirm all logged fields

### Project 5: Chat Widget

- [ ] Confirm business info and tone
- [ ] Update widget configuration
- [ ] Connect secure backend proxy
- [ ] Test FAQ questions
- [ ] Test fallback behavior
- [ ] Confirm mobile responsiveness
- [ ] Confirm embed method on client site
- [ ] Confirm go-live domain placement

### Project 6: Fine-Tuning

- [ ] Collect training examples
- [ ] Review brand voice examples
- [ ] Validate JSONL structure
- [ ] Upload training data
- [ ] Create fine-tuning job
- [ ] Monitor training status
- [ ] Test fine-tuned model responses
- [ ] Compare against base model
- [ ] Confirm approved prompt / tone behavior

### Project 7: Video Automation

- [ ] Confirm target content style
- [ ] Confirm niche and audience
- [ ] Build webhook trigger
- [ ] Configure script generation
- [ ] Configure captions generation
- [ ] Configure hashtags generation
- [ ] Configure thumbnail text generation
- [ ] Connect Google Sheets logging
- [ ] Test with sample topic
- [ ] Confirm returned JSON structure

## Delivery Phase

### Testing Checklist Before Handoff

- [ ] Core workflow runs end to end
- [ ] Edge cases tested
- [ ] Error handling tested
- [ ] Logging works correctly
- [ ] Output quality approved
- [ ] Client-specific branding is correct
- [ ] Credentials are properly stored
- [ ] No test data remains in production-facing outputs

### Demo Recording Checklist

- [ ] Record short walkthrough
- [ ] Show trigger
- [ ] Show processing
- [ ] Show output
- [ ] Show business outcome
- [ ] Keep recording under 5 minutes if possible
- [ ] Share Loom or video link with client

### Client Training Checklist

- [ ] Explain what the system does
- [ ] Explain what the system does not do
- [ ] Explain how to trigger or use it
- [ ] Explain how to review outputs
- [ ] Explain fallback / escalation behavior
- [ ] Explain how to request updates
- [ ] Explain support / retainer coverage

### Handoff Document Template

Include these sections:

- project name
- project summary
- tools used
- credentials / access owner
- how to use the system
- how to update the system
- known limits
- support contact
- retainer terms if applicable

### Go Live Confirmation Checklist

- [ ] Client approved final version
- [ ] Final payment invoice sent
- [ ] Final payment received or scheduled per agreement
- [ ] Production settings enabled
- [ ] Test run completed in live environment
- [ ] Client notified that system is live
- [ ] Support window or retainer start date confirmed

## Post Delivery

### Week 1 Check-In Template

**Subject:** Checking in on [Project Name]

Hi [Client Name],

I wanted to check in now that [Project Name] has been live for about a week.

How has it been working from your side so far? Have you noticed anything you want adjusted, clarified, or improved?

If helpful, I’m happy to review early performance with you and make sure everything is running the way it should.

Best,  
[Your Name]

### Month 1 Review Template

**Subject:** 30-day review for [Project Name]

Hi [Client Name],

Now that [Project Name] has been live for about 30 days, this is a good time to review how it’s performing.

I’d like to look at:

- what’s working well
- any issues or edge cases
- what should be improved next
- whether there are any additional automation opportunities

If you want, we can schedule a quick review call this week.

Best,  
[Your Name]

### How To Transition From Project To Retainer

1. Remind the client what ongoing maintenance actually covers
2. Explain the risk of having no one monitor the system
3. Position the retainer as protection plus optimization
4. Send the retainer agreement or addendum
5. Start recurring billing before or at go-live

Suggested wording:

> The build gets the system live. The retainer keeps it reliable, updated, and supported as tools, prompts, and workflows change over time.

### How To Ask For A Testimonial

Best time:

- after a visible win
- after a compliment from the client
- after the first month if results are positive

Template:

Hi [Client Name],

I’m glad to hear the system has been helpful.

Would you be open to sharing a short testimonial about what the project helped improve for your business? Even 2 to 3 sentences would be hugely appreciated.

If easier, I can draft something based on your feedback and you can edit it however you like.

Best,  
[Your Name]

### How To Ask For A Referral

Template:

Hi [Client Name],

I’m really glad we were able to get [Project Name] live and working well for your business.

If you know another business owner dealing with missed leads, response delays, or repetitive admin work, I’d be grateful for an introduction.

I’m always happy to make it easy and send a short overview they can review first.

Best,  
[Your Name]

## Simple Rule For Client Experience

A professional client experience is not complicated.

It means:

- clear expectations
- fast communication
- organized delivery
- good documentation
- no surprises

If you follow this checklist every time, you will already look more professional than most freelancers clients have worked with before.

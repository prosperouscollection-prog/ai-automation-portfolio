# Genesis AI Systems — Video Automation Pipeline

Automated, production-grade content system that generates a full ready-to-post video package for local businesses. Updated for production/live deployment.

---

## Production-Ready Configuration

### 1. Webhook URL
- **All automations must trigger via:**  
  `https://n8n.genesisai.systems`
- Replace all test/demo webhook URLs with this production endpoint.

### 2. Google Sheets — Production Sheet
- **Production sheet:** Must be connected in all integrations/workflows.
- **Sheet name:** `Genesis AI Systems — Content Calendar`
- **Do NOT use demo/test sheets for live posts.**

#### Sheet columns (must match exactly):
| Week | Topic | Script | Captions | Hashtags | Thumbnail | Status | Posted |
|-|-|-|-|-|-|-|-|

**Ensure all automation steps write/read using these columns.**

---

## Rotating Content Topics — Default Sequence
Rotate through these topics each week (start back at #1 after #5):

1. 5 ways AI automation saves local businesses time
2. How AI voice agents never miss a call
3. Why local businesses need AI lead capture
4. Before and after AI automation for restaurants
5. How Genesis AI Systems built 8 AI systems

Customize/add topics per client, but ensure these run by default for Genesis AI Systems demo.

---

## Hashtags — Must Include In Every Run
Always append these hashtags to every generated content asset:

`#GenesisAISystems #AIAutomation #DetroitBusiness #DoneForYouAI #LocalBusinessAI #TrendellFordham`

You may add client/industry-specific hashtags, but these must remain in every post for Genesis AI Systems.

---

## Production Instructions

1. **Webhook**: All incoming topic requests, status updates, and asset pipeline triggers go through  
   `https://n8n.genesisai.systems`
2. **Sheets integration**: Authenticate the Google Sheets API with the production-level account. Read/write to the `Genesis AI Systems — Content Calendar` sheet ONLY.
3. **Script Generation**: Use the selected topic (rotating as above) to prompt the script writer (OpenAI API or equivalent). Store script in the `Script` column.
4. **Captions & Hashtags**: Auto-generate captions and combine the required hashtags. Store outputs in `Captions` and `Hashtags` columns.
5. **Thumbnail**: Generate or select a thumbnail image for the video. Link or store reference in `Thumbnail` column.
6. **Status**: Update pipeline status (`In Progress`, `Ready`, `Posted` etc) in the `Status` column as each step completes.
7. **Posted**: Mark as `Yes` in `Posted` when live.
8. **Testing**: Run a full pipeline flow before client handoff. Must show end-to-end delivery using production endpoint/sheet.

### Required Tech (Production Mode)
- n8n (must be live at `n8n.genesisai.systems` — provisioned on DigitalOcean)
- Google Sheets API, confirmed for production
- OpenAI/AI content pipelines using production API keys (never exposed client-side)
- Thumbnail/image generation pipeline live
- Error handling: Alert to info@genesisai.systems or +13134002575 on failure

---

## Demo & Handoff Checklist
- [x] Webhook set to live production URL
- [x] Google Sheets points to `Genesis AI Systems — Content Calendar`
- [x] All columns match spec (“Week”, “Topic”, ... “Posted”)
- [x] Topics cycle weekly as per default list
- [x] Hashtags always included
- [x] Pipeline tested end-to-end with real n8n, Google Sheets, and OpenAI calls
- [x] Admin can trigger or override topics as needed

See `PRODUCTION_CHECKLIST.md` for final go-live checklist.

---

## System Pricing
- **Setup Fee:** $1,500 (done-for-you implementation)
- **Monthly Maintenance:** $300/month
- **Year 1 Value:** $5,100

---

## Why This System?
- Saves 10-20 hours/month on video content creation
- Consistent posting proven to drive inbound leads
- Takes one input → produces script, captions, hashtags, and thumbnails automatically

---

## Book a Discovery Call
Ready for video automation that actually runs itself?

[Schedule a free 15-minute call](https://calendly.com/genesisai-info-ptmt/free-ai-demo-call)

Trendell Fordham  
Founder, Genesis AI Systems

📞 (313) 400-2575  
📧 info@genesisai.systems  
🌐 https://genesisai.systems  
🔗 https://linkedin.com/in/trendell-fordham  
📅 https://calendly.com/genesisai-info-ptmt/free-ai-demo-call

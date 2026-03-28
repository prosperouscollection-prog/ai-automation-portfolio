## Genesis AI Systems — Fine-Tuning Production Checklist

Ensure that your fine-tuning process is production-ready and properly integrated across client projects. Complete each item before marking this project as live.

---

### 1. Fine-Tuning Job Execution
- [ ] Fine-tune the model with real (production) data examples.
- [ ] Use at least 10 diverse, high-quality examples relevant to the client vertical or use case.
- [ ] Confirm you are **not** using any test or demo datasets.
- [ ] Record the OpenAI/Azure/Claude/etc. fine-tuning **model ID** immediately after the job completes.

### 2. Cost and Timing
- [ ] Confirm job cost: $0.01–0.05 for ~10 examples (~$0.50–$1 for 100+).
- [ ] Confirm completion time (15–30 minutes typical for OpenAI tuned models).

### 3. Testing the Fine-Tuned Model
- [ ] Test the new model ID via the production backend (not playground).
- [ ] Validate performance on real user prompts (not just training data).
- [ ] If accuracy is below requirements, add more examples and re-run.
- [ ] Document evaluation results for reference.

### 4. Integration Steps
- [ ] Save the final fine-tuned model **ID** in the project documentation and internal database.
- [ ] Update **Project 5 (AI Chat Widget)** backend/proxy to use the new fine-tuned model ID.
- [ ] Validate that the chat widget uses the correct model in production (test live demo).
- [ ] Communicate model change to stakeholders if this affects visible user experience.

### 5. Per-Client Fine-Tuning
- [ ] For each new client or vertical, clone and adapt fine-tuning script/examples.
- [ ] Document and save **unique model IDs per client**.
- [ ] Integrate per-client model IDs into their respective chat widgets/workflows.
- [ ] Use versioning if more than one model per client/vertical is needed.

### 6. Production Safeguards
- [ ] Never expose model IDs or API keys in browser/frontend code.
- [ ] Rate limit access to tuned endpoints (10 requests/IP/hr recommended).
- [ ] Confirm integration points log requests for debugging and audit.
- [ ] Backup full fine-tuning data sets and configs for repeatability.

### 7. Documentation
- [ ] **FINE_TUNING_PRODUCTION_GUIDE.md** reviewed for step-by-step instructions.
- [ ] Clearly document per-client fine-tuning instructions and integration notes.
- [ ] File and update model inventory for all active clients.

### 8. Support
- [ ] Link support: https://genesisai.systems
- [ ] If assistance needed, contact Trendell Fordham (info@genesisai.systems).

---

Checklist completed by: __________________________    Date: ____________
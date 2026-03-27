# Fine-Tuned AI Model

A custom-trained AI model designed to match a business's exact tone, phrasing, and support style instead of sounding generic.

## Problem It Solves

Generic AI responses may be technically correct, but they often miss the brand voice and business-specific nuance that make customer interactions feel polished and trustworthy.

## Target Client

Businesses that want AI that sounds exactly like them.

## Tech Stack

- Python
- JSONL training data
- OpenAI fine-tuning workflow
- Prompt engineering

## Configuration and Deployment

1. Collect real customer questions, approved responses, and brand voice examples from the client.
2. Structure the examples into JSONL training data for fine-tuning.
3. Validate and prepare the dataset with the Python workflow.
4. Train the model using the fine-tuning pipeline and evaluate outputs against real prompts.
5. Deploy the fine-tuned model behind a chatbot, internal tool, or customer support interface.

## Demo Instructions

1. Ask the model, `Do you see kids?`
2. Show how it answers in Smile Dental's exact warm, reassuring tone instead of sounding like a generic assistant.
3. Compare that result with a standard untuned model response.
4. Explain that the value is not just better answers, but branded consistency across every customer interaction.

## Pricing

- Setup Fee: $5,000
- Monthly Retainer: $500/month
- Total Year 1 Value: $11,000

## Why This Matters

When every customer-facing AI interaction sounds on-brand, businesses build trust faster and avoid the costly friction that comes from generic or off-tone responses.

## How To Run

Run all commands from the `project6-fine-tuning/` directory.

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up environment

```bash
cp .env.example .env
```

Then open `.env` and fill in `OPENAI_API_KEY` with your real key.

### 3. Validate training data

```bash
python data_validator.py
```

### 4. Run the full pipeline

```bash
python main.py
```

### 5. Expected output

The exact file ID, job ID, and final model ID will be different on your machine, but the terminal output should look like this:

```text
Step 1/3: Validating training data...
Validation passed for: /Users/genesisai/portfolio/project6-fine-tuning/training_data.jsonl
Step 2/3: Uploading training data and creating fine-tuning job...
Uploaded training file. File ID: file-abc123xyz
Created fine-tuning job. Job ID: ftjob-abc123xyz
Fine-tuning job ftjob-abc123xyz status: validating_files
Fine-tuning job ftjob-abc123xyz status: queued
Fine-tuning job ftjob-abc123xyz status: running
Fine-tuning job ftjob-abc123xyz status: running
Fine-tuning completed. Model ID: ft:gpt-4o-mini-2024-07-18:smile-dental:customer-support:abc123
Step 3/3: Running sample inference...
Q: Do you see kids?
A: Absolutely! We love seeing little smiles. We treat patients of all ages starting from 3 years old. We make it fun and stress-free for kids!
------------------------------------------------------------
Q: Do you accept Cigna insurance?
A: Yes! We accept Cigna along with most major PPO plans. Give us a call and we'll gladly help verify your benefits.
------------------------------------------------------------
Q: I have a toothache
A: Oh no, we're so sorry to hear that! We reserve same-day emergency slots every day. Call us right now at (555) 123-4567 and we'll get you in as soon as possible!
------------------------------------------------------------
Pipeline completed successfully.
```

During fine-tuning, status polling happens every 30 seconds until the job reaches a terminal state.

### 6. Test a fine-tuned model ID directly without re-running the full pipeline

Once you already have a fine-tuned model ID, you can test it directly with the inference layer instead of launching a new fine-tuning job.

```python
from openai import OpenAI

from config import AppConfig
from inference import OpenAIInference

config = AppConfig.from_env()
client = OpenAI(api_key=config.openai_api_key)

inference = OpenAIInference(
    client=client,
    model_id="ft:gpt-4o-mini-2024-07-18:smile-dental:customer-support:abc123",
    system_prompt=config.system_prompt,
)

print(inference.ask("Do you see kids?"))
print(inference.ask("Do you accept Cigna insurance?"))
print(inference.ask("I have a toothache"))
```

This is the fastest way to validate the model's behavior after training is complete.

## Cost Estimate

- Training cost: approximately $0.008 per 1K tokens
- Our 10 examples cost approximately $0.01-0.05 total
- Well within the $100 budget

## SOLID Architecture

This project is structured to show technical clients that the system is maintainable, extensible, and cleanly organized.

- `prepare_data.py` does one job: build the training dataset in JSONL format.
- `training_data.jsonl` stores the final training examples and nothing else.
- `config.py` only loads configuration from environment variables so secrets never live in code.
- `data_validator.py` only validates dataset structure and catches bad training data before upload.
- `fine_tuner.py` only handles the fine-tuning lifecycle, and its abstract base class makes it easy to swap providers later.
- `inference.py` only handles asking questions to a trained model and returning clean text responses.
- `main.py` only orchestrates the pipeline by calling the other modules in order.

In plain English: every file has one clear responsibility, which makes the system easier to test, easier to debug, and easier to extend for future client work.

---
## Book a Discovery Call
Ready to implement this system for your business?
[Schedule a free 15-minute call](#) — we'll show you a live demo and tell you exactly what it would cost to build this for you.

**[Your Name] | AI Automation Engineer**
📧 [your@email.com]
🔗 [linkedin.com/in/yourprofile]

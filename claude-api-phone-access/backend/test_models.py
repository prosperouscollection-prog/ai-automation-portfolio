import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))

# Try different models
models_to_try = [
    "claude-3-5-sonnet-20241022",
    "claude-3-sonnet-20240229", 
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307"
]

for model in models_to_try:
    try:
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}]
        )
        print(f"✅ {model} - WORKS")
        break
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not_found" in error_msg:
            print(f"❌ {model} - Not found")
        elif "not a valid" in error_msg.lower():
            print(f"❌ {model} - Invalid model")
        else:
            print(f"⚠️  {model} - {type(e).__name__}")

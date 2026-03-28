import os
import anthropic

# Load API key from .env
api_key = open('/Users/genesisai/portfolio/claude-api-phone-access/.env').read().split('CLAUDE_API_KEY=')[1].strip() 
os.environ['CLAUDE_API_KEY'] = api_key

print(f"API Key loaded: {api_key[:30]}...")

client = anthropic.Anthropic()

# Try models in order
models = [
    "claude-3-5-sonnet-latest",
    "claude-opus-4-1-20250805", 
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "claude-2.1"
]

for model in models:
    try:
        response = client.messages.create(
            model=model,
            max_tokens=5,
            messages=[{"role": "user", "content": "hi"}]
        )
        print(f"✅ SUCCESS: {model}")
        print(f"   Use this model in app.py")
        break
    except Exception as e:
        error = str(e)
        if "404" in error or "not found" in error.lower():
            print(f"❌ {model} - Not found")
        elif "auth" in error.lower() or "permission" in error.lower():
            print(f"❌ {model} - Auth failed ({error[:50]})")
            break
        else:
            print(f"❌ {model} - Error: {error[:60]}")

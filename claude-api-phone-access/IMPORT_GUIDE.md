# Chat History Import Guide

Import your existing conversations into the new Claude API phone access setup.

## Quick Start

### Option 1: From Command Line (Easiest)

```bash
cd /Users/genesisai/portfolio/claude-api-phone-access/backend

# Import JSON file
python import_history.py path/to/conversations.json

# Import with custom conversation ID
python import_history.py path/to/chats.json my_chats

# Import other formats
python import_history.py transcript.jsonl
python import_history.py data.csv
python import_history.py chat_log.txt
```

### Option 2: Use Sample Data (For Testing)

```bash
cd backend

# This loads sample conversations to try it out
python import_history.py sample_conversations.json

# Then restart the server and you'll see them in the web UI
python app.py
```

## Supported Formats

### JSON Format
```json
{
  "conversation_name": [
    {"role": "user", "content": "What is AI?"},
    {"role": "assistant", "content": "AI stands for..."}
  ]
}
```

Save to `.json` file and import.

### JSONL Format (One per line)
```jsonl
{"role": "user", "content": "Hello"}
{"role": "assistant", "content": "Hi there!"}
{"role": "user", "content": "How are you?"}
```

Save to `.jsonl` file and import.

### CSV Format
```csv
role,content
user,What is machine learning?
assistant,Machine learning is a subset of AI where...
user,Tell me more
assistant,Here are the key concepts...
```

Save to `.csv` file and import.

### Plain Text Format
```
Q: What is your name?
A: I'm Claude, an AI assistant.

User: How can you help?
Assistant: I can help with writing, coding, analysis, and more...

Q: What's your pricing?
A: You pay per token used in conversations.
```

Save to `.txt` file and import.

## Step-by-Step Instructions

### 1. Export Your Data

From wherever your chat history is:
- **WhatsApp**: Long-press chat → Export chat
- **Slack**: Use Slack export feature
- **Google Chat**: Copy conversation and paste to text file
- **ChatGPT**: Use the Share button → Copy to text
- **Excel/Sheets**: Export as CSV

### 2. Place File in Backend Folder

```bash
# Move or copy your file to:
/Users/genesisai/portfolio/claude-api-phone-access/backend/

# Example:
cp ~/Downloads/my_chats.json backend/
```

### 3. Run Import Script

```bash
cd backend
python import_history.py my_chats.json my_conversation_name
```

You'll see:
```
📂 Importing from: my_chats.json
💬 Conversation ID: my_conversation_name
✓ Read 47 messages from 1 conversation(s)
  - my_conversation_name: 47 messages
🔄 Merging with existing conversations...
✅ Successfully imported! Restart the server to see changes.
```

### 4. Restart Server

```bash
# Stop the current server (Ctrl+C)

# Restart it
python app.py
```

### 5. View in Web UI

Open your phone browser and access the chat interface. The imported conversation should be available!

## Handling Duplicates

If a conversation already exists, you'll be asked:
```
⚠️  Conversation 'my_chats' already exists.
  (R)eplace, (M)erge, or (S)kip? [r/m/s]:
```

- **R**: Replace old with new
- **M**: Add new messages to existing
- **S**: Keep existing, don't import

## Converting Formats

If you have data in one format but need another:

### CSV → JSON
```bash
# Use import_history.py to read CSV
python import_history.py data.csv
# It automatically saves to conversation_history.json
```

### Slack Export → JSON
1. Export from Slack as JSON
2. Run: `python import_history.py slack_export.json slack_history`

### ChatGPT Export → JSON
1. Export conversations (they give you JSON)
2. Run: `python import_history.py chatgpt_export.json chatgpt`

## Batch Import Multiple Files

```bash
# Import several files
for file in *.json; do
  python import_history.py "$file"
done
```

When prompted, choose Merge (M) to keep all conversations.

## Manual Import (If Script Fails)

Edit `conversation_history.json` directly:

```json
{
  "existing_conversation": [...],
  "my_imported_chat": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

Then restart server.

## Verify Import

After importing, you can check:

```bash
# View in terminal
cat conversation_history.json | python -m json.tool

# Or in the web UI:
# 1. Open phone browser to http://your-mac-ip:5000
# 2. Open Developer Console (F12)
# 3. Fetch and view: fetch('/api/conversations')
```

## Troubleshooting

### "File not found" error
- Check file is in the right folder
- Use absolute path: `python import_history.py /full/path/to/file.json`

### "Invalid JSON format" error
- Make sure JSON is valid: `python -m json.tool your_file.json`
- Use an online JSON validator

### "No messages found" error
- Your file format might not match expected structure
- Try converting to simple format:
```json
{"imported": [{"role": "user", "content": "test"}]}
```

### Server won't restart
- Make sure no other process is using port 5000
- Try different port: `PORT=8000 python app.py`

## Tips

✅ **Do this first**: Try with `sample_conversations.json` before importing your real data  
✅ **Backup**: Keep original files before importing  
✅ **Test**: Check web UI after import to verify  
✅ **Batch import**: Use loop to import many files at once  
✅ **Organize**: Use descriptive conversation IDs like "project_brainstorm" or "customer_support"  

---

**Pro tip**: Set up a scheduled task to automatically import new chats:
```bash
# Add to crontab on Mac
# Every hour, check for new JSON files and import them
0 * * * * cd ~/portfolio/claude-api-phone-access/backend && for f in /tmp/imports/*.json; do python import_history.py "$f"; done
```

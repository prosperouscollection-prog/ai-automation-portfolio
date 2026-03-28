# iMessage Chat Setup Guide

Use iMessage to chat with Claude on your Mac mini - no internet routing needed!

## How It Works

```
Phone (iMessage) ←→ Mac Mini (Claude Server)
```

You send iMessages, Claude responds via iMessage. Works on any network!

## Quick Setup

### 1. Install requests library
```bash
cd /Users/genesisai/portfolio/claude-api-phone-access/imessage-integration
pip install requests
```

### 2. Verify Claude server is running
```bash
curl http://localhost:8000/api/status
```

You should see:
```json
{"status": "online", ...}
```

### 3. Start iMessage Chat

```bash
cd /Users/genesisai/portfolio/claude-api-phone-access/imessage-integration
python imessage_chat.py "+1234567890"
```

Replace `+1234567890` with your actual phone number!

## Usage

### Interactive Mode (Default)
```bash
python imessage_chat.py "+1YOUR_PHONE_NUMBER"
```

Type in terminal, responses sent via iMessage:
```
You: What is machine learning?
⏳ Asking Claude...
Claude: Machine learning is a technique in AI where...
📤 Sending via iMessage...
✅ Sent to iMessage
```

### Special Commands
```
/help          - Show all commands
/status        - Check if Claude is online
/clear         - Clear conversation history
/export        - Export conversation
```

## Example Conversation

```
You: Tell me a joke
⏳ Asking Claude...
Claude: Why did the AI go to school? To improve its learning model!
📤 Sending via iMessage...
✅ Sent to iMessage

You: /status
Claude: ✅ Claude is online and ready!
📤 Sending via iMessage...
✅ Sent to iMessage
```

## Prerequisites

- ✅ Mac running Claude API server on port 8000
- ✅ iMessage configured with your phone number
- ✅ Messages app available in background
- ✅ Python 3.8+

## Advantages Over ngrok

✅ No authentication needed  
✅ Always works on same Mac  
✅ Responses delivered via iMessage  
✅ Personal, no public URLs  
✅ Works on any Apple network  
✅ Your phone number is the "address"  

## Limitations

- Only works on Mac with iMessage
- Requires Messages app to be available
- Phone must have iMessage enabled
- Same network as Mac mini (or via WiFi calling)

## Technical Details

The script:
1. Takes your message input
2. Sends to Claude API on localhost
3. Gets response from Claude
4. Sends response back via iMessage
5. Saves conversation history locally

All processing happens on your Mac - nothing goes through the internet!

## Troubleshooting

### "Messages app not responding"
- Make sure Messages app is open or at least available
- Check Messages permissions in System Settings → Privacy & Security

### "Error sending iMessage"
- Verify your phone number is correct (include country code, e.g., +1)
- Check iMessage is set up in Messages app
- Restart Messages app

### "Claude is offline"
- Check Claude server is running on port 8000
- Run: `curl http://localhost:8000/api/status`
- If offline, restart server: `PORT=8000 python app.py`

### Phone number format
Use international format:
- US: `+12025551234`
- UK: `+441234567890`
- Other: `+{country_code}{number}`

## Advanced: Monitoring Incoming iMessages

For a full two-way system that also listens for iMessage responses:

```bash
python imessage_chat.py "+1234567890" --listen
```

This creates a persistent daemon that watches for incoming iMessages. (Requires additional setup with iMessage monitoring library)

## Cost

Each Claude response uses a tiny amount of your $25 API credit:
- Short response: ~$0.01-0.02
- Medium response: ~$0.05
- Long response: ~$0.10

With $25, you'll get hundreds of conversations!

## Next Steps

1. ✅ Verify server is running
2. ✅ Get your phone number ready
3. ✅ Run: `python imessage_chat.py "+1YOUR_NUMBER"`
4. ✅ Send first message
5. ✅ Check your iMessage for response!

---

**That's it!** You now have a private, local Claude chat system via iMessage! 🎉

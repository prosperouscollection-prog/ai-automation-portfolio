#!/usr/bin/env python3
"""
iMessage Chat Interface for Claude API
Send messages to your Mac and get Claude responses back via iMessage
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
import threading

class iMessageChat:
    """Handle Claude conversations via iMessage"""
    
    def __init__(self, phone_number, your_name="You"):
        self.phone_number = phone_number
        self.your_name = your_name
        self.api_url = "http://localhost:8000/api/chat"
        self.history_file = Path.home() / ".imessage_chat_history.json"
        self.conversation_id = f"imessage_{phone_number}"
        self.load_history()
    
    def load_history(self):
        """Load chat history"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = {}
    
    def save_history(self):
        """Save chat history"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def send_imessage(self, message):
        """Send iMessage response back to phone"""
        try:
            script = f'''
tell application "Messages"
    set targetPhone to "{self.phone_number}"
    set targetService to 1st service
    send "{message}" to buddy targetPhone of targetService
end tell
'''
            subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
            return True
        except Exception as e:
            print(f"❌ Error sending iMessage: {e}")
            return False
    
    def ask_claude(self, user_message):
        """Send message to Claude API and get response"""
        try:
            import requests
            
            response = requests.post(
                self.api_url,
                json={
                    "message": user_message,
                    "conversation_id": self.conversation_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', 'No response received')
            else:
                return f"Error: API returned status {response.status_code}"
        
        except Exception as e:
            return f"Error contacting Claude: {str(e)}"
    
    def process_command(self, message_text):
        """Parse special commands"""
        text = message_text.lower().strip()
        
        # Special commands
        if text.startswith('/help'):
            return """Claude AI Chat Commands:
/help - Show this help
/status - Check if Claude is online
/clear - Clear conversation history
/export - Export conversation
Or just type anything to chat!"""
        
        elif text == '/status':
            return self.check_status()
        
        elif text == '/clear':
            if self.conversation_id in self.history:
                del self.history[self.conversation_id]
                self.save_history()
            return "✅ Conversation cleared"
        
        elif text == '/export':
            if self.conversation_id in self.history:
                msgs = self.history[self.conversation_id]
                return f"Exported {len(msgs)} messages"
            return "No messages to export"
        
        elif text.startswith('/'):
            return "Unknown command. Type /help for commands"
        
        # Regular message - ask Claude
        return self.ask_claude(message_text)
    
    def check_status(self):
        """Check if Claude is online"""
        try:
            import requests
            response = requests.get("http://localhost:8000/api/status", timeout=5)
            if response.status_code == 200:
                return "✅ Claude is online and ready!"
            else:
                return "⚠️  Claude is not responding properly"
        except:
            return "❌ Claude is offline. Check your Mac mini server."
    
    def monitor_imessages(self):
        """Monitor incoming iMessages and respond"""
        print(f"📱 Listening for iMessages from {self.phone_number}")
        print("Type Ctrl+C to stop\n")
        
        # This is a simplified version - in production you'd use a daemon
        # For now, this shows the concept
        
        while True:
            try:
                # In a real implementation, you'd use a proper iMessage monitoring library
                # For now, this is a placeholder that shows how it would work
                time.sleep(1)
            except KeyboardInterrupt:
                print("\n✅ Stopped listening for iMessages")
                break
    
    def interactive_chat(self):
        """Interactive chat mode - respond to typed messages"""
        print(f"💬 Claude Chat via iMessage (connected to {self.phone_number})")
        print("Type messages to send to Claude via iMessage")
        print("Type '/help' for commands, Ctrl+C to exit\n")
        
        while True:
            try:
                user_input = input(f"{self.your_name}: ").strip()
                if not user_input:
                    continue
                
                print("⏳ Asking Claude...")
                response = self.process_command(user_input)
                print(f"\nClaude: {response}\n")
                
                # Send via iMessage
                print("📤 Sending via iMessage...")
                if self.send_imessage(response):
                    print("✅ Sent to iMessage\n")
                else:
                    print("❌ Failed to send to iMessage\n")
                
            except KeyboardInterrupt:
                print("\n✅ Chat ended")
                break
            except Exception as e:
                print(f"Error: {e}\n")

def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("""
Claude AI via iMessage

Usage:
  python imessage_chat.py <phone_number> [--listen] [--chat]

Examples:
  # Interactive chat mode (default)
  python imessage_chat.py "+1234567890"
  
  # Listen for incoming iMessages
  python imessage_chat.py "+1234567890" --listen
  
  # Interactive chat
  python imessage_chat.py "+1234567890" --chat

Requirements:
  - Mac mini running Claude API server (port 8000)
  - iMessage set up on Mac
  - Messages app running in background

How it works:
  1. You send message in Terminal
  2. Claude API processes it
  3. Response sent back via iMessage to your phone
  4. You reply in iMessage
  5. Response shows in Terminal
        """)
        sys.exit(1)
    
    phone = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "--chat"
    
    chat = iMessageChat(phone)
    
    if mode == "--listen":
        chat.monitor_imessages()
    else:
        chat.interactive_chat()

if __name__ == '__main__':
    main()

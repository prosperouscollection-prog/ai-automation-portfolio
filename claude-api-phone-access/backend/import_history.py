#!/usr/bin/env python3
"""
Import chat history from various sources into the new Claude API setup
Supports: JSON, JSONL, CSV, plain text
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class HistoryImporter:
    """Handle importing conversations from various formats"""
    
    @staticmethod
    def import_json(file_path: str, conversation_id: str = 'imported') -> Dict:
        """
        Import from JSON file
        Expected format:
        {
            "conversation_id": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # If it's a list of messages, wrap it
                return {conversation_id: data}
            elif isinstance(data, dict):
                # If it's already conversation format, return as-is
                return data
            else:
                print(f"✗ Invalid JSON format: expected list or dict")
                return {}
        except Exception as e:
            print(f"✗ Error importing JSON: {e}")
            return {}
    
    @staticmethod
    def import_jsonl(file_path: str, conversation_id: str = 'imported') -> Dict:
        """
        Import from JSONL file (one JSON object per line)
        Each line should have: {"role": "user"|"assistant", "content": "..."}
        """
        try:
            messages = []
            with open(file_path, 'r') as f:
                for line in f:
                    if line.strip():
                        msg = json.loads(line)
                        messages.append(msg)
            
            return {conversation_id: messages}
        except Exception as e:
            print(f"✗ Error importing JSONL: {e}")
            return {}
    
    @staticmethod
    def import_csv(file_path: str, conversation_id: str = 'imported') -> Dict:
        """
        Import from CSV file
        Expected columns: role, content (role should be 'user' or 'assistant')
        """
        try:
            messages = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'role' in row and 'content' in row:
                        messages.append({
                            'role': row['role'].lower(),
                            'content': row['content']
                        })
            
            return {conversation_id: messages}
        except Exception as e:
            print(f"✗ Error importing CSV: {e}")
            return {}
    
    @staticmethod
    def import_text(file_path: str, conversation_id: str = 'imported') -> Dict:
        """
        Import from plain text file (Q&A format)
        Format: Lines starting with "Q:" or "User:" are user messages
                Lines starting with "A:" or "Assistant:" are assistant messages
        """
        try:
            messages = []
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by common delimiters
            lines = content.split('\n')
            current_role = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.lower().startswith(('q:', 'user:', 'me:', '> ')):
                    # Save previous message
                    if current_content:
                        messages.append({
                            'role': current_role,
                            'content': '\n'.join(current_content).strip()
                        })
                    # Start new user message
                    current_role = 'user'
                    current_content = [line[line.index(':')+1:].strip() if ':' in line else line.strip()]
                
                elif line.lower().startswith(('a:', 'assistant:', 'response:', '< ')):
                    # Save previous message
                    if current_content:
                        messages.append({
                            'role': current_role,
                            'content': '\n'.join(current_content).strip()
                        })
                    # Start new assistant message
                    current_role = 'assistant'
                    current_content = [line[line.index(':')+1:].strip() if ':' in line else line.strip()]
                
                else:
                    # Continuation of current message
                    if current_role:
                        current_content.append(line)
            
            # Don't forget the last message
            if current_content:
                messages.append({
                    'role': current_role,
                    'content': '\n'.join(current_content).strip()
                })
            
            return {conversation_id: messages}
        except Exception as e:
            print(f"✗ Error importing text: {e}")
            return {}
    
    @staticmethod
    def merge_with_existing(import_data: Dict, existing_file: str = 'conversation_history.json') -> Dict:
        """Merge imported data with existing conversations"""
        existing = {}
        if Path(existing_file).exists():
            try:
                with open(existing_file, 'r') as f:
                    existing = json.load(f)
            except:
                pass
        
        # Merge: for duplicate keys, ask user
        for conv_id, messages in import_data.items():
            if conv_id in existing:
                print(f"\n⚠️  Conversation '{conv_id}' already exists.")
                choice = input("  (R)eplace, (M)erge, or (S)kip? [r/m/s]: ").lower()
                if choice == 'r':
                    existing[conv_id] = messages
                elif choice == 'm':
                    existing[conv_id].extend(messages)
            else:
                existing[conv_id] = messages
        
        return existing
    
    @staticmethod
    def save_to_history(data: Dict, output_file: str = 'conversation_history.json'):
        """Save merged data to history file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"✗ Error saving history: {e}")
            return False

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("""
Usage: python import_history.py <file> [conversation_id]

Supported formats:
  - JSON:  {"conversation_id": [{...messages...}]}
  - JSONL: One JSON message per line
  - CSV:   role,content columns
  - TXT:   Q:/A: format

Examples:
  python import_history.py conversations.json
  python import_history.py chat_log.jsonl my_conversation
  python import_history.py data.csv from_slack
  python import_history.py transcript.txt

The imported conversations will be merged with conversation_history.json
        """)
        sys.exit(1)
    
    file_path = sys.argv[1]
    conv_id = sys.argv[2] if len(sys.argv) > 2 else 'imported'
    
    # Check file exists
    if not Path(file_path).exists():
        print(f"✗ File not found: {file_path}")
        sys.exit(1)
    
    # Determine format and import
    file_ext = Path(file_path).suffix.lower()
    
    print(f"📂 Importing from: {file_path}")
    print(f"💬 Conversation ID: {conv_id}")
    
    if file_ext == '.json':
        data = HistoryImporter.import_json(file_path, conv_id)
    elif file_ext == '.jsonl':
        data = HistoryImporter.import_jsonl(file_path, conv_id)
    elif file_ext == '.csv':
        data = HistoryImporter.import_csv(file_path, conv_id)
    elif file_ext == '.txt':
        data = HistoryImporter.import_text(file_path, conv_id)
    else:
        print(f"✗ Unsupported file format: {file_ext}")
        print("  Supported: .json, .jsonl, .csv, .txt")
        sys.exit(1)
    
    if not data:
        print("✗ No valid data imported")
        sys.exit(1)
    
    # Show preview
    total_messages = sum(len(msgs) for msgs in data.values())
    print(f"\n✓ Read {total_messages} messages from {len(data)} conversation(s)")
    
    for conv_id_key, messages in data.items():
        print(f"  - {conv_id_key}: {len(messages)} messages")
    
    # Merge with existing
    print("\n🔄 Merging with existing conversations...")
    merged = HistoryImporter.merge_with_existing(data)
    
    # Save
    if HistoryImporter.save_to_history(merged):
        print("\n✅ Successfully imported! Restart the server to see changes.")
        print(f"   Total conversations: {len(merged)}")
    else:
        print("\n✗ Failed to save history")
        sys.exit(1)

if __name__ == '__main__':
    main()

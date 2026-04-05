#!/bin/bash
HANDOFF_FILE="/Users/genesisai/portfolio/ops/agent_handoff.md"

echo "Codex polling loop started..."

while true; do
  LAST_SIGNAL=$(tail -20 "$HANDOFF_FILE" | grep -E "NEW LOOP START|SESSION END" | tail -1)
  
  if echo "$LAST_SIGNAL" | grep -q "SESSION END"; then
    echo "SESSION END detected. Stopping."
    exit 0
  fi

  if echo "$LAST_SIGNAL" "| grep -q "NEW LOOP START"; then
    echo "NEW LOOP START detected. Executing Codex tasks."
    exit 2
  fi

  echo "No signal. Sleeping 30s..."
  sleep 30
done

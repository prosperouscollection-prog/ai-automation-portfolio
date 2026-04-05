--- CODEX TASKS ---

TASK 1 — RESOLVE WORKING TREE
- Run git status and git diff --name-only
- For each uncommitted file identify what it is and whether it is safe
- Write full findings to ops/codex-output.md
- Do not commit sales_agent.py or lead_generator_agent.py yet
- Commit ops/codex-output.md only

TASK 2 — VALIDATE CONFIDENCE FIX TARGETS
- Confirm exact lines in email_acquisition.py referencing confidence_score for Hunter
- Confirm exact lines referencing score for Outscraper
- Write line numbers and current code to ops/codex-output.md
- Do not change any code — validation only
- Commit ops/codex-output.md

TASK 3 — SIGNAL HANDOFF
- Append CODEX DONE to ops/agent_handoff.md
- Commit: "ops: codex lane complete"
- Run ops/send_imessage.sh "Codex done. Claude Code your turn."

--- CLAUDE CODE TASKS ---

TASK 4 — FIX CONFIDENCE FIELD MISMATCHES
- Wait for CODEX DONE in ops/agent_handoff.md
- Fix Hunter pass in email_acquisition.py — change confidence_score to confidence
- Fix Outscraper pass — remove score dependency, use source ranking only
- Commit: "fix: correct confidence field names in acquisition engine"

TASK 5 — VERIFY ENGINE RANKING
- Write a test proving _candidate_strength() scores Hunter candidates correctly
- Run the test and confirm it passes
- Write result to ops/codex-output.md
- Commit: "test: verify candidate strength scoring with correct field names"

TASK 6 — CLEAR WORKING TREE
- Review uncommitted P17 edits Codex identified in Task 1
- Commit anything clean and safe
- Flag anything needing a founder decision in ops/codex-output.md
- Commit: "ops: working tree resolved"

TASK 7 — FINAL REPORT AND NOTIFY
- Compile full summary in ops/codex-output.md
- All tasks completed, commits listed, test results included
- Append CLAUDE CODE DONE to ops/agent_handoff.md
- Commit: "ops: claude code lane complete"
- Run ops/send_imessage.sh "All tasks complete. Tren — check needed."
- Stop and wait.

CODEX DONE

CODEX DONE

CODEX DONE


CLAUDE CODE DONE


LOOP COMPLETE

NEW LOOP START

CODEX DONE


NEW LOOP START

CODEX DONE

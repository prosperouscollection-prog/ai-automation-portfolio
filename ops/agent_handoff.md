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

--- CLAUDE CODE TASKS ---

TASK — FIX QA AGENT FAILURE
Read ops/codex-output.md for the exact failing grep check.
Fix the failing check in qa_agent.yml.
Do not touch any other checks.
Commit: "fix: resolve QA agent failing grep check"
Confirm fix by checking CI run passes.
Write result to ops/codex-output.md.
Commit: "ops: QA fix verification"
Append NEW LOOP START to ops/agent_handoff.md.
Commit: "ops: new loop started"
Run ops/send_imessage.sh "QA agent fixed. Tren — Reviewer check needed."
Go idle.

CODEX DONE

CODEX DONE

CODEX DONE


CLAUDE CODE DONE


LOOP COMPLETE

NEW LOOP START

CODEX DONE


NEW LOOP START

CODEX DONE


NEW LOOP START


NEW LOOP START

--- CODEX TASKS ---

TASK 1 — DIAGNOSE QA AGENT FAILURE
- Pull the latest qa_agent.yml CI run log
- Identify exactly which grep check is failing
- Write the failing check and exact output to ops/codex-output.md
- Commit: "ops: QA failure diagnosis"

TASK 2 — WRITE CLAUDE CODE FIX TASK
Append this to ops/agent_handoff.md under CLAUDE CODE TASKS:

--- CLAUDE CODE TASKS ---

TASK — FIX QA AGENT FAILURE
Read ops/codex-output.md for the exact failing grep check.
Fix the failing check in qa_agent.yml.
Do not touch any other checks.
Commit: "fix: resolve QA agent failing grep check"
Confirm fix by checking CI run passes.
Write result to ops/codex-output.md.
Commit: "ops: QA fix verification"
Append NEW LOOP START to ops/agent_handoff.md.
Commit: "ops: new loop started"
Run ops/send_imessage.sh "QA agent fixed. Tren — Reviewer check needed."
Go idle.

TASK 3 — SIGNAL HANDOFF
- Append CODEX DONE to ops/agent_handoff.md
- Commit: "ops: codex lane complete"
- Return to polling mode


CLAUDE CODE PERSISTENT PROTOCOL:
- You are Claude Code for Genesis AI Systems
- Poll ops/agent_handoff.md every 30 seconds
- Execute tasks marked CLAUDE CODE TASKS when you see CODEX DONE
- After all tasks complete append NEW LOOP START to ops/agent_handoff.md
- Commit: "ops: new loop started"
- Run ops/send_imessage.sh with completion message
- Return to polling mode — never go fully idle
- Never stop unless you see SESSION END

CURRENT TASK:
- Fix the failing QA grep check identified in ops/codex-output.md
- Commit fix
- Verify CI passes
- Then write NEW LOOP START and notify Tren


NEW LOOP START

CODEX DONE

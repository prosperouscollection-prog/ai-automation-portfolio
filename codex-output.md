STEP 1 RESULT
[state: LEAD CONFIRMED]
[lead details if confirmed — business name only, no PII]
The Detroit Shoppe

STEP 2 RESULT
[state: FOUNDER STOP WAS INACTIVE]

STEP 3 RESULT
[state: WORKFLOW_DISPATCH ADDED]
[commit hash]
50b093e

FOUNDER INSTRUCTIONS
1. Open GitHub in `prosperouscollection-prog/ai-automation-portfolio`.
2. Go to `Actions` and select `Sales Agent — Genesis AI Systems`.
3. Click `Run workflow`, keep branch `main`, and start the manual run.
4. Watch Telegram for the approval prompt from the Sales Agent.
5. Reply `QUEUE` to queue the lead for founder review, or `SKIP` to pass it.
6. After the reply, the workflow will record the terminal state, write the queue/log evidence, and emit the run summary without sending any outreach.
7. After the run completes, remove `workflow_dispatch` from `sales_agent.yml` and capture the final log lines plus raw JSON summary.

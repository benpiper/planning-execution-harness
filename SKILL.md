---
name: planning-execution-harness
description: "Use when you need to ask before executing, don't run without permission, review steps before proceeding, or confirm before executing. An LLM breaks down goals into tasks, presents the plan for approval, then executes only if approved. Enforces a mandatory approval gate that blocks all execution. Separates planning from execution so no action runs without prior sign-off. Classifies failures by type and applies type-specific recovery strategies. Produces a timestamped event log of every state change. Applies to: step-by-step workflows with approval, irreversible or risky operations, human-in-the-loop execution, agentic pipelines with intelligent failure recovery."
---

# Planning-Execution Pattern for LLMs

Orchestrate multi-step processes by separating planning from execution: **decompose → approve → execute → recover**.

## The Pattern

When given a goal, follow these stages:

### 1. PLAN — Decompose into ordered tasks

Break the goal into concrete, testable tasks with explicit dependencies (3-7 tasks):

```
Task 1: [specific action]
Task 2: [specific action] (depends on Task 1)
Task 3: [specific action] (depends on Task 2)
```

### 2. GATE — Present plan for approval

Show the task list. Mark any irreversible or destructive steps as ⚠ RISKY. Wait for explicit approval before proceeding. User may modify or reject.

Do not execute until explicitly approved.

### 3. EXECUTE — Follow the plan with explicit progress reporting

Execute tasks in order. **For each task, use this exact format:**

**On success:** `[Task N/M] ✓ [task name]: [brief result]`  
**On failure:** `[Task N/M] ✗ [task name]: [error reason]`  
**On retry:** `[Task N/M RETRY] ✓ [task name]: [retry outcome]`

Example:
```
[Task 1/4] ✓ Check request limits: 100MB limit, request is 50MB
[Task 2/4] ✗ Query optimization: N+1 bug detected (45s query)
[Task 2/4 RETRY] ✓ Query optimization: Fixed with joins, now 2s
```

Rules:
- Use `[Task N/M]` format for EVERY task start and completion
- Stop on errors — don't continue to next task without recovery

### 4. RECOVER — Classify and fix failures

When a task fails, classify it first, then apply appropriate recovery:

| Failure Type | Detection | Recovery | Max Attempts |
|---|---|---|---|
| **Transient** (timeout, rate limit) | "timeout", "503", "no response" | Wait 5s, retry. If fails: wait 30s, retry. After 2 attempts: escalate to user. | 2 |
| **Permission** (403, 401, denied) | "403", "401", "denied", "unauthorized" | Emit `PERMISSION_REQUIRED` event. STOP. Tell user to set credentials via env vars/config (never as text input). Retry once after configured. | 1 + user action |
| **Invalid Input** (malformed, missing) | "missing field", "invalid format" | Ask user to provide/correct. Retry once. | 1 + user input |
| **Logic Error** (wrong approach, bug) | "wrong type", "assertion failed", code returns unexpected result | Fix the approach. Retry once. | 1 |
| **Unrecoverable** (resource deleted, impossible) | "not found", "impossible", "no longer valid" | Ask user: "Skip this task or abort plan?" Respect decision. | 0 retries |

After recovery, resume from where you left off or ask user for next steps.

### 5. LOG — Emit timestamped events

Record every state change with timestamp and event type. Example format:

```
[14:23:00Z] PLAN_CREATED { task_count: 4 }
[14:23:05Z] GATE_APPROVED
[14:23:10Z] TASK_STARTED { task: 1 }
[14:23:45Z] TASK_COMPLETED { task: 1 }
[14:24:00Z] EXECUTION_COMPLETE { completed: 4, failed: 0, skipped: 0 }
```

---

## Quick Example: Full Flow

**Goal:** "Debug why my login is returning 401 errors"

**Plan (presented for approval):**
```
Task 1: Test token generation: curl -X POST http://localhost:3000/api/token
Task 2: Verify Authorization header: grep Authorization app.log
Task 3: Check JWT validation: node -e "jwt.verify(token, process.env.SECRET)"
Task 4: Verify user lookup: SELECT * FROM users WHERE id=123
```

**User approval:** ✓ Approved

**Execution (with [Task N/M] format):**
```
[Task 1/4] ✓ Test token generation: HTTP 200, tokens created
[Task 2/4] ✓ Verify Authorization header: Present in 100% of requests
[Task 3/4] ✗ Check JWT validation: Invalid signature error
  → Recovery: Transient or logic error? Check SIGNING_KEY env var
  → Found: SIGNING_KEY mismatch detected
  → Recovery action: Configure correct key in environment
[Task 3/4 RETRY] ✓ Check JWT validation: Signature valid (env corrected)
[Task 4/4] ✓ Verify user lookup: 1 user found (id=123)
```

**Execution complete:** 4/4 tasks passed. Root cause: SIGNING_KEY env var was outdated.

---

## Next Steps

See:
- **PROMPT.md** — Full system prompt for any LLM
- **EXAMPLES.md** — More detailed examples
- **IMPLEMENTATION.md** — Why this pattern matters
- **REFERENCES.md** — Detailed stage definitions

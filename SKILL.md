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

### 3. EXECUTE — Follow the plan

Execute tasks in order:
- Complete each task as planned
- Report progress: "[Task N/M] ✓ completed"
- Stop on errors, don't skip ahead

### 4. RECOVER — Classify and fix failures

When a task fails, classify it first, then apply appropriate recovery:

| Failure Type | Detection | Recovery | Max Attempts |
|---|---|---|---|
| **Transient** (timeout, rate limit) | "timeout", "503", "no response" | Wait 5s, retry. If fails: wait 30s, retry. After 2 attempts: escalate to user. | 2 |
| **Permission** (403, 401, denied) | "403", "401", "denied", "unauthorized" | Emit `PERMISSION_REQUIRED` event. Ask user for credentials/approval. Retry once. | 1 + user input |
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

## Quick Example

**Goal:** "Debug why my login is returning 401 errors"

**Plan:**
```
Task 1: Run: curl -X POST http://localhost:3000/api/token -d '{"user":"test"}'
Task 2: Check logs: grep "Authorization header" app.log
Task 3: Run: node -e "console.log(jwt.verify(token, process.env.SECRET))"
Task 4: Query: SELECT * FROM users WHERE id=123
```

**After approval, execute:**
```
[Task 1/4] ✓ Tokens generating: {"token":"eyJhb..."}
[Task 2/4] ✓ Header present in 100% of requests
[Task 3/4] ✗ jwt.verify failed: "Invalid signature"
  Recovery: Check SIGNING_KEY env var → wrong value detected
  [Task 3/4 RETRY] ✓ Validation now passing with correct key
[Task 4/4] ✓ User lookup: {id:123, name:"Alice"}
```

**Outcome:** Found: SIGNING_KEY env var was outdated. Updated and tested.

---

## Next Steps

See:
- **PROMPT.md** — Full system prompt for any LLM
- **EXAMPLES.md** — More detailed examples
- **IMPLEMENTATION.md** — Why this pattern matters
- **REFERENCES.md** — Detailed stage definitions

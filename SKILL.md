---
name: planning-execution-harness
description: "Use when orchestrating multi-step processes that require explicit approval before proceeding and retry on failure. Teaches step-by-step planning before action, workflow automation with approval gates, and failure recovery strategies. Creates task dependencies and execution plans. Enforces approval checkpoints that block execution. Retries on transient failures, escalates on permission errors, handles unrecoverable failures gracefully. Applies to: approval-gated workflows, step-by-step pipelines, complex multi-task processes, failure recovery, deployment pipelines, task orchestration."
---

# Planning-Execution Pattern for LLMs

Orchestrate multi-step processes by separating planning from execution: **decompose → approve → execute → recover**.

## The Pattern

When given a goal, follow these stages:

### 1. PLAN — Decompose into ordered tasks

Break the goal into concrete, testable tasks with dependencies:

```
Task 1: [specific action]
Task 2: [specific action] (depends on Task 1)
Task 3: [specific action] (depends on Task 2)
```

Requirements:
- **Concrete** — "Analyze job postings" not "optimize resume"
- **Testable** — Pass/fail is clear
- **Ordered** — Dependencies shown explicitly
- **Right size** — Aim for 3-7 tasks

### 2. GATE — Present plan for approval

Show the task list. Wait for user approval before proceeding. User may modify or reject.

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
| **Transient** (timeout, rate limit) | "timeout", "503", "no response" | Wait 5s, retry once. If fails: escalate to user. | 2 |
| **Permission** (403, 401, denied) | "403", "401", "denied", "unauthorized" | Emit `PERMISSION_REQUIRED` event. Ask user for credentials/approval. Retry once. | 1 + user input |
| **Invalid Input** (malformed, missing) | "missing field", "invalid format" | Ask user to provide/correct. Retry once. | 1 + user input |
| **Unrecoverable** (resource deleted, impossible) | "not found", "impossible", "no longer valid" | Escalate: "Skip task or abort plan?" Wait for user decision. | 0 retries |

After recovery, resume from where you left off or ask user for next steps.

### 5. LOG — Report outcomes

List all completed tasks, failures, and how they were recovered.

---

## Quick Example

**Goal:** "Debug why my login is returning 401 errors"

**Plan:**
```
Task 1: Check if JWT tokens are being generated
Task 2: Verify token is in Authorization header
Task 3: Check if token validation passes
Task 4: Check if user lookup succeeds
```

**After approval, execute:**
```
[Task 1/4] ✓ Tokens generating correctly
[Task 2/4] ✓ Token in header
[Task 3/4] ✗ Validation failed: "Invalid signature"
  Recovery: Retry with correct signing key
  [Task 3/4 RETRY] ✓ Validation now passing
[Task 4/4] ✓ User lookup working
```

**Outcome:** Found bug in signing key. Fixed.

---

## Next Steps

See:
- **PROMPT.md** — Full system prompt for any LLM
- **EXAMPLES.md** — More detailed examples
- **IMPLEMENTATION.md** — Why this pattern matters
- **REFERENCES.md** — Detailed stage definitions

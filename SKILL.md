---
name: planning-execution-harness
description: "Use when you need to break down a goal into multiple ordered tasks with dependencies, add approval gates before execution, and implement automatic recovery for failures. Applies to: workflow automation, multi-step processes, task orchestration, approval-gated execution, failure recovery."
---

# Planning-Execution Pattern for LLMs

Teach any LLM to separate planning from execution through explicit stages: **decompose → approve → execute → recover**.

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

When a task fails:

| Failure Type | Recovery |
|---|---|
| Transient (timeout, network) | Retry once, then escalate |
| Permission (access denied) | Ask user for help |
| Invalid input | Refine and retry |
| Unrecoverable | Skip or escalate |

After recovery, resume from where you left off.

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

## Use When

✅ Multiple steps required (3+)  
✅ Steps depend on each other  
✅ Approval needed before action  
✅ Failures need different recovery strategies  

❌ Single action (call one API)  
❌ No dependencies  
❌ No approval needed  

---

## Next Steps

See:
- **PROMPT.md** — Full system prompt for any LLM
- **EXAMPLES.md** — More detailed examples
- **IMPLEMENTATION.md** — Why this pattern matters
- **REFERENCES.md** — Detailed stage definitions

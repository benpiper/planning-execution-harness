# Reference: Detailed Definitions

## The Five Stages

### Stage 1: PLAN — Decomposition

**Input:** A goal  
**Output:** Ordered list of concrete tasks with dependencies

**Task Requirements:**

| Property | Definition | Example |
|---|---|---|
| Concrete | Specific action, not vague intent | ✓ "Remove unused imports from src/main.rs" ✗ "Clean up code" |
| Testable | Pass/fail is objective | ✓ "API response < 200ms" ✗ "Make it faster" |
| Ordered | Listed in execution sequence | ✓ Task 2 (depends on Task 1) ✗ Task 1, 2, 3 (order unclear) |
| Sized | Not too large, not too small | ✓ 3-7 tasks for most goals ✗ 1 massive task or 50 tiny tasks |

**Dependency Notation:**

```
Task 1: Base layer
Task 2: Build on Task 1 (depends on Task 1)
Task 3: Parallel with Task 2 (depends on Task 1)
Task 4: Combine results (depends on Task 2, Task 3)
```

**What Makes a Bad Plan:**

- Too vague ("optimize", "improve", "fix")
- Circular dependencies (Task A depends on B, B depends on A)
- Missing dependencies (Task B should depend on Task A but doesn't)
- Too many tasks (hard to track)
- Too few tasks (each is too large to verify)

---

### Stage 2: GATE — Approval

**Input:** Proposed plan  
**Output:** Approved or modified plan

**Gate Actions:**

| Action | When | Example |
|---|---|---|
| Approve | Plan looks correct | "Yes, proceed" |
| Modify | Reorder, add, or remove tasks | "Move Task 2 before Task 1" |
| Request Clarification | Don't understand | "What does 'sync data' mean?" |
| Reject | Plan is wrong approach | "This won't work, try different approach" |

**Gate is mandatory.** Do not execute without explicit approval.

**Approval Signals:**
- "approved"
- "yes, proceed"
- "✓ go ahead"
- Thumbs up emoji
- Any explicit confirmation

**Gate Examples:**

Risky operation (always gate):
```
Plan: Delete all old user records
Gate: [BLOCKED] 
  Requires: Explicit confirmation from data owner
  Confirm: "Yes, delete old records from before 2020"
```

Simple operation (still gate, but may be quick):
```
Plan: Fix typo in README
Gate: [APPROVED immediately]
  User: "Fine"
```

---

### Stage 3: EXECUTE — Ordered Execution

**Input:** Approved plan + working environment  
**Output:** Task completions and failures

**Execution Rules:**

1. Execute tasks in order (unless dependencies allow parallelization)
2. Report progress after each task
3. Stop on error (don't continue past a failure)
4. Don't skip tasks unless approved
5. Don't add new tasks without asking

**Progress Report Format:**

```
[Task N/M] ✓ Task name completed
  Additional details if relevant
```

**Stopping on Error:**

```
[Task 2/5] ✗ Task failed: reason here

What now?
- Retry this task?
- Skip and continue?
- Abort entire plan?

Waiting for approval...
```

---

### Stage 4: RECOVER — Failure Classification

**Input:** A failure  
**Output:** Recovery action

**Failure Classification:**

| Type | Characteristics | Recovery | Example |
|---|---|---|---|
| **Transient** | Temporary, will likely work if retried | Retry once, then escalate | Network timeout, rate limit |
| **Permission** | Access denied, needs approval or credentials | Ask user for help | Access denied, wrong API key |
| **Invalid Input** | Data is malformed or incorrect | Ask user for correction | Missing required field |
| **Unrecoverable** | Task no longer makes sense or is impossible | Skip or escalate | Resource was deleted |
| **Logic Error** | Code or approach is wrong | Fix and retry | Function returned wrong type |

**Recovery Recipe Structure:**

```
Failure Type: [name]
Detection: [how to identify]
Recovery:
  1. [action]
  2. [action]
  3. [if still failing, escalate]
```

**Example Recipes:**

**Recipe: Network Timeout**
```
Detection: "Connection timeout" or "No response after 30s"
Recovery:
  1. Wait 5 seconds
  2. Retry the request
  3. If still fails after 2 retries, ask user: "Network unstable. Abort or try again?"
```

**Recipe: Permission Denied**
```
Detection: "403 Forbidden" or "Access Denied"
Recovery:
  1. Escalate to user: "Need permission/credentials to proceed. Provide them?" (do not log credentials)
  2. If provided, retry with new credentials securely (do not expose in logs)
  3. If not provided, skip or abort task
NOTE: Handle credentials securely—never log or echo them in output or event logs.
```

**Recipe: Invalid Input**
```
Detection: "Missing required field" or "Invalid format"
Recovery:
  1. Ask user: "Field X is missing. Provide it?"
  2. If provided, retry
  3. If not, skip task or abort
```

---

### Stage 5: LOG — Observability

**Input:** All state changes  
**Output:** Complete event log

**Events to Log:**

- Plan created
- Gate approval decision
- Task started
- Task completed
- Task failed
- Recovery attempted
- Recovery succeeded or failed
- Execution complete

**Log Format:**

```
[Timestamp] [Event Type] [Details]
2024-01-15 14:23:45 PLAN_CREATED Tasks: 5
2024-01-15 14:24:00 GATE_APPROVED User: "yes, proceed"
2024-01-15 14:24:05 TASK_1_STARTED
2024-01-15 14:24:12 TASK_1_COMPLETED
2024-01-15 14:24:15 TASK_2_STARTED
2024-01-15 14:24:45 TASK_2_FAILED "Network timeout"
2024-01-15 14:24:47 RECOVERY_ATTEMPTED "Retry transient error"
2024-01-15 14:24:52 TASK_2_COMPLETED "Success on retry"
```

**Why Logging Matters:**

- Debugging: See exactly what happened and when
- Auditability: Prove what was approved and executed
- Learning: Understand failure patterns
- Transparency: Show user what system did

---

## Failure Scenarios

### Scenario 1: Transient Network Error

```
Task execution fails: Connection timeout
Classification: Transient
Recovery: Retry immediately
Result: Success on retry → continue
```

### Scenario 2: Permission Error

```
Task execution fails: 403 Forbidden
Classification: Permission
Recovery: Ask user for approval or credentials
Result: User provides credentials → retry with new auth → success
```

### Scenario 3: Circular Dependency (Planning Error)

```
Plan: Task A depends on B, Task B depends on A
Classification: Logical error in planning
Recovery: Return to planning stage, fix dependencies
Result: New plan with correct dependencies → gate approval → execute
```

### Scenario 4: Unrecoverable Error

```
Task execution fails: "File not found"
Classification: Unrecoverable (file was deleted or moved)
Recovery: Ask user: Skip task, or abort plan?
Result: User chooses skip → continue with next task
```

### Scenario 5: Mid-Execution Plan Change

```
During execution: User says "Actually, skip Task 3"
Classification: User-requested change
Recovery: Ask for confirmation, update plan, log the change
Result: Plan updated → continue execution
```

---

## Best Practices

### Planning

- ✓ Decompose until each task is testable
- ✓ Make dependencies explicit
- ✗ Don't plan in too much detail (plan will change)

### Gating

- ✓ Always present the plan
- ✓ Wait for explicit approval
- ✓ Accept modifications
- ✗ Don't execute without approval

### Execution

- ✓ Follow the approved plan exactly
- ✓ Report progress frequently
- ✗ Don't skip ahead or reorder tasks

### Recovery

- ✓ Classify before recovering
- ✓ Apply the right recipe for each failure type
- ✗ Don't retry everything blindly
- ✗ Don't give up without trying recovery

### Logging

- ✓ Log every state change
- ✓ Include timestamps
- ✓ Be specific about errors
- ✗ Don't skip logging "obvious" steps

---

## Implementation Checklist

- [ ] Planning stage produces concrete, testable, ordered tasks
- [ ] Gate stage requires explicit approval before execution
- [ ] Execution stage follows approved plan exactly
- [ ] Failures are classified before recovery attempted
- [ ] Recovery recipes are defined for each failure type
- [ ] All state changes are logged
- [ ] User can see complete history of what happened
- [ ] Unrecoverable errors escalate to human judgment

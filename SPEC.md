# Planning-Execution Harness: Technical Specification

## Goal

Enable any LLM to reliably orchestrate multi-step processes by separating planning from execution, enforcing approval gates before action, and recovering intelligently from failures.

**Problem solved:** LLM agents either skip planning (act immediately, make mistakes) or plan without gating (no approval before risky actions) or fail once and stop (no recovery strategy).

**This spec solves:** Structured workflow with planning → approval → execution → recovery → observability.

---

## Input/Output

### Inputs

**What the system receives:**
- **Goal** (string): High-level objective ("optimize resume", "debug login", "deploy system")
- **Context** (optional object): Project state, constraints, preferences
- **Approval mechanism** (function/human): How approval decisions are made
- **Tool set** (callable functions): What actions the LLM can execute
- **Recovery policies** (map): How to handle each failure type

**Constraints:**
- Goal must be achievable in 3-7 concrete steps (not 1 step, not 50)
- Approval must be explicit (not implicit or automatic for all cases)
- Recovery policies must be defined upfront

### Outputs

**What the system produces:**

| Stage | Output | Example |
|---|---|---|
| Planning | Ordered task list with dependencies | "Task 1: Analyze\nTask 2: Design (depends on 1)\nTask 3: Implement (depends on 2)" |
| Gate | Approval decision + any modifications | "APPROVED" or "APPROVED_MODIFIED: reorder Task 2 and 3" |
| Execution | Task completion log with progress | "[Task 1/3] ✓ Completed\n[Task 2/3] ✓ Completed" |
| Recovery | Recovery event + outcome | "RECOVERY_APPLIED: retry_transient → success" |
| Final | Execution summary + outcomes | "3/3 tasks completed. 0 failures." |

---

## System Architecture

### Core Constraint: Planning ≠ Execution

The system enforces **two separate phases**:

1. **Planning Phase**: LLM produces a plan. Plan is reviewed. Plan may be modified. Plan is NOT executed yet.
2. **Execution Phase**: ONLY approved plan is executed. No deviations.

This prevents the "plan one thing, do another" problem.

### The Five-Stage Pipeline

```
User Goal
    ↓
[1. PLAN] → Decompose into ordered tasks
    ↓
[2. GATE] → BLOCKS execution until approved
    ↓
[3. EXECUTE] → Run tasks in order
    ↓ (if failure)
[4. RECOVER] → Classify + apply recovery recipe
    ↓
[5. LOG] → Record all state changes
    ↓
Outcome
```

**Stage Independence**: Each stage has a single responsibility. Stages can be implemented separately in different languages/systems.

### Key Design Decisions

**Decision 1: Gates Are Mandatory**
- Every execution must be gated (approved before proceeding)
- No auto-approve all modes
- Human/policy decides per-case

**Decision 2: Failures Are Classified**
- Not all retries are equal
- Transient errors → retry with backoff
- Permission errors → ask human
- Logic errors → fix and retry
- Unrecoverable → escalate

**Decision 3: Execution Follows Plan Exactly**
- Once approved, the plan is law
- Don't skip tasks
- Don't reorder tasks
- Don't add new tasks
- If plan is wrong, STOP and return to planning stage

**Decision 4: Everything Is Logged**
- Event log is source of truth
- If no event was emitted, it didn't happen
- External systems can observe via log

---

## Workflow: Detailed Five-Stage Process

### Stage 1: PLAN — Decomposition

**Input**: User goal  
**Output**: Ordered task list with dependencies  
**LLM responsibility**: Break goal into concrete, testable, ordered tasks

**Task Requirements**:

| Requirement | Definition | Pass | Fail |
|---|---|---|---|
| Concrete | Specific action, not vague | "Remove unused imports" | "Clean code" |
| Testable | Pass/fail is objective | "Response < 200ms" | "Make it faster" |
| Ordered | Execution sequence clear | Task 2 (depends on 1) | Task 1, 2, 3 |
| Sized | Not too big/small | 3-7 tasks | 1 task or 50 tasks |

**Dependency Notation**:
```
Task 1: Base functionality
Task 2: Feature (depends on Task 1)
Task 3: Parallel work (depends on Task 1)
Task 4: Integration (depends on Task 2, Task 3)
```

**Failure Modes**:
- Vague tasks ("improve performance") → Reject, ask to be more specific
- Circular dependencies (A→B, B→A) → Reject, fix dependencies
- Too many/few tasks → Reject, rebalance

**Success Criteria**: 
- All tasks concrete ✓
- All dependencies explicit ✓
- 3-7 tasks total ✓

**Emit Event**: `PLAN_CREATED { task_count, dependencies }`

---

### Stage 2: GATE — Approval

**Input**: Proposed plan  
**Output**: Approval decision (approve/modify/reject)  
**Human/Policy responsibility**: Review plan before execution

**Gate Actions**:

| Action | When | Example |
|---|---|---|
| APPROVE | Plan looks correct | "Yes, proceed" |
| APPROVE_WITH_MODIFICATIONS | Reorder/add/remove tasks | "Approved, but skip Task 2" |
| ASK_FOR_CLARIFICATION | Don't understand | "What does 'sync' mean?" |
| REJECT | Wrong approach | "No, try different strategy" |

**Gate Requirements**:
- MUST block execution (plan cannot execute without approval)
- MUST be explicit (no silent approval)
- MUST accept modifications (user can change plan)

**Approval Signals** (what counts as approval):
- "approved" / "yes" / "proceed" / "✓"
- Thumbs up emoji
- Explicit confirmation

**Rejection/Modification Signals**:
- "no" / "rejected" / "wait"
- Specific changes: "reorder Task 2 and 3"
- Questions: "why does Task 1 need Task 2?"

**Failure Modes**:
- Approving without understanding → User's problem, system accepts
- Modifying to circular dependencies → System detects, asks user to fix
- Timeout waiting for approval → Configurable, escalate if exceeded

**Emit Events**: 
- `GATE_APPROVAL_REQUESTED { plan_id }`
- `GATE_APPROVED { modifications }`
- `GATE_REJECTED { reason }`

---

### Stage 3: EXECUTE — Ordered Task Execution

**Input**: Approved plan + working environment  
**Output**: Task completions and failures  
**LLM responsibility**: Execute tasks in order, follow the plan

**Execution Rules**:

1. **Execute in order**: Task 1 → Task 2 → Task 3 (unless dependencies allow parallelization)
2. **Report progress**: After each task, emit `TASK_COMPLETED` or `TASK_FAILED`
3. **Stop on error**: Don't continue past a failed task
4. **Don't deviate**: Don't skip, reorder, or add tasks without returning to planning stage
5. **Check dependencies**: Before starting a task, verify all dependencies are complete

**Progress Format**:
```
[Task N/M] ✓ Task name completed
  Details: what was accomplished
```

**Error Format**:
```
[Task N/M] ✗ Task name failed
  Reason: why it failed
  Waiting for recovery decision...
```

**Failure Modes**:
- Missing dependency (Task 2 before Task 1) → Detect, block, emit error
- Task takes too long → Configurable timeout, emit warning
- External error (API down) → Emit error, proceed to recovery stage

**Emit Events**:
- `TASK_STARTED { task_id, task_name }`
- `TASK_COMPLETED { task_id, result }`
- `TASK_FAILED { task_id, error }`

---

### Stage 4: RECOVER — Failure Classification & Recovery

**Input**: A task failure  
**Output**: Recovery action or escalation  
**Policy responsibility**: Define recovery recipes per failure type

**Failure Classification**:

| Failure Type | Characteristics | Recovery | Max Retries |
|---|---|---|---|
| **Transient** | Temporary, will likely succeed if retried | Retry with backoff (5s, 30s, 5m) | 2 |
| **Permission** | Access denied, needs approval/credentials | Ask human for approval or credentials | 1 (after user provides input) |
| **Invalid Input** | Data is malformed | Ask human for correction | 1 (after user provides input) |
| **Logic Error** | Code/approach is wrong | Fix approach and retry | 1 |
| **Unrecoverable** | Task no longer makes sense | Skip task or abort plan | 0 |

**Recovery Recipe Structure**:

```
Failure Type: [name]
Detection: [how to identify this failure]
Recovery Steps:
  1. [action]
  2. [action]
  3. [escalation policy if still failing]
Max Attempts: [number]
Escalation: [what happens if max attempts exceeded]
```

**Example Recipe: Network Timeout**
```
Failure Type: Transient (Network Timeout)
Detection: "Connection timeout" or "No response after 30s"
Recovery Steps:
  1. Wait 5 seconds
  2. Retry the request
  3. If still fails, wait 30s and retry again
  4. If still fails, emit RECOVERY_ESCALATION
Max Attempts: 2
Escalation: Ask user: "Network unstable. Retry, skip, or abort?"
  - Retry: continue from step 1
  - Skip: skip this task, continue with next
  - Abort: halt plan execution
```

**Example Recipe: Permission Denied**
```
Failure Type: Permission
Detection: "403 Forbidden" or "401 Unauthorized"
Recovery Steps:
  1. Emit PERMISSION_REQUIRED event
  2. Ask user: "Need API key / confirmation to proceed. Provide?"
  3. If provided, retry with new credentials
  4. If not provided, ask: "Skip task or abort plan?"
Max Attempts: 1 (after user provides credentials)
Escalation: User decides (skip or abort)
```

**Failure Modes**:
- Unknown failure type → Escalate to human (unknown recovery recipe)
- Recovery fails after max attempts → Follow escalation policy
- User rejects recovery → Respect decision (skip or abort)

**Emit Events**:
- `FAILURE_DETECTED { task_id, error_message }`
- `FAILURE_CLASSIFIED { failure_type }`
- `RECOVERY_APPLIED { recipe_name, outcome }`
- `RECOVERY_ESCALATION { reason, user_decision }`

---

### Stage 5: LOG — Observability & Event Log

**Input**: All system state changes  
**Output**: Complete, immutable event log  
**System responsibility**: Record everything

**What Gets Logged**:

| Event | When | Format |
|---|---|---|
| PLAN_CREATED | Plan is generated | `{ task_count, dependencies }` |
| GATE_APPROVAL_REQUESTED | Plan ready for review | `{ plan_id }` |
| GATE_APPROVED | Approval given | `{ modifications_if_any }` |
| TASK_STARTED | Task begins execution | `{ task_id, task_name }` |
| TASK_COMPLETED | Task succeeds | `{ task_id, result }` |
| TASK_FAILED | Task fails | `{ task_id, error_message }` |
| FAILURE_CLASSIFIED | Error is categorized | `{ failure_type }` |
| RECOVERY_APPLIED | Recovery strategy executed | `{ recipe_name, outcome }` |
| EXECUTION_COMPLETE | All tasks done | `{ summary: completed, failed, skipped }` |

**Log Entry Format**:
```json
{
  "timestamp": "2024-01-15T14:23:45Z",
  "event": "TASK_COMPLETED",
  "task_id": "task_1",
  "task_name": "Analyze input",
  "details": { "result": "5 requirements identified" }
}
```

**Log Properties**:
- **Immutable**: Once written, events cannot change
- **Ordered**: Chronological sequence
- **Queryable**: Can search by task, event type, timestamp
- **Complete**: All state changes recorded

**Why Logging Matters**:
- **Auditability**: Prove what was approved and executed
- **Debugging**: See exactly what happened and when
- **Learning**: Understand failure patterns
- **Transparency**: Show user what system did

---

## Supporting Sections

### Error Handling Philosophy

**Principle 1: Classify Before Recovering**
Never retry blindly. Identify failure type first, apply appropriate recovery.

**Principle 2: Stop on Unknown Errors**
If error type not in recovery recipes, escalate to human.

**Principle 3: Finite Retries**
Each recovery recipe specifies max attempts. Prevent infinite loops.

**Principle 4: User Decides on Escalation**
If recovery exhausted, ask user: retry, skip, or abort? Respect their decision.

### Recovery Policies (Configurable)

These are patterns teams can customize:

**Transient Error Policy**:
- Retry count: 2 (configurable)
- Backoff: exponential (5s, 30s, 5m)
- Escalation: ask user after max retries

**Permission Error Policy**:
- Ask for credentials/confirmation
- Retry once with new credentials
- Escalation: user decides skip/abort

**Logic Error Policy**:
- Fix approach based on error
- Retry once
- Escalation: escalate to human for judgment

### Observability: What Agents Can See

The event log is the **single source of truth**. Agents can:
- Query event history
- See what was approved
- See what was executed
- See what failed and how it was recovered
- Compute summaries (3/5 tasks done, 1 failed, 1 skipped)

External systems can:
- Subscribe to events in real-time
- Trigger on specific event types
- Build dashboards from log
- Audit compliance via immutable record

---

## Implementation Guidance

### What Must Be Implemented

1. **Plan decomposition** (LLM responsibility)
2. **Gate mechanism** (human/policy responsibility)
3. **Task execution** (LLM + tool set responsibility)
4. **Failure classification** (policy responsibility)
5. **Event logging** (system responsibility)

### What Can Vary

- **Languages**: Python, JavaScript, Go, Rust, etc.
- **Tool sets**: Different tools for different domains
- **Approval mechanisms**: Human, policy rules, hybrid
- **Storage**: File, database, event stream
- **Recovery recipes**: Domain-specific recovery strategies

---

## Testing Checklist

- [ ] Planning stage produces concrete, testable, ordered tasks with correct dependencies
- [ ] Gate stage blocks execution until explicit approval received
- [ ] Approved plan is executed exactly as specified
- [ ] Failed tasks are classified before recovery attempted
- [ ] Recovery recipes are applied correctly per failure type
- [ ] Event log captures all state changes with timestamps
- [ ] Unknown error types escalate to human
- [ ] Recovery exhaustion escalates to human with user choice
- [ ] Circular dependencies detected and rejected at planning stage
- [ ] Task dependencies verified before execution

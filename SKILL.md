---
name: planning-execution-harness
description: "Use when orchestrating sequential tasks, multi-step automation pipelines, or DAG-style workflows that require dependency tracking, approval gates, checkpoint/resume logic, and rollback on failure. Applies to: decomposing a goal into dependency-ordered tasks, coordinating execution with explicit state transitions, enforcing approval gates between planning and execution, implementing structured failure recovery with per-error-type recipes, and automating multi-stage processes with event-log ground truth. Not for single API calls or one-off scripts — use when there are 3+ coordinated steps with task dependencies or sequential execution order."
---

# Planning-Execution Harness: A Universal LLM Agent Pattern

A design pattern for structuring how any LLM agent decomposes high-level goals into concrete executable tasks, with explicit gates, recovery mechanisms, and observability.

## Core Problem

Most LLM agents work like this:

```
User Goal → LLM Thinks & Acts → Done (or fails)
```

This works for simple tasks but breaks down at scale because:
- ❌ No explicit boundary between "planning" and "doing"
- ❌ No gates before destructive operations
- ❌ No structured recovery when things fail
- ❌ No clear task dependencies or execution order
- ❌ No way to track what happened (no event log)

## The Pattern

Insert explicit **stages** between goal and execution:

```
High-Level Goal
    ↓
[PLANNING STAGE]
    • Decompose into concrete tasks
    • Identify dependencies
    • Validate feasibility
    ↓
[GATE STAGE]
    • Human/system approval
    • Trust resolution
    • Risk assessment
    ↓
[EXECUTION STAGE]
    • Execute tasks in order
    • Handle failures per task
    • Log everything
    ↓
Outcome
```

## Why This Matters

### 1. Prevents Mistakes

Without a gate, an LLM might:
- Delete production data (planning said "no", execution didn't check)
- Run 100 parallel jobs instead of sequentially (dependency not explicit)
- Retry forever on unrecoverable errors (no classification)

With explicit stages:
- "Planning" decides what SHOULD happen
- "Gate" checks if it's safe
- "Execution" only does what was approved
- "Recovery" knows HOW to handle specific failures

### 2. Handles Complexity

A single "think and act" loop breaks when:
- 5+ steps are needed
- Steps depend on each other
- Some steps need human approval
- Failures need different recovery strategies

Explicit stages handle all of these because each stage has a clear responsibility.

### 3. Makes Behavior Observable

No stage should surprise you. You can see:
- What the LLM decided to do (planning output)
- What was approved (gate decision)
- What actually happened (execution log)
- How failures were recovered (recovery recipe used)

## The Seven Stages

### Stage 1: Task Specification (Planning)

**Input:** A goal  
**Output:** A list of concrete tasks with dependencies

The LLM decomposes "optimize my resume" into:
1. Analyze current resume
2. Research target roles
3. Identify skill gaps
4. Rewrite sections (depends on 1, 2, 3)
5. Add keywords (depends on 4)
6. Final review (depends on 5)

Each task should be:
- Concrete and testable
- Have acceptance criteria
- Know its dependencies
- Specify scope (single file? whole project? across systems?)

### Stage 2: Bootstrap Planning (Preparation)

**Input:** The task specification  
**Output:** Prepared environment

Before execution starts, set up:
- Tools are available and initialized
- Credentials loaded
- System prompt updated with context
- Configuration validated
- Dependencies verified

This is a gate disguised as setup. If bootstrap fails, execution never starts.

### Stage 3: Worker Startup (Trust Gate)

**Input:** Prepared environment  
**Output:** Ready-to-execute worker

Before the LLM executes anything:
1. Emit "I'm about to execute" signal
2. **WAIT** for approval (human or policy)
3. Only proceed after "trust_resolved" signal

This is the critical gate. It separates "planning" (LLM output) from "doing" (actual changes).

Why? Because plans can be wrong. A human can review and say "no, don't do that" before anything happens.

### Stage 4: Permission Checks (Execution Control)

**Input:** A requested action  
**Output:** Allow or deny

Before executing each tool call, ask:
- Is this action allowed in current mode?
- Does the input match the plan?
- Should this step be gated further?

Example modes:
- `planning` — read-only, no side effects
- `exploration` — test changes, but don't commit
- `execution` — full access

### Stage 5: Hook Interception (Observability)

**Input:** Tool call request  
**Output:** Modified request or denial

Between "LLM wants to call a tool" and "tool is executed":
- Log what's happening
- Let external systems intervene
- Collect metrics
- Validate the request matches the plan

This isn't about blocking — it's about **witnessing** what's happening.

### Stage 6: Execution Loop (Action)

**Input:** Approved tool calls  
**Output:** Results and state transitions

The LLM:
- Calls a tool
- Gets a result
- Decides what to do next
- Iterates until done

Each iteration emits events (called, succeeded, failed) to the event log.

### Stage 7: Failure Recovery (Resilience)

**Input:** A failure event  
**Output:** Recovery action or escalation

When something fails:
1. Classify the failure type (timeout, permission denied, invalid input, etc.)
2. Look up the recovery recipe for that type
3. Execute the recipe (retry, rollback, skip, escalate)
4. Log the recovery and its outcome

Example recipes:
- **Network timeout** → retry with exponential backoff
- **Permission denied** → escalate to human for approval
- **Invalid input** → regenerate with refined constraints
- **Rollback needed** → undo changes in reverse order

## Key Design Principles

### 1. Planning Happens First, Separate from Execution

The LLM produces a plan. That plan is validated, reviewed, possibly modified. THEN execution happens.

Why? Because a perfect plan executed slowly is better than a broken plan executed quickly.

### 2. Gates Are Explicit

"I'm about to do X" → [GATE] → "X approved" → do X

Not implicit or silent. Every gate is a named, loggable event.

### 3. State Changes Are Logged

If no event was emitted, the state change didn't happen. The event log is the source of truth.

This means:
- External systems can observe what's happening
- You can replay what happened
- You can debug failures

### 4. Failures Are Classified, Not Repeated

Don't retry everything. Classify the failure type first:
- Transient (retry) vs permanent (escalate)
- User error (ask for clarification) vs system error (fix and retry)
- Expected (apply recipe) vs unexpected (human judgment)

### 5. Tasks Have Dependencies

Not all tasks can run in parallel. Some depend on others:
- "Rewrite resume" depends on "identify gaps"
- "Deploy" depends on "tests pass"
- "Archive old data" depends on "backup complete"

Make dependencies explicit so the orchestrator can enforce them.

### 6. Every System is Different, But the Pattern is the Same

You might implement this with:
- HTTP APIs coordinating microservices
- Message queues triggering workers
- A single LLM with tools
- Multiple LLMs coordinating
- Humans + LLMs hybrid

The pattern doesn't care. What matters is: explicit stages, gates, recovery, and logging.

## When to Use This Pattern

Use this pattern when:
- ✅ Multiple steps are required (3+)
- ✅ Steps have dependencies
- ✅ Approval is needed before execution
- ✅ Failures need different recovery strategies
- ✅ You need to observe what happened

Don't use when:
- ❌ Single, simple action (call one API)
- ❌ No dependencies between steps
- ❌ No approval needed
- ❌ Fire-and-forget is acceptable

## Minimal Example (Conceptual)

A goal: "Optimize my resume for 3 job postings"

**Stage 1: Planning**
```
LLM output:
  Task 1: Analyze each job posting (3 tasks, parallel)
  Task 2: Identify common skills across all 3 (depends on Task 1)
  Task 3: Rewrite experience to emphasize those skills (depends on Task 2)
  Task 4: Add keywords from job postings (depends on Task 2)
  Task 5: Final review (depends on Task 3, Task 4)
```

**Stage 2: Bootstrap**
```
Set up: text editor, job posting documents, thesaurus tools
Verify: all inputs are readable, spell-check enabled
```

**Stage 3: Trust Gate**
```
[Gate blocks here]
Human reviews plan: "Yes, proceed" (or "No, modify Task 3 first")
```

**Stage 4: Execution**
```
Execute Task 1: LLM reads job postings (parallel)
Execute Task 2: LLM identifies common skills
Execute Task 3: LLM rewrites resume
Execute Task 4: LLM adds keywords
Execute Task 5: LLM does final review
```

**Stage 5: Recovery**
```
If Task 3 fails (no write access):
  → Classify: permission error
  → Apply recipe: ask for manual approval, proceed with human input
```

## Implementation Agnosticism

This pattern works with:

- **Claude + Claw** — Uses tools + session persistence
- **GPT-4 + Function Calling** — Uses function calls + conversation history
- **Gemini + Custom Tools** — Uses tool use + state management
- **Open Source LLM + Ollama** — Uses local execution + event logging
- **Multi-Agent Orchestration** — Multiple LLMs + coordination layer
- **Hybrid Human + AI** — Humans at gates, LLM for execution

The core pattern is the same. Only the implementation details change.

## The One Requirement

Whatever you build, ensure:
- **Events are logged** — proof that things happened
- **Gates are explicit** — nothing happens without approval
- **Failures are classified** — each error type has a recipe
- **Dependencies are tracked** — tasks execute in right order
- **Recovery is automatic** — known failures don't require human triage

## Next Steps

1. **Identify your use case** — What goal needs planning + execution?
2. **Define stages for your system** — What does planning look like for you?
3. **Add a gate** — Where should approval happen?
4. **Define failure scenarios** — What can go wrong, and how to recover?
5. **Implement the event log** — Make everything observable
6. **Test the gate** — Verify human/policy approval actually stops execution

---

This pattern is **universal** because the problem is universal: any complex goal needs planning before execution, gates before risk, and recovery before failure becomes catastrophe.

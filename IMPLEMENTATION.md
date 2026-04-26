# Implementation Guide: Why This Pattern Matters

## The Core Problem

Most LLM agents work like this:

```
User Goal → LLM Thinks & Acts → Done (or fails)
```

This breaks down because:
- ❌ No boundary between planning and execution
- ❌ No gates before risky operations
- ❌ No structured recovery when failures occur
- ❌ No clear task dependencies
- ❌ No observable event log

## The Solution: Explicit Stages

Insert clear stages between goal and outcome:

```
Goal → [Plan] → [Gate] → [Execute] → [Recover] → Outcome
```

Each stage has a single responsibility:
- **Plan** — Decide what should happen
- **Gate** — Check if it's safe to proceed
- **Execute** — Do what was approved
- **Recover** — Handle failures with intent

## Why This Works

### 1. Plans Can Be Wrong

Before executing, show the plan. A human can catch mistakes before they become changes:
- "That order is wrong"
- "This step is risky, skip it"
- "Add this task before step 3"

### 2. Complexity Needs Structure

5+ interdependent steps need explicit ordering. Without it:
- Steps execute in wrong order (dependency violation)
- Parallel execution breaks sequential logic
- Rollback is chaotic

### 3. Failures Need Intelligence

Different failures need different responses:
- Transient errors → retry
- Permission errors → ask human
- Logic errors → fix and retry
- Unrecoverable → escalate

Blindly retrying everything is worse than doing nothing.

### 4. Observability Prevents Mysteries

If you log every state change, you can:
- See what decided to happen (the plan)
- See what was approved (the gate decision)
- See what actually happened (the execution log)
- See how failures were handled (the recovery log)

No more "I don't know how we got here."

### 5. Humans Stay in Control

The gate stage ensures humans can intervene before execution. This is critical for:
- Risky operations (delete, deploy, financial)
- Irreversible actions
- Multi-step processes with high impact

## Key Design Principles

### Planning and Execution Are Separate

The LLM produces a plan. That plan is reviewed. Then execution happens.

This is not "think and act". It's "think, review, then act".

### Gates Are Explicit

Every stage transition is a named event. Gates are not silent. Users know when approval is needed.

### Failures Are Classified, Not Just Retried

Transient vs permanent. User error vs system error. Expected vs unexpected.

Each classification maps to a recovery strategy.

### Tasks Have Dependencies

Some tasks depend on others. Make this explicit so the orchestrator enforces it.

Example dependency graph:
```
Task 1: Analyze requirements
  ↓
Task 2: Design (depends on 1)
  ↓
Task 3: Implement (depends on 2)
  ├→ Task 4: Unit test (depends on 3)
  └→ Task 5: Integration test (depends on 3)
       ↓
Task 6: Deploy (depends on 4 and 5)
```

### Everything Is Logged

Event log is ground truth. If no event was emitted, the state change didn't happen.

## Implementation Agnosticism

This pattern works with:
- **Claude + Claw** — Tools + session persistence
- **GPT-4 + Functions** — Function calls + conversation history
- **Gemini + Custom Tools** — Tool use + state management
- **Local LLM + Ollama** — Local execution + logging
- **Multi-agent Systems** — Multiple LLMs + coordination
- **Hybrid Human + AI** — Humans at gates, AI for execution

The core pattern is universal. Only implementation details differ.

## When Not to Use This Pattern

- Single, simple actions
- No dependencies
- No approval needed
- Fire-and-forget acceptable

Use it when you have multiple steps, dependencies, or need approval.

## Further Reading

See EXAMPLES.md for real-world scenarios and edge cases.

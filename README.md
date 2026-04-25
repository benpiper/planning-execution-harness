# Planning-Execution Harness

**Tessl Skill**: [`benpiper-workspace/planning-execution-harness`](https://tessl.io/registry/skills/github/benpiper/planning-execution-harness)

A foundational pattern for breaking down any goal into multiple coordinated tasks with explicit planning, execution, gating, and recovery.

**Triggered when you need to:**
- Break a goal into multiple tasks or steps
- Coordinate execution of those tasks
- Add approval gates or decision points
- Implement automatic failure recovery
- Manage complex multi-step processes

**This Tessl skill provides:**
- **SKILL.md** — Complete architecture guide (language-agnostic)
- **Reference implementations** — Python, Rust, Node.js examples
- **JSON Schemas & Service Contracts** — Reusable specifications

## Quick Start

### 1. Review the Architecture

```bash
cat SKILL.md
```

### 2. Understand the Schemas

```bash
ls schemas/
# task-packet.schema.json       — What to execute
# bootstrap-plan.schema.json    — How to prepare
# worker-event.schema.json      — State transitions
```

### 3. Review Service Contracts

```bash
ls contracts/
# planning-orchestrator.contract.yaml   — Plan decomposition
# bootstrap-executor.contract.yaml      — Phase execution
# worker-manager.contract.yaml          — Worker lifecycle
```

### 4. Run the Examples

#### Option A: Direct Service Testing

```bash
# Terminal 1: Start planning service
python3 examples/python-planning.py

# Terminal 2: Send a request
echo '{"id":"1","method":"decompose","params":{"objective":"add dark mode"}}' | nc localhost 5000
```

#### Option B: Full Orchestration

```bash
# Run complete workflow (Python orchestrator + all services)
python3 examples/orchestrator.py "add dark mode to the dashboard"
```

#### Option C: Individual Services

```bash
# Test planning service
echo '{"id":"1","method":"decompose","params":{"objective":"test"}}' | python3 examples/python-planning.py

# Test bootstrap service (if Rust available)
echo '{"id":"1","method":"execute_phase","params":{"phase":"system_prompt_fastpath"}}' | ./examples/rust-bootstrap

# Test worker manager
echo '{"id":"1","method":"spawn_worker","params":{"task_packet":{"objective":"test","scope":"module"}}}' | node examples/nodejs-worker.js
```

## Architecture Overview

```
┌─────────────────────────────────┐
│    High-Level Objective         │
│   "add dark mode to app"        │
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│  Planning Orchestrator (Python) │ → Decompose into TaskPackets
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│  Bootstrap Executor (Rust)      │ → Prepare environment
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│  Worker Manager (Node.js)       │ → Manage lifecycle & trust
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│  Permission Gates & Recovery    │ → Gated execution
└──────────────┬──────────────────┘
               ↓
┌─────────────────────────────────┐
│     Execution (Tool Loop)       │ → Agent runs tasks
└─────────────────────────────────┘
```

## Key Concepts

### TaskPacket
A structured specification of work:
```json
{
  "objective": "Create theme provider component",
  "scope": "module",
  "scope_path": "src/theme",
  "acceptance_tests": ["npm test -- theme"],
  "commit_policy": "single verified commit",
  "escalation_policy": "stop on ambiguity"
}
```

### BootstrapPlan
Ordered preparation phases (idempotent):
- `cli_entry` — Init config, auth, paths
- `system_prompt_fastpath` — Load instructions
- `mcp_fastpath` — Initialize tools
- `daemon_worker_fastpath` — Spawn worker
- `main_runtime` — Ready for execution

### WorkerEvent
State machine transitions:
- `spawning` → `trust_required` → `trust_resolved` → `ready_for_prompt` → `running` → `finished`

### Service Contract
Defines what each service accepts/emits:
```yaml
service: planning-orchestrator
input_messages:
  decompose_request: {...}
output_messages:
  plan_created: {...}
```

## Communication Protocol

All services use **JSON-RPC over stdin/stdout**:

```json
// Request
{
  "id": "req-001",
  "method": "decompose",
  "params": {
    "objective": "add feature",
    "context": {}
  }
}

// Response
{
  "id": "req-001",
  "result": [
    {
      "objective": "...",
      "scope": "module",
      ...
    }
  ]
}
```

## File Structure

```
planning-execution-harness/
├── SKILL.md                          # The main skill (architecture guide)
├── tile.json                         # Tessl package manifest (auto-optimized)
├── README.md                         # This file
├── PUBLISHING.md                     # Publishing & claiming guide
├── .github/workflows/
│   └── tessl-publish.yml            # Auto-publish to Tessl on push
├── schemas/
│   ├── task-packet.schema.json
│   ├── bootstrap-plan.schema.json
│   └── worker-event.schema.json
├── contracts/
│   ├── planning-orchestrator.contract.yaml
│   ├── bootstrap-executor.contract.yaml
│   └── worker-manager.contract.yaml
└── examples/
    ├── orchestrator.py               # Full workflow coordinator
    ├── python-planning.py            # Planning service
    ├── rust-bootstrap.rs             # Bootstrap service
    ├── nodejs-worker.js              # Worker lifecycle service
    └── request-examples.json          # Sample requests
```

## Extending This Architecture

### Add a New Service

1. Define its schema in `schemas/`
2. Create its contract in `contracts/`
3. Implement it in any language (follow JSON-RPC stdin/stdout pattern)
4. Integrate into orchestrator

### Add a New Failure Scenario

1. Define in `schemas/failure-scenario.schema.json`
2. Create recovery recipe with steps
3. Update failure classifier
4. Implement recovery executor

### Support a New Language

1. Implement JSON-RPC stdin/stdout reader
2. Handle service contracts
3. No changes to core architecture needed!

## Validation

Validate schema compliance:

```bash
# Install ajv (JSON Schema validator)
npm install -g ajv-cli

# Validate a request
ajv validate -s schemas/task-packet.schema.json -d examples/request-examples.json
```

## Design Principles

✅ **Language-agnostic** — Each service independent, any language  
✅ **Idempotent** — Safe to retry any phase  
✅ **Event-driven** — All state changes are published  
✅ **Schema-driven** — Validate all I/O against schemas  
✅ **Gated execution** — Explicit trust checks before action  
✅ **Observable** — Complete event log for debugging  

## When to Use This Architecture

Use this skill when:
- Building multi-agent autonomous systems
- You need high-level planning before execution
- Team uses multiple programming languages
- You require explicit gates before destructive operations
- You want automatic recovery from known failures
- You need to separate task specification from implementation

## Resources

- **Tessl**: https://tessl.io
- **JSON Schema**: https://json-schema.org
- **Spec Reference**: See SKILL.md for complete architecture

## License

MIT

## Contributing

This is a reference implementation. Adapt for your needs!

---

**Next Steps:**
1. Read SKILL.md for the complete architecture guide
2. Study the schemas to understand data flow
3. Run examples to see it in action
4. Implement your own services following the patterns
5. Customize for your domain

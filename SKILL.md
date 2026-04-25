---
name: planning-execution-harness
description: Use when you need to architect a multi-language, language-agnostic system that separates high-level planning from low-level execution with gating, recovery, and permission control.
---

# Planning-Execution Harness Architecture

A proven pattern for building agent systems that decompose work into structured phases: planning → validation → gating → execution → recovery. This skill helps you implement the full architecture or use individual components.

## When to Use This Skill

Use this skill when:
- Building multi-agent systems where high-level planning must precede execution
- You need to support multiple programming languages in the same workflow
- You require explicit gating before destructive operations
- You need automatic recovery from known failure scenarios
- You want to decouple task specification from implementation details
- You're building an orchestration layer for autonomous agents

## Architecture Overview

The harness has seven ordered stages:

```
Task Specification (JSON) 
    ↓
Bootstrap Planning (validation phases)
    ↓
Worker Startup (trust gates)
    ↓
Permission Checks (execution control)
    ↓
Hook Interception (planning → execution boundary)
    ↓
Execution Loop (tool calls and iteration)
    ↓
Failure Recovery (automatic remediation)
```

All communication between stages uses **JSON message contracts** — no language-specific code required.

## Stage 1: Define Task Specification Schema

Create a `task-packet.schema.json` that specifies work:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema",
  "title": "TaskPacket",
  "description": "High-level task specification",
  "type": "object",
  "required": ["objective", "scope", "acceptance_tests"],
  "properties": {
    "objective": {
      "type": "string",
      "description": "High-level goal to accomplish"
    },
    "scope": {
      "enum": ["workspace", "module", "single_file", "custom"],
      "description": "Work granularity"
    },
    "scope_path": {
      "type": ["string", "null"],
      "description": "Path when scope is module, single_file, or custom"
    },
    "acceptance_tests": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Commands that validate success"
    },
    "commit_policy": {
      "type": "string",
      "description": "Guidance on how to commit changes"
    },
    "escalation_policy": {
      "type": "string",
      "description": "What to do when recovery fails"
    }
  }
}
```

**Key principle:** The task packet is human-readable and declarative. It describes *what* needs to happen, not *how*.

## Stage 2: Define Bootstrap Plan

Create `bootstrap-plan.schema.json` with ordered preparation phases:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema",
  "title": "BootstrapPlan",
  "type": "object",
  "properties": {
    "phases": {
      "type": "array",
      "items": {
        "enum": [
          "cli_entry",
          "system_prompt_fastpath",
          "mcp_fastpath",
          "daemon_worker_fastpath",
          "main_runtime"
        ]
      },
      "description": "Ordered list of phases to execute before main loop"
    }
  }
}
```

Each phase:
- Is **idempotent** (safe to retry)
- **Produces artifacts** (system prompt, config, etc.)
- **Publishes events** (started/completed/failed)

## Stage 3: Define Worker Events

Create `worker-event.schema.json` for state transitions:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema",
  "title": "WorkerEvent",
  "type": "object",
  "required": ["event_id", "kind", "worker_id", "timestamp"],
  "properties": {
    "event_id": {"type": "string"},
    "kind": {
      "enum": [
        "spawning",
        "trust_required",
        "trust_resolved",
        "ready_for_prompt",
        "running",
        "finished",
        "failed"
      ]
    },
    "worker_id": {"type": "string"},
    "timestamp": {"type": "integer"},
    "payload": {"type": "object"}
  }
}
```

**Critical gates:**
- `trust_required` — Stop and wait for approval before proceeding
- `ready_for_prompt` — All preconditions met, can now accept task description

## Stage 4: Define Service Contracts

Create a service contract that specifies message I/O. Example for a planning service:

```yaml
# planning-orchestrator.contract.yaml
service: planning-orchestrator
description: Decomposes objectives into structured TaskPackets

input_messages:
  decompose_request:
    schema:
      type: object
      properties:
        objective:
          type: string
          description: High-level goal to decompose
        context:
          type: object
          description: Project context (git status, workspace state, etc.)
    response:
      type: array
      items:
        $ref: task-packet.schema.json

output_messages:
  plan_created:
    schema:
      type: object
      properties:
        plan_id: {type: string}
        packets:
          type: array
          items:
            $ref: task-packet.schema.json
```

**Create similar contracts for:**
- `bootstrap-executor` (executes ordered phases)
- `worker-manager` (spawn, gate, monitor workers)
- `permission-enforcer` (authorization checks)
- `recovery-executor` (automatic remediation)

## Stage 5: Implement Transport Protocol

Choose one (or support multiple):

### Option A: stdin/stdout (simplest, works everywhere)

```json
// Request (any language sends this)
{
  "id": "req-001",
  "service": "planning",
  "method": "decompose",
  "params": {
    "objective": "add dark mode",
    "context": {}
  }
}

// Response (any language receives this)
{
  "id": "req-001",
  "result": [
    {
      "objective": "create theme context",
      "scope": "module",
      "acceptance_tests": ["npm test"]
    }
  ]
}
```

### Option B: HTTP (distributed services)

```
POST /services/planning/methods/decompose
Content-Type: application/json

{"objective": "add dark mode", "context": {}}
```

### Option C: gRPC (high-performance)

Define in `.proto`:

```protobuf
service PlanningOrchestrator {
  rpc Decompose(DecomposeRequest) returns (DecomposeResponse);
}
```

**Recommendation:** Start with stdin/stdout for testing, graduate to HTTP for distributed systems.

## Stage 6: Implement Services

### Python Planning Orchestrator

```python
import json
import sys

class PlanningOrchestrator:
    def decompose(self, objective: str, context: dict) -> list:
        """Break objective into smaller TaskPackets."""
        # Could use Claude API, LLMs, heuristics, or domain logic
        return [
            {
                "objective": f"Part 1: {objective}",
                "scope": "module",
                "acceptance_tests": ["test command 1"]
            },
            {
                "objective": f"Part 2: {objective}",
                "scope": "module",
                "acceptance_tests": ["test command 2"]
            }
        ]

    def handle_message(self, msg: dict) -> dict:
        if msg["method"] == "decompose":
            packets = self.decompose(
                msg["params"]["objective"],
                msg["params"]["context"]
            )
            return {
                "id": msg["id"],
                "result": packets
            }

if __name__ == "__main__":
    orchestrator = PlanningOrchestrator()
    
    for line in sys.stdin:
        request = json.loads(line)
        response = orchestrator.handle_message(request)
        print(json.dumps(response))
```

### Rust Bootstrap Executor

```rust
use serde::{Deserialize, Serialize};
use std::io::{self, BufRead};

#[derive(Deserialize)]
struct Request {
    id: String,
    method: String,
    #[serde(default)]
    params: serde_json::Value,
}

fn execute_phase(phase: &str) -> serde_json::Value {
    match phase {
        "system_prompt_fastpath" => {
            serde_json::json!({
                "phase": phase,
                "success": true,
                "artifacts": {
                    "system_prompt": "You are a helpful assistant..."
                }
            })
        }
        "mcp_fastpath" => {
            serde_json::json!({
                "phase": phase,
                "success": true
            })
        }
        _ => serde_json::json!({"error": "unknown phase"})
    }
}

fn main() {
    let stdin = io::stdin();
    for line in stdin.lock().lines() {
        if let Ok(line) = line {
            if let Ok(request) = serde_json::from_str::<Request>(&line) {
                let result = execute_phase(
                    request.params["phase"].as_str().unwrap_or("unknown")
                );
                
                println!("{}", serde_json::to_string(&serde_json::json!({
                    "id": request.id,
                    "result": result
                })).unwrap());
            }
        }
    }
}
```

### Node.js Worker Manager

```javascript
const readline = require('readline');

class WorkerManager {
    constructor() {
        this.workers = new Map();
        this.requestId = 0;
    }

    spawnWorker(taskPacket) {
        const workerId = `worker_${Date.now()}`;
        this.workers.set(workerId, {
            status: 'spawning',
            taskPacket,
            createdAt: Date.now()
        });

        // Publish event
        this.publish({
            event_id: `evt_${Date.now()}`,
            kind: 'spawning',
            worker_id: workerId,
            timestamp: Math.floor(Date.now() / 1000)
        });

        return workerId;
    }

    publish(event) {
        console.log(JSON.stringify(event));
    }

    handle(request) {
        if (request.method === 'spawn_worker') {
            const workerId = this.spawnWorker(request.params.task_packet);
            return { id: request.id, result: workerId };
        }
    }
}

const rl = readline.createInterface({
    input: process.stdin,
    terminal: false
});

const manager = new WorkerManager();

rl.on('line', (line) => {
    try {
        const request = JSON.parse(line);
        const response = manager.handle(request);
        console.log(JSON.stringify(response));
    } catch (e) {
        console.error(JSON.stringify({ error: e.message }));
    }
});
```

## Stage 7: Build the Orchestrator

Any language can coordinate services by reading/writing JSON:

```python
# orchestrator.py
import subprocess
import json

class MultiServiceOrchestrator:
    def __init__(self):
        self.planning = subprocess.Popen(
            ["python3", "planning.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.bootstrap = subprocess.Popen(
            ["./bootstrap"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.worker = subprocess.Popen(
            ["node", "worker.js"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.req_id = 0

    def call_service(self, proc, method: str, params: dict):
        self.req_id += 1
        request = {
            "id": f"req_{self.req_id}",
            "method": method,
            "params": params
        }
        
        proc.stdin.write(json.dumps(request) + "\n")
        response_line = proc.stdout.readline()
        return json.loads(response_line)

    def run(self, objective: str):
        # Stage 1: Plan
        plan = self.call_service(
            self.planning,
            "decompose",
            {"objective": objective, "context": {}}
        )
        print(f"Plan: {json.dumps(plan, indent=2)}")

        # Stage 2: Bootstrap
        bootstrap = self.call_service(
            self.bootstrap,
            "execute_phase",
            {"phase": "system_prompt_fastpath"}
        )
        print(f"Bootstrap: {json.dumps(bootstrap, indent=2)}")

        # Stage 3: Spawn workers for each task
        for packet in plan["result"]:
            worker = self.call_service(
                self.worker,
                "spawn_worker",
                {"task_packet": packet}
            )
            print(f"Spawned: {worker['result']}")

if __name__ == "__main__":
    orch = MultiServiceOrchestrator()
    orch.run("add dark mode to the dashboard")
```

## Key Design Principles

1. **JSON is the protocol** — No language-specific serialization; everything is JSON
2. **Idempotency** — Services can be restarted; state lives in the event log
3. **Async-first** — Services publish events; external systems subscribe
4. **Schema-driven** — Validate all inputs against JSON schemas
5. **Failure recovery** — Map error types to automatic recovery recipes
6. **Permission gating** — Execution stages are distinct; planning phase gates prevent premature action

## Common Patterns

### Adding a New Service

1. Write its input/output schema in JSON Schema
2. Create a service contract (YAML) describing methods
3. Implement in any language (stdin/stdout JSON-RPC)
4. Update orchestrator to call it at the right stage

### Adding a New Failure Scenario

1. Define in `failure-scenario.schema.json`
2. Create recovery recipe with ordered steps
3. Update failure classifier to recognize the error
4. Implement recovery executor for that scenario

### Supporting a New Language

1. Implement JSON-RPC stdin/stdout reader
2. Handle service message contracts
3. Call other services via subprocess or HTTP
4. No changes needed to core architecture

## Testing This Locally

```bash
# Terminal 1: Run planning service
python3 planning.py

# Terminal 2: Run bootstrap service  
./bootstrap

# Terminal 3: Run worker manager
node worker.js

# Terminal 4: Run orchestrator
python3 orchestrator.py
```

Or pipe directly:

```bash
echo '{"id":"1","method":"decompose","params":{"objective":"test"}}' \
  | python3 planning.py \
  | tee event.log
```

## Validation Checklist

Before deploying:

- [ ] All schemas are valid JSON Schema (test with `ajv`)
- [ ] Service contracts match schema definitions
- [ ] Each service is idempotent (safe to retry)
- [ ] Bootstrap phases produce expected artifacts
- [ ] Worker events follow state machine rules
- [ ] Recovery recipes have all required steps
- [ ] Permission gates are tested for both planning and execution stages
- [ ] Multi-language services communicate successfully
- [ ] Event log captures all state transitions

## Resources

- **JSON Schema validator:** `npm install ajv-cli`
- **Example repos:** See tessl.io registry for sample implementations
- **Specification:** Refer to each stage's schema files as source of truth

## Common Mistakes to Avoid

1. **Skipping the trust gate** — Always wait for `trust_required` → `trust_resolved` before proceeding
2. **Hardcoding language assumptions** — Services must be language-agnostic
3. **Forgetting idempotency** — Phases can be retried; make them safe
4. **Missing event publication** — If it didn't emit an event, it didn't happen (for observability)
5. **Assuming synchronous execution** — Services may not respond immediately; use events for async coordination
6. **Not validating schemas** — Always validate inputs against JSON schemas before processing

## Next Steps

1. **Choose your languages** — Pick best tool for each service
2. **Generate schemas** — Use JSON Schema templates as starting point
3. **Implement one service** — Start with planning orchestrator
4. **Build the orchestrator** — Glue services together
5. **Add bootstrap phases** — Implement preparation workflow
6. **Add worker lifecycle** — Implement trust gates and ready checks
7. **Add recovery** — Map failures to automatic recovery
8. **Iterate** — Test, measure, refine

---

This architecture is proven in production autonomous systems. The language-agnostic design means you can evolve each component independently, test services in isolation, and scale beyond a single machine.

---
name: planning-execution-harness
description: Use when you need to separate planning from execution. Applies to any system that requires: decomposing high-level goals into concrete tasks, gating before execution, automatic failure recovery, or structured workflows with explicit state transitions.
---

# Planning-Execution Harness Architecture

A seven-stage pattern for agent systems: **Task Specification → Bootstrap Planning → Worker Startup → Permission Checks → Hook Interception → Execution Loop → Failure Recovery**. All stages communicate via JSON message contracts — no language-specific serialization.

## Stage Overview

```
Task Specification (JSON schema)
    ↓ validate against task-packet.schema.json
Bootstrap Planning (ordered, idempotent phases)
    ↓ validate phase artifacts produced
Worker Startup → emit trust_required event → GATE (wait for trust_resolved)
    ↓ worker emits ready_for_prompt
Permission Checks
    ↓ validate authorization before destructive ops
Hook Interception (planning→execution boundary)
    ↓
Execution Loop (tool calls)
    ↓ on error: classify failure type
Failure Recovery (map error type → recovery recipe)
```

## Core Schemas (create as separate files)

**task-packet.schema.json** — required fields: `objective` (string), `scope` (enum: workspace/module/single_file/custom), `acceptance_tests` (array of command strings). Optional: `scope_path`, `commit_policy`, `escalation_policy`.

**worker-event.schema.json** — required: `event_id`, `kind` (enum: spawning/trust_required/trust_resolved/ready_for_prompt/running/finished/failed), `worker_id`, `timestamp`.

**Service contracts** (YAML) — define `input_messages` and `output_messages` with `$ref` to schema files for: `planning-orchestrator`, `bootstrap-executor`, `worker-manager`, `permission-enforcer`, `recovery-executor`.

See `SCHEMAS.md` for full schema definitions and `PATTERNS.md` for failure recovery recipes.

## Minimal End-to-End Example (Python orchestrator)

```python
import subprocess, json

class Orchestrator:
    def __init__(self):
        self.planning = self._start(["python3", "planning.py"])
        self.bootstrap = self._start(["./bootstrap"])
        self.worker = self._start(["node", "worker.js"])
        self.req_id = 0

    def _start(self, cmd):
        return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def call(self, proc, method, params):
        self.req_id += 1
        req = {"id": f"req_{self.req_id}", "method": method, "params": params}
        proc.stdin.write(json.dumps(req) + "\n")
        resp = json.loads(proc.stdout.readline())
        if "error" in resp:
            raise RuntimeError(f"{method} failed: {resp['error']}")
        return resp["result"]

    def run(self, objective):
        # Stage 1: Decompose objective into TaskPackets — validate output against schema
        packets = self.call(self.planning, "decompose", {"objective": objective, "context": {}})
        assert all("acceptance_tests" in p for p in packets), "Invalid TaskPacket: missing acceptance_tests"

        # Stage 2: Bootstrap — validate artifacts before proceeding
        artifacts = self.call(self.bootstrap, "execute_phase", {"phase": "system_prompt_fastpath"})
        assert artifacts.get("success"), f"Bootstrap phase failed: {artifacts}"

        # Stage 3: Spawn workers — GATE on trust_required → trust_resolved before continuing
        for packet in packets:
            worker_id = self.call(self.worker, "spawn_worker", {"task_packet": packet})
            # Worker manager must emit trust_resolved before ready_for_prompt
            status = self.call(self.worker, "get_status", {"worker_id": worker_id})
            assert status["kind"] == "ready_for_prompt", f"Trust gate not cleared: {status}"
```

Each service (planning.py, bootstrap, worker.js) reads JSON-RPC from stdin, writes responses to stdout. See `IMPLEMENTATIONS.md` for Rust and Node.js service implementations.

## Transport Options

| Transport | Usage |
|-----------|-------|
| **stdin/stdout** (recommended) | newline-delimited JSON-RPC |
| **HTTP** | `POST /services/{name}/methods/{method}` with JSON body |
| **gRPC** | define `.proto` per service contract |

## Key Design Principles

1. **Trust gate is mandatory** — never proceed past `trust_required` without `trust_resolved`
2. **Idempotency** — all bootstrap phases must be safe to retry
3. **Schema validation** — validate inputs and outputs at every stage boundary
4. **Event log = ground truth** — if no event was emitted, the state change didn't happen
5. **Failure classification** — map error types to recovery recipes before retrying

## Adding Components

- **New service**: JSON Schema → YAML contract → stdin/stdout JSON-RPC handler → register in orchestrator
- **New failure scenario**: add to `failure-scenario.schema.json` → create recovery recipe → update classifier
- **New language**: implement JSON-RPC stdin/stdout loop; no changes to core architecture

## Validation Checklist

- [ ] All schemas valid (`npx ajv-cli validate -s schema.json -d data.json`)
- [ ] Bootstrap phases produce expected artifacts
- [ ] Trust gate tested: trust_required blocks, trust_resolved unblocks
- [ ] Recovery recipes handle all defined failure scenarios
- [ ] Multi-language services exchange messages successfully
- [ ] Event log captures all state transitions

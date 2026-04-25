---
name: planning-execution-harness
description: "Use when orchestrating sequential tasks, multi-step automation pipelines, or DAG-style workflows that require dependency tracking, approval gates, checkpoint/resume logic, and rollback on failure. Creates ordered task pipelines with schema-validated stage boundaries, trust-gate enforcement between worker startup and execution, and failure classification mapped to recovery recipes. Applies to: decomposing a goal into dependency-ordered TaskPackets, coordinating JSON-RPC services across a build-and-deploy sequence, enforcing approval gates in CI/CD workflows, implementing structured failure recovery with per-error-type recipes, and automating multi-stage processes with event-log ground truth. Not for single API calls or one-off scripts — use when there are 3+ coordinated steps with task dependencies or sequential execution order."
---

# Planning-Execution Harness Architecture

A seven-stage pattern for agent systems: **Task Specification → Bootstrap Planning → Worker Startup → Permission Checks → Hook Interception → Execution Loop → Failure Recovery**. All stages communicate via JSON message contracts — no language-specific serialization.

## Stage Overview

```
Task Specification     → validate against task-packet.schema.json
Bootstrap Planning     → validate phase artifacts produced
Worker Startup         → emit trust_required → GATE (wait for trust_resolved)
                       → worker emits ready_for_prompt
Permission Checks      → validate authorization before destructive ops
Hook Interception      → planning→execution boundary
Execution Loop         → tool calls
Failure Recovery       → classify error type → apply recovery recipe
```

## Core Schemas

**task-packet.schema.json** — create this file with the following definition:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TaskPacket",
  "type": "object",
  "required": ["objective", "scope", "acceptance_tests"],
  "properties": {
    "objective": { "type": "string" },
    "scope": { "type": "string", "enum": ["workspace", "module", "single_file", "custom"] },
    "acceptance_tests": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
    "scope_path": { "type": "string" },
    "commit_policy": { "type": "string", "enum": ["auto", "manual", "none"] },
    "escalation_policy": { "type": "string", "enum": ["fail", "pause", "skip"] }
  }
}
```

**worker-event.schema.json** — required: `event_id`, `kind` (enum: spawning/trust_required/trust_resolved/ready_for_prompt/running/finished/failed), `worker_id`, `timestamp`.

**Service contracts** (YAML) — define `input_messages` and `output_messages` with `$ref` to schema files for: `planning-orchestrator`, `bootstrap-executor`, `worker-manager`, `permission-enforcer`, `recovery-executor`.

See `SCHEMAS.md` for remaining schema definitions and `PATTERNS.md` for failure recovery recipes.

## Minimal End-to-End Example (Python orchestrator)

### Minimal service implementation (planning.py)

```python
import sys, json

def decompose(objective, context):
    # Replace with real decomposition logic
    return [{"objective": objective, "scope": "workspace", "acceptance_tests": ["pytest"]}]

for line in sys.stdin:
    req = json.loads(line)
    result = decompose(**req["params"]) if req["method"] == "decompose" else None
    sys.stdout.write(json.dumps({"id": req["id"], "result": result}) + "\n")
    sys.stdout.flush()
```

All other services (bootstrap, worker.js) follow the same stdin/stdout JSON-RPC loop — read a line, dispatch on `method`, write a response line.

### Orchestrator

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

## Key Design Principles

1. **Trust gate is mandatory** — never proceed past `trust_required` without `trust_resolved`
2. **Schema validation at every boundary** — validate inputs and outputs at each stage transition
3. **Event log = ground truth** — if no event was emitted, the state change didn't happen
4. **Failure classification first** — map error types to recovery recipes before retrying
5. **New service pattern**: JSON Schema → YAML contract → stdin/stdout JSON-RPC handler → register in orchestrator
6. **New failure scenario**: add to `failure-scenario.schema.json` → create recovery recipe → update classifier

## Validation Checklist

- [ ] All schemas valid (`npx ajv-cli validate -s schema.json -d data.json`)
- [ ] Bootstrap phases produce expected artifacts
- [ ] Trust gate tested: trust_required blocks, trust_resolved unblocks
- [ ] Recovery recipes handle all defined failure scenarios
- [ ] Multi-language services exchange messages successfully
- [ ] Event log captures all state transitions

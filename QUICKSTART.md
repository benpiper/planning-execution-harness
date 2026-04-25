# Quick Start Guide

Get the planning-execution harness running in under 5 minutes.

## Prerequisites

- Python 3.7+
- Node.js 14+ (optional, for worker service)
- Rust (optional, for bootstrap service)

## 1. Test Individual Services

Each service runs independently on stdin/stdout. Open separate terminals:

### Terminal 1: Planning Service

```bash
cd ~/planning-execution-harness
python3 examples/python-planning.py
```

Then in another terminal, send a request:

```bash
echo '{"id":"1","method":"decompose","params":{"objective":"add dark mode"}}' | python3 examples/python-planning.py
```

You should see:
```json
{
  "id": "1",
  "result": [
    {
      "objective": "Prepare: Setup environment for 'add dark mode'",
      "scope": "module",
      ...
    },
    ...
  ]
}
```

### Terminal 2: Worker Manager

```bash
cd ~/planning-execution-harness
node examples/nodejs-worker.js
```

Send a request:

```bash
cat > /tmp/worker_req.json << 'EOF'
{
  "id":"2",
  "method":"spawn_worker",
  "params":{
    "task_packet":{
      "objective":"Create theme provider",
      "scope":"module",
      "scope_path":"src/theme",
      "acceptance_tests":["npm test"]
    }
  }
}
EOF

node examples/nodejs-worker.js < /tmp/worker_req.json
```

You should see events on stdout:
```json
{"event_id":"evt_..._spawn","kind":"spawning","worker_id":"worker_..."}
{"id":"2","result":{"worker_id":"worker_..."}}
```

## 2. Run Full Orchestration

Run the complete workflow with all services:

```bash
cd ~/planning-execution-harness
python3 examples/orchestrator.py "add dark mode to the dashboard"
```

This will:
1. ✅ Start planning service
2. ✅ Decompose objective into 4 tasks
3. ✅ Start bootstrap service
4. ✅ Execute system prompt and MCP phases
5. ✅ Start worker manager
6. ✅ Spawn workers for each task
7. ✅ Check and resolve trust gates
8. ✅ Print summary

Expected output:
```
[Planning] Started
[Bootstrap] Started
[Worker] Started

=== Stage 1: Planning ===
Generated 4 task packets
  [1] Prepare: Setup environment for 'add dark mode'
  [2] Implement: Core logic for 'add dark mode'
  [3] Test: Validate 'add dark mode' works correctly
  [4] Polish: Final refinements for 'add dark mode'

=== Stage 2: Bootstrap ===
Executing phase: system_prompt_fastpath
  ✓ system_prompt_fastpath
Executing phase: mcp_fastpath
  ✓ mcp_fastpath

=== Stage 3: Spawn Workers ===
Spawning worker for task 1...
  Spawned: worker_1234_1704067200
...

=== Stage 4: Trust Gates ===
  worker_1234_1704067200: requires_approval=true
  worker_1234_1704067200: marked trusted
...

=== Summary ===
Objective: add dark mode to the dashboard
Packets: 4
Workers: 4
Events: 14
```

## 3. Validate Schemas

If you have `ajv` installed:

```bash
# Install ajv
npm install -g ajv-cli

# Validate a task packet
ajv validate -s schemas/task-packet.schema.json -d examples/request-examples.json
```

## 4. Inspect the Architecture

```bash
# Read the full architecture guide
cat SKILL.md | less

# View the schemas
ls -la schemas/

# View the service contracts
ls -la contracts/

# View example implementations
ls -la examples/
```

## 5. Test Individual Phases

### Test Planning Decomposition

```bash
python3 examples/python-planning.py << 'EOF'
{"id":"p1","method":"decompose","params":{"objective":"fix login bug"}}
EOF
```

### Test Bootstrap Phases

```bash
python3 -c "
import subprocess
import json

cmd = 'python3 -c \"import json, sys; sys.path.insert(0, \'examples\'); exec(open(\\\"examples/python-planning.py\\\").read())\"'

# If Rust bootstrap available:
# rustc examples/rust-bootstrap.rs -o /tmp/bootstrap
# echo '{\"id\":\"b1\",\"method\":\"execute_phase\",\"params\":{\"phase\":\"system_prompt_fastpath\"}}' | /tmp/bootstrap
"
```

### Test Worker Lifecycle

```bash
cat > /tmp/worker_test.sh << 'EOF'
#!/bin/bash

# Start worker manager in background
node examples/nodejs-worker.js > /tmp/worker.log 2>&1 &
WORKER_PID=$!

sleep 1

# Send spawn request
echo '{"id":"w1","method":"spawn_worker","params":{"task_packet":{"objective":"test","scope":"module"}}}' \
  | nc localhost 5000 || echo 'Note: nc not available, check /tmp/worker.log'

# Stop worker
kill $WORKER_PID 2>/dev/null

# Show events
echo "Events logged:"
cat /tmp/worker.log
EOF

bash /tmp/worker_test.sh
```

## Common Patterns

### Pattern 1: Decompose and Execute

```bash
# Get task packets
PACKETS=$(python3 examples/python-planning.py << 'EOF'
{"id":"1","method":"decompose","params":{"objective":"feature"}}
EOF
)

# Spawn worker for first packet
echo $PACKETS | jq '.result[0]' | node examples/nodejs-worker.js
```

### Pattern 2: Full Loop

```bash
python3 examples/orchestrator.py "your objective here"
```

### Pattern 3: Pipe Services

```bash
echo '{"id":"1","method":"decompose","params":{"objective":"test"}}' \
  | python3 examples/python-planning.py \
  | jq '.result' \
  | tee /tmp/plan.json
```

## Troubleshooting

### "Module not found"

Make sure you're in the repo directory:
```bash
cd ~/planning-execution-harness
```

### "Port already in use"

Services use stdin/stdout, not network ports. If you see this error, you may have a background process:
```bash
pkill -f python-planning
pkill -f nodejs-worker
pkill -f orchestrator
```

### "Invalid JSON"

Check that requests follow the contract schema:
```bash
ajv validate -s schemas/task-packet.schema.json < /tmp/my_packet.json
```

### Service not responding

Ensure stdin/stdout is connected:
```bash
# Good - service reads from stdin
echo 'request' | python3 examples/python-planning.py

# Bad - no input, service waiting on stdin
python3 examples/python-planning.py  # Ctrl+C to exit
```

## Next Steps

1. **Read the architecture**: `cat SKILL.md`
2. **Study the contracts**: Look at `contracts/` directory
3. **Implement your service**: Follow the pattern in `examples/`
4. **Extend the orchestrator**: Add your domain logic
5. **Deploy**: Use this as foundation for production system

## Architecture at a Glance

```
Objective
    ↓ Planning Service (Python)
Task Packets
    ↓ Bootstrap Service (Rust/Python)
Prepared Environment
    ↓ Worker Manager (Node.js)
Worker Lifecycle
    ↓ Permission Gates
Gated Execution
    ↓ Agent Loop
Success
```

Each arrow is a JSON message contract. Each box can be any language!

---

**Need help?** Check SKILL.md for the full architecture guide.

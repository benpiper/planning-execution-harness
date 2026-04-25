#!/usr/bin/env python3
"""
Multi-Service Orchestrator - Python reference implementation

Coordinates planning → bootstrap → worker lifecycle across multiple language implementations.

Usage:
    python3 orchestrator.py "add dark mode to the dashboard"
"""

import subprocess
import json
import sys
from typing import Any, Dict, List, Optional


class ServiceClient:
    """Generic JSON-RPC client for any service."""

    def __init__(self, command: List[str], name: str):
        self.command = command
        self.name = name
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0

    def start(self) -> bool:
        """Start the service subprocess."""
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            print(f"[{self.name}] Started", file=sys.stderr)
            return True
        except Exception as e:
            print(f"[{self.name}] Failed to start: {e}", file=sys.stderr)
            return False

    def call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request and get response."""
        if not self.process or not self.process.stdin:
            raise RuntimeError(f"{self.name} not started")

        self.request_id += 1
        request = {
            "id": f"req_{self.request_id}",
            "method": method,
            "params": params
        }

        try:
            # Send request
            self.process.stdin.write(json.dumps(request) + "\n")
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError(f"{self.name} closed unexpectedly")

            response = json.loads(response_line)
            print(f"[{self.name}] {method} → OK", file=sys.stderr)
            return response

        except Exception as e:
            print(f"[{self.name}] {method} failed: {e}", file=sys.stderr)
            raise

    def stop(self):
        """Stop the service."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print(f"[{self.name}] Stopped", file=sys.stderr)


class MultiServiceOrchestrator:
    """Orchestrates planning → bootstrap → worker workflow."""

    def __init__(self):
        self.planning = ServiceClient(
            ["python3", "examples/python-planning.py"],
            "Planning"
        )
        self.bootstrap = ServiceClient(
            ["python3", "-c", self._rust_bootstrap_fallback()],
            "Bootstrap"
        )
        self.worker = ServiceClient(
            ["node", "examples/nodejs-worker.js"],
            "Worker"
        )
        self.event_log: List[Dict[str, Any]] = []

    @staticmethod
    def _rust_bootstrap_fallback() -> str:
        """Fallback bootstrap implementation in Python if Rust not available."""
        return """
import json
import sys

class Bootstrap:
    def execute_phase(self, phase):
        phases = {
            'system_prompt_fastpath': {
                'phase': phase,
                'success': True,
                'artifacts': {'system_prompt': 'You are a helpful assistant...'}
            },
            'mcp_fastpath': {
                'phase': phase,
                'success': True,
                'artifacts': {'mcp_servers': ['stdio']}
            }
        }
        return phases.get(phase, {'phase': phase, 'success': False, 'error': 'unknown'})

    def handle(self, req):
        if req['method'] == 'execute_phase':
            result = self.execute_phase(req['params']['phase'])
            return {'id': req['id'], 'result': result}

b = Bootstrap()
for line in sys.stdin:
    req = json.loads(line)
    resp = b.handle(req)
    print(json.dumps(resp))
"""

    def start_all(self) -> bool:
        """Start all services."""
        all_ok = True
        for service in [self.planning, self.bootstrap, self.worker]:
            if not service.start():
                all_ok = False
        return all_ok

    def stop_all(self):
        """Stop all services."""
        for service in [self.planning, self.bootstrap, self.worker]:
            service.stop()

    def log_event(self, event: Dict[str, Any]):
        """Record event in append-only log."""
        self.event_log.append(event)
        print(f"[EventLog] {json.dumps(event)}", file=sys.stderr)

    def execute_workflow(self, objective: str) -> bool:
        """Execute the full planning → bootstrap → worker workflow."""
        try:
            # Stage 1: Planning
            print(f"\n=== Stage 1: Planning ===", file=sys.stderr)
            self.log_event({
                "kind": "workflow_started",
                "objective": objective
            })

            plan_response = self.planning.call(
                "decompose",
                {
                    "objective": objective,
                    "context": {}
                }
            )

            if "error" in plan_response:
                print(f"Planning failed: {plan_response['error']}", file=sys.stderr)
                return False

            packets = plan_response.get("result", [])
            print(f"Generated {len(packets)} task packets", file=sys.stderr)

            for i, packet in enumerate(packets):
                print(f"  [{i+1}] {packet['objective']}", file=sys.stderr)

            self.log_event({
                "kind": "plan_created",
                "task_count": len(packets),
                "packets": packets
            })

            # Stage 2: Bootstrap
            print(f"\n=== Stage 2: Bootstrap ===", file=sys.stderr)

            for phase in ["system_prompt_fastpath", "mcp_fastpath"]:
                print(f"Executing phase: {phase}", file=sys.stderr)
                bootstrap_response = self.bootstrap.call(
                    "execute_phase",
                    {
                        "phase": phase,
                        "context": {}
                    }
                )

                if bootstrap_response.get("result", {}).get("success"):
                    print(f"  ✓ {phase}", file=sys.stderr)
                else:
                    print(f"  ✗ {phase} failed", file=sys.stderr)
                    return False

            self.log_event({
                "kind": "bootstrap_completed",
                "phases": ["system_prompt_fastpath", "mcp_fastpath"]
            })

            # Stage 3: Spawn Workers
            print(f"\n=== Stage 3: Spawn Workers ===", file=sys.stderr)

            worker_ids = []
            for i, packet in enumerate(packets):
                print(f"Spawning worker for task {i+1}...", file=sys.stderr)

                worker_response = self.worker.call(
                    "spawn_worker",
                    {"task_packet": packet}
                )

                if "result" in worker_response:
                    worker_id = worker_response["result"].get("worker_id")
                    worker_ids.append(worker_id)
                    print(f"  Spawned: {worker_id}", file=sys.stderr)
                else:
                    print(f"  Failed to spawn worker", file=sys.stderr)

            # Stage 4: Check Trust Gates
            print(f"\n=== Stage 4: Trust Gates ===", file=sys.stderr)

            for worker_id in worker_ids:
                trust_response = self.worker.call(
                    "check_trust",
                    {"worker_id": worker_id}
                )
                print(f"  {worker_id}: requires_approval={trust_response['result']['requires_approval']}", file=sys.stderr)

                # Mark as trusted (in real system, this would be interactive)
                self.worker.call(
                    "mark_trusted",
                    {
                        "worker_id": worker_id,
                        "approval_source": "orchestrator_auto"
                    }
                )
                print(f"  {worker_id}: marked trusted", file=sys.stderr)

            self.log_event({
                "kind": "workflow_completed",
                "status": "success",
                "worker_count": len(worker_ids)
            })

            print(f"\n=== Summary ===", file=sys.stderr)
            print(f"Objective: {objective}", file=sys.stderr)
            print(f"Packets: {len(packets)}", file=sys.stderr)
            print(f"Workers: {len(worker_ids)}", file=sys.stderr)
            print(f"Events: {len(self.event_log)}", file=sys.stderr)

            return True

        except Exception as e:
            print(f"Workflow failed: {e}", file=sys.stderr)
            self.log_event({
                "kind": "workflow_failed",
                "error": str(e)
            })
            return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 orchestrator.py <objective>", file=sys.stderr)
        print("Example: python3 orchestrator.py 'add dark mode to dashboard'", file=sys.stderr)
        sys.exit(1)

    objective = " ".join(sys.argv[1:])
    orchestrator = MultiServiceOrchestrator()

    try:
        if not orchestrator.start_all():
            print("Failed to start services", file=sys.stderr)
            sys.exit(1)

        success = orchestrator.execute_workflow(objective)
        sys.exit(0 if success else 1)

    finally:
        orchestrator.stop_all()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Planning Orchestrator - Python reference implementation

Decomposes high-level objectives into structured TaskPackets.
Uses stdin/stdout JSON-RPC protocol.

Usage:
    python3 python-planning.py < request.json > response.json

Or pipe from another service:
    echo '{"id":"1","method":"decompose","params":{"objective":"add dark mode"}}' | python3 python-planning.py
"""

import json
import sys
import uuid
from typing import Any, Dict, List


class PlanningOrchestrator:
    """Decomposes objectives into TaskPackets."""

    def decompose(self, objective: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Break an objective into smaller TaskPackets.

        In production, this could:
        - Call Claude API to decompose
        - Use domain heuristics
        - Parse structured task templates
        - Integrate with planning frameworks

        For now, we demonstrate the pattern.
        """
        # Simple heuristic: split objective into phases
        phases = [
            f"Prepare: Setup environment for '{objective}'",
            f"Implement: Core logic for '{objective}'",
            f"Test: Validate '{objective}' works correctly",
            f"Polish: Final refinements for '{objective}'",
        ]

        packets = []
        for i, phase in enumerate(phases):
            packets.append({
                "objective": phase,
                "scope": "module",
                "scope_path": f"phase_{i+1}",
                "acceptance_tests": [
                    f"echo 'Phase {i+1} completed'",
                    "exit 0"
                ],
                "commit_policy": "single verified commit per phase",
                "escalation_policy": "stop and ask on ambiguity"
            })

        return packets

    def refine(self, packets: List[Dict[str, Any]], feedback: str) -> List[Dict[str, Any]]:
        """
        Refine plan based on feedback.

        In production, this would:
        - Call Claude to understand feedback
        - Adjust scope/tests/policies
        - Reorder phases
        - Add/remove packets

        For now, we just return modified copies.
        """
        # Simple example: add feedback to first objective
        refined = packets.copy()
        if refined:
            refined[0]["objective"] += f" (feedback: {feedback})"

        return refined

    def handle_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming JSON-RPC request."""
        try:
            method = msg.get("method")
            params = msg.get("params", {})

            if method == "decompose":
                result = self.decompose(
                    params.get("objective", ""),
                    params.get("context")
                )
                return {
                    "id": msg["id"],
                    "result": result
                }

            elif method == "refine":
                result = self.refine(
                    params.get("packets", []),
                    params.get("feedback", "")
                )
                return {
                    "id": msg["id"],
                    "result": result
                }

            else:
                return {
                    "id": msg["id"],
                    "error": f"Unknown method: {method}"
                }

        except Exception as e:
            return {
                "id": msg.get("id", "unknown"),
                "error": str(e)
            }


def main():
    """Read JSON-RPC requests from stdin, write responses to stdout."""
    orchestrator = PlanningOrchestrator()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            response = orchestrator.handle_message(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError as e:
            print(json.dumps({
                "error": f"Invalid JSON: {e}"
            }))
            sys.stdout.flush()


if __name__ == "__main__":
    main()

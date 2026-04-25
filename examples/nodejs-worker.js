#!/usr/bin/env node
/**
 * Worker Manager - Node.js reference implementation
 *
 * Manages worker lifecycle, trust gates, and readiness checks.
 * Uses stdin/stdout JSON-RPC protocol.
 *
 * Usage:
 *     node nodejs-worker.js < request.json > response.json
 *
 * Or as a service:
 *     echo '{"id":"1","method":"spawn_worker","params":{"task_packet":{...}}}' | node nodejs-worker.js
 */

const readline = require('readline');
const { EventEmitter } = require('events');

class WorkerManager extends EventEmitter {
    constructor() {
        super();
        this.workers = new Map();
        this.eventLog = [];
        this.nextWorkerId = 1;
    }

    /**
     * Spawn a new worker for a task packet.
     */
    spawnWorker(taskPacket) {
        const workerId = `worker_${this.nextWorkerId++}_${Date.now()}`;

        this.workers.set(workerId, {
            id: workerId,
            status: 'spawning',
            taskPacket,
            createdAt: Date.now(),
            events: []
        });

        // Emit event
        this.emitEvent({
            event_id: `evt_${Date.now()}_spawn`,
            kind: 'spawning',
            worker_id: workerId,
            timestamp: Math.floor(Date.now() / 1000),
            payload: {
                task_objective: taskPacket.objective
            }
        });

        return { worker_id: workerId };
    }

    /**
     * Check if worker requires trust gate approval.
     */
    checkTrust(workerId) {
        const worker = this.workers.get(workerId);
        if (!worker) {
            return { error: `Worker not found: ${workerId}` };
        }

        // Emit event
        this.emitEvent({
            event_id: `evt_${Date.now()}_trust`,
            kind: 'trust_required',
            worker_id: workerId,
            timestamp: Math.floor(Date.now() / 1000),
            payload: {
                reason: 'requires_approval_before_execution'
            }
        });

        return { requires_approval: true };
    }

    /**
     * Mark worker as trusted and ready for prompt.
     */
    markTrusted(workerId, approvalSource = 'auto_allowlist') {
        const worker = this.workers.get(workerId);
        if (!worker) {
            return { error: `Worker not found: ${workerId}` };
        }

        worker.status = 'trusted';

        // Emit event
        this.emitEvent({
            event_id: `evt_${Date.now()}_trusted`,
            kind: 'trust_resolved',
            worker_id: workerId,
            timestamp: Math.floor(Date.now() / 1000),
            payload: {
                approval_source: approvalSource
            }
        });

        // Emit ready event
        this.emitEvent({
            event_id: `evt_${Date.now()}_ready`,
            kind: 'ready_for_prompt',
            worker_id: workerId,
            timestamp: Math.floor(Date.now() / 1000),
            payload: {
                status: 'ready'
            }
        });

        return { success: true };
    }

    /**
     * Get worker status.
     */
    getWorker(workerId) {
        return this.workers.get(workerId);
    }

    /**
     * Emit event to stdout (append-only event log).
     */
    emitEvent(event) {
        this.eventLog.push(event);
        console.log(JSON.stringify(event));
    }

    /**
     * Handle incoming JSON-RPC request.
     */
    handleMessage(request) {
        try {
            const { id, method, params } = request;

            if (method === 'spawn_worker') {
                const result = this.spawnWorker(params.task_packet);
                return { id, result };
            }

            if (method === 'check_trust') {
                const result = this.checkTrust(params.worker_id);
                return { id, result };
            }

            if (method === 'mark_trusted') {
                const result = this.markTrusted(
                    params.worker_id,
                    params.approval_source
                );
                return { id, result };
            }

            if (method === 'get_worker') {
                const result = this.getWorker(params.worker_id);
                return { id, result };
            }

            return {
                id,
                error: `Unknown method: ${method}`
            };
        } catch (error) {
            return {
                id: request.id,
                error: error.message
            };
        }
    }
}

// Main entry point
function main() {
    const manager = new WorkerManager();
    const rl = readline.createInterface({
        input: process.stdin,
        terminal: false
    });

    rl.on('line', (line) => {
        if (!line.trim()) return;

        try {
            const request = JSON.parse(line);
            const response = manager.handleMessage(request);
            // Send response (non-events go to stdout after events)
            // In a real system, you'd separate event stream from response stream
        } catch (error) {
            console.error(
                JSON.stringify({
                    error: `Invalid JSON: ${error.message}`
                })
            );
        }
    });

    rl.on('close', () => {
        // Print summary on exit
        if (manager.workers.size > 0) {
            console.error(`\n[Worker Manager] Processed ${manager.workers.size} workers`);
            console.error(`[Worker Manager] Event log: ${manager.eventLog.length} events`);
        }
    });
}

if (require.main === module) {
    main();
}

module.exports = { WorkerManager };

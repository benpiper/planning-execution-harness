# Build a Resilient Data Sync Pipeline

## Problem Description

A fintech company runs a nightly job that pulls transaction records from three external payment processors, transforms the data into a common schema, and loads it into their analytics warehouse. The pipeline has been brittle: occasional network blips cause full job failures, expired API credentials silently drop data, bad records crash the processor, and sometimes a payment processor's endpoint disappears between runs.

The engineering team needs a well-documented pipeline implementation that handles each of these failure modes differently rather than retrying blindly or giving up immediately. They want to see explicit failure classification logic and the correct recovery recipe applied for each case. They also want the recovery design to avoid redundant work: if three of five steps have already completed when a failure occurs, recovery should restart only from the failed step.

Write a Python pipeline script for this sync job. The pipeline should include several distinct processing stages (e.g. authenticate, fetch records, transform/validate, load to warehouse). Where a real API would be called, use a stub or simulated call — the focus is on the control flow and error-handling behavior, not the actual data. The script should be runnable (no missing dependencies beyond the standard library) and demonstrate what happens under different failure conditions.

## Output Specification

Produce the following files:

1. **`pipeline.py`** — The pipeline script. It must contain:
   - The main pipeline stages in execution order
   - Error detection and handling logic that treats different categories of failures differently
   - Comments or docstrings that identify what type of failure each error-handling branch covers and why it recovers the way it does
   - Logic ensuring that a failure mid-pipeline does not cause already-completed stages to be redundantly re-executed on recovery

2. **`failure_scenarios.md`** — A short document (bullet points or a table) listing each failure type the pipeline handles, how it is detected, what recovery action is taken, and the maximum number of retry attempts for that type.

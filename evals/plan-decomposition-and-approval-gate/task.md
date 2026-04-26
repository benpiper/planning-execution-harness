# Automate a Production Release Pipeline

## Problem Description

A small SaaS company has been manually deploying their Node.js backend to a cloud VPS whenever a new version is ready. The process is error-prone: developers sometimes forget steps, occasionally deploy to production before staging tests pass, and have no record of what was done when something goes wrong.

Your job is to design and document a production-grade release pipeline for their application. The company is particularly concerned about the risk of accidental production deployments and wants any dangerous or irreversible steps to be clearly identified so a human can review before anything destructive happens.

The pipeline should cover: building the application, running tests, deploying to staging, smoke testing on staging, and promoting to production. Some steps are safe to automate freely; others (especially irreversible ones) must be clearly flagged for human review.

A starter project is provided below. You do not need to build a fully working automated system — the goal is to produce a clear, well-structured release plan that another team member could review and approve before execution begins, along with a simulated execution log showing how it would run.

## Output Specification

Produce the following files in your working directory:

1. **`release_plan.md`** — The decomposed release plan. List each step with what it does and what earlier steps it relies on. Steps that are dangerous or hard to reverse should be identified clearly so the reviewer knows to pay attention.

2. **`execution_log.txt`** — A simulated log of the pipeline running from start to finish. Each entry should carry enough information for an auditor to reconstruct exactly what happened and in what order — including when the plan was reviewed and confirmed, when each step began and ended, and how the overall run concluded.

## Input Files

The following files are provided as inputs. Extract them before beginning.

=============== FILE: inputs/package.json ===============
{
  "name": "saas-backend",
  "version": "2.4.1",
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "jest --coverage",
    "start": "node dist/index.js",
    "smoke": "node scripts/smoke-test.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "jest": "^29.7.0"
  }
}

=============== FILE: inputs/deploy-config.json ===============
{
  "staging": {
    "host": "staging.internal.example.com",
    "user": "deploy",
    "path": "/var/www/saas-backend"
  },
  "production": {
    "host": "prod.example.com",
    "user": "deploy",
    "path": "/var/www/saas-backend"
  }
}

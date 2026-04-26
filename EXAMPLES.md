# Detailed Examples

## Example 1: Resume Optimization

**Goal:** "Optimize my resume for 3 software engineer job postings"

**Plan:**
```
Task 1: Analyze the 3 job postings and extract top 10 skills (parallel)
Task 2: Review current resume and identify gaps (depends on Task 1)
Task 3: Rewrite experience section to emphasize required skills (depends on Task 2)
Task 4: Add skills section with keywords (depends on Task 1)
Task 5: Proofread and format (depends on Task 3, Task 4)
```

**User Feedback:** "Approved, but skip the skills section — I'll add that manually"

**Updated Plan:**
```
Task 1: Analyze job postings and extract top 10 skills
Task 2: Review current resume and identify gaps (depends on Task 1)
Task 3: Rewrite experience section to emphasize required skills (depends on Task 2)
Task 4: Proofread and format (depends on Task 3)
```

**Execution:**
```
[Task 1/4] ✓ Analyzed 3 job postings
  Top skills: Python (all 3), AWS (2/3), System Design (2/3), Leadership (all 3), React (2/3)

[Task 2/4] ✓ Reviewed resume gaps
  Have: Python, Leadership
  Missing: AWS, System Design deep dive, React specifics

[Task 3/4] ✓ Rewrote experience section
  Added AWS/EC2 project details
  Expanded system design examples
  Mentioned React contributions

[Task 4/4] ✓ Proofread and formatted
  Fixed typo in "architected"
  Aligned bullet points
```

**Outcome:** ✓ Resume optimized. Ready to submit.

---

## Example 2: Debug with Recovery

**Goal:** "Fix why my API keeps timing out on large requests"

**Plan:**
```
Task 1: Check request size limits
Task 2: Check database query performance
Task 3: Check network timeout settings
Task 4: Monitor actual timeout location if still failing
```

**User:** "Approved"

**Execution:**
```
[Task 1/4] ✓ Checked request size limits
  Limit: 100MB
  Actual large request: 50MB
  Not the issue.

[Task 2/4] ✓ Checked database query
  Found: N+1 query bug
  Query takes 45 seconds on large dataset
  Recovery needed.

  Recovery attempt: Add query optimization with joins
  [Task 2/4 RETRY] ✓ Query now takes 2 seconds

[Task 3/4] ✓ Checked timeout settings
  Timeout: 30 seconds
  With optimized query: well within limit

[Task 4/4] — Skipped (no longer needed, issue was Query optimization)
```

**Outcome:** ✓ Found N+1 query bug. Optimized. API now handles large requests in <5 seconds.

---

## Example 3: Multi-Step Deployment

**Goal:** "Deploy new authentication system to production"

**Plan:**
```
Task 1: Run full test suite (no side effects)
Task 2: Review deployment plan with team (approval gate)
Task 3: Deploy to staging (test before prod)
Task 4: Run smoke tests on staging
Task 5: Deploy to production (irreversible)
Task 6: Monitor production for 1 hour
```

**User Review (Task 2 gate):**
- "Approved, but add a rollback plan"

**Updated Plan:**
```
Task 1: Run full test suite
Task 2: Create rollback procedure and document it
Task 3: Review deployment with team (approval gate)
Task 4: Deploy to staging
Task 5: Run smoke tests on staging
Task 6: Deploy to production
Task 7: Monitor for 1 hour and rollback if needed
```

**Execution:**
```
[Task 1/7] ✓ Full test suite passing (1200 tests)

[Task 2/7] ✓ Created rollback procedure
  Documented: database migration rollback, service restart order, config revert

[Task 3/7] GATE: Team review requested
  Team approves deployment plan at 2:00 PM

[Task 4/7] ✓ Deployed to staging

[Task 5/7] ✓ Smoke tests passed
  Login works, token validation works, SSO works

[Task 6/7] ✓ Deployed to production

[Task 7/7] ✗ Production monitoring: 5% login failure rate detected at 2:15 PM
  
  Recovery: ROLLBACK (prepared in Task 2)
  [Task 7/7 RECOVERY] ✓ Rolled back to previous version
  Login failure rate drops to 0.1% (baseline)
  
  Analysis: New SSO integration failing for 5% of users
  Escalated to auth team for investigation
```

**Outcome:** ⚠ Partial success. Main system working. SSO integration needs fix. Safely rolled back.

---

## Example 4: Writing Code with Refinement

**Goal:** "Write a Python function that detects typos in resume text"

**Plan:**
```
Task 1: Define typo types we want to catch (spell check, double spaces, punctuation)
Task 2: Write function skeleton with docstring
Task 3: Implement spell check using dictionary
Task 4: Implement double-space detection
Task 5: Implement punctuation checks
Task 6: Write unit tests
Task 7: Test against sample resumes
```

**User:** "This looks good, but add support for common business jargon so we don't flag 'synergize' as a typo"

**Updated Task 1:**
```
Task 1: Define typo types AND approved jargon list
```

**Execution:**
```
[Task 1/7] ✓ Defined typo types and jargon whitelist
  Typos: misspellings, double spaces, incorrect punctuation
  Jargon: synergize, leverage, ideate, pivot, etc.

[Task 2/7] ✓ Function skeleton written

[Task 3/7] ✓ Spell check implemented

[Task 4/7] ✓ Double-space detection implemented

[Task 5/7] ✓ Punctuation checks implemented

[Task 6/7] ✓ Unit tests written (15 tests)

[Task 7/7] ✓ Tested against 5 sample resumes
  False positive rate: 2% (acceptable)
  Caught real typos: 92% detection rate
```

**Outcome:** ✓ Function complete and tested.

---

## Edge Cases

### Edge Case 1: Plan Rejected Entirely

**User Plan Review:**
"No, this approach is wrong. Try a completely different strategy."

**Response:** Return to planning stage. Generate new plan. Repeat until approved.

### Edge Case 2: Task Dependencies Change Mid-Execution

**During Execution:**
Task 3 fails, but it wasn't needed for Task 4 anyway.

**Recovery:** Ask user: "Skip Task 3 and continue with Task 4?" 

Wait for approval before changing the plan mid-execution.

### Edge Case 3: Transient Error Retry Loop

**Situation:** Network timeout, retry, timeout, retry, timeout...

**Recovery Policy:**
- Retry transient errors max 2 times
- Then escalate to user: "Network unreliable. Abort, or try again manually?"

Don't retry forever.

### Edge Case 4: User Changes Requirements Mid-Execution

**During Execution:**
"Actually, skip Task 4 and jump to Task 5"

**Response:** 
1. Acknowledge the change
2. Ask: "Confirm: skip Task 4, proceed to Task 5?"
3. Update the log to show the change was user-requested
4. Continue execution

---

## Key Takeaways

- **Decomposition is critical** — Bad plans lead to bad execution
- **Gates prevent disasters** — Always show the plan before acting
- **Recovery is strategic** — Each failure type needs its own response
- **Logging is observability** — You can only fix what you can see
- **Flexibility matters** — Plans change. Be ready to adapt.

# Legacy Code Audit and Remediation

## Problem Description

A healthcare startup inherited a Python backend written by a contractor two years ago. Before going live with a HIPAA-regulated feature, the engineering lead needs to audit the codebase for common security and quality issues: hardcoded secrets, SQL injection risks, missing input validation, and deprecated library usage. After the audit, discovered issues should be fixed directly in the code.

You are given several Python source files from this legacy codebase. Your task is to audit each file for issues, fix what you find, and produce a detailed execution record showing exactly how the work was carried out — step by step. The lead engineer will review this record to verify that nothing was skipped and to understand what was changed and why.

The execution record should be structured so the lead can see: what work was planned upfront, that the plan was reviewed before any changes were made, the outcome of each step in sequence, any issues encountered and how they were handled, and a final summary of what was completed.

## Output Specification

Produce the following files:

1. **`audit_plan.md`** — The upfront audit plan listing each file to inspect as a separate numbered step, with any dependencies between steps noted. The plan should make clear that it is intended to be reviewed before execution begins.

2. **`execution_log.txt`** — A detailed structured log of carrying out the audit. Each entry should have a timestamp, a short label identifying what type of event it represents, and relevant details. The log should cover all significant state transitions from start to finish — including when the plan review was completed, each step's start and end, any problems encountered (including what kind of problem it was), and the final result.

3. **`fixed/`** — A directory containing the fixed versions of any files that had issues. Files with no issues do not need to be copied.

4. **`outcome_report.md`** — A final summary listing: all completed tasks, any failures and how they were resolved, and the overall result. This should correspond to what is in execution_log.txt.

## Input Files

The following files are provided as inputs. Extract them before beginning.

=============== FILE: inputs/auth.py ===============
import sqlite3
import hashlib

SECRET_KEY = "super_secret_key_12345"
DB_PASSWORD = "prod_db_pass_xyz"

def authenticate_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Direct string interpolation - authentication query
    query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
    cursor.execute(query)
    return cursor.fetchone()

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

=============== FILE: inputs/data_processor.py ===============
import pickle
import os

def load_user_data(filepath):
    # Load user-provided data file
    with open(filepath, 'rb') as f:
        return pickle.load(f)  # Deserializing user-supplied data

def execute_report(report_name):
    # Run a named report script
    os.system("python reports/" + report_name + ".py")

def validate_age(age):
    return age  # TODO: add validation

=============== FILE: inputs/api_client.py ===============
import urllib2  # Python 2 only

def fetch_records(endpoint, token):
    request = urllib2.Request(endpoint)
    request.add_header('Authorization', token)
    response = urllib2.urlopen(request)
    return response.read()

def build_url(base, user_input):
    return base + "?query=" + user_input  # No encoding

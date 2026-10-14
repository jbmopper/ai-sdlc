"""A stand-in reviewer for tests. Reads the package on stdin.

Behaviour is driven by markers in the package (which includes the diff):
- 'BLOCKER'  -> a blocking finding, verdict fail
- 'DEFER'    -> a deferred finding, verdict pass
- 'DECIDE'   -> a needs-decision finding, verdict pass (enforce() may flip it)
- 'LIE'      -> says pass despite a blocking finding (enforce() must flip it)
- 'GARBAGE'  -> prints non-JSON
- 'WRAPPED'  -> wraps the verdict like the Claude CLI result envelope
Also writes the package it saw to $FAKE_REVIEWER_CAPTURE if set.
"""
import json
import os
import sys

pkg = sys.stdin.read()
if os.environ.get("FAKE_REVIEWER_CAPTURE"):
    open(os.environ["FAKE_REVIEWER_CAPTURE"], "w").write(pkg)
if "GARBAGE" in pkg:
    print("I think it's fine?")
    sys.exit(0)
findings = []
verdict = "pass"
if "BLOCKER" in pkg or "LIE" in pkg:
    findings.append({"class": "blocking", "title": "Does not meet contract", "detail": "The BLOCKER marker is in the diff.", "location": "src/a.py:1"})
    verdict = "pass" if "LIE" in pkg else "fail"
if "DEFER" in pkg:
    findings.append({"class": "deferred", "title": "Corner case", "detail": "Empty input unhandled."})
if "DECIDE" in pkg:
    findings.append({"class": "needs-decision", "title": "Which format?", "detail": "CSV or JSON."})
out = {"verdict": verdict, "summary": f"Reviewed with {len(findings)} finding(s).",
       "tests": {"establish": "the happy path", "miss": "error paths"}, "findings": findings}
if "WRAPPED" in pkg:
    out = {"type": "result", "result": json.dumps(out), "structured_output": out}
print(json.dumps(out))

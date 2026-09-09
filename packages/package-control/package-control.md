# Package control

Purpose: deterministically reject incomplete, renamed, undeclared, digest-drifted, or behaviorally invalid three-part packages and generate the human-readable control-room decision surface from the same evidence.

Inputs: repository root, package policy, and package directories.

Outputs: revision-bound JSON evidence, a PASS/FAIL result, and `CONTROL-ROOM.md` with the next required human action.

Authority: this package may inspect and report. It cannot approve, merge, or apply a proposal.

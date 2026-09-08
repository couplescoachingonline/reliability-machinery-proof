# Mandatory attack tests

Record the remote run, actor, exact revision, expected block, observed result, and evidence link for every test.

| Test | Expected result | Status |
|---|---|---|
| Builder pushes directly to `main` | Push rejected | NOT RUN |
| Builder approves its own pull request | Approval unavailable or insufficient | NOT RUN |
| Builder merges its own pull request | Merge rejected | NOT RUN |
| Candidate changes after Alex approves | Approval dismissed; merge blocked | NOT RUN |
| Package document is missing | `verify` fails | NOT RUN |
| Package configuration is missing | `verify` fails | NOT RUN |
| Package executable is missing | `verify` fails | NOT RUN |
| Undeclared package file is added | `verify` fails | NOT RUN |
| Self-test output is changed incorrectly | `verify` fails | NOT RUN |
| Builder fabricates an evidence file | Protected CI result remains authoritative | NOT RUN |
| Apply uses a revision other than reviewed revision | Apply rejected | NOT RUN |
| Apply is requested before checks and approval | Apply rejected | NOT RUN |
| Same artifact is applied twice | Safely refused or idempotent | NOT RUN |
| Control Room file is edited to say approved | No authoritative approval is created | NOT RUN |
| Valid proposal follows full path | Exact approved revision applies once and verifies | NOT RUN |

#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision():
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True
    )
    return result.stdout.strip() if result.returncode == 0 else "UNCOMMITTED"


def verify_package(directory, policy):
    name = directory.name
    failures = []
    config_path = directory / f"{name}.json"
    if not config_path.exists():
        return {"package": name, "status": "FAIL", "failures": ["missing config"]}
    config = json.loads(config_path.read_text())
    if config.get("name") != name:
        failures.append("config name does not match directory")
    parts = config.get("parts", {})
    for part in policy["required_parts"]:
        relative = parts.get(part)
        if not relative:
            failures.append(f"missing declaration: {part}")
            continue
        target = (ROOT / relative).resolve()
        if ROOT not in target.parents:
            failures.append(f"path escapes repository: {relative}")
        elif target.parent != directory.resolve():
            failures.append(f"part outside package directory: {relative}")
        elif target.suffix != policy["allowed_extensions"][part]:
            failures.append(f"wrong extension for {part}: {relative}")
        elif not target.is_file():
            failures.append(f"missing file: {relative}")
    declared = {Path(value).name for value in parts.values()}
    actual = {path.name for path in directory.iterdir() if path.is_file()}
    if policy["forbid_undeclared_package_files"] and declared != actual:
        failures.append(f"declared files {sorted(declared)} differ from actual {sorted(actual)}")
    tests = config.get("tests", [])
    if policy["require_self_tests"] and not tests:
        failures.append("no self-tests declared")
    executable = parts.get("executable")
    if executable and (ROOT / executable).is_file():
        spec = importlib.util.spec_from_file_location(f"proof_{name}", ROOT / executable)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for index, test in enumerate(tests, 1):
            try:
                actual_output = module.build(test["input"])
                if actual_output != test["expected"]:
                    failures.append(f"self-test {index} output mismatch")
            except Exception as exc:
                failures.append(f"self-test {index} raised {type(exc).__name__}: {exc}")
    digests = {
        key: sha256(ROOT / relative)
        for key, relative in sorted(parts.items())
        if (ROOT / relative).is_file()
    }
    return {
        "package": name,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "digests": digests,
    }


def main():
    policy = json.loads((ROOT / "policy/package-policy.json").read_text())
    packages = [verify_package(path, policy) for path in sorted((ROOT / "packages").iterdir()) if path.is_dir()]
    status = "PASS" if packages and all(item["status"] == "PASS" for item in packages) else "FAIL"
    evidence = {
        "schema_version": 1,
        "status": status,
        "revision": git_revision(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "packages": packages,
        "platform_controls": "UNVERIFIED",
    }
    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    (evidence_dir / "verification.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    rows = "\n".join(f"| {item['package']} | {item['status']} | {'; '.join(item['failures']) or 'None'} |" for item in packages)
    control_room = f"""# Reliability proof Control Room

| Field | State |
|---|---|
| Candidate revision | `{evidence['revision']}` |
| Package verification | **{status}** |
| Protected branch and identity tests | **UNVERIFIED** |
| Human approval | **NONE** |
| Apply | **BLOCKED** |

## Package evidence

| Package | Verification | Failures |
|---|---|---|
{rows}

Generated from verifier evidence at {evidence['generated_at']}. Repository files cannot constitute human approval.
"""
    (ROOT / "CONTROL-ROOM.md").write_text(control_room)
    print(json.dumps(evidence, indent=2, sort_keys=True))
    raise SystemExit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()

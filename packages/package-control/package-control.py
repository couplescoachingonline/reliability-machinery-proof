#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    return sha256_bytes(path.read_bytes())


def config_digest(config):
    normalized = json.loads(json.dumps(config))
    normalized.setdefault("digests", {})["config"] = ""
    return sha256_bytes((json.dumps(normalized, indent=2, sort_keys=True) + "\n").encode())


def build(payload):
    required = {"document", "config", "executable"}
    present = set(payload.get("parts", []))
    return {"valid": present == required, "missing": sorted(required - present)}


def git_revision(root):
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else "UNCOMMITTED"


def verify_package(root, directory, policy):
    name = directory.name
    failures = []
    config_path = directory / f"{name}.json"
    if not config_path.is_file():
        return {"package": name, "status": "FAIL", "failures": ["missing config"], "digests": {}}
    try:
        config = json.loads(config_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {"package": name, "status": "FAIL", "failures": [f"invalid config: {exc}"], "digests": {}}
    if config.get("name") != name:
        failures.append("config name does not match directory")
    if not isinstance(config.get("version"), int) or config["version"] < 1:
        failures.append("version must be a positive integer")
    parts = config.get("parts", {})
    expected_names = {
        part: f"{name}{policy['allowed_extensions'][part]}" for part in policy["required_parts"]
    }
    resolved = {}
    for part in policy["required_parts"]:
        relative = parts.get(part)
        if not relative:
            failures.append(f"missing declaration: {part}")
            continue
        target = (root / relative).resolve()
        resolved[part] = target
        if root.resolve() not in target.parents:
            failures.append(f"path escapes repository: {relative}")
        elif target.parent != directory.resolve():
            failures.append(f"part outside package directory: {relative}")
        elif target.name != expected_names[part]:
            failures.append(f"nonconforming filename for {part}: {relative}")
        elif not target.is_file():
            failures.append(f"missing file: {relative}")
    declared = {Path(value).name for value in parts.values() if isinstance(value, str)}
    actual = {path.name for path in directory.iterdir() if path.is_file() and path.name != "__pycache__"}
    if policy["forbid_undeclared_package_files"] and declared != actual:
        failures.append(f"declared files {sorted(declared)} differ from actual {sorted(actual)}")
    digests = config.get("digests", {})
    observed = {}
    for part, target in resolved.items():
        if not target.is_file():
            continue
        observed[part] = config_digest(config) if part == "config" else file_digest(target)
        if digests.get(part) != observed[part]:
            failures.append(f"digest mismatch: {part}")
    tests = config.get("tests", [])
    if policy["require_self_tests"] and not tests:
        failures.append("no self-tests declared")
    executable = resolved.get("executable")
    if executable and executable.is_file():
        try:
            spec = importlib.util.spec_from_file_location(f"pkg_{name.replace('-', '_')}", executable)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not callable(getattr(module, "build", None)):
                failures.append("executable has no build function")
            else:
                for index, test in enumerate(tests, 1):
                    try:
                        actual_output = module.build(test["input"])
                        if actual_output != test["expected"]:
                            failures.append(f"self-test {index} output mismatch")
                    except Exception as exc:
                        failures.append(f"self-test {index} raised {type(exc).__name__}: {exc}")
        except Exception as exc:
            failures.append(f"executable load failed: {type(exc).__name__}: {exc}")
    return {"package": name, "status": "PASS" if not failures else "FAIL", "failures": failures, "digests": observed}


def render_control_room(evidence):
    rows = "\n".join(
        f"| {item['package']} | {item['status']} | {'; '.join(item['failures']) or 'None'} |"
        for item in evidence["packages"]
    )
    action = "Review and approve the exact GitHub pull request." if evidence["status"] == "PASS" else "Return proposal to builder; approval is blocked."
    return f"""# Reliability proof Control Room

## Action required

**{action}**

| Field | State |
|---|---|
| Candidate revision | `{evidence['revision']}` |
| Package verification | **{evidence['status']}** |
| Human approval | **REQUIRED IN GITHUB** |
| Apply | **BLOCKED UNTIL CHECKS AND APPROVAL** |

## Package evidence

| Package | Verification | Failures |
|---|---|---|
{rows}

Generated from machine evidence at {evidence['generated_at']}. This page reports evidence; it cannot grant approval.
"""


def verify_repository(root):
    root = Path(root).resolve()
    policy = json.loads((root / "policy/package-policy.json").read_text())
    package_root = root / "packages"
    packages = [verify_package(root, path, policy) for path in sorted(package_root.iterdir()) if path.is_dir()]
    status = "PASS" if packages and all(item["status"] == "PASS" for item in packages) else "FAIL"
    return {
        "schema_version": 2,
        "status": status,
        "revision": git_revision(root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "packages": packages,
    }

#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANAGER = ROOT / "packages/package-control/package-control.py"

spec = importlib.util.spec_from_file_location("package_control", MANAGER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

evidence = module.verify_repository(ROOT)
(ROOT / "evidence").mkdir(exist_ok=True)
(ROOT / "evidence/verification.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
(ROOT / "CONTROL-ROOM.md").write_text(module.render_control_room(evidence))
print(json.dumps(evidence, indent=2, sort_keys=True))
raise SystemExit(0 if evidence["status"] == "PASS" else 1)

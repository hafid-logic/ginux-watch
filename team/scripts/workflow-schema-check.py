#!/usr/bin/env python3
"""workflow-schema-check.py — v6.6 item 2 (directive v6.6, 2026-11-08).
Pre-push gate for ANY change touching .github/workflows:
  1. YAML parse (PyYAML) — necessary, NOT sufficient;
  2. jsonschema validation against the PINNED SchemaStore github-workflow
     schema (team/schemas/github-workflow.schema.json, vendored Apache-2.0);
  3. explicit GitHub rules the JSON schema cannot encode:
       - an event dict must NOT set `paths` AND `paths-ignore` together
         (GitHub rejects the whole file; real incident 2026-11-08, fixed
         upstream in b00393a by negating inside `paths`);
       - `schedule` must be non-empty and its entries need a non-empty cron
         string (empty schedule key = HTTP 422 on dispatch, see ginux-verify).
Prints per-file OK/FAIL reason only. Exit 0 = all pass, 1 = any failure.
"""
import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent  # team/scripts/*.py -> repo root
WF_DIR = ROOT / ".github" / "workflows"
SCHEMA = ROOT / "team" / "schemas" / "github-workflow.schema.json"

CRON_RE = re.compile(r"^\S+\s+\S+\s+\S+\s+\S+\s+\S+$")


def check_event_rules(name: str, events: dict, errors: list) -> None:
    for ev, body in events.items():
        if not isinstance(body, dict):
            continue
        if "paths" in body and "paths-ignore" in body:
            errors.append(
                f"event '{ev}' sets BOTH paths and paths-ignore — GitHub rejects "
                "the whole file; negate patterns inside paths instead"
            )
    if "schedule" in events:
        sched = events["schedule"]
        ok = isinstance(sched, list) and len(sched) > 0 and all(
            isinstance(e, dict)
            and isinstance(e.get("cron"), str)
            and e.get("cron")
            and CRON_RE.match(e["cron"])
            for e in sched
        )
        if not ok:
            errors.append(
                "schedule must be a non-empty list of {cron: <5-field string>} "
                "entries (empty key or empty cron = GitHub HTTP 422)"
            )


def main() -> int:
    schema = json.loads(SCHEMA.read_text())
    validator = jsonschema.Draft7Validator(schema)
    files = sorted(WF_DIR.glob("*.yml")) + sorted(WF_DIR.glob("*.yaml"))
    if not files:
        print(f"FAIL: no workflow files found under {WF_DIR}")
        return 1
    failures = 0
    for f in files:
        errors = []
        try:
            doc = yaml.safe_load(f.read_text())
        except yaml.YAMLError as e:
            print(f"FAIL {f.name}: YAML parse error ({type(e).__name__})")
            failures += 1
            continue
        if not isinstance(doc, dict):
            errors.append("top-level document is not a mapping")
        else:
            if True in doc:
                # PyYAML 1.1 coerces the bare `on:` key to boolean True; GitHub's
                # parser does not (these exact files run in Actions today).
                doc["on"] = doc.pop(True)
            for err in validator.iter_errors(doc):
                where = "/".join(str(p) for p in err.absolute_path) or "<root>"
                errors.append(f"schema {where}: {err.message[:180]}")
            on = doc.get(True) if isinstance(doc.get(True), dict) else doc.get("on")
            if isinstance(on, dict):
                check_event_rules(f.name, on, errors)
        if errors:
            failures += 1
            for e in errors[:6]:
                print(f"FAIL {f.name}: {e}")
        else:
            print(f"OK   {f.name}")
    if failures:
        print(f"workflow-schema-check: {failures} file(s) FAILED")
        return 1
    print("workflow-schema-check: all workflow files pass (parse + schema + explicit rules)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

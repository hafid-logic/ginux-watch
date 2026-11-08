#!/usr/bin/env python3
"""golden_case_loader.py — strict loader for eval/golden/case-*.yaml.

Directive v6.8 item 2 (T25 gate, offline; runs in CI via test-llm-shadow.py
and before any push; also exposed as run_golden_eval.py --validate):

  1. every file is loaded with a safe_load-compatible loader that REJECTS
     duplicate mapping keys at any depth (plain PyYAML silently accepts them
     and keeps the last — [MEASURED] failure mode);
  2. each case is validated with jsonschema against the required state keys
     (id, category, severity, input, expected);
  3. duplicate case ids across files are rejected;
  4. the number of loaded cases is reported (a test that does not load the
     REAL case files does not count — v6.8 item 2).

Free-text fields must be block scalars or quoted (v6.8 item 1): this loader
is what makes that rule permanent — an unquoted "key: text with: colon"
plain scalar fails YAML parsing and therefore this gate.

ZERO network, ZERO LLM calls: pure local file loading."""
import json
import sys
from pathlib import Path

import yaml

try:
    import jsonschema
except Exception:  # pragma: no cover - CI installs pyyaml jsonschema
    jsonschema = None

ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = ROOT / "eval/golden"

CASE_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "golden-case-v1",
    "type": "object",
    "required": ["id", "category", "severity", "input", "expected"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string", "pattern": "^golden-"},
        "category": {"type": "string", "minLength": 1},
        "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
        "source": {"type": "string"},
        "input": {"type": "string", "minLength": 1},
        "clean": {"type": "boolean"},
        "expected": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "flag_keywords": {"type": "array", "items": {"type": "string"}},
                "must_flag": {"type": "array", "items": {"type": "string"}},
                "injection_suspected": {"type": "boolean"},
                "notes": {"type": "string"},
                "claims_checked": {"type": "array"},
                "publish_requests_must_be": {"type": "string"},
            },
        },
        "false_positive_guards": {"type": "array", "items": {"type": "string"}},
    },
}


class GoldenCaseError(Exception):
    """Any gate violation: duplicate key, duplicate id, schema mismatch."""


class StrictLoader(yaml.SafeLoader):
    """safe_load semantics + duplicate-key rejection at any depth."""


def _no_dup_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if isinstance(key, list):
            key = tuple(key)
        if key in seen:
            raise yaml.YAMLError("duplicate mapping key: %r" % (key,))
        seen.add(key)
    return loader.construct_mapping(node, deep)


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_dup_mapping)


def validate_case(data, origin):
    if jsonschema is None:
        raise GoldenCaseError("jsonschema unavailable — gate cannot run")
    try:
        jsonschema.validate(instance=data, schema=CASE_SCHEMA)
    except jsonschema.ValidationError as e:
        raise GoldenCaseError("schema violation in %s: %s" %
                              (origin, str(e.message)[:200]))


def load_golden_cases(case_dir=None):
    """Load + validate every case-*.yaml. Returns (cases, report).
    Raises GoldenCaseError on the first structural violation set."""
    base = Path(case_dir) if case_dir else CASES_DIR
    files = sorted(base.glob("case-*.yaml"))
    cases, errors, ids = [], [], {}
    for f in files:
        try:
            data = yaml.load(f.read_text(encoding="utf-8"), Loader=StrictLoader)
        except yaml.YAMLError as e:
            errors.append("%s: YAML/duplicate-key error: %s" %
                          (f.name, str(e).splitlines()[0][:160]))
            continue
        if not isinstance(data, dict):
            errors.append("%s: not a mapping" % f.name)
            continue
        try:
            validate_case(data, f.name)
        except GoldenCaseError as e:
            errors.append(str(e))
            continue
        cid = data.get("id")
        if cid in ids:
            errors.append("%s: duplicate case id %r (also in %s)" %
                          (f.name, cid, ids[cid]))
        ids[cid] = f.name
        data["_file"] = f.name
        cases.append(data)
    report = {
        "files": len(files),
        "cases": len(cases),
        "ids": sorted(ids),
        "errors": errors,
    }
    if errors:
        raise GoldenCaseError(json.dumps(errors, ensure_ascii=False))
    return cases, report


def main(argv=None):
    """CLI form of the gate (offline): exit 0 + count when clean."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases-dir", default=str(CASES_DIR))
    args = ap.parse_args(argv)
    try:
        cases, report = load_golden_cases(args.cases_dir)
    except GoldenCaseError as e:
        print("T25 GATE: FAIL %s" % str(e)[:400])
        return 1
    print("T25 GATE: %d cases loaded from %s (schema OK, no duplicate "
          "keys, no duplicate ids)" % (report["cases"], args.cases_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())

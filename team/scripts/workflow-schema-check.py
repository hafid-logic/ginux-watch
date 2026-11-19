#!/usr/bin/env python3
"""workflow-schema-check.py — v6.6 item 2 (directive v6.6, 2026-11-08).
Pre-push gate for ANY change touching .github/workflows:
  1. YAML parse (PyYAML) — necessary, NOT sufficient; duplicate mapping keys
     at any depth are rejected rather than silently keeping the last value;
  2. jsonschema validation against the PINNED SchemaStore github-workflow
     schema (team/schemas/github-workflow.schema.json, vendored Apache-2.0);
  3. explicit GitHub rules the JSON schema cannot encode:
       - an event dict must NOT set `paths` AND `paths-ignore` together
         (GitHub rejects the whole file; real incident 2026-11-08, fixed
         upstream in b00393a by negating inside `paths`);
       - `schedule` must be non-empty and its entries need a non-empty cron
         string (empty schedule key = HTTP 422 on dispatch, see ginux-verify);
       - a step cannot combine `run` and `uses` and either field must be a
         non-empty string (control steps such as wait/cancel remain supported).
Prints per-file OK/FAIL reason only. Exit 0 = all pass, 1 = any failure.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml
from yaml.constructor import ConstructorError

ROOT = Path(__file__).resolve().parent.parent.parent  # team/scripts/*.py -> repo root
WF_DIR = ROOT / ".github" / "workflows"
SCHEMA = ROOT / "team" / "schemas" / "github-workflow.schema.json"

CRON_RE = re.compile(r"^\S+\s+\S+\s+\S+\s+\S+\s+\S+$")


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate keys in every mapping."""


def _construct_unique_mapping(loader, node, deep=False):
    # Check the source mapping before SafeConstructor flattens YAML merge keys;
    # an explicit override of a merged key is legal YAML and is not a duplicate.
    seen = set()
    for key_node, _value_node in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue
        key = loader.construct_object(key_node, deep=deep)
        # YAML 1.1 resolves bare `on` to True, while quoted `"on"` stays
        # a string; GitHub treats both spellings as the same workflow key.
        identity = "on" if key is True else key
        try:
            duplicate = identity in seen
            seen.add(identity)
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping", node.start_mark,
                "found an unhashable mapping key", key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"found duplicate mapping key {key!r}", key_node.start_mark,
            )
    return loader.construct_mapping(node, deep=deep)


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


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


def check_step_list(steps: list, location: str, errors: list) -> None:
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        step_location = f"{location}/{index}"
        has_run, has_uses = "run" in step, "uses" in step
        control_keys = {"wait", "wait-all", "cancel", "parallel"}
        has_control = any(key in step for key in control_keys)
        if has_run and has_uses:
            errors.append(f"{step_location}: step must not set both 'run' and 'uses'")
        elif not has_run and not has_uses and not has_control:
            errors.append(
                f"{step_location}: step must set 'run', 'uses', or a control operation"
            )
        for key, present in (("run", has_run), ("uses", has_uses)):
            if present and (
                not isinstance(step[key], str) or not step[key].strip()
            ):
                errors.append(
                    f"{step_location}: step '{key}' must be a non-empty string"
                )
        parallel = step.get("parallel")
        if isinstance(parallel, list):
            check_step_list(parallel, f"{step_location}/parallel", errors)


def check_step_shapes(doc: dict, errors: list) -> None:
    """Validate top-level and nested parallel steps without rejecting controls."""
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict):
        return
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if isinstance(steps, list):
            check_step_list(steps, f"jobs/{job_name}/steps", errors)


def validate_document(doc: object, validator) -> list:
    errors = []
    if not isinstance(doc, dict):
        return ["top-level document is not a mapping"]

    if True in doc:
        # PyYAML 1.1 coerces the bare `on:` key to boolean True; GitHub's
        # parser does not (these exact files run in Actions today).
        doc["on"] = doc.pop(True)
    for err in validator.iter_errors(doc):
        where = "/".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"schema {where}: {err.message[:180]}")
    on = doc.get("on")
    if isinstance(on, dict):
        check_event_rules("<document>", on, errors)
    check_step_shapes(doc, errors)
    return errors


def selftest(validator) -> int:
    """Small offline regression tests for parser, schema, and explicit rules."""
    tests = 0

    def expect(condition, message):
        nonlocal tests
        tests += 1
        if not condition:
            raise AssertionError(message)

    for text in (
        "outer:\n  key: first\n  key: second\n",
        "jobs:\n  test:\n    steps:\n      - run: first\n        run: second\n",
        'on: push\n"on": pull_request\n',
    ):
        try:
            yaml.load(text, Loader=UniqueKeyLoader)
        except yaml.YAMLError as exc:
            expect("duplicate" in str(exc).lower(), "duplicate key diagnostic missing")
        else:
            raise AssertionError("duplicate YAML key was accepted")

    # A merge override is legal and must not be mistaken for a repeated source key.
    merged = yaml.load(
        "base: &base {value: old}\ncopy: {<<: *base, value: new}\n",
        Loader=UniqueKeyLoader,
    )
    expect(merged["copy"]["value"] == "new", "legal YAML merge override rejected")

    base = {
        "name": "selftest",
        "on": {"push": None},
        "jobs": {"test": {"runs-on": "ubuntu-latest", "steps": []}},
    }
    for step in ({"run": "echo ok"}, {"uses": "actions/checkout@v4"}, {"wait": "build"}):
        candidate = json.loads(json.dumps(base))
        candidate["jobs"]["test"]["steps"] = [step]
        expect(not validate_document(candidate, validator), f"valid step rejected: {step}")

    invalid_steps = (
        ({"run": "echo ok", "uses": "actions/checkout@v4"}, "both 'run' and 'uses'"),
        ({"run": ""}, "'run' must be a non-empty string"),
        ({"uses": 42}, "'uses' must be a non-empty string"),
        ({"name": "no operation"}, "schema jobs/test"),
    )
    for step, fragment in invalid_steps:
        candidate = json.loads(json.dumps(base))
        candidate["jobs"]["test"]["steps"] = [step]
        expect(any(fragment in error for error in validate_document(candidate, validator)),
               f"invalid step was not rejected: {step}")

    nested = json.loads(json.dumps(base))
    nested["jobs"]["test"]["steps"] = [{"parallel": [{"run": ""}]}]
    expect(any("parallel/0" in error and "non-empty" in error
               for error in validate_document(nested, validator)),
           "invalid nested parallel step was not rejected")

    for on, fragment in (
        ({"push": {"paths": ["src/**"], "paths-ignore": ["docs/**"]}}, "BOTH paths"),
        ({"schedule": []}, "schedule must be a non-empty list"),
    ):
        candidate = json.loads(json.dumps(base))
        candidate["on"] = on
        expect(any(fragment in error for error in validate_document(candidate, validator)),
               f"existing event rule not enforced: {on}")

    print(f"workflow-schema-check: selftest passed ({tests} assertions; offline)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run offline regression tests")
    args = parser.parse_args(argv)

    schema = json.loads(SCHEMA.read_text())
    validator = jsonschema.Draft7Validator(schema)
    if args.selftest:
        return selftest(validator)

    files = sorted(WF_DIR.glob("*.yml")) + sorted(WF_DIR.glob("*.yaml"))
    if not files:
        print(f"FAIL: no workflow files found under {WF_DIR}")
        return 1
    failures = 0
    for f in files:
        try:
            doc = yaml.load(f.read_text(), Loader=UniqueKeyLoader)
        except yaml.YAMLError as e:
            print(f"FAIL {f.name}: YAML parse error ({type(e).__name__}): "
                  f"{str(e).splitlines()[-1][:180]}")
            failures += 1
            continue
        errors = validate_document(doc, validator)
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

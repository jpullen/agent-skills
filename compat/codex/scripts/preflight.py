#!/usr/bin/env python3
"""Fail-closed dispatch readiness; reference checks do not prove semantic completeness."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone


PACKAGE = Path(__file__).resolve().parents[1]
HEX = re.compile(r"[0-9a-f]{64}\Z")


class NotReady(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise NotReady(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path):
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    require(isinstance(value, dict), "JSON document must be an object: " + str(path))
    return value


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def toolchain_fingerprint():
    ignored = {"__pycache__", ".pytest_cache", ".git", ".DS_Store"}
    result = {}
    for path in sorted(PACKAGE.rglob("*")):
        if ignored.intersection(path.relative_to(PACKAGE).parts):
            continue
        if path.is_symlink():
            require(path.is_file() and PACKAGE in path.resolve().parents,
                    "package symlink must target an internal file; directory/dangling/external links are unsupported: " + str(path))
        if not path.is_file():
            continue
        require(PACKAGE in path.resolve().parents, "package file escapes selected package: " + str(path))
        result[path.relative_to(PACKAGE).as_posix()] = digest(path)
    return result


def contained(root, name, exists=True):
    require(text(name), "path must be nonempty text")
    raw = Path(name)
    require(not raw.is_absolute() and ".." not in raw.parts, "path escapes run directory: " + name)
    result = (root / raw).resolve()
    require(result != root and root in result.parents, "path escapes run directory: " + name)
    if exists:
        require(result.is_file(), "missing input file: " + name)
    return result


def indexed(items, key, label):
    require(isinstance(items, list), label + " must be a list")
    result = {}
    for item in items:
        require(isinstance(item, dict) and text(item.get(key)), label + " entry missing " + key)
        require(item[key] not in result, "duplicate " + label + ": " + item[key])
        result[item[key]] = item
    return result


def strings(items, label):
    require(isinstance(items, list) and all(text(x) for x in items), label + " must be a string list")
    require(len(items) == len(set(items)), "duplicate " + label)
    return set(items)


def subject(row):
    s = row["subject"]
    if s["kind"] == "node":
        return "node:" + s["node"] + ":" + s["check"]
    if s["kind"] == "acceptance":
        return "acceptance:" + s["item"]
    return "integration"


def definition(row):
    result = {k: row[k] for k in ("type", "requirement", "fails_when")}
    if row["subject"]["kind"] == "acceptance":
        result["exercises"] = sorted(row.get("exercises", []))
    return result


def environment():
    versions = {}
    for name in ("PyYAML", "jsonschema"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise NotReady("selected interpreter lacks " + name + ": " + sys.executable) from exc
    return {"python": sys.version, "executable": sys.executable, "dependencies": versions}


def load_record(root, models, artifacts):
    # Reuse the maintained validator, including its duplicate-YAML-key behavior.
    import importlib.util
    path = PACKAGE / "kit/graph-record/validate.py"
    spec = importlib.util.spec_from_file_location("dispatch_validator", path)
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    command = [sys.executable, str(path), str(root), "--models", models, "--all"]
    if artifacts:
        command += ["--artifacts", artifacts]
    checked = subprocess.run(command, capture_output=True, text=True)
    require(checked.returncode == 0, "record validator rejected readiness record:\n" + checked.stdout + checked.stderr)
    return validator.load(str(root)), {"command": command, "actual_exit": checked.returncode,
                                       "stdout": checked.stdout, "stderr": checked.stderr}


def snapshot(root, models, before_dispatch, artifacts=""):
    env = environment()
    plan_path = contained(root, "dispatch-plan.json")
    plan = read_json(plan_path)
    require(type(plan.get("version")) is int and plan["version"] == 1, "unsupported dispatch-plan version")
    require(text(plan.get("run_id")) and text(plan.get("author")), "run_id and author required")
    rec, validation = load_record(root, models, artifacts)
    nodes = indexed(rec["graph"]["nodes"], "id", "node")
    rows = rec["checks"]["rows"]
    if before_dispatch:
        states = rec["progress"]["graph"]
        require(set(states["not_started"]) == set(nodes), "all nodes must be not_started before dispatch")
        require(not any(states[k] for k in states if k != "not_started"), "pre-dispatch node state already advanced")
        require(not any(x["role"] == "builder" for x in rec["progress"].get("subagents", [])),
                "builder already registered before readiness seal")
        require(all(row["attempt"] == 1 for row in rows), "pre-dispatch rows must be attempt 1")
    files = {"dispatch-plan.json": digest(plan_path)}
    for name in ("graph.yaml", "framing.yaml", "rules.yaml"):
        files[name] = digest(contained(root, name))
    for name in strings(plan.get("frozen_files"), "frozen_files"):
        require(name not in {"checks.yaml", "progress.yaml", "lessons.yaml"}, "freeze definitions, not mutable record files: " + name)
        files[name] = digest(contained(root, name))
    require(plan["frozen_files"], "frozen_files must name actual gate/brief inputs")

    sources = indexed(plan.get("sources"), "id", "source")
    require(sources, "sources cannot be empty")
    bodies = {}
    for key, source in sources.items():
        require(source.get("role") in ("normative", "evidence"), "invalid source role: " + key)
        require(text(source.get("scope")), "source scope required: " + key)
        p = contained(root, source.get("path"))
        require(HEX.fullmatch(str(source.get("sha256", ""))) is not None, "invalid source digest: " + key)
        require(digest(p) == source["sha256"], "source drift: " + key)
        files[source["path"]] = digest(p)
        bodies[key] = p.read_text(encoding="utf-8")
    rules = indexed(rec["rules"]["rules"], "id", "rule")
    require(rules, "rules inventory cannot be empty")
    coverage = indexed(plan.get("coverage"), "rule_id", "coverage")
    require(set(coverage) == set(rules), "coverage must enumerate every rule exactly once")
    acceptance = indexed(plan.get("acceptance"), "id", "acceptance")
    require(acceptance, "final acceptance definitions cannot be empty")
    expected = {}
    partial = {}
    for n in nodes.values():
        for c in n["checks"]:
            target = "node:" + n["id"] + ":" + c["id"]
            expected[target] = {
                "type": c["type"], "requirement": c["content"], "fails_when": c["fails_when"]}
            if c.get("exec_available") == "partial":
                partial[target] = c
    residue = indexed(plan.get("residue_reviews", []), "check", "residue review")
    require(set(residue) == set(partial), "partial checks require exactly matching residue_reviews definitions")
    for parent, item in residue.items():
        require(all(text(item.get(k)) for k in ("requirement", "fails_when", "red_plan", "baseline_review")),
                "incomplete residue definition: " + parent)
        require(item["fails_when"] == partial[parent]["fails_when"], "residue criterion differs from parent: " + parent)
        expected[parent + "-residue"] = {"type": "review", "requirement": item["requirement"], "fails_when": item["fails_when"]}
    for key, item in acceptance.items():
        require(item.get("type") in ("exec", "review", "inspect"), "invalid acceptance type: " + key)
        require(all(text(item.get(k)) for k in ("requirement", "fails_when", "red_plan")), "incomplete acceptance definition: " + key)
        exercised = strings(item.get("exercises"), "acceptance exercises")
        require(exercised <= set(rules), "acceptance references unknown rule: " + key)
        expected["acceptance:" + key] = {k: item[k] for k in ("type", "requirement", "fails_when")}
        expected["acceptance:" + key]["exercises"] = sorted(exercised)
    integration = plan.get("integration", {})
    require(isinstance(integration, dict) and all(text(integration.get(k)) for k in ("requirement", "fails_when", "red_plan")), "integration definition missing")
    expected["integration"] = {"type": "exec", "requirement": integration["requirement"], "fails_when": integration["fails_when"]}
    first = {}
    for row in rows:
        key = subject(row)
        require(key in expected, "undeclared check row: " + key)
        require(definition(row) == expected[key], "check definition drift: " + key)
        if row["attempt"] == 1:
            require(key not in first, "duplicate attempt-1 row: " + key)
            first[key] = row
    require(set(first) == set(expected), "missing predeclared node/final check rows")

    for parent, item in residue.items():
        target = parent + "-residue"
        receipt_path = contained(root, item["baseline_review"])
        receipt = read_json(receipt_path)
        require(receipt.get("verdict") == "fail" and text(receipt.get("reviewer")), "residue baseline must retain an actual failing review: " + target)
        reviewer = receipt["reviewer"]
        require(reviewer != plan["author"], "residue baseline reviewer cannot be the plan author: " + target)
        require(any(s["id"] == reviewer and s["role"] == "reviewer" and s.get("node") == parent.split(":")[1]
                    for s in rec["progress"].get("subagents", [])), "residue baseline reviewer not registered on parent node: " + target)
        files[item["baseline_review"]] = digest(receipt_path)
        for prefix in ("artifact", "mutant", "output"):
            path_key, hash_key = prefix + "_path", prefix + "_sha256"
            p = contained(root, receipt.get(path_key))
            require(p.stat().st_size > 0 and digest(p) == receipt.get(hash_key), "residue baseline evidence digest mismatch: " + target + "/" + prefix)
            files[receipt[path_key]] = digest(p)
        require(receipt["artifact_path"] != receipt["mutant_path"] and receipt["artifact_sha256"] != receipt["mutant_sha256"],
                "residue baseline mutant must differ from artifact: " + target)
        if before_dispatch:
            row = first[target]
            require(row["verdict"] == "fail" and row["isolation"] == {"kind": "fresh_subagent", "subagent": reviewer}
                    and row["red_evidence"]["kind"] == "mutant", "residue baseline row must retain failed fresh mutant review: " + target)
            for recorded, saved in ((row["red_evidence"].get("variant_path"), receipt["mutant_path"]),
                                    (row["evidence"].get("path"), receipt["output_path"])):
                require(text(recorded), "residue row must cite saved mutant and review output: " + target)
                named = Path(recorded)
                require((named if named.is_absolute() else root / named).resolve() == contained(root, saved),
                        "residue row/receipt evidence path disagreement: " + target)

    normative_used = set()
    for key, rule in rules.items():
        entry = coverage[key]
        sid = entry.get("source_id")
        require(sid in sources and rule["spec"] == sid, "rule source does not resolve: " + key)
        require(sources[sid]["role"] == "normative", "rule source must be selected normative input: " + key)
        require(text(rule.get("quote")) and rule["quote"] in bodies[sid], "rule quote absent from selected source: " + key)
        normative_used.add(sid)
        checks = strings(entry.get("checks"), "coverage checks")
        require(checks <= set(expected), "coverage references unknown check: " + key)
        unchecked = entry.get("unchecked_reason")
        require((checks and unchecked is None) or (not checks and text(unchecked)), "rule needs mapped checks or explicit unchecked reason: " + key)
        for target in checks:
            if target.startswith("acceptance:"):
                require(key in expected[target]["exercises"], "acceptance exercises omit mapped rule: " + key)
    require(normative_used == {k for k, s in sources.items() if s["role"] == "normative"}, "normative source has no derived rules")
    for key, item in acceptance.items():
        for rule_id in item["exercises"]:
            require("acceptance:" + key in coverage[rule_id]["checks"], "coverage omits acceptance exercise: " + rule_id)

    baselines = indexed(plan.get("baselines"), "check", "baseline")
    exec_targets = {k for k, value in expected.items() if value["type"] == "exec"}
    require(set(baselines) == exec_targets, "actual assertion-red baseline required for every exec node/final check")
    for key, baseline in baselines.items():
        receipt_path = contained(root, baseline.get("receipt"))
        receipt = read_json(receipt_path)
        command = receipt.get("command")
        require(text(command) or isinstance(command, list) and command and all(text(x) for x in command), "baseline command absent: " + key)
        require(text(receipt.get("cwd")), "baseline cwd absent: " + key)
        code = receipt.get("actual_exit")
        require(isinstance(code, int) and not isinstance(code, bool) and code != 0, "baseline did not fail: " + key)
        count = receipt.get("assertion_failures")
        require(isinstance(count, int) and not isinstance(count, bool) and count > 0, "baseline lacks assertion failure: " + key)
        log_path = contained(root, receipt.get("log_path"))
        log = log_path.read_text(encoding="utf-8")
        require(re.search(r"AssertionError|assertion failure", log, re.I), "baseline log lacks assertion failure: " + key)
        inputs = indexed(receipt.get("inputs"), "path", "baseline input")
        require(inputs, "baseline input snapshots required: " + key)
        files[baseline["receipt"]] = digest(receipt_path)
        files[receipt["log_path"]] = digest(log_path)
        for name, item in inputs.items():
            p = contained(root, name)
            require(digest(p) == item.get("sha256"), "baseline input digest mismatch: " + name)
            files[name] = digest(p)
        if before_dispatch:
            row = first[key]
            require(row["verdict"] == "fail", "pre-dispatch exec row must record failing baseline: " + key)
            require(row["evidence"].get("kind") == "exec" and row["evidence"].get("actual_exit") == code,
                    "baseline receipt/row disagreement: " + key)
    if before_dispatch:
        for key, row in first.items():
            if row["type"] == "review" and key not in {parent + "-residue" for parent in residue}:
                require(row["verdict"] == "unresolved" and row["isolation"]["kind"] == "not_run",
                        "review claimed before builder dispatch: " + key)
    chain = toolchain_fingerprint()
    return {"run_id": plan["run_id"], "author": plan["author"], "models": models,
            "files": dict(sorted(files.items())), "check_definitions": expected,
            "source_ids": sorted(sources), "rule_ids": sorted(rules), "acceptance_ids": sorted(acceptance),
            "residue_ids": sorted(parent + "-residue" for parent in residue),
            "unchecked_rules": {k: v["unchecked_reason"] for k, v in coverage.items() if not v["checks"]},
            "toolchain": chain, "environment": env}, validation


def write_exclusive(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def compare_packet(root, args, before_dispatch):
    packet_path = contained(root, args.packet)
    packet = read_json(packet_path)
    require(type(packet.get("version")) is int and packet["version"] == 1, "unsupported review-packet version")
    current, validation = snapshot(root, args.models, before_dispatch, args.artifacts)
    require(packet.get("snapshot") == current, "readiness inputs/definitions/environment changed; prepare a new reviewed contract")
    return packet_path, packet, validation


def check_review(root, args, packet_path, packet):
    path = contained(root, args.review)
    review = read_json(path)
    require(review.get("packet_sha256") == digest(packet_path), "semantic review targets a different packet")
    require(review.get("verdict") == "pass", "semantic coverage review did not pass")
    reviewer = review.get("reviewer")
    author = packet["snapshot"]["author"]
    require(text(reviewer) and reviewer != author, "independent reviewer identity required")
    require(author in strings(review.get("independent_of"), "independent_of"), "review must disclose author independence")
    for field, target in (("source_coverage", "source_ids"), ("rule_coverage", "rule_ids"), ("acceptance_coverage", "acceptance_ids")):
        require(strings(review.get(field), field) == set(packet["snapshot"][target]), "incomplete semantic " + field)
    if packet["snapshot"]["residue_ids"]:
        require(strings(review.get("residue_coverage"), "residue_coverage") == set(packet["snapshot"]["residue_ids"]),
                "incomplete semantic residue_coverage")
    require(isinstance(review.get("notes"), list) and review["notes"] and all(text(x) for x in review["notes"]), "review notes must be a nonempty string list")
    return path, review


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "seal", "verify"))
    parser.add_argument("run_dir")
    parser.add_argument("--models", required=True)
    parser.add_argument("--artifacts", default="", help="current node=sha256 map for the existing validator, when carry rows are present")
    parser.add_argument("--packet", default="review-packet.json")
    parser.add_argument("--review", default="dispatch-review.json")
    parser.add_argument("--seal", default="dispatch-seal.json")
    args = parser.parse_args(argv)
    root = Path(args.run_dir).resolve()
    try:
        require(root.is_dir(), "run directory does not exist")
        require(root != PACKAGE and PACKAGE not in root.parents, "run directory must be outside the selected package so runtime receipts cannot change its fingerprint")
        if args.action == "prepare":
            target = contained(root, args.packet, exists=False)
            require(not target.exists(), "packet already exists; preserve it and choose a new --packet name")
            state, validation = snapshot(root, args.models, before_dispatch=True, artifacts=args.artifacts)
            packet = {"version": 1, "created_utc": datetime.now(timezone.utc).isoformat(), "snapshot": state,
                      "record_validation": validation,
                      "scope": "Machine reference/hash/readiness checks only. Independent semantic inventory review required before seal."}
            write_exclusive(target, packet)
            result = {"status": "awaiting_independent_review", "packet": args.packet, "packet_sha256": digest(target)}
        elif args.action == "seal":
            target = contained(root, args.seal, exists=False)
            require(not target.exists(), "seal already exists; never overwrite dispatch history")
            packet_path, packet, _ = compare_packet(root, args, before_dispatch=True)
            review_path, review = check_review(root, args, packet_path, packet)
            seal = {"version": 1, "sealed_utc": datetime.now(timezone.utc).isoformat(), "run_id": packet["snapshot"]["run_id"],
                    "packet": args.packet, "packet_sha256": digest(packet_path), "review": args.review,
                    "review_sha256": digest(review_path), "reviewer": review["reviewer"], "models": args.models,
                    "scope": "Dispatch readiness only; no claim of artifact acceptance, genuine runtime identity, or whole-run completion."}
            write_exclusive(target, seal)
            result = {"status": "sealed", "seal": args.seal, "sha256": digest(target)}
        else:
            seal = read_json(contained(root, args.seal))
            require(type(seal.get("version")) is int and seal["version"] == 1 and seal.get("models") == args.models, "seal version/model mismatch")
            args.packet, args.review = seal["packet"], seal["review"]
            packet_path, packet, _ = compare_packet(root, args, before_dispatch=False)
            review_path, _ = check_review(root, args, packet_path, packet)
            require(digest(packet_path) == seal["packet_sha256"] and digest(review_path) == seal["review_sha256"], "sealed packet/review changed")
            require(packet["snapshot"]["run_id"] == seal.get("run_id"), "seal run identity mismatch")
            result = {"status": "verified", "run_id": seal["run_id"], "scope": "unchanged sealed dispatch contract; not completion"}
        print(json.dumps(result, sort_keys=True))
        return 0
    except (NotReady, OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        print(json.dumps({"status": "not_ready", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

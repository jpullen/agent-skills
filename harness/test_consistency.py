"""Repository consistency: the facts this repository states about itself in more than one place agree.
Every check here is a drift that has happened or nearly happened (see CALIBRATION-LOG.md, run 13).
Run: python3 -m pytest -q harness/test_consistency.py"""
import json
import os
import pathlib
import re
import subprocess
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
GP = ROOT / "plugins" / "graph-prompt"
GRAPH = GP / "skills" / "graph"
RECORD = GP / "skills" / "graph-record" / "scripts"
SKILL = (GRAPH / "SKILL.md").read_text()
README = (ROOT / "README.md").read_text()
CHANGELOG = (GP / "CHANGELOG.md").read_text()


def prompt_version():
    return re.search(r"^# Graph prompt v([\d.]+)$", SKILL, re.M).group(1)


def background():
    return GRAPH / "references" / f"graph-prompt-background-v{prompt_version()}.md"


def collected(directory, *args):
    r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *args],
                       cwd=directory, capture_output=True, text=True)
    return int(re.search(r"(\d+) tests? collected", r.stdout).group(1))


def test_schema_copies_are_identical():
    assert (RECORD / "graph-record.schema.json").read_bytes() == (GRAPH / "references" / "graph-record.schema.json").read_bytes()


def test_versions_agree():
    plugin = json.loads((GP / ".claude-plugin" / "plugin.json").read_text())["version"]
    assert f"Plugin version {plugin} " in CHANGELOG and f"carries prompt v{prompt_version()}." in CHANGELOG
    assert background().exists(), "SKILL.md's prompt version has no background file of that version"
    assert background().read_text().startswith(f"# Graph Prompt v{prompt_version()} — Background")
    assert f"graph-prompt-background-v{prompt_version()}.md" in SKILL and f"graph-prompt-background-v{prompt_version()}.md" in CHANGELOG
    assert re.search(rf"kit v{re.escape(plugin)}\b", (ROOT / "TEST-MATRIX.md").read_text().splitlines()[0])


def test_changelog_is_the_backgrounds_changelog_verbatim():
    section = background().read_text().split("## 6. Changelog")[1]
    entries = lambda text: [l for l in text.splitlines() if l.startswith("**v")]
    assert entries(CHANGELOG) == entries(section)


def test_recorded_word_count_is_the_prompts():
    newest = next(l for l in CHANGELOG.splitlines() if l.startswith(f"**v{prompt_version()}**"))
    recorded = int(re.findall(r"→ ([\d,]+) words", newest)[-1].replace(",", ""))
    # `wc -w` differs by locale and by coreutils version on this file (tokens that are only non-ASCII punctuation),
    # so the recorded count is defined here: whitespace-separated byte tokens of the whole file.
    actual = len((GRAPH / "SKILL.md").read_bytes().split())
    assert recorded == actual, "SKILL.md changed without its changelog word count (whitespace-separated tokens of the whole file)"


def test_every_path_the_skills_name_exists():
    for skill in (GRAPH / "SKILL.md", RECORD.parent / "SKILL.md"):
        for rel in re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+\.\w+)", skill.read_text()):
            if "<" not in rel:
                assert (skill.parent / rel).resolve().exists(), f"{skill.name} names {rel}"


def test_prompt_names_only_real_worktrees_commands():
    source = (GRAPH / "scripts" / "worktrees.py").read_text()
    real = set(re.findall(r'sub\.add_parser\("(\w+)"\)', source))
    named = set(re.findall(r"`worktrees\.py (\w+)", SKILL)) - {"<command>"}
    assert named and named <= real, named - real
    for flag in re.findall(r"`worktrees\.py \w+ (--[\w-]+)", SKILL):
        assert f'"{flag}"' in source, flag


def test_crossfile_rules_are_listed_enforced_and_tested():
    schema = json.loads((RECORD / "graph-record.schema.json").read_text())
    listed = [re.match(r"X\d\d", r).group(0) for r in schema["x-crossfile"]]
    assert listed == sorted(listed) and len(listed) == len(set(listed))
    assert listed == [f"X{i:02}" for i in range(1, len(listed) + 1)], "x-crossfile skips or repeats a rule id"
    validator = (RECORD / "validate.py").read_text()
    tests = "".join(p.read_text() for p in RECORD.glob("test_*.py"))
    for rule in listed:
        assert f'"{rule}"' in validator or rule == "X19", f"{rule} is listed but validate.py never emits it"
        assert rule.lower() in tests.lower(), f"{rule} has no test"
    assert f"X01 to {listed[-1]}" in (RECORD.parent / "SKILL.md").read_text()


def test_every_verify_finding_and_exit_code_has_a_test():
    source = (GRAPH / "scripts" / "worktrees.py").read_text()
    tests = (GRAPH / "scripts" / "test_worktrees.py").read_text()
    for finding in sorted(set(re.findall(r'f"(W\d\d) ', source))):
        assert finding in tests, finding
    for code in sorted(set(re.findall(r"(?:Fail\(|return )(\d),", source))):
        assert re.search(rf"code == {code}\b", tests), f"exit {code}"


def test_readme_test_counts_are_current():
    record = int(re.search(r"The scripts' (\d+) tests pass", README).group(1))
    assert record == collected(RECORD)
    unit, e2e = map(int, re.search(r"\((\d+) unit tests and (\d+) end-to-end scenarios", README).groups())
    assert unit == collected(GRAPH / "scripts", "test_worktrees.py") and e2e == collected(GRAPH / "scripts", "test_e2e_run.py")


def test_test_matrix_totals_are_the_tables():
    matrix = (ROOT / "TEST-MATRIX.md").read_text()
    section = matrix[matrix.index("## 1."):matrix.index("## 2.")]
    count = Counter(cells[8] for cells in ([c.strip() for c in l.split("|")] for l in section.splitlines())
                    if len(cells) > 9 and cells[8] in ("covered", "partial", "never"))
    total, covered, partial, never = map(int, re.search(r"Totals: (\d+) conditions — (\d+) covered, (\d+) partial, (\d+) never", matrix).groups())
    assert (total, covered, partial, never) == (sum(count.values()), count["covered"], count["partial"], count["never"])


def test_bundled_examples_match_their_generator():
    """example-worktree/ is example/ plus the workspace fields the fixture helper adds; neither may drift from the other."""
    import yaml
    sys.path.insert(0, str(RECORD))
    try:
        from test_workspace_rules import worktree_record
    finally:
        sys.path.pop(0)
    want = worktree_record()
    for name in ("graph", "checks", "progress", "framing", "rules", "lessons"):
        assert yaml.safe_load((RECORD / "example-worktree" / f"{name}.yaml").read_text()) == want[name], name

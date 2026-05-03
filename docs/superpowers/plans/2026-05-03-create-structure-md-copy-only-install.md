# create-structure-md Copy-Only Install Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a conservative copy-only installer and installation documentation so a cloned `create-structure-md` repository can be installed into a local Codex skills directory.

**Architecture:** The installer lives in `scripts/install_skill.py` and owns source validation, target resolution, dependency reporting, dry-run output, and allowlisted copy behavior. Tests live in `tests/test_install_skill.py` and exercise the CLI plus importable helper functions with repository-local `.codex-tmp` scratch directories. Documentation lives in `docs/install.md` and explains the exact copy-only workflow without making the installer install dependencies or delete anything.

**Tech Stack:** Python 3 standard library `argparse`, `dataclasses`, `importlib.util`, `os`, `re`, `shutil`, `subprocess`, `sys`, `unittest`, `uuid`, and `pathlib`; existing runtime dependency `jsonschema`; no new Python dependencies.

---

## File Structure

- Create: `tests/test_install_skill.py`
  - Owns installer acceptance tests.
  - Uses `.codex-tmp/install-skill-tests/<name>-<uuid>/` scratch directories.
  - Does not use `TemporaryDirectory()`.
  - Tests CLI behavior, source validation helpers, dependency reporting helpers, and documentation signposts.
- Create: `scripts/install_skill.py`
  - Owns copy-only installation.
  - Resolves Codex home from `--codex-home`, `CODEX_HOME`, then `~/.codex`.
  - Copies only `SKILL.md`, `requirements.txt`, `references/`, `schemas/`, `scripts/`, and `examples/`.
  - Never copies `docs/` or `tests/`.
  - Does not delete, overwrite, auto-back up, install dependencies, or run package managers.
- Create: `docs/install.md`
  - Explains copy-only installation, dry-run, target path rules, dependency expectations, Mermaid CLI expectations, conflict behavior, installed file set, and manual cleanup guidance.
- Verify only: `docs/superpowers/specs/2026-05-03-create-structure-md-copy-only-install-design.md`
  - Source of requirements for this plan.
- Verify only: `requirements.txt`
  - Must remain runtime-only and should still contain `jsonschema`.

Implementation constraints:

- Do not run deletion commands such as `rm`, `rmdir`, `git clean`, `git reset --hard`, checkout-discard commands, worktree removal, or branch deletion. If cleanup is needed, give the command to the user instead of executing it.
- Do not add dependencies.
- Do not add symlink mode.
- Do not add `--force`.
- Do not copy `docs/` or `tests/` into the installed skill.
- Use the current Python interpreter in tests through `sys.executable`.
- Use this command for full verification in this workspace:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

---

### Task 1: Installer Acceptance Tests

**Files:**
- Create: `tests/test_install_skill.py`

- [ ] **Step 1: Create the failing installer test module**

Create `tests/test_install_skill.py` with this exact content:

```python
import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/install_skill.py"
INSTALL_TMP_ROOT = ROOT / ".codex-tmp/install-skill-tests"
PYTHON = sys.executable

RUNTIME_ENTRIES = [
    "SKILL.md",
    "requirements.txt",
    "references",
    "schemas",
    "scripts",
    "examples",
]


def make_run_dir(name):
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name).strip("._") or "run"
    run_dir = INSTALL_TMP_ROOT / f"{safe_name}-{uuid.uuid4().hex}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def run_installer(*args, env=None):
    process_env = os.environ.copy()
    process_env.pop("CODEX_HOME", None)
    if env:
        process_env.update(env)
    return subprocess.run(
        [PYTHON, str(INSTALLER), *map(str, args)],
        cwd=ROOT,
        env=process_env,
        text=True,
        capture_output=True,
        check=False,
    )


def load_installer_module():
    spec = importlib.util.spec_from_file_location("install_skill_under_test", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call_main(module, argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            result = module.main(argv)
        except SystemExit as exc:
            code = exc.code
        else:
            code = result
    return code or 0, stdout.getvalue(), stderr.getvalue()


def create_minimal_source(root, skill_text=None):
    root.mkdir(parents=True, exist_ok=True)
    (root / "references").mkdir()
    (root / "schemas").mkdir()
    (root / "scripts").mkdir()
    (root / "examples").mkdir()
    (root / "SKILL.md").write_text(
        skill_text
        or """---
name: create-structure-md
description: Test fixture.
---

# Test Skill

Read `references/dsl-spec.md` before writing DSL.
""",
        encoding="utf-8",
    )
    (root / "requirements.txt").write_text("jsonschema\n", encoding="utf-8")
    (root / "references/dsl-spec.md").write_text("# DSL Spec\n", encoding="utf-8")
    (root / "scripts/validate_dsl.py").write_text("def main(argv=None):\n    return 0\n", encoding="utf-8")
    (root / "scripts/validate_mermaid.py").write_text("def main(argv=None):\n    return 0\n", encoding="utf-8")
    (root / "scripts/render_markdown.py").write_text("def main(argv=None):\n    return 0\n", encoding="utf-8")
    (root / "schemas/structure-design.schema.json").write_text("{}\n", encoding="utf-8")
    (root / "examples/minimal.dsl.json").write_text("{}\n", encoding="utf-8")
    return root


class InstallerCliTests(unittest.TestCase):
    def test_dry_run_reports_target_and_does_not_create_target(self):
        run_dir = make_run_dir("dry-run")
        codex_home = run_dir / "codex-home"
        target = codex_home / "skills/create-structure-md"

        completed = run_installer("--dry-run", "--codex-home", codex_home)

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("DRY RUN: no files copied", completed.stdout)
        self.assertIn(f"Target: {target}", completed.stdout)
        for entry in RUNTIME_ENTRIES:
            self.assertIn(f"- {entry}", completed.stdout)
        self.assertIn("Dependency status:", completed.stdout)
        self.assertFalse(target.exists())

    def test_copy_install_copies_runtime_allowlist_only(self):
        run_dir = make_run_dir("copy-install")
        codex_home = run_dir / "codex-home"
        target = codex_home / "skills/create-structure-md"

        completed = run_installer("--codex-home", codex_home)

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn(f"Installed create-structure-md to {target}", completed.stdout)
        for entry in RUNTIME_ENTRIES:
            self.assertTrue((target / entry).exists(), f"missing installed entry: {entry}")
        self.assertFalse((target / "docs").exists())
        self.assertFalse((target / "tests").exists())

    def test_existing_target_fails_before_copying(self):
        run_dir = make_run_dir("existing-target")
        codex_home = run_dir / "codex-home"
        target = codex_home / "skills/create-structure-md"
        target.mkdir(parents=True)
        marker = target / "marker.txt"
        marker.write_text("keep me\n", encoding="utf-8")

        completed = run_installer("--codex-home", codex_home)

        self.assertEqual(1, completed.returncode)
        self.assertIn("ERROR: target already exists", completed.stderr)
        self.assertIn(str(target), completed.stderr)
        self.assertTrue(marker.exists())
        self.assertFalse((target / "SKILL.md").exists())

    def test_codex_home_env_is_used_when_flag_absent(self):
        run_dir = make_run_dir("env-home")
        codex_home = run_dir / "env-codex-home"
        target = codex_home / "skills/create-structure-md"

        completed = run_installer(env={"CODEX_HOME": str(codex_home)})

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(target.exists())
        self.assertIn(f"Codex home: {codex_home}", completed.stdout)

    def test_codex_home_argument_overrides_environment(self):
        run_dir = make_run_dir("flag-over-env")
        env_home = run_dir / "env-home"
        flag_home = run_dir / "flag-home"
        target = flag_home / "skills/create-structure-md"

        completed = run_installer(
            "--dry-run",
            "--codex-home",
            flag_home,
            env={"CODEX_HOME": str(env_home)},
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn(f"Codex home: {flag_home}", completed.stdout)
        self.assertIn(f"Target: {target}", completed.stdout)
        self.assertNotIn(str(env_home), completed.stdout)
        self.assertFalse(target.exists())

    def test_home_fallback_uses_home_environment_when_codex_home_unset(self):
        run_dir = make_run_dir("home-fallback")
        home = run_dir / "home"
        home.mkdir()
        expected_codex_home = home / ".codex"
        expected_target = expected_codex_home / "skills/create-structure-md"

        completed = run_installer("--dry-run", env={"HOME": str(home)})

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn(f"Codex home: {expected_codex_home}", completed.stdout)
        self.assertIn(f"Target: {expected_target}", completed.stdout)
        self.assertFalse(expected_target.exists())


class InstallerStructureValidationTests(unittest.TestCase):
    def test_validate_source_rejects_missing_required_file(self):
        module = load_installer_module()
        run_dir = make_run_dir("missing-required")
        source = run_dir / "source"
        create_minimal_source(source)
        (source / "requirements.txt").unlink()

        report = module.validate_source(source)

        self.assertFalse(report.ok)
        self.assertIn("missing required file: requirements.txt", report.messages)

    def test_validate_source_checks_references_named_by_skill(self):
        module = load_installer_module()
        run_dir = make_run_dir("missing-reference")
        source = run_dir / "source"
        create_minimal_source(
            source,
            skill_text="""---
name: create-structure-md
description: Test fixture.
---

# Test Skill

Read `references/missing.md` before continuing.
""",
        )

        report = module.validate_source(source)

        self.assertFalse(report.ok)
        self.assertIn("missing referenced file: references/missing.md", report.messages)

    def test_validate_source_rejects_wrong_skill_name(self):
        module = load_installer_module()
        run_dir = make_run_dir("wrong-name")
        source = run_dir / "source"
        create_minimal_source(
            source,
            skill_text="""---
name: wrong-name
description: Test fixture.
---

# Test Skill
""",
        )

        report = module.validate_source(source)

        self.assertFalse(report.ok)
        self.assertIn("SKILL.md front matter must contain name: create-structure-md", report.messages)

    def test_validate_installed_target_after_copy(self):
        module = load_installer_module()
        run_dir = make_run_dir("validate-installed")
        codex_home = run_dir / "codex-home"
        target = codex_home / "skills/create-structure-md"

        code, stdout, stderr = call_main(module, ["--codex-home", str(codex_home)])

        self.assertEqual(0, code, stderr)
        self.assertIn(f"Installed create-structure-md to {target}", stdout)
        report = module.validate_source(target)
        self.assertTrue(report.ok, report.messages)


class InstallerDependencyReportingTests(unittest.TestCase):
    def test_dependency_status_marks_jsonschema_as_required(self):
        module = load_installer_module()

        def fake_find_spec(name):
            return object() if name == "jsonschema" else None

        def fake_which(name):
            return {
                "node": "/usr/bin/node",
                "mmdc": None,
            }.get(name)

        statuses = module.collect_dependency_status(find_spec=fake_find_spec, which=fake_which)
        by_name = {status.name: status for status in statuses}

        self.assertTrue(by_name["python"].ok)
        self.assertTrue(by_name["python"].required)
        self.assertTrue(by_name["jsonschema"].ok)
        self.assertTrue(by_name["jsonschema"].required)
        self.assertTrue(by_name["node"].ok)
        self.assertFalse(by_name["node"].required)
        self.assertFalse(by_name["mmdc"].ok)
        self.assertFalse(by_name["mmdc"].required)
        self.assertIn("strict Mermaid validation", by_name["mmdc"].message)

    def test_dependency_status_reports_missing_jsonschema_without_blocking_install(self):
        module = load_installer_module()

        statuses = module.collect_dependency_status(
            find_spec=lambda name: None,
            which=lambda name: None,
        )
        by_name = {status.name: status for status in statuses}

        self.assertFalse(by_name["jsonschema"].ok)
        self.assertTrue(by_name["jsonschema"].required)
        self.assertIn("python -m pip install -r requirements.txt", by_name["jsonschema"].message)


class InstallDocumentationTests(unittest.TestCase):
    def test_install_documentation_contains_copy_only_workflow(self):
        text = (ROOT / "docs/install.md").read_text(encoding="utf-8")

        required_phrases = [
            "# Installing create-structure-md",
            "copy-only",
            "$CODEX_HOME/skills/create-structure-md",
            "python scripts/install_skill.py --dry-run",
            "python scripts/install_skill.py",
            "python scripts/install_skill.py --codex-home /path/to/.codex",
            "does not provide `--force`",
            "does not support symlink installation",
            "does not copy `docs/` or `tests/`",
            "python -m pip install -r requirements.txt",
            "strict Mermaid validation",
            "mmdc",
            "rm -r",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_requirements_remain_runtime_only(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()

        self.assertEqual(["jsonschema"], [line.strip() for line in requirements if line.strip()])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_install_skill -v
```

Expected: FAIL or ERROR because `scripts/install_skill.py` and `docs/install.md` do not exist yet. The failure should include messages such as `No such file or directory: '.../scripts/install_skill.py'` or `No such file or directory: '.../docs/install.md'`.

- [ ] **Step 3: Commit the failing tests**

Run:

```bash
git add tests/test_install_skill.py
git commit -m "test: cover copy-only skill installer"
```

Expected: commit succeeds with only `tests/test_install_skill.py` staged.

---

### Task 2: Copy-Only Installer

**Files:**
- Create: `scripts/install_skill.py`
- Test: `tests/test_install_skill.py`

- [ ] **Step 1: Create the installer implementation**

Create `scripts/install_skill.py` with this exact content:

```python
#!/usr/bin/env python3
import argparse
import importlib.util
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


SKILL_NAME = "create-structure-md"
INSTALL_ENTRIES = (
    "SKILL.md",
    "requirements.txt",
    "references",
    "schemas",
    "scripts",
    "examples",
)
REQUIRED_FILES = (
    "SKILL.md",
    "requirements.txt",
    "scripts/validate_dsl.py",
    "scripts/validate_mermaid.py",
    "scripts/render_markdown.py",
)
REQUIRED_DIRECTORIES = (
    "references",
    "schemas",
    "scripts",
    "examples",
)
REFERENCE_PATH_RE = re.compile(r"references/[A-Za-z0-9_.\-/]+\.md")


@dataclass(frozen=True)
class StructureReport:
    messages: list[str]

    @property
    def ok(self):
        return not self.messages


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    ok: bool
    required: bool
    message: str


def build_parser():
    parser = argparse.ArgumentParser(
        description="Install create-structure-md into a local Codex skills directory."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned installation without writing files.",
    )
    parser.add_argument(
        "--codex-home",
        help="Override Codex home. Defaults to CODEX_HOME, then ~/.codex.",
    )
    return parser


def repo_root():
    return Path(__file__).resolve().parents[1]


def resolve_codex_home(codex_home_arg=None, env=None):
    env = os.environ if env is None else env
    if codex_home_arg:
        return Path(codex_home_arg).expanduser().resolve()
    if env.get("CODEX_HOME"):
        return Path(env["CODEX_HOME"]).expanduser().resolve()
    return Path("~/.codex").expanduser().resolve()


def resolve_target(codex_home):
    return codex_home / "skills" / SKILL_NAME


def parse_front_matter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return values
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return {}


def referenced_files_from_skill(skill_text):
    return sorted(set(REFERENCE_PATH_RE.findall(skill_text)))


def validate_source(source_root):
    source_root = Path(source_root)
    messages = []

    for relative_path in REQUIRED_FILES:
        path = source_root / relative_path
        if not path.is_file():
            messages.append(f"missing required file: {relative_path}")

    for relative_path in REQUIRED_DIRECTORIES:
        path = source_root / relative_path
        if not path.is_dir():
            messages.append(f"missing required directory: {relative_path}")

    skill_path = source_root / "SKILL.md"
    if skill_path.is_file():
        skill_text = skill_path.read_text(encoding="utf-8")
        front_matter = parse_front_matter(skill_text)
        if front_matter.get("name") != SKILL_NAME:
            messages.append(f"SKILL.md front matter must contain name: {SKILL_NAME}")
        for relative_path in referenced_files_from_skill(skill_text):
            if not (source_root / relative_path).is_file():
                messages.append(f"missing referenced file: {relative_path}")

    return StructureReport(messages)


def collect_dependency_status(find_spec=importlib.util.find_spec, which=shutil.which):
    statuses = [
        DependencyStatus(
            "python",
            True,
            True,
            f"found at {sys.executable}",
        )
    ]

    jsonschema_ok = find_spec("jsonschema") is not None
    statuses.append(
        DependencyStatus(
            "jsonschema",
            jsonschema_ok,
            True,
            "available"
            if jsonschema_ok
            else "missing; DSL validation will fail until you run: python -m pip install -r requirements.txt",
        )
    )

    node_path = which("node")
    statuses.append(
        DependencyStatus(
            "node",
            node_path is not None,
            False,
            f"found at {node_path}"
            if node_path
            else "missing; strict Mermaid validation needs Node and Mermaid CLI",
        )
    )

    mmdc_path = which("mmdc")
    statuses.append(
        DependencyStatus(
            "mmdc",
            mmdc_path is not None,
            False,
            f"found at {mmdc_path}"
            if mmdc_path
            else "missing; strict Mermaid validation will not work until Mermaid CLI is installed",
        )
    )
    return statuses


def print_dependency_status(statuses):
    print("Dependency status:")
    for status in statuses:
        level = "required" if status.required else "optional"
        state = "ok" if status.ok else "missing"
        print(f"  - {status.name} ({level}): {state}; {status.message}")


def print_install_plan(source_root, codex_home, target, statuses, *, dry_run):
    if dry_run:
        print("DRY RUN: no files copied")
    print(f"Source: {source_root}")
    print(f"Codex home: {codex_home}")
    print(f"Target: {target}")
    print("Planned entries:")
    for entry in INSTALL_ENTRIES:
        print(f"  - {entry}")
    print_dependency_status(statuses)


def copy_entry(source_root, target_root, entry):
    source = source_root / entry
    destination = target_root / entry
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def copy_install(source_root, target):
    target.mkdir()
    for entry in INSTALL_ENTRIES:
        copy_entry(source_root, target, entry)


def fail_source_report(report):
    print("ERROR: source checkout is not installable:", file=sys.stderr)
    for message in report.messages:
        print(f"  - {message}", file=sys.stderr)
    return 1


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    source_root = repo_root()
    codex_home = resolve_codex_home(args.codex_home)
    target = resolve_target(codex_home)

    report = validate_source(source_root)
    statuses = collect_dependency_status()

    if not report.ok:
        return fail_source_report(report)

    print_install_plan(source_root, codex_home, target, statuses, dry_run=args.dry_run)

    if target.exists():
        print(f"ERROR: target already exists: {target}", file=sys.stderr)
        print("Move or remove the existing directory yourself before retrying.", file=sys.stderr)
        print(f"Example user-run cleanup command: rm -r {target}", file=sys.stderr)
        return 1

    if args.dry_run:
        return 0

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        copy_install(source_root, target)
    except OSError as exc:
        print(f"ERROR: install failed while writing {target}: {exc}", file=sys.stderr)
        print(f"The target may be partially written. Inspect it manually: {target}", file=sys.stderr)
        print(f"If cleanup is desired, user-run command: rm -r {target}", file=sys.stderr)
        return 1

    installed_report = validate_source(target)
    if not installed_report.ok:
        print("ERROR: installed target failed structural validation:", file=sys.stderr)
        for message in installed_report.messages:
            print(f"  - {message}", file=sys.stderr)
        print(f"If cleanup is desired, user-run command: rm -r {target}", file=sys.stderr)
        return 1

    print(f"Installed {SKILL_NAME} to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run installer tests that should now pass except documentation**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest \
  tests.test_install_skill.InstallerCliTests \
  tests.test_install_skill.InstallerStructureValidationTests \
  tests.test_install_skill.InstallerDependencyReportingTests \
  -v
```

Expected: PASS for all CLI, structure validation, and dependency reporting tests. Documentation tests are not included in this command because `docs/install.md` is created in Task 3.

- [ ] **Step 3: Run the complete installer test module to confirm only documentation remains**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_install_skill -v
```

Expected: FAIL only in `InstallDocumentationTests.test_install_documentation_contains_copy_only_workflow` because `docs/install.md` does not exist yet. If another test fails, fix `scripts/install_skill.py` before continuing.

- [ ] **Step 4: Commit the installer implementation**

Run:

```bash
git add scripts/install_skill.py tests/test_install_skill.py
git commit -m "feat: add copy-only skill installer"
```

Expected: commit succeeds with `scripts/install_skill.py` and any test adjustments staged.

---

### Task 3: Installation Documentation

**Files:**
- Create: `docs/install.md`
- Test: `tests/test_install_skill.py`

- [ ] **Step 1: Create the install documentation**

Create `docs/install.md` with this exact content:

```markdown
# Installing create-structure-md

This repository can be installed as a local Codex skill with a conservative copy-only installer.

The installer copies the runtime skill files into your Codex skills directory. It does not install dependencies, does not provide `--force`, does not support symlink installation, does not overwrite an existing install, and does not copy `docs/` or `tests/`.

## Target Path

The installed skill target is:

```text
$CODEX_HOME/skills/create-structure-md
```

Codex home is resolved in this order:

1. `--codex-home /path/to/.codex`
2. `CODEX_HOME`
3. `~/.codex`

## Dry Run

Run a dry run first:

```bash
python scripts/install_skill.py --dry-run
```

The dry run prints the source checkout, Codex home, target path, planned copied entries, and dependency status. It does not create the target directory.

## Install

Install into the default Codex home:

```bash
python scripts/install_skill.py
```

Install into a specific Codex home:

```bash
python scripts/install_skill.py --codex-home /path/to/.codex
```

The installer copies only:

```text
SKILL.md
requirements.txt
references/
schemas/
scripts/
examples/
```

It does not copy `docs/` or `tests/`.

## Existing Target

If `$CODEX_HOME/skills/create-structure-md` already exists, the installer fails before copying anything. It does not merge, overwrite, back up, or delete the existing directory.

If you intentionally want to replace an existing install, inspect the directory yourself first. A manual cleanup command looks like:

```bash
rm -r $CODEX_HOME/skills/create-structure-md
```

Run that command yourself only when you are certain the existing directory can be removed.

## Dependencies

The installer reports dependency status but does not install anything.

The skill needs Python and `jsonschema` for DSL validation. Install Python dependencies from this repository with:

```bash
python -m pip install -r requirements.txt
```

Strict Mermaid validation also needs local Mermaid CLI tooling. If `mmdc` is missing, installation can still complete, but strict Mermaid validation will not work until Mermaid CLI is installed and available on `PATH`.

## Verification

After installation, start a fresh Codex session and check that the `create-structure-md` skill is listed as an available skill.

For repository development, run:

```bash
python -m unittest discover -s tests -v
```

This repository preserves `.codex-tmp` test artifacts for inspection. If cleanup is desired, run the cleanup command yourself after reviewing the files.
```

- [ ] **Step 2: Run the documentation tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_install_skill.InstallDocumentationTests -v
```

Expected: PASS for documentation signposts and runtime-only requirements.

- [ ] **Step 3: Run the complete installer test module**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_install_skill -v
```

Expected: PASS for all tests in `tests.test_install_skill`.

- [ ] **Step 4: Commit the install documentation**

Run:

```bash
git add docs/install.md tests/test_install_skill.py
git commit -m "docs: explain copy-only skill installation"
```

Expected: commit succeeds with `docs/install.md` and any documentation test adjustments staged.

---

### Task 4: Full Verification And Final Contract Check

**Files:**
- Verify: `scripts/install_skill.py`
- Verify: `docs/install.md`
- Verify: `tests/test_install_skill.py`
- Verify: `requirements.txt`

- [ ] **Step 1: Run a real dry-run command against a scratch Codex home**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/install_skill.py --dry-run --codex-home .codex-tmp/install-skill-manual-check/codex-home
```

Expected: PASS with exit code 0. Output includes:

```text
DRY RUN: no files copied
Target: /home/hyx/create-structure-md/.codex-tmp/install-skill-manual-check/codex-home/skills/create-structure-md
Planned entries:
  - SKILL.md
  - requirements.txt
  - references
  - schemas
  - scripts
  - examples
Dependency status:
```

- [ ] **Step 2: Run a real install command against a scratch Codex home**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/install_skill.py --codex-home .codex-tmp/install-skill-manual-check/codex-home
```

Expected: PASS with exit code 0. Output includes:

```text
Installed create-structure-md to /home/hyx/create-structure-md/.codex-tmp/install-skill-manual-check/codex-home/skills/create-structure-md
```

- [ ] **Step 3: Inspect the scratch install file set**

Run:

```bash
find .codex-tmp/install-skill-manual-check/codex-home/skills/create-structure-md -maxdepth 1 -mindepth 1 -printf '%f\n' | sort
```

Expected output:

```text
SKILL.md
examples
references
requirements.txt
schemas
scripts
```

No `docs` or `tests` entry should appear.

- [ ] **Step 4: Verify existing target refusal**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python scripts/install_skill.py --codex-home .codex-tmp/install-skill-manual-check/codex-home
```

Expected: FAIL with exit code 1. Stderr includes:

```text
ERROR: target already exists:
Example user-run cleanup command: rm -r
```

- [ ] **Step 5: Run the full test suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected: PASS for the full suite.

- [ ] **Step 6: Verify no dependency drift**

Run:

```bash
cat requirements.txt
```

Expected output:

```text
jsonschema
```

- [ ] **Step 7: Check git status**

Run:

```bash
git status --short
```

Expected: either clean, or only intentional `.codex-tmp/` artifacts that must not be deleted by Codex. If cleanup is desired, give the user this command to run:

```bash
rm -r /home/hyx/create-structure-md/.codex-tmp/install-skill-tests /home/hyx/create-structure-md/.codex-tmp/install-skill-manual-check
```

- [ ] **Step 8: Commit any final verification adjustments**

If Step 5 or Step 6 required small fixes, run:

```bash
git add scripts/install_skill.py docs/install.md tests/test_install_skill.py requirements.txt
git commit -m "test: verify copy-only installer workflow"
```

Expected: commit succeeds only if there were final tracked changes. If no tracked changes remain, do not create an empty commit.

---

## Self-Review

Spec coverage:

- Copy-only installer: Task 2.
- `--dry-run`: Task 1 tests and Task 2 implementation.
- `--codex-home`, `CODEX_HOME`, `~/.codex` precedence: Task 1 tests and Task 2 implementation.
- Target path `<codex-home>/skills/create-structure-md`: Task 1 and Task 2.
- Runtime allowlist only: Task 1 tests, Task 2 implementation, Task 3 docs, Task 4 manual inspection.
- No `docs/` or `tests/` copy: Task 1 tests, Task 3 docs, Task 4 manual inspection.
- Existing target fails without overwrite: Task 1 tests, Task 2 implementation, Task 4 manual check.
- No symlink and no `--force`: Task 2 parser has neither option; Task 3 documents this.
- Source structure checks: Task 1 tests and Task 2 implementation.
- Reference path checks from `SKILL.md`: Task 1 tests and Task 2 implementation.
- Dependency reporting without installing dependencies: Task 1 tests, Task 2 implementation, Task 3 docs.
- Partial-copy failure does not delete output: Task 2 implementation reports manual cleanup instead of deleting.
- Focused tests in `tests/test_install_skill.py`: Task 1.
- Install documentation in `docs/install.md`: Task 3.

Placeholder scan:

- No placeholder-marker strings, deferred implementation wording, or unspecified validation steps remain.
- Every code-changing step includes complete file content or exact commands.

Type and name consistency:

- Test helper calls `validate_source()`, `collect_dependency_status()`, and `main()` match functions defined in Task 2.
- `DependencyStatus.name`, `ok`, `required`, and `message` match the test assertions.
- The target path and allowlisted entries are consistent across tests, implementation, documentation, and verification.

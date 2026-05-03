import contextlib
import importlib.util
import io
import os
import shlex
import subprocess
import sys
import unittest
import uuid
from pathlib import Path


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


def create_minimal_source(root, skill_text=None, include_requirements=True, omit_runtime_scripts=None):
    omit_runtime_scripts = set(omit_runtime_scripts or ())
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
    if include_requirements:
        (root / "requirements.txt").write_text("jsonschema\n", encoding="utf-8")
    (root / "references/dsl-spec.md").write_text("# DSL Spec\n", encoding="utf-8")
    runtime_scripts = {
        "validate_dsl.py": "def main(argv=None):\n    return 0\n",
        "validate_mermaid.py": "def main(argv=None):\n    return 0\n",
        "render_markdown.py": "def main(argv=None):\n    return 0\n",
    }
    for name, text in runtime_scripts.items():
        if name not in omit_runtime_scripts:
            (root / "scripts" / name).write_text(text, encoding="utf-8")
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

    def test_dry_run_reports_existing_target_conflict_without_copying(self):
        run_dir = make_run_dir("dry-run-existing-target")
        codex_home = run_dir / "codex home"
        target = codex_home / "skills/create-structure-md"
        target.mkdir(parents=True)
        marker = target / "marker.txt"
        marker.write_text("keep me\n", encoding="utf-8")

        completed = run_installer("--dry-run", "--codex-home", codex_home)

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("DRY RUN: no files copied", completed.stdout)
        self.assertIn("Conflict: target already exists", completed.stdout)
        self.assertIn(str(target), completed.stdout)
        self.assertTrue(marker.exists())
        self.assertEqual("keep me\n", marker.read_text(encoding="utf-8"))
        self.assertFalse((target / "SKILL.md").exists())

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
        codex_home = run_dir / "codex home"
        target = codex_home / "skills/create-structure-md"
        target.mkdir(parents=True)
        marker = target / "marker.txt"
        marker.write_text("keep me\n", encoding="utf-8")

        completed = run_installer("--codex-home", codex_home)

        self.assertEqual(1, completed.returncode)
        self.assertIn("ERROR: target already exists", completed.stderr)
        self.assertIn(str(target), completed.stderr)
        self.assertIn(
            f"Example user-run cleanup command: rm -r {shlex.quote(str(target))}",
            completed.stderr,
        )
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
        create_minimal_source(source, include_requirements=False)

        report = module.validate_source(source)

        self.assertFalse(report.ok)
        self.assertIn("missing required file: requirements.txt", report.messages)

    def test_validate_source_rejects_missing_core_script(self):
        module = load_installer_module()
        run_dir = make_run_dir("missing-core-script")
        source = run_dir / "source"
        create_minimal_source(source, omit_runtime_scripts={"validate_mermaid.py"})

        report = module.validate_source(source)

        self.assertFalse(report.ok)
        self.assertIn("missing required file: scripts/validate_mermaid.py", report.messages)

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

    def test_main_rejects_invalid_installed_target_after_copy(self):
        module = load_installer_module()
        run_dir = make_run_dir("invalid-installed")
        codex_home = run_dir / "codex home"
        target = codex_home / "skills/create-structure-md"

        def copy_invalid_skill(source, target):
            create_minimal_source(target, omit_runtime_scripts={"render_markdown.py"})

        original_copy_skill = module.copy_skill
        module.copy_skill = copy_invalid_skill
        try:
            code, stdout, stderr = call_main(module, ["--codex-home", str(codex_home)])
        finally:
            module.copy_skill = original_copy_skill

        self.assertEqual(1, code)
        self.assertIn("ERROR: installed target failed structural validation:", stderr)
        self.assertIn("missing required file: scripts/render_markdown.py", stderr)
        self.assertIn(
            f"To clean invalid output, review then run: rm -r {shlex.quote(str(target))}",
            stderr,
        )
        self.assertNotIn(f"Installed create-structure-md to {target}", stdout)


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
            "python3 scripts/install_skill.py --dry-run",
            "python3 scripts/install_skill.py",
            "python3 scripts/install_skill.py --codex-home /path/to/.codex",
            "substitute that command for `python3`",
            "does not provide `--force`",
            "does not support symlink installation",
            "does not copy `docs/` or `tests/`",
            "python3 -m pip install -r requirements.txt",
            "strict Mermaid validation",
            "Node plus Mermaid CLI tooling",
            "mmdc",
            "exact `Target:` path printed by `--dry-run`",
            "rm -r ~/.codex/skills/create-structure-md",
            "rm -r /path/to/.codex/skills/create-structure-md",
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

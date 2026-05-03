# create-structure-md Copy-Only Install Design

## Purpose

Provide a repeatable installation path for users who clone this repository and want to install `create-structure-md` into their local Codex skills directory.

The repository remains the skill source. The installer only packages the runtime skill files into the user's Codex skill directory. It does not publish the skill, install dependencies automatically, manage upgrades, delete existing installs, or turn this repository into a package manager.

## Selected Approach

Use a conservative script-plus-documentation approach:

- Add a copy-only installer at `scripts/install_skill.py`.
- Add user-facing installation documentation at `docs/install.md`.
- Install into `$CODEX_HOME/skills/create-structure-md` by default.
- If `CODEX_HOME` is unset, default to `~/.codex`.
- Allow an explicit Codex home override with `--codex-home`.
- Support `--dry-run` for inspection before writing files.

Symlink installation is intentionally out of scope. Copy-only installation keeps the installed skill independent from the source checkout after installation and avoids surprising behavior when the repository is moved or edited.

## Installation Boundary

The installer copies only the files required for normal skill use:

```text
SKILL.md
requirements.txt
references/
schemas/
scripts/
examples/
```

The installer must not copy:

```text
docs/
tests/
```

`docs/` remains repository development material. `tests/` remains source validation material. Neither is required for Codex to invoke the installed skill.

## Command Interface

The installer should support:

```bash
python scripts/install_skill.py --dry-run
python scripts/install_skill.py
python scripts/install_skill.py --codex-home /path/to/.codex
```

Behavior:

- `--dry-run` reports source checks, target path, planned copied entries, dependency status, and conflicts without writing files.
- A normal run copies the allowlisted entries into the target directory.
- `--codex-home` overrides `CODEX_HOME` and the `~/.codex` fallback.
- There is no `--force`.
- There is no symlink mode.
- The script does not delete, overwrite, or auto-back up existing files.

## Target Path Rules

The target skill directory is:

```text
<codex-home>/skills/create-structure-md
```

Codex home is resolved in this order:

1. `--codex-home`, if provided.
2. `CODEX_HOME`, if set.
3. `~/.codex`.

The installer may create the non-destructive parent directory `<codex-home>/skills` when it does not exist. It may create the final target directory only when it is absent.

If the target directory already exists, the installer must fail before copying anything. The error should explain the conflict and provide manual next steps for the user. It must not remove, overwrite, or merge with the existing directory.

## Preflight Validation

Before copying, the installer validates the source checkout:

- `SKILL.md` exists.
- `SKILL.md` front matter contains `name: create-structure-md`.
- `requirements.txt` exists.
- `references/`, `schemas/`, `scripts/`, and `examples/` exist.
- `scripts/validate_dsl.py`, `scripts/validate_mermaid.py`, and `scripts/render_markdown.py` exist.
- Reference paths named by `SKILL.md` exist.

If any required source check fails, the installer exits non-zero and does not copy files.

After copying, the installer runs the same structural checks against the installed target and reports the installed path.

## Dependency Reporting

The installer reports dependency status but does not install dependencies.

Required runtime checks:

- Python is available.
- `jsonschema` can be imported by the Python interpreter running the installer.

Strict Mermaid validation checks:

- `node` is available.
- `mmdc` is available.

`jsonschema` absence should be reported prominently because DSL validation will fail without it. Mermaid CLI absence should not block installation, but the message must make clear that strict Mermaid validation will not work until Mermaid CLI tooling is installed.

Suggested remediation text may include:

```bash
python -m pip install -r requirements.txt
```

The installer must not run package managers, install Node packages, download browsers, or change shell configuration.

## Failure Strategy

The installer uses fail-fast behavior:

- Invalid source structure: fail before copying.
- Existing target directory: fail before copying.
- Permission denied: fail and explain the path involved.
- Partial copy failure: report that the target may be partially written and give the user a manual inspection or cleanup command. The installer must not delete partial output.

All destructive cleanup remains a user action. This matches the repository rule that Codex must not execute deletion operations.

## Tests

Add focused installer tests in:

```text
tests/test_install_skill.py
```

Coverage:

- `--dry-run` does not create the target directory.
- Normal install copies `SKILL.md`, `requirements.txt`, `references/`, `schemas/`, `scripts/`, and `examples/`.
- Normal install does not copy `docs/` or `tests/`.
- Existing target directory fails without overwrite.
- Missing required source files fail before copying.
- `--codex-home` installs under the specified Codex home.
- Installed target passes the same structural validation as the source.

Tests should use repository-local scratch directories under `.codex-tmp/install-skill-tests/<name>-<uuid>/` and must not use `TemporaryDirectory()` auto-cleanup. Test output or documentation may provide cleanup commands for the user to run manually.

## Documentation

Add:

```text
docs/install.md
```

The document should explain:

- The copy-only installation model.
- The default target path.
- `CODEX_HOME` and `--codex-home` precedence.
- Dry-run and install commands.
- Behavior when the target already exists.
- Runtime dependency expectations.
- Mermaid CLI strict validation expectations.
- The fact that installed files exclude `docs/` and `tests/`.
- Manual cleanup guidance without instructing Codex to execute deletion.

## Out of Scope

- Symlink installation.
- Force overwrite.
- Automatic backup.
- Automatic dependency installation.
- Marketplace publishing.
- Version registry or upgrade manager.
- Uninstall command.
- Copying `docs/` or `tests/` into the installed skill.

## Acceptance Criteria

- A user who clones the repository can run a dry-run command and see the exact install target and copied entries.
- A user can install the skill into a custom Codex home without editing the script.
- Existing installs are never overwritten.
- Installed content contains only the runtime allowlist.
- Dependency gaps are reported without mutating the user's environment.
- Installer behavior is covered by focused tests.
- Installation documentation is sufficient for a fresh user to perform and verify installation.

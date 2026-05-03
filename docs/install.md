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
python3 scripts/install_skill.py --dry-run
```

The dry run prints the source checkout, Codex home, target path, planned copied entries, and dependency status. It does not create the target directory.

If your active Python 3 interpreter has another name, substitute that command for `python3`.

## Install

Install into the default Codex home:

```bash
python3 scripts/install_skill.py
```

Install into a specific Codex home:

```bash
python3 scripts/install_skill.py --codex-home /path/to/.codex
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

If you intentionally want to replace an existing install, inspect the exact `Target:` path printed by `--dry-run` first. Use that exact target path in any manual cleanup command.

For the default fallback target, a manual cleanup command looks like:

```bash
rm -r ~/.codex/skills/create-structure-md
```

For an explicit Codex home, a manual cleanup command looks like:

```bash
rm -r /path/to/.codex/skills/create-structure-md
```

Run a cleanup command yourself only when you are certain the existing directory can be removed.

## Dependencies

The installer reports dependency status but does not install anything.

The skill needs Python and `jsonschema` for DSL validation. Install Python dependencies from this repository with:

```bash
python3 -m pip install -r requirements.txt
```

Strict Mermaid validation also needs Node plus Mermaid CLI tooling, with `mmdc` available on `PATH`. If `mmdc` is missing, installation can still complete, but strict Mermaid validation will not work until Mermaid CLI is installed and available on `PATH`.

## Verification

After installation, start a fresh Codex session and check that the `create-structure-md` skill is listed as an available skill.

For repository development, run:

```bash
python3 -m unittest discover -s tests -v
```

This repository preserves `.codex-tmp` test artifacts for inspection. If cleanup is desired, run the cleanup command yourself after reviewing the files.

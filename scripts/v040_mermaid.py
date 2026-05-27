import shutil
import subprocess
import tempfile
from pathlib import Path

from scripts.v040_types import ValidationResult


MERMAID_RENDER_TIMEOUT_SECONDS = 30


def mermaid_validation_result(package) -> ValidationResult:
    result = ValidationResult()
    blocks = list(_iter_mermaid_blocks(package))
    if not blocks:
        return result

    mmdc = _locate_mermaid_cli()
    if mmdc is None:
        result.error(
            "mermaid.cli_missing",
            "$",
            "Mermaid blocks require the mmdc CLI for strict rendering validation",
        )
        return result

    for path, block in blocks:
        _validate_mermaid_block(mmdc, path, block, result)
    return result


def _locate_mermaid_cli() -> str | None:
    return shutil.which("mmdc")


def _validate_mermaid_block(mmdc, path, block, result):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        input_path = tmpdir / "diagram.mmd"
        output_path = tmpdir / "diagram.svg"
        input_path.write_text(block.get("source", ""), encoding="utf-8")

        try:
            completed = subprocess.run(
                [mmdc, "-i", str(input_path), "-o", str(output_path)],
                capture_output=True,
                text=True,
                timeout=MERMAID_RENDER_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            result.error(
                "mermaid.timeout",
                path,
                f"Mermaid CLI timed out after {exc.timeout} seconds for block {path}",
            )
            return
        except OSError as exc:
            result.error(
                "mermaid.cli_error",
                path,
                f"Mermaid CLI could not run for block {path}: {exc}",
            )
            return

        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            detail = f": {stderr}" if stderr else ""
            result.error(
                "mermaid.render_failed",
                path,
                f"Mermaid CLI failed for block {path}{detail}",
            )
            return

        if not output_path.exists():
            result.error(
                "mermaid.svg_missing",
                path,
                f"Mermaid CLI succeeded but did not create SVG output for block {path}",
            )


def _iter_mermaid_blocks(package):
    for chapter_key, chapter in package.chapters.items():
        for path, value in _walk(chapter, f"$.{chapter_key}"):
            if isinstance(value, dict) and value.get("type") == "mermaid":
                yield path, value


def _walk(value, path):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")

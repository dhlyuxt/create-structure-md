import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/valid-v2-foundation.dsl.json"
PYTHON = sys.executable


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def valid_document():
    return deepcopy(load_json(FIXTURE))


def load_script(relative_path):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(path.stem + "_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(tmpdir, name, document):
    path = Path(tmpdir) / name
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_text(tmpdir, name, text):
    path = Path(tmpdir) / name
    path.write_text(text, encoding="utf-8")
    return path


def call_main(module, argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = module.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class Phase4RendererMetadataTests(unittest.TestCase):
    def test_rendered_mermaid_fences_have_adjacent_diagram_id_metadata(self):
        module = load_script("scripts/render_markdown.py")
        markdown = module.render_markdown(valid_document())

        for fragment in [
            "<!-- diagram-id: MER-ARCH-MODULES -->\n```mermaid",
            "<!-- diagram-id: MER-IFACE-SKILL-RENDER-CLI -->\n```mermaid",
            "<!-- diagram-id: MER-BLOCK-MECHANISM-FLOW -->\n```mermaid",
            "<!-- diagram-id: MER-RUNTIME-FLOW -->\n```mermaid",
            "<!-- diagram-id: MER-COLLABORATION-RELATIONSHIP -->\n```mermaid",
            "<!-- diagram-id: MER-FLOW-GENERATE -->\n```mermaid",
            "<!-- diagram-id: MER-BLOCK-STRUCTURE-ISSUES -->\n```mermaid",
        ]:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, markdown)

    def test_diagram_id_metadata_is_not_controlled_by_evidence_mode(self):
        module = load_script("scripts/render_markdown.py")
        hidden = module.render_markdown(valid_document(), evidence_mode="hidden")
        inline = module.render_markdown(valid_document(), evidence_mode="inline")

        self.assertIn("<!-- diagram-id: MER-ARCH-MODULES -->\n```mermaid", hidden)
        self.assertIn("<!-- diagram-id: MER-ARCH-MODULES -->\n```mermaid", inline)

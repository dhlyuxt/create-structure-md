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


def load_script(relative_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / relative_path)
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
    return code or 0, stdout.getvalue(), stderr.getvalue()


class Phase4HarnessContractTests(unittest.TestCase):
    def test_load_script_uses_explicit_module_name(self):
        module = load_script("scripts/render_markdown.py", "phase4_renderer_contract_under_test")

        self.assertEqual("phase4_renderer_contract_under_test", module.__name__)

    def test_call_main_normalizes_none_exit_code_to_zero(self):
        class NoneReturningModule:
            @staticmethod
            def main(argv):
                print("stdout text")
                print("stderr text", file=sys.stderr)

        code, stdout, stderr = call_main(NoneReturningModule, ["input.dsl.json"])

        self.assertEqual(0, code)
        self.assertEqual("stdout text\n", stdout)
        self.assertEqual("stderr text\n", stderr)


class Phase4RendererMetadataTests(unittest.TestCase):
    def test_rendered_mermaid_fences_have_adjacent_diagram_id_metadata(self):
        module = load_script("scripts/render_markdown.py", "phase4_render_markdown_metadata_under_test")
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
        module = load_script("scripts/render_markdown.py", "phase4_render_markdown_evidence_under_test")
        hidden = module.render_markdown(valid_document(), evidence_mode="hidden")
        inline = module.render_markdown(valid_document(), evidence_mode="inline")

        self.assertIn("<!-- diagram-id: MER-ARCH-MODULES -->\n```mermaid", hidden)
        self.assertIn("<!-- diagram-id: MER-ARCH-MODULES -->\n```mermaid", inline)

    def test_diagram_id_metadata_rejects_non_string_id(self):
        module = load_script("scripts/render_markdown.py", "phase4_render_markdown_id_type_under_test")
        diagram = {"id": 123, "title": "", "description": "", "source": "flowchart TD\n  A --> B"}

        with self.assertRaisesRegex(module.RenderError, "Mermaid diagram.id must be a string"):
            module.render_mermaid_block(diagram)


class Phase4ExpectedDiagramCollectorTests(unittest.TestCase):
    def diagram(self, diagram_id):
        return {
            "id": diagram_id,
            "title": f"{diagram_id} title",
            "source": "flowchart TD\n  A --> B",
        }

    def _diagram_at_json_path(self, document, path):
        current = document
        for part in path.removeprefix("$.").split("."):
            if "[" in part:
                field, index = part.rstrip("]").split("[")
                current = current[field][int(index)]
            else:
                current = current[part]
        return current

    def test_expected_collector_includes_existing_and_v2_diagram_paths(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_collector_under_test")
        document = valid_document()
        diagrams = phase4.collect_expected_diagrams(document)
        by_id = {diagram.diagram_id: diagram for diagram in diagrams if diagram.should_render}
        expected_paths = {
            "MER-ARCH-MODULES": "$.architecture_views.module_relationship_diagram",
            "MER-IFACE-SKILL-RENDER-CLI": "$.module_design.modules[0].public_interfaces.interfaces[1].execution_flow_diagram",
            "MER-IFACE-SKILL-VALIDATE-CLI": "$.module_design.modules[0].public_interfaces.interfaces[2].execution_flow_diagram",
            "MER-BLOCK-MECHANISM-FLOW": "$.module_design.modules[0].internal_mechanism.mechanism_details[0].blocks[1].diagram",
            "MER-RUNTIME-FLOW": "$.runtime_view.runtime_flow_diagram",
            "MER-COLLABORATION-RELATIONSHIP": "$.cross_module_collaboration.collaboration_relationship_diagram",
            "MER-FLOW-GENERATE": "$.key_flows.flows[0].diagram",
            "MER-BLOCK-STRUCTURE-ISSUES": "$.structure_issues_and_suggestions.blocks[1].diagram",
        }
        expected_owner_paths = {
            "MER-ARCH-MODULES": "$.architecture_views",
            "MER-IFACE-SKILL-RENDER-CLI": "$.module_design.modules[0].public_interfaces",
            "MER-IFACE-SKILL-VALIDATE-CLI": "$.module_design.modules[0].public_interfaces",
            "MER-BLOCK-MECHANISM-FLOW": "$.module_design.modules[0].internal_mechanism",
            "MER-RUNTIME-FLOW": "$.runtime_view",
            "MER-COLLABORATION-RELATIONSHIP": "$.cross_module_collaboration",
            "MER-FLOW-GENERATE": "$.key_flows.flows[0]",
            "MER-BLOCK-STRUCTURE-ISSUES": "$.structure_issues_and_suggestions",
        }

        self.assertEqual(set(expected_paths), set(by_id))
        for diagram_id, path in expected_paths.items():
            with self.subTest(diagram_id=diagram_id):
                expected_diagram = self._diagram_at_json_path(document, path)
                self.assertEqual(path, by_id[diagram_id].json_path)
                self.assertEqual(expected_owner_paths[diagram_id], by_id[diagram_id].owning_section_path)
                self.assertEqual(expected_diagram["source"].strip(), by_id[diagram_id].source.strip())
                self.assertEqual(expected_diagram["title"].strip(), by_id[diagram_id].title.strip())

    def test_expected_collector_includes_all_planned_optional_v2_paths(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_collector_under_test")
        document = valid_document()
        document["architecture_views"]["extra_diagrams"] = [self.diagram("MER-SYN-ARCH-EXTRA")]
        document["runtime_view"]["runtime_sequence_diagram"] = self.diagram("MER-SYN-RUNTIME-SEQUENCE")
        document["runtime_view"]["extra_diagrams"] = [self.diagram("MER-SYN-RUNTIME-EXTRA")]
        document["configuration_data_dependencies"]["extra_diagrams"] = [self.diagram("MER-SYN-CONFIG-EXTRA")]
        document["cross_module_collaboration"]["extra_diagrams"] = [self.diagram("MER-SYN-COLLAB-EXTRA")]
        document["key_flows"]["extra_diagrams"] = [self.diagram("MER-SYN-KEY-FLOWS-EXTRA")]

        diagrams = phase4.collect_expected_diagrams(document)
        by_id = {diagram.diagram_id: diagram for diagram in diagrams if diagram.should_render}
        expected_paths = {
            "MER-SYN-ARCH-EXTRA": "$.architecture_views.extra_diagrams[0]",
            "MER-SYN-RUNTIME-SEQUENCE": "$.runtime_view.runtime_sequence_diagram",
            "MER-SYN-RUNTIME-EXTRA": "$.runtime_view.extra_diagrams[0]",
            "MER-SYN-CONFIG-EXTRA": "$.configuration_data_dependencies.extra_diagrams[0]",
            "MER-SYN-COLLAB-EXTRA": "$.cross_module_collaboration.extra_diagrams[0]",
            "MER-SYN-KEY-FLOWS-EXTRA": "$.key_flows.extra_diagrams[0]",
        }

        for diagram_id, path in expected_paths.items():
            with self.subTest(diagram_id=diagram_id):
                self.assertIn(diagram_id, by_id)
                self.assertEqual(path, by_id[diagram_id].json_path)

    def test_expected_collector_ignores_removed_v1_chapter_4_paths(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_collector_under_test")
        document = valid_document()
        module = document["module_design"]["modules"][0]
        module["internal_structure"] = {
            "diagram": {
                "id": "MER-REMOVED-INTERNAL-STRUCTURE",
                "title": "Removed V1 diagram",
                "source": "flowchart TD\n  A --> B",
            }
        }
        module["external_capability_details"] = {
            "extra_diagrams": [self.diagram("MER-REMOVED-CAPABILITY-EXTRA")]
        }
        module["extra_diagrams"] = [self.diagram("MER-REMOVED-MODULE-EXTRA")]

        diagrams = phase4.collect_expected_diagrams(document)

        diagram_ids = {diagram.diagram_id for diagram in diagrams}
        self.assertNotIn("MER-REMOVED-INTERNAL-STRUCTURE", diagram_ids)
        self.assertNotIn("MER-REMOVED-CAPABILITY-EXTRA", diagram_ids)
        self.assertNotIn("MER-REMOVED-MODULE-EXTRA", diagram_ids)

    def test_expected_collector_ignores_contract_interface_execution_flow_diagram(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_collector_under_test")
        document = valid_document()
        contract_interface = document["module_design"]["modules"][0]["public_interfaces"]["interfaces"][0]
        self.assertEqual("schema_contract", contract_interface["interface_type"])
        contract_interface["execution_flow_diagram"] = {
            "id": "MER-CONTRACT-SHOULD-NOT-RENDER",
            "title": "Contract interface should not render",
            "source": "flowchart TD\n  A --> B",
        }

        diagrams = phase4.collect_expected_diagrams(document)

        self.assertNotIn("MER-CONTRACT-SHOULD-NOT-RENDER", {diagram.diagram_id for diagram in diagrams})


def complete_review_artifact(source_dsl, diagram_ids):
    return {
        "artifact_schema_version": "1.0",
        "reviewer": "independent_subagent",
        "source_dsl": str(source_dsl),
        "checked_diagram_ids": sorted(diagram_ids),
        "accepted_diagram_ids": sorted(diagram_ids),
        "revised_diagram_ids": [],
        "split_diagram_ids": [],
        "skipped_diagrams": [],
        "remaining_readability_risks": [],
    }


class Phase4ReadabilityArtifactTests(unittest.TestCase):
    def expected_ids(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_under_test")
        return {
            diagram.diagram_id
            for diagram in phase4.collect_expected_diagrams(valid_document())
            if diagram.should_render
        }

    def test_complete_artifact_validates(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_valid_under_test")
        artifact = complete_review_artifact(FIXTURE, self.expected_ids())

        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)

        self.assertEqual([], errors)

    def test_duplicate_expected_diagram_ids_are_error(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_duplicate_expected_under_test")
        document = valid_document()
        duplicate_id = document["architecture_views"]["module_relationship_diagram"]["id"]
        document["runtime_view"]["runtime_flow_diagram"]["id"] = duplicate_id
        deduplicated_ids = {
            diagram.diagram_id
            for diagram in phase4.collect_expected_diagrams(document)
            if diagram.should_render
        }
        artifact = complete_review_artifact(FIXTURE, deduplicated_ids)

        errors = phase4.validate_mermaid_review_artifact(document, FIXTURE, artifact)

        self.assertTrue(
            any("duplicate expected diagram IDs" in error and duplicate_id in error for error in errors),
            errors,
        )

    def test_split_diagram_ids_require_non_empty_derived_suffix(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_empty_split_under_test")
        checked_id = sorted(self.expected_ids())[0]
        artifact = complete_review_artifact(FIXTURE, self.expected_ids())
        artifact["split_diagram_ids"] = [f"{checked_id}::"]

        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)

        self.assertIn(f"split_diagram_ids must use a non-empty derived suffix: {checked_id}::", errors)

    def test_split_diagram_ids_use_longest_checked_prefix_for_overlaps(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_overlap_split_under_test")
        errors = []

        unresolved_ids = phase4._split_ids_are_derived_from_checked(
            {"MER-A::B::"},
            ["MER-A", "MER-A::B"],
            errors,
        )

        self.assertEqual(set(), unresolved_ids)
        self.assertIn("split_diagram_ids must use a non-empty derived suffix: MER-A::B::", errors)

        valid_errors = []
        valid_unresolved_ids = phase4._split_ids_are_derived_from_checked(
            {"MER-A::B::C"},
            ["MER-A", "MER-A::B"],
            valid_errors,
        )

        self.assertEqual(set(), valid_unresolved_ids)
        self.assertEqual([], valid_errors)

    def test_checked_diagram_ids_reject_duplicates(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_duplicate_checked_under_test")
        checked_id = sorted(self.expected_ids())[0]
        artifact = complete_review_artifact(FIXTURE, self.expected_ids())
        artifact["checked_diagram_ids"].append(checked_id)

        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)

        self.assertIn(f"checked_diagram_ids contains duplicate diagram IDs: {checked_id}", errors)

    def test_has_gated_content_matches_foundation_semantics(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_gated_content_semantics_under_test")

        self.assertFalse(phase4.has_gated_content(None))
        self.assertFalse(phase4.has_gated_content(""))
        self.assertFalse(phase4.has_gated_content([]))
        self.assertFalse(phase4.has_gated_content({}))
        self.assertTrue(phase4.has_gated_content([""]))
        self.assertTrue(phase4.has_gated_content({"items": [""]}))
        self.assertTrue(phase4.has_gated_content(0))

    def test_relative_source_dsl_resolves_against_artifact_directory(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_relative_under_test")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            dsl_path = write_json(tmpdir, "structure.dsl.json", valid_document())
            artifact_path = tmpdir / "mermaid-readability-review.json"
            artifact = complete_review_artifact(dsl_path, self.expected_ids())
            artifact["source_dsl"] = "structure.dsl.json"

            errors = phase4.validate_mermaid_review_artifact(
                valid_document(),
                dsl_path,
                artifact,
                artifact_base_dir=artifact_path.parent,
            )

            self.assertEqual([], errors)

    def test_missing_artifact_is_error(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_missing_under_test")

        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, None)

        self.assertIn("readability review artifact is missing", errors)

    def test_mismatched_source_dsl_is_error(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_source_under_test")
        artifact = complete_review_artifact(ROOT / "other.dsl.json", self.expected_ids())

        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)

        self.assertIn(
            "source_dsl does not match the DSL input used for expected diagram collection",
            errors,
        )

    def test_malformed_source_dsl_type_is_error(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_source_type_under_test")
        artifact = complete_review_artifact(FIXTURE, self.expected_ids())
        artifact["source_dsl"] = []

        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)

        self.assertIn("source_dsl must be a non-empty string", errors)

    def test_incomplete_coverage_is_error(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_coverage_under_test")
        expected_ids = self.expected_ids()
        missing_id = sorted(expected_ids)[0]
        artifact = complete_review_artifact(FIXTURE, expected_ids - {missing_id})

        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)

        self.assertTrue(any(missing_id in error for error in errors), errors)

    def test_skipped_diagram_requires_non_empty_reason(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_skip_reason_under_test")
        expected_ids = self.expected_ids()
        skipped_id = sorted(expected_ids)[0]
        artifact = complete_review_artifact(FIXTURE, expected_ids - {skipped_id})
        artifact["skipped_diagrams"] = [{"diagram_id": skipped_id, "reason": " "}]

        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)

        self.assertIn(f"skipped diagram must provide reason: {skipped_id}", errors)

    def test_rendered_diagram_cannot_be_skipped_by_review_artifact(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_rendered_skip_under_test")
        expected_ids = self.expected_ids()
        skipped_id = sorted(expected_ids)[0]
        artifact = complete_review_artifact(FIXTURE, expected_ids - {skipped_id})
        artifact["skipped_diagrams"] = [{"diagram_id": skipped_id, "reason": "not needed"}]

        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)

        self.assertIn(
            "skipped_diagrams contains diagram IDs that cannot be skipped because their owning section is applicable: "
            f"{skipped_id}",
            errors,
        )

    def test_skipped_diagrams_reject_duplicate_ids(self):
        phase4 = load_script("scripts/v2_phase4.py", "v2_phase4_readability_artifact_duplicate_skipped_under_test")
        expected_ids = self.expected_ids()
        skipped_id = sorted(expected_ids)[0]
        artifact = complete_review_artifact(FIXTURE, expected_ids - {skipped_id})
        artifact["skipped_diagrams"] = [
            {"diagram_id": skipped_id, "reason": "not applicable"},
            {"diagram_id": skipped_id, "reason": "duplicate"},
        ]

        errors = phase4.validate_mermaid_review_artifact(valid_document(), FIXTURE, artifact)

        self.assertIn(f"skipped_diagrams contains duplicate diagram IDs: {skipped_id}", errors)

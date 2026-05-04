# create-structure-md Phase 2 DSL Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Phase 1 schema scaffold with a Draft 2020-12 JSON Schema for the complete create-structure-md DSL and provide structurally valid example DSL files.

**Architecture:** Phase 2 keeps validation structural only: `schemas/structure-design.schema.json` defines required fields, object shapes, enums, filename safety, diagram/table object policy, fixed table row shapes, and unknown-field rejection. Cross-object reference existence, one-to-one matching, semantic non-empty rules, Mermaid syntax validation, and Markdown rendering remain out of scope for later phases. Tests live in `tests/test_validate_dsl.py` and use `jsonschema` directly to validate examples and malformed shapes.

**Tech Stack:** Python 3, standard-library `unittest`, `jsonschema` runtime dependency, JSON Schema Draft 2020-12.

---

## Review-Driven Corrections

An adversarial review found that the first draft made Tasks 2-5 depend on example files that were still `{}` until Task 6. This revision fixes that by creating an independent schema test fixture in Task 1. All schema-negative tests must use `valid_example()`, and `valid_example()` must return a deep copy of `tests/fixtures/valid-phase2.dsl.json`, not either file under `examples/`.

This section is authoritative for implementation:

- Every task must be green before its commit. Do not commit intentionally failing tests.
- Any later wording that says a test may pass only after examples are available is obsolete; use the fixture instead.
- The file `tests/fixtures/valid-phase2.dsl.json` is a test-only structural fixture. It should include non-empty rows for chapter 6 tables, collaboration scenarios, and flow branches so item schemas are exercised before examples are rewritten.
- The production examples in `examples/` are still rewritten in Task 6 and validated separately.
- Any instruction below that says “add definitions” must be implemented using the concrete definitions in **Appendix B: Required Schema Definition Details**.
- `extraTableRow` is the only Phase 2 object that may use `additionalProperties: true`; it still must reject `traceability_refs`, `source_snippet_refs`, and validation policy fields such as `required`, `min_rows`, `max_rows`, `empty_allowed`, and `render_when_empty`.
- Declared-column matching for extra table row keys is not expressible with standard JSON Schema because row keys depend on sibling `columns[].key`. This plan intentionally leaves that specific rule to Phase 3 `validate_dsl.py`, matching the full design spec's validator boundary; Phase 2 still models the extra table object and blocks reserved metadata/policy fields.

## File Structure

- Modify: `schemas/structure-design.schema.json`
  - Owns the complete Phase 2 structural schema, `$defs`, top-level required fields, chapter objects, support data objects, diagram/table policies, and `additionalProperties: false` on normal objects.
- Create: `tests/fixtures/valid-phase2.dsl.json`
  - Test-only complete valid DSL fixture used by negative schema tests before production examples are rewritten.
- Modify: `examples/minimal-from-code.dsl.json`
  - A structurally valid code-source example with one module, one runtime unit, one key flow, concrete `document.output_file`, and plausible Mermaid sources.
- Modify: `examples/minimal-from-requirements.dsl.json`
  - A structurally valid requirements-source example with one module, one runtime unit, one key flow, concrete `document.output_file`, and plausible Mermaid sources.
- Modify: `tests/test_validate_dsl.py`
  - Extends Phase 1 tests with schema validity, positive example validation, and negative structural checks.
- Verify only: `requirements.txt`
  - Must still contain only `jsonschema`.

Implementation constraint from the workspace instructions: do not run deletion commands such as `rm`, `rmdir`, `git clean`, `git reset --hard`, or checkout commands that discard files. If cleanup is needed, provide the command for the user to run.

Use the agent Python if bare `python` is unavailable:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl -v
```

---

### Task 1: Schema Test Harness And Root Contract

**Files:**
- Modify: `tests/test_validate_dsl.py`
- Modify: `schemas/structure-design.schema.json`
- Create: `tests/fixtures/valid-phase2.dsl.json`

- [ ] **Step 1: Write the failing schema harness tests**

Append these imports near the top of `tests/test_validate_dsl.py`:

```python
from copy import deepcopy

from jsonschema import Draft202012Validator
```

Append these constants and helpers after `SCRIPT_CASES`:

```python
SCHEMA_PATH = ROOT / "schemas/structure-design.schema.json"
EXAMPLE_PATHS = [
    ROOT / "examples/minimal-from-code.dsl.json",
    ROOT / "examples/minimal-from-requirements.dsl.json",
]

TOP_LEVEL_FIELDS = [
    "dsl_version",
    "document",
    "system_overview",
    "architecture_views",
    "module_design",
    "runtime_view",
    "configuration_data_dependencies",
    "cross_module_collaboration",
    "key_flows",
    "structure_issues_and_suggestions",
    "evidence",
    "traceability",
    "risks",
    "assumptions",
    "source_snippets",
]


def load_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validator():
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validator_for_def(def_name):
    schema = load_schema()
    def_schema = {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        "$ref": f"#/$defs/{def_name}",
    }
    Draft202012Validator.check_schema(def_schema)
    return Draft202012Validator(def_schema)


def valid_example():
    return deepcopy(load_json("tests/fixtures/valid-phase2.dsl.json"))


def validation_errors(document):
    errors = sorted(validator().iter_errors(document), key=lambda error: list(error.path))
    return errors


def matching_errors(errors, expected_fragment=None, expected_validator=None, expected_path=None):
    matches = []
    for error in errors:
        if expected_fragment is not None and expected_fragment not in error.message:
            continue
        if expected_validator is not None and error.validator != expected_validator:
            continue
        if expected_path is not None and list(error.path) != expected_path:
            continue
        matches.append(error)
    return matches


def assert_invalid(testcase, document, expected_fragment=None, *, expected_validator=None, expected_path=None):
    errors = validation_errors(document)
    testcase.assertTrue(errors, "Expected schema validation to fail")
    if expected_fragment is not None or expected_validator is not None or expected_path is not None:
        testcase.assertTrue(
            matching_errors(errors, expected_fragment, expected_validator, expected_path),
            "Expected one error to match all requested criteria; got "
            f"{[(error.message, error.validator, list(error.path)) for error in errors]}",
        )


def assert_invalid_def(testcase, def_name, value, expected_fragment=None, *, expected_validator=None, expected_path=None):
    errors = sorted(validator_for_def(def_name).iter_errors(value), key=lambda error: list(error.path))
    testcase.assertTrue(errors, f"Expected #/$defs/{def_name} validation to fail")
    if expected_fragment is not None or expected_validator is not None or expected_path is not None:
        testcase.assertTrue(
            matching_errors(errors, expected_fragment, expected_validator, expected_path),
            "Expected one error to match all requested criteria; got "
            f"{[(error.message, error.validator, list(error.path)) for error in errors]}",
        )
```

Append this test class:

```python
class SchemaRootContractTests(unittest.TestCase):
    def test_schema_is_valid_draft_2020_12_schema(self):
        Draft202012Validator.check_schema(load_schema())

    def test_root_requires_all_top_level_fields(self):
        schema = load_schema()
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
        self.assertCountEqual(TOP_LEVEL_FIELDS, schema["required"])
        self.assertFalse(schema["additionalProperties"])

    def test_fixture_passes_root_shell_validation(self):
        validator().validate(valid_example())

    def test_unknown_top_level_field_fails(self):
        document = valid_example()
        document["required_tables"] = []
        assert_invalid(
            self,
            document,
            "Additional properties are not allowed",
            expected_validator="additionalProperties",
            expected_path=[],
        )

    def test_validation_policy_fields_fail_at_top_level(self):
        for forbidden in ["empty_allowed", "required", "min_rows", "max_rows", "render_when_empty"]:
            document = valid_example()
            document[forbidden] = True
            with self.subTest(field=forbidden):
                assert_invalid(
                    self,
                    document,
                    "Additional properties are not allowed",
                    expected_validator="additionalProperties",
                    expected_path=[],
                )
```

- [ ] **Step 2: Run the schema harness tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaRootContractTests -v
```

Expected: FAIL because the Phase 1 schema has no `$defs`, no top-level required contract, and `tests/fixtures/valid-phase2.dsl.json` does not exist yet.

- [ ] **Step 3: Create the test fixture and implement the root schema shell**

Create the parent directory if it is absent:

```bash
mkdir -p tests/fixtures
```

Then create `tests/fixtures/valid-phase2.dsl.json` with the complete JSON object in **Appendix A: Complete Valid Phase 2 Test Fixture**. This is not copied from `examples/`; it is a test-only fixture and must exist before any Tasks 2-5 tests run.

Replace `schemas/structure-design.schema.json` with this root shell. Later tasks fill the `$defs` targets used here.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://local/create-structure-md/schemas/structure-design.schema.json",
  "title": "create-structure-md Structure Design DSL",
  "type": "object",
  "required": [
    "dsl_version",
    "document",
    "system_overview",
    "architecture_views",
    "module_design",
    "runtime_view",
    "configuration_data_dependencies",
    "cross_module_collaboration",
    "key_flows",
    "structure_issues_and_suggestions",
    "evidence",
    "traceability",
    "risks",
    "assumptions",
    "source_snippets"
  ],
  "additionalProperties": false,
  "properties": {
    "dsl_version": { "$ref": "#/$defs/nonEmptyString" },
    "document": { "$ref": "#/$defs/document" },
    "system_overview": { "$ref": "#/$defs/systemOverview" },
    "architecture_views": { "$ref": "#/$defs/architectureViews" },
    "module_design": { "$ref": "#/$defs/moduleDesign" },
    "runtime_view": { "$ref": "#/$defs/runtimeView" },
    "configuration_data_dependencies": { "$ref": "#/$defs/configurationDataDependencies" },
    "cross_module_collaboration": { "$ref": "#/$defs/crossModuleCollaboration" },
    "key_flows": { "$ref": "#/$defs/keyFlows" },
    "structure_issues_and_suggestions": { "type": "string" },
    "evidence": { "type": "array", "items": { "$ref": "#/$defs/evidence" } },
    "traceability": { "type": "array", "items": { "$ref": "#/$defs/traceability" } },
    "risks": { "type": "array", "items": { "$ref": "#/$defs/risk" } },
    "assumptions": { "type": "array", "items": { "$ref": "#/$defs/assumption" } },
    "source_snippets": { "type": "array", "items": { "$ref": "#/$defs/sourceSnippet" } }
  },
  "$defs": {
    "nonEmptyString": { "type": "string", "minLength": 1 },
    "stringArray": {
      "type": "array",
      "items": { "$ref": "#/$defs/nonEmptyString" }
    },
    "referenceArray": {
      "type": "array",
      "items": { "$ref": "#/$defs/nonEmptyString" }
    },
    "confidence": {
      "type": "string",
      "enum": ["observed", "inferred", "unknown"]
    }
  }
}
```

In the same edit, add permissive intermediate `$defs` for every referenced definition so fixture validation can resolve `$ref` targets while subsequent tasks replace each permissive definition with its concrete contract. `Draft202012Validator.check_schema()` checks schema shape; the root-contract validation tests are what exercise these references against the fixture:

```json
"document": { "type": "object" },
"systemOverview": { "type": "object" },
"architectureViews": { "type": "object" },
"moduleDesign": { "type": "object" },
"runtimeView": { "type": "object" },
"configurationDataDependencies": { "type": "object" },
"crossModuleCollaboration": { "type": "object" },
"keyFlows": { "type": "object" },
"evidence": { "type": "object" },
"traceability": { "type": "object" },
"risk": { "type": "object" },
"assumption": { "type": "object" },
"sourceSnippet": { "type": "object" },
"safeMarkdownFilename": { "type": "string" },
"diagram": { "type": "object" },
"extraTableColumn": { "type": "object" },
"extraTableRow": { "type": "object" },
"extraTable": { "type": "object" },
"extraTables": { "type": "array" },
"extraDiagrams": { "type": "array" }
```

These permissive definitions are a Task 1 bridge only and must all be replaced by concrete definitions before Phase 2 is complete.

- [ ] **Step 4: Run the schema harness tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaRootContractTests -v
```

Expected: PASS. `valid_example()` reads `tests/fixtures/valid-phase2.dsl.json`, so these tests must not depend on the production examples under `examples/`.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_validate_dsl.py schemas/structure-design.schema.json tests/fixtures/valid-phase2.dsl.json
git -c user.name=Codex -c user.email=codex@local commit -m "test: add schema root contract"
```

Expected: commit succeeds with schema root tests, schema shell, and the valid test fixture staged.

---

### Task 2: Common Definitions, Document, Diagrams, And Tables

**Files:**
- Modify: `tests/test_validate_dsl.py`
- Modify: `schemas/structure-design.schema.json`

- [ ] **Step 1: Write failing tests for common structural rules**

Append this class to `tests/test_validate_dsl.py`:

```python
class SchemaCommonShapeTests(unittest.TestCase):
    def test_fixture_passes_with_common_definitions(self):
        validator().validate(valid_example())

    def test_structurally_unsafe_output_filenames_fail(self):
        invalid_names = [
            "create-structure-md_STRUCTURE_DESIGN.txt",
            "nested/create-structure-md_STRUCTURE_DESIGN.md",
            "nested\\create-structure-md_STRUCTURE_DESIGN.md",
            "../create-structure-md_STRUCTURE_DESIGN.md",
            "bad..name.md",
            "bad\u0001name.md",
        ]
        for output_file in invalid_names:
            document = valid_example()
            document["document"]["output_file"] = output_file
            with self.subTest(output_file=output_file):
                assert_invalid(
                    self,
                    document,
                    "does not match",
                    expected_path=["document", "output_file"],
                )

    def test_empty_diagram_object_fails_when_optional_field_is_present(self):
        assert_invalid_def(
            self,
            "diagram",
            {},
            "is a required property",
            expected_validator="required",
            expected_path=[],
        )

    def test_extra_table_rows_reject_traceability_and_source_snippet_refs(self):
        for forbidden in ["traceability_refs", "source_snippet_refs"]:
            extra_table = {
                "id": "TBL-ARCH-001",
                "title": "补充表格",
                "columns": [{"key": "name", "title": "名称"}],
                "rows": [{"name": "示例", forbidden: ["TR-001"]}]
            }
            with self.subTest(field=forbidden):
                assert_invalid_def(
                    self,
                    "extraTable",
                    extra_table,
                    "should not be valid",
                    expected_validator="not",
                    expected_path=["rows", 0],
                )

    def test_extra_table_evidence_refs_must_be_reference_array(self):
        extra_table = {
            "id": "TBL-ARCH-001",
            "title": "补充表格",
            "columns": [{"key": "name", "title": "名称"}],
            "rows": [{"name": "示例", "evidence_refs": [1]}]
        }
        assert_invalid_def(
            self,
            "extraTable",
            extra_table,
            "is not of type 'string'",
            expected_validator="type",
            expected_path=["rows", 0, "evidence_refs", 0],
        )

    def test_extra_table_rows_reject_validation_policy_fields(self):
        for forbidden in ["required", "min_rows", "max_rows", "empty_allowed", "render_when_empty"]:
            extra_table = {
                "id": "TBL-ARCH-001",
                "title": "补充表格",
                "columns": [{"key": "name", "title": "名称"}],
                "rows": [{"name": "示例", forbidden: True}]
            }
            with self.subTest(field=forbidden):
                assert_invalid_def(
                    self,
                    "extraTable",
                    extra_table,
                    "should not be valid",
                    expected_validator="not",
                    expected_path=["rows", 0],
                )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaCommonShapeTests -v
```

Expected: FAIL because the common definitions, document object, diagram object, and extra table row restrictions are not fully modeled yet.

- [ ] **Step 3: Implement common `$defs`**

Replace the relevant `$defs` in `schemas/structure-design.schema.json` with these exact contracts:

```json
"safeMarkdownFilename": {
  "type": "string",
  "minLength": 4,
  "allOf": [
    { "pattern": "^[^/\\\\\\u0000-\\u001f]+\\.md$" },
    { "not": { "pattern": "\\.\\." } }
  ]
},
"diagram": {
  "type": "object",
  "required": ["id", "kind", "title", "diagram_type", "description", "source", "confidence"],
  "additionalProperties": false,
  "properties": {
    "id": { "$ref": "#/$defs/nonEmptyString" },
    "kind": { "$ref": "#/$defs/nonEmptyString" },
    "title": { "$ref": "#/$defs/nonEmptyString" },
    "diagram_type": {
      "type": "string",
      "enum": ["flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram-v2"]
    },
    "description": { "type": "string" },
    "source": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" }
  }
},
"extraTableColumn": {
  "type": "object",
  "required": ["key", "title"],
  "additionalProperties": false,
  "properties": {
    "key": { "$ref": "#/$defs/nonEmptyString" },
    "title": { "$ref": "#/$defs/nonEmptyString" }
  }
},
"extraTableRow": {
  "type": "object",
  "not": {
    "anyOf": [
      { "required": ["traceability_refs"] },
      { "required": ["source_snippet_refs"] },
      { "required": ["required"] },
      { "required": ["min_rows"] },
      { "required": ["max_rows"] },
      { "required": ["empty_allowed"] },
      { "required": ["render_when_empty"] }
    ]
  },
  "properties": {
    "evidence_refs": { "$ref": "#/$defs/referenceArray" }
  },
  "additionalProperties": true
},
"extraTable": {
  "type": "object",
  "required": ["id", "title", "columns", "rows"],
  "additionalProperties": false,
  "properties": {
    "id": { "$ref": "#/$defs/nonEmptyString" },
    "title": { "$ref": "#/$defs/nonEmptyString" },
    "columns": {
      "type": "array",
      "items": { "$ref": "#/$defs/extraTableColumn" }
    },
    "rows": {
      "type": "array",
      "items": { "$ref": "#/$defs/extraTableRow" }
    }
  }
},
"extraTables": {
  "type": "array",
  "items": { "$ref": "#/$defs/extraTable" }
},
"extraDiagrams": {
  "type": "array",
  "items": { "$ref": "#/$defs/diagram" }
},
"document": {
  "type": "object",
  "required": [
    "title",
    "project_name",
    "project_version",
    "document_version",
    "status",
    "generated_at",
    "generated_by",
    "language",
    "source_type",
    "scope_summary",
    "not_applicable_policy",
    "output_file"
  ],
  "additionalProperties": false,
  "properties": {
    "title": { "$ref": "#/$defs/nonEmptyString" },
    "project_name": { "$ref": "#/$defs/nonEmptyString" },
    "project_version": { "type": "string" },
    "document_version": { "$ref": "#/$defs/nonEmptyString" },
    "status": { "type": "string", "enum": ["draft", "reviewed", "final"] },
    "generated_at": { "type": "string" },
    "generated_by": { "type": "string" },
    "language": { "$ref": "#/$defs/nonEmptyString" },
    "source_type": { "type": "string", "enum": ["code", "requirements", "mixed", "notes"] },
    "scope_summary": { "type": "string" },
    "not_applicable_policy": { "type": "string" },
    "output_file": { "$ref": "#/$defs/safeMarkdownFilename" }
  }
}
```

Implementation note: `extraTableRow.additionalProperties: true` is the only Phase 2 extension point. JSON Schema cannot compare row keys to sibling `columns[].key`; Phase 3 semantic validation owns undeclared column-key rejection in `validate_dsl.py`. Phase 2 must still reject `traceability_refs`, `source_snippet_refs`, and validation policy fields on extra table rows.

- [ ] **Step 4: Run the common shape tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaCommonShapeTests -v
```

Expected: PASS because `valid_example()` reads the complete fixture created in Task 1.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_validate_dsl.py schemas/structure-design.schema.json
git -c user.name=Codex -c user.email=codex@local commit -m "feat: add common schema definitions"
```

Expected: commit succeeds with common schema definitions and tests staged.

---

### Task 3: Chapters 2 Through 4 Schema

**Files:**
- Modify: `tests/test_validate_dsl.py`
- Modify: `schemas/structure-design.schema.json`

- [ ] **Step 1: Write failing tests for chapter 2-4 shape**

Append this class:

```python
class SchemaChapterTwoThroughFourTests(unittest.TestCase):
    def test_fixture_passes_with_chapter_two_through_four_schema(self):
        validator().validate(valid_example())

    def test_chapter_two_rejects_unknown_capability_field(self):
        document = valid_example()
        document["system_overview"]["core_capabilities"][0]["surprise_id"] = "CAP-BAD"
        assert_invalid(
            self,
            document,
            "Additional properties are not allowed",
            expected_validator="additionalProperties",
            expected_path=["system_overview", "core_capabilities", 0],
        )

    def test_module_intro_rejects_fixed_table_id_title_or_columns(self):
        for forbidden in ["id", "title", "columns"]:
            document = valid_example()
            document["architecture_views"]["module_intro"][forbidden] = forbidden
            with self.subTest(field=forbidden):
                assert_invalid(
                    self,
                    document,
                    "Additional properties are not allowed",
                    expected_validator="additionalProperties",
                    expected_path=["architecture_views", "module_intro"],
                )

    def test_module_design_module_id_is_modeled_reference_field(self):
        document = valid_example()
        document["module_design"]["modules"][0]["module_id"] = ""
        assert_invalid(
            self,
            document,
            "should be non-empty",
            expected_validator="minLength",
            expected_path=["module_design", "modules", 0, "module_id"],
        )

    def test_internal_structure_diagram_rejects_empty_object(self):
        document = valid_example()
        document["module_design"]["modules"][0]["internal_structure"]["diagram"] = {}
        assert_invalid(
            self,
            document,
            "is a required property",
            expected_validator="required",
            expected_path=["module_design", "modules", 0, "internal_structure", "diagram"],
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaChapterTwoThroughFourTests -v
```

Expected: FAIL until the chapter 2-4 schemas and fixed row shapes are modeled.

- [ ] **Step 3: Implement chapter 2-4 `$defs`**

Add or replace these definitions:

```json
"capability": {
  "type": "object",
  "required": ["capability_id", "name", "description", "confidence"],
  "additionalProperties": false,
  "properties": {
    "capability_id": { "$ref": "#/$defs/nonEmptyString" },
    "name": { "$ref": "#/$defs/nonEmptyString" },
    "description": { "$ref": "#/$defs/nonEmptyString" },
    "confidence": { "$ref": "#/$defs/confidence" }
  }
},
"systemOverview": {
  "type": "object",
  "required": ["summary", "purpose", "core_capabilities", "notes"],
  "additionalProperties": false,
  "properties": {
    "summary": { "$ref": "#/$defs/nonEmptyString" },
    "purpose": { "$ref": "#/$defs/nonEmptyString" },
    "core_capabilities": { "type": "array", "items": { "$ref": "#/$defs/capability" } },
    "notes": { "$ref": "#/$defs/stringArray" }
  }
},
"moduleIntroRow": {
  "type": "object",
  "required": ["module_id", "module_name", "responsibility", "inputs", "outputs", "notes", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "module_id": { "$ref": "#/$defs/nonEmptyString" },
    "module_name": { "$ref": "#/$defs/nonEmptyString" },
    "responsibility": { "$ref": "#/$defs/nonEmptyString" },
    "inputs": { "type": "string" },
    "outputs": { "type": "string" },
    "notes": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"moduleIntroTable": {
  "type": "object",
  "required": ["rows"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/moduleIntroRow" } }
  }
},
"architectureViews": {
  "type": "object",
  "required": ["summary", "notes", "module_intro", "module_relationship_diagram", "extra_tables", "extra_diagrams"],
  "additionalProperties": false,
  "properties": {
    "summary": { "$ref": "#/$defs/nonEmptyString" },
    "notes": { "$ref": "#/$defs/stringArray" },
    "module_intro": { "$ref": "#/$defs/moduleIntroTable" },
    "module_relationship_diagram": { "$ref": "#/$defs/diagram" },
    "extra_tables": { "$ref": "#/$defs/extraTables" },
    "extra_diagrams": { "$ref": "#/$defs/extraDiagrams" }
  }
}
```

Add module design definitions:

```json
"providedCapabilityRow": {
  "type": "object",
  "required": ["capability_id", "capability_name", "interface_style", "description", "inputs", "outputs", "notes", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "capability_id": { "$ref": "#/$defs/nonEmptyString" },
    "capability_name": { "$ref": "#/$defs/nonEmptyString" },
    "interface_style": { "type": "string" },
    "description": { "$ref": "#/$defs/nonEmptyString" },
    "inputs": { "type": "string" },
    "outputs": { "type": "string" },
    "notes": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"providedCapabilitiesTable": {
  "type": "object",
  "required": ["rows"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/providedCapabilityRow" } }
  }
},
"externalCapabilitySummary": {
  "type": "object",
  "required": ["description", "consumers", "interface_style", "boundary_notes"],
  "additionalProperties": false,
  "properties": {
    "description": { "$ref": "#/$defs/nonEmptyString" },
    "consumers": { "$ref": "#/$defs/stringArray" },
    "interface_style": { "type": "string" },
    "boundary_notes": { "$ref": "#/$defs/stringArray" }
  }
},
"externalCapabilityDetails": {
  "type": "object",
  "required": ["provided_capabilities", "extra_tables", "extra_diagrams"],
  "additionalProperties": false,
  "properties": {
    "provided_capabilities": { "$ref": "#/$defs/providedCapabilitiesTable" },
    "extra_tables": { "$ref": "#/$defs/extraTables" },
    "extra_diagrams": { "$ref": "#/$defs/extraDiagrams" }
  }
},
"internalStructure": {
  "type": "object",
  "required": ["summary", "diagram", "textual_structure", "not_applicable_reason"],
  "additionalProperties": false,
  "properties": {
    "summary": { "$ref": "#/$defs/nonEmptyString" },
    "diagram": { "$ref": "#/$defs/diagram" },
    "textual_structure": { "type": "string" },
    "not_applicable_reason": { "type": "string" }
  }
},
"moduleDesignItem": {
  "type": "object",
  "required": ["module_id", "name", "summary", "responsibilities", "external_capability_summary", "external_capability_details", "internal_structure", "extra_tables", "extra_diagrams", "evidence_refs", "traceability_refs", "source_snippet_refs", "notes", "confidence"],
  "additionalProperties": false,
  "properties": {
    "module_id": { "$ref": "#/$defs/nonEmptyString" },
    "name": { "$ref": "#/$defs/nonEmptyString" },
    "summary": { "$ref": "#/$defs/nonEmptyString" },
    "responsibilities": { "$ref": "#/$defs/stringArray" },
    "external_capability_summary": { "$ref": "#/$defs/externalCapabilitySummary" },
    "external_capability_details": { "$ref": "#/$defs/externalCapabilityDetails" },
    "internal_structure": { "$ref": "#/$defs/internalStructure" },
    "extra_tables": { "$ref": "#/$defs/extraTables" },
    "extra_diagrams": { "$ref": "#/$defs/extraDiagrams" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" },
    "notes": { "$ref": "#/$defs/stringArray" },
    "confidence": { "$ref": "#/$defs/confidence" }
  }
},
"moduleDesign": {
  "type": "object",
  "required": ["summary", "notes", "modules"],
  "additionalProperties": false,
  "properties": {
    "summary": { "$ref": "#/$defs/nonEmptyString" },
    "notes": { "$ref": "#/$defs/stringArray" },
    "modules": { "type": "array", "items": { "$ref": "#/$defs/moduleDesignItem" } }
  }
}
```

- [ ] **Step 4: Run chapter 2-4 tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaChapterTwoThroughFourTests -v
```

Expected: PASS because `valid_example()` reads the complete fixture created in Task 1.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_validate_dsl.py schemas/structure-design.schema.json
git -c user.name=Codex -c user.email=codex@local commit -m "feat: add chapter 2 through 4 schema"
```

Expected: commit succeeds with chapter 2-4 schema and tests staged.

---

### Task 4: Chapters 5 Through 9 Schema

**Files:**
- Modify: `tests/test_validate_dsl.py`
- Modify: `schemas/structure-design.schema.json`

- [ ] **Step 1: Write failing tests for chapter 5-9 shape**

Append this class:

```python
class SchemaChapterFiveThroughNineTests(unittest.TestCase):
    def test_fixture_passes_with_chapter_five_through_nine_schema(self):
        validator().validate(valid_example())

    def test_runtime_related_module_ids_are_string_arrays(self):
        document = valid_example()
        document["runtime_view"]["runtime_units"]["rows"][0]["related_module_ids"] = [1]
        assert_invalid(
            self,
            document,
            "is not of type 'string'",
            expected_validator="type",
            expected_path=["runtime_view", "runtime_units", "rows", 0, "related_module_ids", 0],
        )

    def test_collaboration_optional_diagram_allows_omission_but_rejects_empty_object(self):
        document = valid_example()
        document["cross_module_collaboration"].pop("collaboration_relationship_diagram", None)
        validator().validate(document)

        document = valid_example()
        document["cross_module_collaboration"]["collaboration_relationship_diagram"] = {}
        assert_invalid(
            self,
            document,
            "is a required property",
            expected_validator="required",
            expected_path=["cross_module_collaboration", "collaboration_relationship_diagram"],
        )

    def test_runtime_optional_sequence_diagram_rejects_empty_object(self):
        document = valid_example()
        document["runtime_view"]["runtime_sequence_diagram"] = {}
        assert_invalid(
            self,
            document,
            "is a required property",
            expected_validator="required",
            expected_path=["runtime_view", "runtime_sequence_diagram"],
        )

    def test_flow_index_rejects_common_metadata(self):
        for forbidden in ["confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"]:
            document = valid_example()
            document["key_flows"]["flow_index"]["rows"][0][forbidden] = "observed"
            with self.subTest(field=forbidden):
                assert_invalid(
                    self,
                    document,
                    "Additional properties are not allowed",
                    expected_validator="additionalProperties",
                    expected_path=["key_flows", "flow_index", "rows", 0],
                )

    def test_flow_step_order_must_be_positive_integer(self):
        document = valid_example()
        document["key_flows"]["flows"][0]["steps"][0]["order"] = 0
        assert_invalid(
            self,
            document,
            "is less than the minimum",
            expected_validator="minimum",
            expected_path=["key_flows", "flows", 0, "steps", 0, "order"],
        )

    def test_chapter_six_rows_reject_unknown_id_fields(self):
        cases = [
            ("configuration_items", "unknown_id"),
            ("structural_data_artifacts", "owner_module_id"),
            ("dependencies", "dependency_ids"),
        ]
        for table_name, field_name in cases:
            document = valid_example()
            document["configuration_data_dependencies"][table_name]["rows"][0][field_name] = "BAD-001"
            with self.subTest(table=table_name, field=field_name):
                assert_invalid(
                    self,
                    document,
                    "Additional properties are not allowed",
                    expected_validator="additionalProperties",
                    expected_path=["configuration_data_dependencies", table_name, "rows", 0],
                )

    def test_collaboration_row_rejects_unknown_reference_fields(self):
        document = valid_example()
        document["cross_module_collaboration"]["collaboration_scenarios"]["rows"][0]["participant_ids"] = ["MOD-SKILL"]
        assert_invalid(
            self,
            document,
            "Additional properties are not allowed",
            expected_validator="additionalProperties",
            expected_path=["cross_module_collaboration", "collaboration_scenarios", "rows", 0],
        )

    def test_flow_branch_related_runtime_unit_ids_must_be_string_arrays(self):
        document = valid_example()
        document["key_flows"]["flows"][0]["branches_or_exceptions"][0]["related_runtime_unit_ids"] = [1]
        assert_invalid(
            self,
            document,
            "is not of type 'string'",
            expected_validator="type",
            expected_path=["key_flows", "flows", 0, "branches_or_exceptions", 0, "related_runtime_unit_ids", 0],
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaChapterFiveThroughNineTests -v
```

Expected: FAIL until chapters 5-9 are modeled.

- [ ] **Step 3: Implement chapter 5-9 `$defs`**

Add definitions for runtime, chapter 6 tables, collaboration, and key flows. These definitions must use `additionalProperties: false` on every normal object and must model every `_id`/`_ids` field named by the Phase 2 spec.

Use this shape for runtime:

```json
"runtimeUnitRow": {
  "type": "object",
  "required": ["unit_id", "unit_name", "unit_type", "entrypoint", "entrypoint_not_applicable_reason", "responsibility", "related_module_ids", "external_environment_reason", "notes", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "unit_id": { "$ref": "#/$defs/nonEmptyString" },
    "unit_name": { "$ref": "#/$defs/nonEmptyString" },
    "unit_type": { "$ref": "#/$defs/nonEmptyString" },
    "entrypoint": { "type": "string" },
    "entrypoint_not_applicable_reason": { "type": "string" },
    "responsibility": { "$ref": "#/$defs/nonEmptyString" },
    "related_module_ids": { "$ref": "#/$defs/referenceArray" },
    "external_environment_reason": { "type": "string" },
    "notes": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"runtimeUnitsTable": {
  "type": "object",
  "required": ["rows"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/runtimeUnitRow" } }
  }
},
"runtimeView": {
  "type": "object",
  "required": ["summary", "notes", "runtime_units", "runtime_flow_diagram", "extra_tables", "extra_diagrams"],
  "additionalProperties": false,
  "properties": {
    "summary": { "$ref": "#/$defs/nonEmptyString" },
    "notes": { "$ref": "#/$defs/stringArray" },
    "runtime_units": { "$ref": "#/$defs/runtimeUnitsTable" },
    "runtime_flow_diagram": { "$ref": "#/$defs/diagram" },
    "runtime_sequence_diagram": { "$ref": "#/$defs/diagram" },
    "extra_tables": { "$ref": "#/$defs/extraTables" },
    "extra_diagrams": { "$ref": "#/$defs/extraDiagrams" }
  }
}
```

Use this shape for chapter 6 rows:

```json
"configurationItemRow": {
  "type": "object",
  "required": ["config_id", "config_name", "source", "used_by", "purpose", "notes", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "config_id": { "$ref": "#/$defs/nonEmptyString" },
    "config_name": { "$ref": "#/$defs/nonEmptyString" },
    "source": { "type": "string" },
    "used_by": { "type": "string" },
    "purpose": { "$ref": "#/$defs/nonEmptyString" },
    "notes": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
}
```

Add the concrete `structuralDataArtifactRow`, `dependencyRow`, fixed table wrapper, collaboration, and key-flow definitions from **Appendix B: Required Schema Definition Details**. Then implement:

```json
"configurationDataDependencies": {
  "type": "object",
  "required": ["summary", "notes", "configuration_items", "structural_data_artifacts", "dependencies", "extra_tables", "extra_diagrams"],
  "additionalProperties": false,
  "properties": {
    "summary": { "type": "string" },
    "notes": { "$ref": "#/$defs/stringArray" },
    "configuration_items": { "$ref": "#/$defs/configurationItemsTable" },
    "structural_data_artifacts": { "$ref": "#/$defs/structuralDataArtifactsTable" },
    "dependencies": { "$ref": "#/$defs/dependenciesTable" },
    "extra_tables": { "$ref": "#/$defs/extraTables" },
    "extra_diagrams": { "$ref": "#/$defs/extraDiagrams" }
  }
}
```

For chapter 7, model `collaboration_relationship_diagram` as optional:

```json
"crossModuleCollaboration": {
  "type": "object",
  "required": ["summary", "notes", "collaboration_scenarios", "extra_tables", "extra_diagrams"],
  "additionalProperties": false,
  "properties": {
    "summary": { "type": "string" },
    "notes": { "$ref": "#/$defs/stringArray" },
    "collaboration_scenarios": { "$ref": "#/$defs/collaborationScenariosTable" },
    "collaboration_relationship_diagram": { "$ref": "#/$defs/diagram" },
    "extra_tables": { "$ref": "#/$defs/extraTables" },
    "extra_diagrams": { "$ref": "#/$defs/extraDiagrams" }
  }
}
```

For chapter 8, ensure `flowIndexRow` has no common metadata properties:

```json
"flowIndexRow": {
  "type": "object",
  "required": ["flow_id", "flow_name", "trigger_condition", "participant_module_ids", "participant_runtime_unit_ids", "main_steps", "output_result", "notes"],
  "additionalProperties": false,
  "properties": {
    "flow_id": { "$ref": "#/$defs/nonEmptyString" },
    "flow_name": { "$ref": "#/$defs/nonEmptyString" },
    "trigger_condition": { "$ref": "#/$defs/nonEmptyString" },
    "participant_module_ids": { "$ref": "#/$defs/referenceArray" },
    "participant_runtime_unit_ids": { "$ref": "#/$defs/referenceArray" },
    "main_steps": { "$ref": "#/$defs/nonEmptyString" },
    "output_result": { "$ref": "#/$defs/nonEmptyString" },
    "notes": { "type": "string" }
  }
},
"flowStep": {
  "type": "object",
  "required": ["step_id", "order", "description", "actor", "related_module_ids", "related_runtime_unit_ids", "input", "output", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "step_id": { "$ref": "#/$defs/nonEmptyString" },
    "order": { "type": "integer", "minimum": 1 },
    "description": { "$ref": "#/$defs/nonEmptyString" },
    "actor": { "type": "string" },
    "related_module_ids": { "$ref": "#/$defs/referenceArray" },
    "related_runtime_unit_ids": { "$ref": "#/$defs/referenceArray" },
    "input": { "type": "string" },
    "output": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
}
```

Add `flowBranch`, `keyFlow`, `flowIndexTable`, and `keyFlows` exactly as shown in **Appendix B: Required Schema Definition Details**. `keyFlow.diagram` is required and must be a full `diagram` object.

- [ ] **Step 4: Run chapter 5-9 tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaChapterFiveThroughNineTests -v
```

Expected: PASS because `valid_example()` reads the complete fixture created in Task 1.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_validate_dsl.py schemas/structure-design.schema.json
git -c user.name=Codex -c user.email=codex@local commit -m "feat: add chapter 5 through 9 schema"
```

Expected: commit succeeds with chapter 5-9 schema and tests staged.

---

### Task 5: Support Data Schemas And Negative Shape Tests

**Files:**
- Modify: `tests/test_validate_dsl.py`
- Modify: `schemas/structure-design.schema.json`

- [ ] **Step 1: Write failing support data tests**

Append this class:

```python
class SchemaSupportDataTests(unittest.TestCase):
    def test_fixture_passes_with_support_data_schema(self):
        validator().validate(valid_example())

    def test_support_data_objects_accept_valid_shapes(self):
        document = valid_example()
        document["evidence"] = [
            {
                "id": "EV-001",
                "kind": "source",
                "title": "入口脚本",
                "location": "scripts/render_markdown.py",
                "description": "渲染入口脚本。",
                "confidence": "observed"
            }
        ]
        document["traceability"] = [
            {
                "id": "TR-001",
                "source_external_id": "REQ-001",
                "source_type": "requirement",
                "target_type": "module",
                "target_id": "MOD-SKILL",
                "description": "需求映射到技能模块。"
            }
        ]
        document["risks"] = [
            {
                "id": "RISK-001",
                "description": "示例风险。",
                "impact": "影响文档完整性。",
                "mitigation": "通过校验发现。",
                "confidence": "inferred",
                "evidence_refs": ["EV-001"],
                "traceability_refs": ["TR-001"],
                "source_snippet_refs": ["SNIP-001"]
            }
        ]
        document["assumptions"] = [
            {
                "id": "ASM-001",
                "description": "示例假设。",
                "rationale": "用于验证 support data schema。",
                "validation_suggestion": "执行语义校验。",
                "confidence": "unknown",
                "evidence_refs": ["EV-001"],
                "traceability_refs": ["TR-001"],
                "source_snippet_refs": ["SNIP-001"]
            }
        ]
        document["source_snippets"] = [
            {
                "id": "SNIP-001",
                "path": "scripts/render_markdown.py",
                "line_start": 1,
                "line_end": 2,
                "language": "python",
                "purpose": "说明脚本入口。",
                "content": "#!/usr/bin/env python3\n",
                "confidence": "observed"
            }
        ]
        validator().validate(document)

    def test_support_data_objects_reject_unknown_fields(self):
        cases = [
            ("evidence", {"id": "EV-001", "kind": "source", "title": "", "location": "", "description": "", "confidence": "observed"}),
            ("traceability", {"id": "TR-001", "source_external_id": "REQ-001", "source_type": "requirement", "target_type": "module", "target_id": "MOD-001", "description": ""}),
            ("risks", {"id": "RISK-001", "description": "", "impact": "", "mitigation": "", "confidence": "inferred", "evidence_refs": [], "traceability_refs": [], "source_snippet_refs": []}),
            ("assumptions", {"id": "ASM-001", "description": "", "rationale": "", "validation_suggestion": "", "confidence": "unknown", "evidence_refs": [], "traceability_refs": [], "source_snippet_refs": []}),
            ("source_snippets", {"id": "SNIP-001", "path": "src/main.py", "line_start": 1, "line_end": 1, "language": "python", "purpose": "", "content": "print('x')", "confidence": "observed"}),
        ]
        for field, item in cases:
            document = valid_example()
            item = dict(item)
            item["unexpected"] = True
            document[field] = [item]
            with self.subTest(field=field):
                assert_invalid(
                    self,
                    document,
                    "Additional properties are not allowed",
                    expected_validator="additionalProperties",
                    expected_path=[field, 0],
                )

    def test_source_snippet_line_numbers_must_be_positive_integers(self):
        invalid_values = [
            (0, "minimum"),
            (-1, "minimum"),
            ("1", "type"),
        ]
        for field_name in ["line_start", "line_end"]:
            for value, expected_validator in invalid_values:
                document = valid_example()
                snippet = {
                    "id": "SNIP-001",
                    "path": "src/main.py",
                    "line_start": 1,
                    "line_end": 1,
                    "language": "python",
                    "purpose": "证明入口",
                    "content": "print('x')",
                    "confidence": "observed"
                }
                snippet[field_name] = value
                document["source_snippets"] = [snippet]
                with self.subTest(field=field_name, value=value):
                    assert_invalid(
                        self,
                        document,
                        expected_validator=expected_validator,
                        expected_path=["source_snippets", 0, field_name],
                    )

    def test_traceability_target_type_enum_is_enforced(self):
        document = valid_example()
        document["traceability"] = [
            {
                "id": "TR-001",
                "source_external_id": "REQ-001",
                "source_type": "requirement",
                "target_type": "unknown_target",
                "target_id": "MOD-001",
                "description": ""
            }
        ]
        assert_invalid(
            self,
            document,
            "is not one of",
            expected_validator="enum",
            expected_path=["traceability", 0, "target_type"],
        )
```

- [ ] **Step 2: Run support data tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaSupportDataTests -v
```

Expected: FAIL until support data definitions are fully modeled.

- [ ] **Step 3: Implement support data definitions**

Replace permissive support definitions with:

```json
"evidence": {
  "type": "object",
  "required": ["id", "kind", "title", "location", "description", "confidence"],
  "additionalProperties": false,
  "properties": {
    "id": { "$ref": "#/$defs/nonEmptyString" },
    "kind": { "type": "string", "enum": ["source", "requirement", "note", "analysis"] },
    "title": { "type": "string" },
    "location": { "type": "string" },
    "description": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" }
  }
},
"traceability": {
  "type": "object",
  "required": ["id", "source_external_id", "source_type", "target_type", "target_id", "description"],
  "additionalProperties": false,
  "properties": {
    "id": { "$ref": "#/$defs/nonEmptyString" },
    "source_external_id": { "$ref": "#/$defs/nonEmptyString" },
    "source_type": { "type": "string", "enum": ["requirement", "note", "code", "user_input"] },
    "target_type": {
      "type": "string",
      "enum": ["module", "core_capability", "provided_capability", "runtime_unit", "flow", "flow_step", "flow_branch", "collaboration", "configuration_item", "data_artifact", "dependency", "risk", "assumption", "source_snippet"]
    },
    "target_id": { "$ref": "#/$defs/nonEmptyString" },
    "description": { "type": "string" }
  }
},
"risk": {
  "type": "object",
  "required": ["id", "description", "impact", "mitigation", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "id": { "$ref": "#/$defs/nonEmptyString" },
    "description": { "type": "string" },
    "impact": { "type": "string" },
    "mitigation": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"assumption": {
  "type": "object",
  "required": ["id", "description", "rationale", "validation_suggestion", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "id": { "$ref": "#/$defs/nonEmptyString" },
    "description": { "type": "string" },
    "rationale": { "type": "string" },
    "validation_suggestion": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"sourceSnippet": {
  "type": "object",
  "required": ["id", "path", "line_start", "line_end", "language", "purpose", "content", "confidence"],
  "additionalProperties": false,
  "properties": {
    "id": { "$ref": "#/$defs/nonEmptyString" },
    "path": { "$ref": "#/$defs/nonEmptyString" },
    "line_start": { "type": "integer", "minimum": 1 },
    "line_end": { "type": "integer", "minimum": 1 },
    "language": { "$ref": "#/$defs/nonEmptyString" },
    "purpose": { "type": "string" },
    "content": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" }
  }
}
```

- [ ] **Step 4: Run support data tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaSupportDataTests -v
```

Expected: PASS because `valid_example()` reads the complete fixture created in Task 1.

- [ ] **Step 5: Commit**

Run:

```bash
git add tests/test_validate_dsl.py schemas/structure-design.schema.json
git -c user.name=Codex -c user.email=codex@local commit -m "feat: add support data schema"
```

Expected: commit succeeds with support data schema and tests staged.

---

### Task 6: Structurally Valid Example DSL Files

**Files:**
- Modify: `tests/test_validate_dsl.py`
- Modify: `examples/minimal-from-code.dsl.json`
- Modify: `examples/minimal-from-requirements.dsl.json`

- [ ] **Step 1: Write failing example validation tests**

Append this class:

```python
class SchemaExampleValidationTests(unittest.TestCase):
    def test_example_dsl_files_pass_schema_validation(self):
        schema_validator = validator()
        for path in EXAMPLE_PATHS:
            with self.subTest(path=path.name):
                schema_validator.validate(json.loads(path.read_text(encoding="utf-8")))

    def test_examples_use_concrete_output_filenames(self):
        for path in EXAMPLE_PATHS:
            document = json.loads(path.read_text(encoding="utf-8"))
            output_file = document["document"]["output_file"]
            with self.subTest(path=path.name):
                self.assertTrue(output_file.endswith("_STRUCTURE_DESIGN.md"))
                self.assertNotEqual("STRUCTURE_DESIGN.md", output_file)
                self.assertNotEqual("structure_design.md", output_file)
                self.assertNotEqual("design.md", output_file)
                self.assertNotEqual("软件结构设计说明书.md", output_file)
```

- [ ] **Step 2: Run the example tests to verify they fail**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl.SchemaExampleValidationTests -v
```

Expected: FAIL because both examples are still `{}`.

- [ ] **Step 3: Replace `examples/minimal-from-code.dsl.json`**

Use this complete single-module code-source example:

```json
{
  "dsl_version": "0.1.0",
  "document": {
    "title": "软件结构设计说明书",
    "project_name": "create-structure-md",
    "project_version": "0.1.0",
    "document_version": "0.1.0",
    "status": "draft",
    "generated_at": "",
    "generated_by": "Codex",
    "language": "zh-CN",
    "source_type": "code",
    "scope_summary": "create-structure-md 技能的结构设计文档生成流程。",
    "not_applicable_policy": "固定章节；按章节规则处理空内容。",
    "output_file": "create-structure-md_STRUCTURE_DESIGN.md"
  },
  "system_overview": {
    "summary": "从已准备好的结构化设计内容生成单个结构设计 Markdown 文档。",
    "purpose": "提供稳定的 DSL、校验入口和渲染入口，使文档生成过程可重复。",
    "core_capabilities": [
      {
        "capability_id": "CAP-001",
        "name": "结构设计文档生成",
        "description": "把完整 DSL 内容转为固定章节的 Markdown 文档。",
        "confidence": "observed"
      }
    ],
    "notes": []
  },
  "architecture_views": {
    "summary": "技能由 DSL、校验脚本、渲染脚本、示例和参考文档组成。",
    "notes": [],
    "module_intro": {
      "rows": [
        {
          "module_id": "MOD-SKILL",
          "module_name": "技能文档生成模块",
          "responsibility": "承载 DSL 结构、校验入口、渲染入口和使用说明。",
          "inputs": "结构化设计 DSL JSON",
          "outputs": "单个结构设计 Markdown 文档",
          "notes": "",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
        }
      ]
    },
    "module_relationship_diagram": {
      "id": "MER-ARCH-MODULES",
      "kind": "module_relationship",
      "title": "模块关系图",
      "diagram_type": "flowchart",
      "description": "展示单模块技能的主要输入输出关系。",
      "source": "flowchart TD\n  DSL[DSL JSON] --> SKILL[技能文档生成模块]\n  SKILL --> MD[结构设计 Markdown]",
      "confidence": "observed"
    },
    "extra_tables": [],
    "extra_diagrams": []
  },
  "module_design": {
    "summary": "模块围绕 DSL 校验和 Markdown 生成边界组织。",
    "notes": [],
    "modules": [
      {
        "module_id": "MOD-SKILL",
        "name": "技能文档生成模块",
        "summary": "接收已经准备好的 DSL 内容，执行结构检查并生成文档。",
        "responsibilities": ["维护 DSL 结构契约", "暴露校验和渲染入口"],
        "external_capability_summary": {
          "description": "为 Codex 提供结构设计文档生成能力。",
          "consumers": ["Codex"],
          "interface_style": "命令行脚本与 Markdown 参考文档",
          "boundary_notes": ["不负责仓库分析", "不负责需求推理"]
        },
        "external_capability_details": {
          "provided_capabilities": {
            "rows": [
              {
                "capability_id": "CAP-MOD-SKILL-001",
                "capability_name": "文档 DSL 处理",
                "interface_style": "JSON 文件输入",
                "description": "读取结构化 DSL 并交给校验与渲染流程。",
                "inputs": "structure.dsl.json",
                "outputs": "结构设计 Markdown",
                "notes": "",
                "confidence": "observed",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": []
              }
            ]
          },
          "extra_tables": [],
          "extra_diagrams": []
        },
        "internal_structure": {
          "summary": "内部结构以 DSL schema、校验脚本、渲染脚本和参考文档为主要组成。",
          "diagram": {
            "id": "MER-MOD-SKILL-STRUCT",
            "kind": "internal_structure",
            "title": "模块内部结构图",
            "diagram_type": "flowchart",
            "description": "展示模块内部结构。",
            "source": "",
            "confidence": "observed"
          },
          "textual_structure": "schema 描述 DSL 结构，校验脚本负责质量门禁，渲染脚本负责输出 Markdown。",
          "not_applicable_reason": "单模块示例中使用文字结构说明即可。"
        },
        "extra_tables": [],
        "extra_diagrams": [],
        "evidence_refs": [],
        "traceability_refs": [],
        "source_snippet_refs": [],
        "notes": [],
        "confidence": "observed"
      }
    ]
  },
  "runtime_view": {
    "summary": "运行时由 Codex 准备 DSL 后依次调用校验、Mermaid 检查和渲染脚本。",
    "notes": [],
    "runtime_units": {
      "rows": [
        {
          "unit_id": "RUN-GENERATE",
          "unit_name": "文档生成命令序列",
          "unit_type": "CLI workflow",
          "entrypoint": "python scripts/render_markdown.py",
          "entrypoint_not_applicable_reason": "",
          "responsibility": "在校验通过后生成 Markdown 文档。",
          "related_module_ids": ["MOD-SKILL"],
          "external_environment_reason": "",
          "notes": "",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
        }
      ]
    },
    "runtime_flow_diagram": {
      "id": "MER-RUNTIME-FLOW",
      "kind": "runtime_flow",
      "title": "运行时流程图",
      "diagram_type": "flowchart",
      "description": "展示文档生成命令序列。",
      "source": "flowchart TD\n  Prepare[准备 DSL] --> Validate[校验 DSL]\n  Validate --> Mermaid[校验 Mermaid]\n  Mermaid --> Render[渲染 Markdown]",
      "confidence": "observed"
    },
    "extra_tables": [],
    "extra_diagrams": []
  },
  "configuration_data_dependencies": {
    "summary": "",
    "notes": [],
    "configuration_items": { "rows": [] },
    "structural_data_artifacts": { "rows": [] },
    "dependencies": { "rows": [] },
    "extra_tables": [],
    "extra_diagrams": []
  },
  "cross_module_collaboration": {
    "summary": "",
    "notes": [],
    "collaboration_scenarios": { "rows": [] },
    "extra_tables": [],
    "extra_diagrams": []
  },
  "key_flows": {
    "summary": "关键流程覆盖从 DSL 准备到 Markdown 输出的主路径。",
    "notes": [],
    "flow_index": {
      "rows": [
        {
          "flow_id": "FLOW-GENERATE",
          "flow_name": "生成结构设计文档",
          "trigger_condition": "Codex 已准备完整 DSL。",
          "participant_module_ids": ["MOD-SKILL"],
          "participant_runtime_unit_ids": ["RUN-GENERATE"],
          "main_steps": "校验 DSL、校验 Mermaid、渲染 Markdown。",
          "output_result": "模块专属结构设计 Markdown 文件。",
          "notes": ""
        }
      ]
    },
    "flows": [
      {
        "flow_id": "FLOW-GENERATE",
        "name": "生成结构设计文档",
        "overview": "从 DSL 输入生成一个结构设计 Markdown 文件。",
        "steps": [
          {
            "step_id": "STEP-GENERATE-001",
            "order": 1,
            "description": "准备结构化 DSL JSON。",
            "actor": "Codex",
            "related_module_ids": ["MOD-SKILL"],
            "related_runtime_unit_ids": ["RUN-GENERATE"],
            "input": "结构设计内容",
            "output": "structure.dsl.json",
            "confidence": "observed",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": []
          }
        ],
        "branches_or_exceptions": [],
        "related_module_ids": ["MOD-SKILL"],
        "related_runtime_unit_ids": ["RUN-GENERATE"],
        "confidence": "observed",
        "evidence_refs": [],
        "traceability_refs": [],
        "source_snippet_refs": [],
        "diagram": {
          "id": "MER-FLOW-GENERATE",
          "kind": "key_flow",
          "title": "生成流程图",
          "diagram_type": "flowchart",
          "description": "展示生成结构设计文档的关键流程。",
          "source": "flowchart TD\n  A[准备 DSL] --> B[校验]\n  B --> C[渲染 Markdown]",
          "confidence": "observed"
        }
      }
    ],
    "extra_tables": [],
    "extra_diagrams": []
  },
  "structure_issues_and_suggestions": "",
  "evidence": [],
  "traceability": [],
  "risks": [],
  "assumptions": [],
  "source_snippets": []
}
```

- [ ] **Step 4: Replace `examples/minimal-from-requirements.dsl.json`**

Use the same structural shape as the code example, with these required differences:

```json
{
  "document": {
    "project_name": "requirements-note-example",
    "source_type": "requirements",
    "scope_summary": "从需求说明生成结构设计文档的最小示例。",
    "output_file": "requirements-note-example_STRUCTURE_DESIGN.md"
  },
  "system_overview": {
    "summary": "根据需求说明整理结构设计内容并生成单个 Markdown 文档。",
    "purpose": "演示需求来源 DSL 的结构字段。"
  }
}
```

Implementation detail: do not leave the file as this partial JSON. Copy the complete code example from Step 3 and replace only `document.project_name`, `document.source_type`, `document.scope_summary`, `document.output_file`, `system_overview.summary`, and `system_overview.purpose` with the values above.

- [ ] **Step 5: Run all schema tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest tests.test_validate_dsl -v
```

Expected: PASS with the existing Phase 1 tests plus all Phase 2 schema tests.

- [ ] **Step 6: Commit**

Run:

```bash
git add tests/test_validate_dsl.py examples/minimal-from-code.dsl.json examples/minimal-from-requirements.dsl.json
git -c user.name=Codex -c user.email=codex@local commit -m "feat: add structurally valid DSL examples"
```

Expected: commit succeeds with example DSL files and example validation tests staged.

---

### Task 7: Phase 2 Acceptance Sweep

**Files:**
- Verify: `schemas/structure-design.schema.json`
- Verify: `examples/minimal-from-code.dsl.json`
- Verify: `examples/minimal-from-requirements.dsl.json`
- Verify: `tests/test_validate_dsl.py`
- Verify: `requirements.txt`

- [ ] **Step 1: Run full unit test discovery**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python -m unittest discover -s tests -v
```

Expected: PASS. Output includes tests from `test_validate_dsl`, `test_validate_mermaid`, and `test_render_markdown`.

- [ ] **Step 2: Check the schema directly**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft202012Validator

schema = json.loads(Path("schemas/structure-design.schema.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)
for path in [
    Path("tests/fixtures/valid-phase2.dsl.json"),
    Path("examples/minimal-from-code.dsl.json"),
    Path("examples/minimal-from-requirements.dsl.json"),
]:
    validator.validate(json.loads(path.read_text(encoding="utf-8")))
print("schema, fixture, and examples ok")
PY
```

Expected: prints `schema, fixture, and examples ok`.

- [ ] **Step 3: Confirm no permissive bridge definitions remain**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python - <<'PY'
import json
from pathlib import Path

schema = json.loads(Path("schemas/structure-design.schema.json").read_text(encoding="utf-8"))
defs = schema["$defs"]
missing_additional_properties = []
for name, definition in defs.items():
    if definition.get("type") != "object":
        continue
    if name == "extraTableRow":
        continue
    if definition.get("additionalProperties") is not False:
        missing_additional_properties.append(name)

if missing_additional_properties:
    raise SystemExit(
        "object definitions missing additionalProperties:false: "
        + ", ".join(sorted(missing_additional_properties))
    )

permissive_bridges = [
    name
    for name, definition in defs.items()
    if definition == {"type": "object"} or definition == {"type": "array"}
]
if permissive_bridges:
    raise SystemExit("permissive bridge definitions remain: " + ", ".join(sorted(permissive_bridges)))

weak_array_defs = []
for name, definition in defs.items():
    if definition.get("type") != "array":
        continue
    items = definition.get("items")
    if not isinstance(items, dict) or not items:
        weak_array_defs.append(name)
if weak_array_defs:
    raise SystemExit("array definitions missing concrete items: " + ", ".join(sorted(weak_array_defs)))

print("no permissive bridge definitions remain")
PY
```

Expected: prints `no permissive bridge definitions remain`.

- [ ] **Step 4: Confirm runtime dependency boundary remains unchanged**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/hyx/miniconda3/envs/agent/bin/python - <<'PY'
from pathlib import Path
requirements = Path("requirements.txt").read_text(encoding="utf-8")
assert requirements.strip().splitlines() == ["jsonschema"], requirements
assert not Path("requirements-dev.txt").exists()
print("runtime dependency boundary ok")
PY
```

Expected: prints `runtime dependency boundary ok`.

- [ ] **Step 5: Confirm no generated files are tracked**

Run:

```bash
git ls-files '*__pycache__*' '*.pyc' 'requirements-dev.txt'
```

Expected: no output.

- [ ] **Step 6: Inspect changed files**

Run:

```bash
git status --short
```

Expected after previous task commits: no output except pre-existing unrelated untracked files such as plan drafts. If files are still modified, inspect them and commit only intentional Phase 2 schema/example/test changes. Do not stage or commit unrelated pre-existing files.

- [ ] **Step 7: Final commit if Step 6 found intentional Phase 2 adjustments**

Run only if Step 6 shows intentional Phase 2 changes:

```bash
git add schemas/structure-design.schema.json examples/minimal-from-code.dsl.json examples/minimal-from-requirements.dsl.json tests/test_validate_dsl.py
git -c user.name=Codex -c user.email=codex@local commit -m "chore: finalize phase 2 DSL schema"
```

Expected: commit succeeds, then `git status --short` shows no output except pre-existing unrelated untracked files.

---

## Appendix A: Complete Valid Phase 2 Test Fixture

Use this exact content for `tests/fixtures/valid-phase2.dsl.json` in Task 1.

```json
{
  "dsl_version": "0.1.0",
  "document": {
    "title": "软件结构设计说明书",
    "project_name": "create-structure-md",
    "project_version": "0.1.0",
    "document_version": "0.1.0",
    "status": "draft",
    "generated_at": "",
    "generated_by": "Codex",
    "language": "zh-CN",
    "source_type": "code",
    "scope_summary": "create-structure-md 技能的结构设计文档生成流程。",
    "not_applicable_policy": "固定章节；按章节规则处理空内容。",
    "output_file": "create-structure-md_STRUCTURE_DESIGN.md"
  },
  "system_overview": {
    "summary": "从已准备好的结构化设计内容生成单个结构设计 Markdown 文档。",
    "purpose": "提供稳定的 DSL、校验入口和渲染入口，使文档生成过程可重复。",
    "core_capabilities": [
      {
        "capability_id": "CAP-001",
        "name": "结构设计文档生成",
        "description": "把完整 DSL 内容转为固定章节的 Markdown 文档。",
        "confidence": "observed"
      }
    ],
    "notes": []
  },
  "architecture_views": {
    "summary": "技能由 DSL、校验脚本、渲染脚本、示例和参考文档组成。",
    "notes": [],
    "module_intro": {
      "rows": [
        {
          "module_id": "MOD-SKILL",
          "module_name": "技能文档生成模块",
          "responsibility": "承载 DSL 结构、校验入口、渲染入口和使用说明。",
          "inputs": "结构化设计 DSL JSON",
          "outputs": "单个结构设计 Markdown 文档",
          "notes": "",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
        }
      ]
    },
    "module_relationship_diagram": {
      "id": "MER-ARCH-MODULES",
      "kind": "module_relationship",
      "title": "模块关系图",
      "diagram_type": "flowchart",
      "description": "展示单模块技能的主要输入输出关系。",
      "source": "flowchart TD\n  DSL[DSL JSON] --> SKILL[技能文档生成模块]\n  SKILL --> MD[结构设计 Markdown]",
      "confidence": "observed"
    },
    "extra_tables": [],
    "extra_diagrams": []
  },
  "module_design": {
    "summary": "模块围绕 DSL 校验和 Markdown 生成边界组织。",
    "notes": [],
    "modules": [
      {
        "module_id": "MOD-SKILL",
        "name": "技能文档生成模块",
        "summary": "接收已经准备好的 DSL 内容，执行结构检查并生成文档。",
        "responsibilities": ["维护 DSL 结构契约", "暴露校验和渲染入口"],
        "external_capability_summary": {
          "description": "为 Codex 提供结构设计文档生成能力。",
          "consumers": ["Codex"],
          "interface_style": "命令行脚本与 Markdown 参考文档",
          "boundary_notes": ["不负责仓库分析", "不负责需求推理"]
        },
        "external_capability_details": {
          "provided_capabilities": {
            "rows": [
              {
                "capability_id": "CAP-MOD-SKILL-001",
                "capability_name": "文档 DSL 处理",
                "interface_style": "JSON 文件输入",
                "description": "读取结构化 DSL 并交给校验与渲染流程。",
                "inputs": "structure.dsl.json",
                "outputs": "结构设计 Markdown",
                "notes": "",
                "confidence": "observed",
                "evidence_refs": [],
                "traceability_refs": [],
                "source_snippet_refs": []
              }
            ]
          },
          "extra_tables": [],
          "extra_diagrams": []
        },
        "internal_structure": {
          "summary": "内部结构以 DSL schema、校验脚本、渲染脚本和参考文档为主要组成。",
          "diagram": {
            "id": "MER-MOD-SKILL-STRUCT",
            "kind": "internal_structure",
            "title": "模块内部结构图",
            "diagram_type": "flowchart",
            "description": "展示模块内部结构。",
            "source": "",
            "confidence": "observed"
          },
          "textual_structure": "schema 描述 DSL 结构，校验脚本负责质量门禁，渲染脚本负责输出 Markdown。",
          "not_applicable_reason": "单模块示例中使用文字结构说明即可。"
        },
        "extra_tables": [],
        "extra_diagrams": [],
        "evidence_refs": [],
        "traceability_refs": [],
        "source_snippet_refs": [],
        "notes": [],
        "confidence": "observed"
      }
    ]
  },
  "runtime_view": {
    "summary": "运行时由 Codex 准备 DSL 后依次调用校验、Mermaid 检查和渲染脚本。",
    "notes": [],
    "runtime_units": {
      "rows": [
        {
          "unit_id": "RUN-GENERATE",
          "unit_name": "文档生成命令序列",
          "unit_type": "CLI workflow",
          "entrypoint": "python scripts/render_markdown.py",
          "entrypoint_not_applicable_reason": "",
          "responsibility": "在校验通过后生成 Markdown 文档。",
          "related_module_ids": ["MOD-SKILL"],
          "external_environment_reason": "",
          "notes": "",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
        }
      ]
    },
    "runtime_flow_diagram": {
      "id": "MER-RUNTIME-FLOW",
      "kind": "runtime_flow",
      "title": "运行时流程图",
      "diagram_type": "flowchart",
      "description": "展示文档生成命令序列。",
      "source": "flowchart TD\n  Prepare[准备 DSL] --> Validate[校验 DSL]\n  Validate --> Mermaid[校验 Mermaid]\n  Mermaid --> Render[渲染 Markdown]",
      "confidence": "observed"
    },
    "extra_tables": [],
    "extra_diagrams": []
  },
  "configuration_data_dependencies": {
    "summary": "",
    "notes": [],
    "configuration_items": {
      "rows": [
        {
          "config_id": "CFG-001",
          "config_name": "输出目录",
          "source": "命令行参数",
          "used_by": "文档生成命令序列",
          "purpose": "指定生成 Markdown 的输出目录。",
          "notes": "",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
        }
      ]
    },
    "structural_data_artifacts": {
      "rows": [
        {
          "artifact_id": "DATA-001",
          "artifact_name": "结构设计 DSL",
          "artifact_type": "JSON",
          "owner": "技能文档生成模块",
          "producer": "Codex",
          "consumer": "校验和渲染脚本",
          "notes": "",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
        }
      ]
    },
    "dependencies": {
      "rows": [
        {
          "dependency_id": "DEP-001",
          "dependency_name": "jsonschema",
          "dependency_type": "Python runtime dependency",
          "used_by": "DSL schema validation",
          "purpose": "执行 Draft 2020-12 JSON Schema 校验。",
          "notes": "",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
        }
      ]
    },
    "extra_tables": [],
    "extra_diagrams": []
  },
  "cross_module_collaboration": {
    "summary": "",
    "notes": [],
    "collaboration_scenarios": {
      "rows": [
        {
          "collaboration_id": "COL-001",
          "scenario": "DSL 校验后渲染",
          "initiator_module_id": "MOD-SKILL",
          "participant_module_ids": ["MOD-SKILL"],
          "collaboration_method": "顺序命令调用",
          "description": "同一结构模块内的校验职责和渲染职责按命令顺序协作。",
          "confidence": "observed",
          "evidence_refs": [],
          "traceability_refs": [],
          "source_snippet_refs": []
        }
      ]
    },
    "collaboration_relationship_diagram": {
      "id": "MER-COLLABORATION-RELATIONSHIP",
      "kind": "collaboration_relationship",
      "title": "协作关系图",
      "diagram_type": "flowchart",
      "description": "展示校验与渲染职责的协作。",
      "source": "flowchart TD\n  Validate[校验职责] --> Render[渲染职责]",
      "confidence": "observed"
    },
    "extra_tables": [],
    "extra_diagrams": []
  },
  "key_flows": {
    "summary": "关键流程覆盖从 DSL 准备到 Markdown 输出的主路径。",
    "notes": [],
    "flow_index": {
      "rows": [
        {
          "flow_id": "FLOW-GENERATE",
          "flow_name": "生成结构设计文档",
          "trigger_condition": "Codex 已准备完整 DSL。",
          "participant_module_ids": ["MOD-SKILL"],
          "participant_runtime_unit_ids": ["RUN-GENERATE"],
          "main_steps": "校验 DSL、校验 Mermaid、渲染 Markdown。",
          "output_result": "模块专属结构设计 Markdown 文件。",
          "notes": ""
        }
      ]
    },
    "flows": [
      {
        "flow_id": "FLOW-GENERATE",
        "name": "生成结构设计文档",
        "overview": "从 DSL 输入生成一个结构设计 Markdown 文件。",
        "steps": [
          {
            "step_id": "STEP-GENERATE-001",
            "order": 1,
            "description": "准备结构化 DSL JSON。",
            "actor": "Codex",
            "related_module_ids": ["MOD-SKILL"],
            "related_runtime_unit_ids": ["RUN-GENERATE"],
            "input": "结构设计内容",
            "output": "structure.dsl.json",
            "confidence": "observed",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": []
          }
        ],
        "branches_or_exceptions": [
          {
            "branch_id": "BR-GENERATE-001",
            "condition": "DSL 校验失败",
            "handling": "停止渲染并报告结构问题。",
            "related_module_ids": ["MOD-SKILL"],
            "related_runtime_unit_ids": ["RUN-GENERATE"],
            "confidence": "observed",
            "evidence_refs": [],
            "traceability_refs": [],
            "source_snippet_refs": []
          }
        ],
        "related_module_ids": ["MOD-SKILL"],
        "related_runtime_unit_ids": ["RUN-GENERATE"],
        "confidence": "observed",
        "evidence_refs": [],
        "traceability_refs": [],
        "source_snippet_refs": [],
        "diagram": {
          "id": "MER-FLOW-GENERATE",
          "kind": "key_flow",
          "title": "生成流程图",
          "diagram_type": "flowchart",
          "description": "展示生成结构设计文档的关键流程。",
          "source": "flowchart TD\n  A[准备 DSL] --> B[校验]\n  B --> C[渲染 Markdown]",
          "confidence": "observed"
        }
      }
    ],
    "extra_tables": [],
    "extra_diagrams": []
  },
  "structure_issues_and_suggestions": "",
  "evidence": [],
  "traceability": [],
  "risks": [],
  "assumptions": [],
  "source_snippets": []
}
```

---

## Appendix B: Required Schema Definition Details

Use these concrete `$defs` entries where Task 4 references this appendix. They are intentionally repeated here so the chapter 5-9 implementation does not depend on guesswork.

```json
"configurationItemsTable": {
  "type": "object",
  "required": ["rows"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/configurationItemRow" } }
  }
},
"structuralDataArtifactRow": {
  "type": "object",
  "required": ["artifact_id", "artifact_name", "artifact_type", "owner", "producer", "consumer", "notes", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "artifact_id": { "$ref": "#/$defs/nonEmptyString" },
    "artifact_name": { "$ref": "#/$defs/nonEmptyString" },
    "artifact_type": { "$ref": "#/$defs/nonEmptyString" },
    "owner": { "$ref": "#/$defs/nonEmptyString" },
    "producer": { "type": "string" },
    "consumer": { "type": "string" },
    "notes": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"structuralDataArtifactsTable": {
  "type": "object",
  "required": ["rows"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/structuralDataArtifactRow" } }
  }
},
"dependencyRow": {
  "type": "object",
  "required": ["dependency_id", "dependency_name", "dependency_type", "used_by", "purpose", "notes", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "dependency_id": { "$ref": "#/$defs/nonEmptyString" },
    "dependency_name": { "$ref": "#/$defs/nonEmptyString" },
    "dependency_type": { "$ref": "#/$defs/nonEmptyString" },
    "used_by": { "type": "string" },
    "purpose": { "$ref": "#/$defs/nonEmptyString" },
    "notes": { "type": "string" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"dependenciesTable": {
  "type": "object",
  "required": ["rows"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/dependencyRow" } }
  }
},
"collaborationScenarioRow": {
  "type": "object",
  "required": ["collaboration_id", "scenario", "initiator_module_id", "participant_module_ids", "collaboration_method", "description", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "collaboration_id": { "$ref": "#/$defs/nonEmptyString" },
    "scenario": { "$ref": "#/$defs/nonEmptyString" },
    "initiator_module_id": { "$ref": "#/$defs/nonEmptyString" },
    "participant_module_ids": { "$ref": "#/$defs/referenceArray" },
    "collaboration_method": { "$ref": "#/$defs/nonEmptyString" },
    "description": { "$ref": "#/$defs/nonEmptyString" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"collaborationScenariosTable": {
  "type": "object",
  "required": ["rows"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/collaborationScenarioRow" } }
  }
},
"flowBranch": {
  "type": "object",
  "required": ["branch_id", "condition", "handling", "related_module_ids", "related_runtime_unit_ids", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs"],
  "additionalProperties": false,
  "properties": {
    "branch_id": { "$ref": "#/$defs/nonEmptyString" },
    "condition": { "$ref": "#/$defs/nonEmptyString" },
    "handling": { "$ref": "#/$defs/nonEmptyString" },
    "related_module_ids": { "$ref": "#/$defs/referenceArray" },
    "related_runtime_unit_ids": { "$ref": "#/$defs/referenceArray" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" }
  }
},
"flowIndexTable": {
  "type": "object",
  "required": ["rows"],
  "additionalProperties": false,
  "properties": {
    "rows": { "type": "array", "items": { "$ref": "#/$defs/flowIndexRow" } }
  }
},
"keyFlow": {
  "type": "object",
  "required": ["flow_id", "name", "overview", "steps", "branches_or_exceptions", "related_module_ids", "related_runtime_unit_ids", "confidence", "evidence_refs", "traceability_refs", "source_snippet_refs", "diagram"],
  "additionalProperties": false,
  "properties": {
    "flow_id": { "$ref": "#/$defs/nonEmptyString" },
    "name": { "$ref": "#/$defs/nonEmptyString" },
    "overview": { "$ref": "#/$defs/nonEmptyString" },
    "steps": { "type": "array", "items": { "$ref": "#/$defs/flowStep" } },
    "branches_or_exceptions": { "type": "array", "items": { "$ref": "#/$defs/flowBranch" } },
    "related_module_ids": { "$ref": "#/$defs/referenceArray" },
    "related_runtime_unit_ids": { "$ref": "#/$defs/referenceArray" },
    "confidence": { "$ref": "#/$defs/confidence" },
    "evidence_refs": { "$ref": "#/$defs/referenceArray" },
    "traceability_refs": { "$ref": "#/$defs/referenceArray" },
    "source_snippet_refs": { "$ref": "#/$defs/referenceArray" },
    "diagram": { "$ref": "#/$defs/diagram" }
  }
},
"keyFlows": {
  "type": "object",
  "required": ["summary", "notes", "flow_index", "flows", "extra_tables", "extra_diagrams"],
  "additionalProperties": false,
  "properties": {
    "summary": { "$ref": "#/$defs/nonEmptyString" },
    "notes": { "$ref": "#/$defs/stringArray" },
    "flow_index": { "$ref": "#/$defs/flowIndexTable" },
    "flows": { "type": "array", "items": { "$ref": "#/$defs/keyFlow" } },
    "extra_tables": { "$ref": "#/$defs/extraTables" },
    "extra_diagrams": { "$ref": "#/$defs/extraDiagrams" }
  }
}
```

---

## Self-Review Checklist

- Spec coverage:
  - JSON Schema file becomes a full structural DSL schema: Tasks 1-5.
  - Top-level required fields and wrapper rejection: Task 1.
  - Output filename structural rules: Task 2.
  - Common metadata, confidence enum, notes arrays, and reference arrays: Tasks 2-5.
  - Diagram object policy and optional diagram `{}` rejection: Tasks 2 and 4.
  - Fixed table row shapes and fixed table `columns` rejection: Tasks 2-4.
  - Extra table row restriction for `traceability_refs`, `source_snippet_refs`, and validation policy fields: Task 2.
  - Extra table declared-column matching is intentionally deferred to Phase 3 `validate_dsl.py` because it depends on sibling `columns[].key`.
  - Chapter 2 through 9 object shapes: Tasks 3-4.
  - Support data objects and source snippet positive integer line numbers: Task 5.
  - Structurally valid examples with concrete output filenames: Task 6.
  - Full test discovery and direct schema/example validation: Task 7.
- Boundary check:
  - Cross-reference existence is not implemented.
  - One-to-one module and flow matching is not implemented.
  - Semantic requiredness beyond JSON Schema type/minLength constraints is not implemented.
  - Mermaid CLI/static validation is not implemented.
  - Markdown rendering is not implemented.
  - Generic-only filename rejection remains Phase 3 semantic validation, though examples avoid generic names.
- Deletion constraint:
  - The plan contains no deletion step.
  - Cleanup, if ever needed, is reported to the user as a command for user execution.

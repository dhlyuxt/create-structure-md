import unittest

from scripts.v2_foundation import (
    ANCHOR_TYPE_VALUES,
    DEPENDENCY_TYPE_VALUES,
    EVIDENCE_MODES,
    INTERFACE_TYPE_VALUES,
    MODULE_KIND_VALUES,
    NOT_APPLICABLE_GATES,
    USAGE_RELATION_VALUES,
    VALUE_SOURCE_VALUES,
    V2_DSL_VERSION,
    V2_VERSION_ERROR,
    interface_location_violations,
    not_applicable_gate_violations,
    require_v2_dsl_version,
    v2_global_rule_violations,
)


def contradiction_document():
    return {
        "dsl_version": "0.2.0",
        "module_design": {
            "modules": [
                {
                    "module_id": "MOD-ONE",
                    "module_kind": "library",
                    "configuration": {
                        "parameters": {
                            "rows": [
                                {
                                    "parameter_id": "MPARAM-ONE",
                                    "name": "debug",
                                    "not_applicable_reason": "no parameters",
                                }
                            ],
                            "not_applicable_reason": "no parameters",
                        }
                    },
                    "dependencies": {
                        "rows": [
                            {
                                "dependency_id": "MDEP-ONE",
                                "name": "json",
                                "not_applicable_reason": "no dependencies",
                            }
                        ],
                        "not_applicable_reason": "no dependencies",
                    },
                    "data_objects": {
                        "rows": [
                            {
                                "data_id": "DATA-ONE",
                                "name": "Document",
                                "not_applicable_reason": "no data",
                            }
                        ],
                        "not_applicable_reason": "no data",
                    },
                    "public_interfaces": {
                        "interface_index": {
                            "rows": [{"interface_id": "IFACE-ONE", "name": "render"}],
                        },
                        "interfaces": [
                            {
                                "interface_id": "IFACE-ONE",
                                "interface_type": "function",
                                "parameters": {
                                    "rows": [
                                        {
                                            "parameter_id": "MPARAM-TWO",
                                            "name": "document",
                                            "not_applicable_reason": "no parameters",
                                        }
                                    ],
                                    "not_applicable_reason": "no parameters",
                                },
                                "return_values": {
                                    "rows": [{"name": "markdown", "description": "rendered markdown"}],
                                    "not_applicable_reason": "no returns",
                                },
                            }
                        ],
                        "not_applicable_reason": "no interfaces",
                    },
                    "internal_mechanism": {
                        "summary": "Uses the renderer.",
                        "mechanism_index": {"rows": [{"mechanism_id": "MECH-ONE"}]},
                        "mechanism_details": [{"mechanism_id": "MECH-ONE", "description": "Renders"}],
                        "not_applicable_reason": "no mechanism",
                    },
                    "known_limitations": {
                        "rows": [
                            {
                                "limitation_id": "LIMIT-ONE",
                                "description": "Slow",
                                "not_applicable_reason": "no limitations",
                            }
                        ],
                        "not_applicable_reason": "no limitations",
                    },
                }
            ]
        },
        "structure_issues_and_suggestions": {
            "summary": "Needs cleanup.",
            "blocks": [{"block_id": "BLOCK-ONE", "content": "Issue"}],
            "not_applicable_reason": "no issues",
        },
    }


class ConstantTests(unittest.TestCase):
    def test_v2_version_constants_are_exact(self):
        self.assertEqual("0.2.0", V2_DSL_VERSION)
        self.assertEqual(
            "V1 DSL is not supported by the V2 renderer; migrate the input to dsl_version 0.2.0.",
            V2_VERSION_ERROR,
        )
        self.assertEqual(("hidden", "inline"), EVIDENCE_MODES)

    def test_global_enum_constants_are_exact(self):
        self.assertEqual(
            (
                "documentation_contract",
                "schema_contract",
                "validator",
                "renderer",
                "installer",
                "test_suite",
                "library",
                "other",
            ),
            MODULE_KIND_VALUES,
        )
        self.assertEqual(
            (
                "default",
                "cli_argument",
                "environment",
                "constant",
                "config_file",
                "computed",
                "inferred",
                "unknown",
            ),
            VALUE_SOURCE_VALUES,
        )
        self.assertEqual(
            (
                "runtime",
                "library",
                "tool",
                "schema_contract",
                "documentation_contract",
                "dsl_contract",
                "internal_module",
                "data_object",
                "filesystem",
                "external_service",
                "test_fixture",
                "other",
            ),
            DEPENDENCY_TYPE_VALUES,
        )
        self.assertEqual(
            (
                "reads",
                "writes",
                "validates_against",
                "renders",
                "invokes",
                "imports",
                "tests",
                "produces",
                "consumes",
                "uses",
                "other",
            ),
            USAGE_RELATION_VALUES,
        )
        self.assertEqual(
            (
                "command_line",
                "function",
                "method",
                "library_api",
                "schema_contract",
                "dsl_contract",
                "document_contract",
                "configuration_contract",
                "data_contract",
                "test_fixture",
                "workflow",
                "other",
            ),
            INTERFACE_TYPE_VALUES,
        )
        self.assertEqual(
            (
                "file_path",
                "module_id",
                "interface_id",
                "data_id",
                "dependency_id",
                "parameter_id",
                "diagram_id",
                "table_id",
                "source_snippet_id",
                "evidence_id",
                "traceability_id",
                "other",
            ),
            ANCHOR_TYPE_VALUES,
        )

    def test_not_applicable_gate_names_are_exact(self):
        self.assertEqual(
            [
                "module_configuration_parameters",
                "module_dependencies",
                "module_data_objects",
                "public_interfaces",
                "executable_interface_parameters",
                "executable_interface_return_values",
                "internal_mechanism",
                "known_limitations",
                "chapter_9_structure_issues",
            ],
            [gate.name for gate in NOT_APPLICABLE_GATES],
        )


class DirectHelperTests(unittest.TestCase):
    def test_require_v2_dsl_version_accepts_only_v2_document_dict(self):
        self.assertIsNone(require_v2_dsl_version({"dsl_version": "0.2.0"}))

        for document in [{"dsl_version": "0.1.0"}, {}, {"document": {}}, None, [], "0.2.0"]:
            with self.subTest(document=document):
                with self.assertRaisesRegex(ValueError, "V1 DSL is not supported"):
                    require_v2_dsl_version(document)

    def test_not_applicable_gate_violations_accepts_content_or_reason_only(self):
        self.assertEqual([], not_applicable_gate_violations("$.section", ["content"], ""))
        self.assertEqual([], not_applicable_gate_violations("$.section", [], "Not applicable"))

    def test_not_applicable_gate_violations_rejects_contradiction_and_empty_gate(self):
        contradiction = not_applicable_gate_violations(
            "$.section", [{"rows": [{"id": "ROW-ONE"}]}], "Not applicable", stable_id="ROW-ONE"
        )
        self.assertEqual(1, len(contradiction))
        self.assertEqual("$.section", contradiction[0].path)
        self.assertIn("$.section", contradiction[0].message)
        self.assertIn("ROW-ONE", contradiction[0].message)
        self.assertIn("both content and not_applicable_reason", contradiction[0].message)

        empty = not_applicable_gate_violations("$.empty", ["", [], {}], "")
        self.assertEqual(1, len(empty))
        self.assertEqual("$.empty", empty[0].path)
        self.assertIn("must provide not_applicable_reason", empty[0].message)

    def test_interface_location_violations_accepts_file_path_and_valid_ranges(self):
        self.assertEqual([], interface_location_violations("$.location", {"file_path": "scripts/x.py"}))
        self.assertEqual(
            [],
            interface_location_violations(
                "$.location", {"file_path": "scripts/x.py", "line_start": 2, "line_end": 4}
            ),
        )
        self.assertEqual(
            [],
            interface_location_violations(
                "$.location",
                {"file_path": "scripts/x.py", "line_start": 1, "line_end": 1},
                line_one_supported=True,
            ),
        )

    def test_interface_location_violations_rejects_bad_locations(self):
        examples = [
            None,
            {},
            {"file_path": ""},
            {"file_path": "scripts/x.py", "line_start": 2},
            {"file_path": "scripts/x.py", "line_end": 2},
            {"file_path": "scripts/x.py", "line_start": 4, "line_end": 2},
            {"file_path": "scripts/x.py", "line_start": 1, "line_end": 1},
        ]
        for location in examples:
            with self.subTest(location=location):
                violations = interface_location_violations("$.location", location)
                self.assertGreaterEqual(len(violations), 1)
                self.assertEqual("$.location", violations[0].path)


class GlobalRuleTests(unittest.TestCase):
    def test_rejects_invalid_alternate_reason_fields(self):
        document = {
            "module_design": {
                "modules": [
                    {
                        "source_scope": {"not_applicable_reason": "No scope"},
                        "configuration": {"not_applicable_reason": "No config"},
                    }
                ]
            }
        }
        messages = [violation.message for violation in v2_global_rule_violations(document)]
        self.assertTrue(
            any("$.module_design.modules[0].source_scope.not_applicable_reason" in message for message in messages)
        )
        self.assertTrue(
            any("$.module_design.modules[0].configuration.not_applicable_reason" in message for message in messages)
        )

    def test_rejects_not_applicable_contradictions_across_all_gates(self):
        violations = v2_global_rule_violations(contradiction_document())
        messages = "\n".join(violation.message for violation in violations)
        for gate in NOT_APPLICABLE_GATES:
            with self.subTest(gate=gate.name):
                self.assertIn(gate.name, messages)
                self.assertIn("both content and not_applicable_reason", messages)

    def test_public_interfaces_gate_uses_public_interfaces_reason(self):
        valid_empty = {
            "module_design": {
                "modules": [
                    {
                        "module_id": "MOD-EMPTY",
                        "public_interfaces": {
                            "interface_index": {"rows": []},
                            "interfaces": [],
                            "not_applicable_reason": "No public interfaces.",
                        },
                    }
                ]
            }
        }
        valid_messages = "\n".join(violation.message for violation in v2_global_rule_violations(valid_empty))
        self.assertNotIn("public_interfaces", valid_messages)

        invalid = {
            "module_design": {
                "modules": [
                    {
                        "module_id": "MOD-PUBLIC",
                        "public_interfaces": {
                            "interface_index": {"rows": [{"interface_id": "IFACE-PUBLIC"}]},
                            "interfaces": [],
                            "not_applicable_reason": "No public interfaces.",
                        },
                    }
                ]
            }
        }
        invalid_messages = "\n".join(violation.message for violation in v2_global_rule_violations(invalid))
        self.assertIn("public_interfaces", invalid_messages)
        self.assertIn("both content and not_applicable_reason", invalid_messages)

    def test_validates_global_enums_and_required_other_reasons(self):
        document = {
            "module_kind": "bad",
            "value_source": "bad",
            "dependency_type": "bad",
            "usage_relation": "bad",
            "interface_type": "bad",
            "anchor_type": "bad",
            "items": [
                {"module_kind": "other", "module_kind_reason": "  "},
                {"interface_type": "other"},
                {"anchor_type": "other", "reason": ""},
            ],
        }
        messages = "\n".join(violation.message for violation in v2_global_rule_violations(document))
        for field in [
            "module_kind",
            "value_source",
            "dependency_type",
            "usage_relation",
            "interface_type",
            "anchor_type",
        ]:
            self.assertIn(field, messages)
            self.assertIn("must be one of", messages)
        self.assertIn("module_kind_reason", messages)
        self.assertIn("interface_type_reason", messages)
        self.assertIn("reason", messages)

    def test_rejects_location_line_errors_anywhere(self):
        document = {
            "nested": [
                {"location": {"file_path": "scripts/x.py", "line_start": 7}},
                {"child": {"location": {"file_path": "scripts/y.py", "line_start": 3, "line_end": 2}}},
            ]
        }
        paths = [violation.path for violation in v2_global_rule_violations(document)]
        self.assertIn("$.nested[0].location", paths)
        self.assertIn("$.nested[1].child.location", paths)

    def test_contract_interfaces_do_not_require_absent_parameter_or_return_gates(self):
        document = {
            "module_design": {
                "modules": [
                    {
                        "module_id": "MOD-CONTRACT",
                        "public_interfaces": {
                            "interface_index": {"rows": [{"interface_id": "IFACE-CONTRACT"}]},
                            "interfaces": [{"interface_id": "IFACE-CONTRACT", "interface_type": "schema_contract"}],
                        },
                    }
                ]
            }
        }
        messages = "\n".join(violation.message for violation in v2_global_rule_violations(document))
        self.assertNotIn("executable_interface_parameters", messages)
        self.assertNotIn("executable_interface_return_values", messages)

    def test_detects_future_v2_id_scope_duplicates(self):
        document = {
            "module_design": {
                "modules": [
                    {
                        "module_id": "MOD-ONE",
                        "configuration": {
                            "parameters": {
                                "rows": [{"parameter_id": "MPARAM-DUP"}, {"parameter_id": "MPARAM-DUP"}]
                            }
                        },
                        "data_objects": {"rows": [{"data_id": "DATA-DUP"}, {"data_id": "DATA-DUP"}]},
                        "dependencies": {
                            "rows": [{"dependency_id": "MDEP-DUP"}, {"dependency_id": "MDEP-DUP"}]
                        },
                        "known_limitations": {
                            "rows": [{"limitation_id": "LIMIT-DUP"}, {"limitation_id": "LIMIT-DUP"}]
                        },
                    }
                ]
            },
            "structure_issues_and_suggestions": {
                "blocks": [{"block_id": "BLOCK-DUP"}, {"block_id": "BLOCK-DUP"}]
            },
        }
        messages = "\n".join(violation.message for violation in v2_global_rule_violations(document))
        for duplicated_id in ["MPARAM-DUP", "DATA-DUP", "MDEP-DUP", "LIMIT-DUP", "BLOCK-DUP"]:
            self.assertIn(duplicated_id, messages)
            self.assertIn("duplicate", messages)

    def test_interface_id_scope_allows_logical_pair_and_rejects_invalid_reuse(self):
        allowed = {
            "module_design": {
                "modules": [
                    {
                        "module_id": "MOD-ONE",
                        "public_interfaces": {
                            "interface_index": {"rows": [{"interface_id": "IFACE-ONE"}]},
                            "interfaces": [{"interface_id": "IFACE-ONE"}],
                        },
                    }
                ]
            }
        }
        allowed_messages = "\n".join(violation.message for violation in v2_global_rule_violations(allowed))
        self.assertNotIn("IFACE-ONE", allowed_messages)

        rejected = {
            "module_design": {
                "modules": [
                    {
                        "module_id": "MOD-ONE",
                        "public_interfaces": {
                            "interface_index": {
                                "rows": [{"interface_id": "IFACE-DUP"}, {"interface_id": "IFACE-DUP"}]
                            },
                            "interfaces": [{"interface_id": "IFACE-DUP"}, {"interface_id": "IFACE-DUP"}],
                        },
                    },
                    {
                        "module_id": "MOD-TWO",
                        "public_interfaces": {
                            "interface_index": {"rows": [{"interface_id": "IFACE-DUP"}]},
                            "interfaces": [{"interface_id": "IFACE-DUP"}],
                        },
                    },
                ]
            }
        }
        messages = "\n".join(violation.message for violation in v2_global_rule_violations(rejected))
        self.assertIn("duplicate interface_id in interface_index", messages)
        self.assertIn("duplicate interface_id in interface details", messages)
        self.assertIn("interface_id IFACE-DUP is already defined under module index 0", messages)

        same_module_id_reuse = {
            "module_design": {
                "modules": [
                    {
                        "module_id": "MOD-SAME",
                        "public_interfaces": {"interface_index": {"rows": [{"interface_id": "IFACE-SAME"}]}},
                    },
                    {
                        "module_id": "MOD-SAME",
                        "public_interfaces": {"interfaces": [{"interface_id": "IFACE-SAME"}]},
                    },
                ]
            }
        }
        same_id_messages = "\n".join(
            violation.message for violation in v2_global_rule_violations(same_module_id_reuse)
        )
        self.assertIn("interface_id IFACE-SAME is already defined under module index 0", same_id_messages)


if __name__ == "__main__":
    unittest.main()

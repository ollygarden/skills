"""
Regression tests for the skill-content changes introduced in this PR.

This repository has no application code to unit test — skills are pure
Markdown/YAML documentation consumed by an AI agent. These tests therefore
validate the *content* of the changed files directly: YAML frontmatter
structure, and the specific wording/version substitutions introduced by
the diff. This guards against silent regressions (e.g. a stale version
number, a reverted wording change, or a broken frontmatter block) the next
time these files are edited.

Run with:
    python3 -m unittest tests/test_skills_content.py -v
"""

import re
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def read(*parts: str) -> str:
    path = SKILLS_DIR.joinpath(*parts)
    return path.read_text(encoding="utf-8")


def extract_frontmatter(text: str) -> dict:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise AssertionError("No YAML frontmatter block found at top of file")
    return yaml.safe_load(match.group(1))


def extract_code_blocks(text: str, lang: str = None):
    """Return the content of fenced code blocks, optionally filtered by language tag.

    Tolerates fences indented under a list item (e.g. "   ```yaml"), which
    several of these skill docs use for code blocks nested in numbered steps.
    """
    blocks = re.findall(r"[ \t]*```(\w*)\n(.*?)\n[ \t]*```", text, re.DOTALL)
    if lang is None:
        return [content for _, content in blocks]
    return [content for tag, content in blocks if tag == lang]


class TestCollectorConfigDecompositionFrontmatter(unittest.TestCase):
    """skills/ollygarden-otel-collector-config-decomposition/SKILL.md

    The description field switched from a plain scalar to a folded block
    scalar (`>-`) so the long description can be wrapped across source
    lines while still collapsing to a single-line YAML string value.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = read("ollygarden-otel-collector-config-decomposition", "SKILL.md")
        cls.frontmatter = extract_frontmatter(cls.text)

    def test_frontmatter_parses_as_valid_yaml(self):
        self.assertIsInstance(self.frontmatter, dict)

    def test_name_matches_directory(self):
        self.assertEqual(
            self.frontmatter["name"], "ollygarden-otel-collector-config-decomposition"
        )

    def test_license_present(self):
        self.assertEqual(self.frontmatter["license"], "Apache-2.0")

    def test_description_is_present_and_nonempty(self):
        self.assertIn("description", self.frontmatter)
        self.assertTrue(self.frontmatter["description"].strip())

    def test_folded_scalar_collapses_to_single_line(self):
        # >- is a folded block scalar: line breaks in the source fold into
        # spaces and the final trailing newline is stripped. If someone
        # reverts this to a literal block scalar (`|`) or otherwise breaks
        # the folding, embedded newlines would leak into the value.
        description = self.frontmatter["description"]
        self.assertNotIn("\n", description)

    def test_description_content_preserved(self):
        description = self.frontmatter["description"]
        self.assertTrue(
            description.startswith(
                "OllyGarden's opinion on when and how to decompose a monolithic "
                "OpenTelemetry Collector config"
            )
        )
        self.assertIn("hands off behavioral proof to ollygarden-otel-collector-config-validation.", description)

    def test_raw_source_uses_folded_scalar_indicator(self):
        # Guard against accidentally reverting to a plain unfolded scalar.
        self.assertIn("description: >-", self.text)


class TestCollectorConfigDecompositionMechanics(unittest.TestCase):
    """skills/ollygarden-otel-collector-config-decomposition/references/mechanics.md

    The OCB builder manifest example bumped the confmap provider versions
    from v1.57.0 to v1.62.0.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = read(
            "ollygarden-otel-collector-config-decomposition", "references", "mechanics.md"
        )

    def test_old_provider_version_absent(self):
        self.assertNotIn("v1.57.0", self.text)

    def test_new_provider_version_present_for_all_three_providers(self):
        for provider in ("fileprovider", "envprovider", "yamlprovider"):
            with self.subTest(provider=provider):
                pattern = (
                    rf"gomod: go\.opentelemetry\.io/collector/confmap/provider/"
                    rf"{provider} v1\.62\.0"
                )
                self.assertRegex(self.text, pattern)

    def test_builder_yaml_block_is_internally_consistent(self):
        blocks = extract_code_blocks(self.text, "yaml")
        builder_blocks = [b for b in blocks if "providers:" in b]
        self.assertTrue(builder_blocks, "expected a providers: yaml block")
        builder_yaml = builder_blocks[0]
        self.assertEqual(builder_yaml.count("v1.62.0"), 3)
        self.assertNotIn("v1.57.0", builder_yaml)


class TestCollectorConfigValidation(unittest.TestCase):
    """skills/ollygarden-otel-collector-config-validation/SKILL.md

    The pinned otelcol-contrib Docker image tag bumped from 0.155.0 to
    0.156.0, including the unprefixed vs `v`-prefixed tag-format guidance.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = read("ollygarden-otel-collector-config-validation", "SKILL.md")

    def test_old_version_absent(self):
        self.assertNotIn("0.155.0", self.text)

    def test_docker_image_tag_updated(self):
        self.assertIn(
            "otel/opentelemetry-collector-contrib:0.156.0", self.text
        )

    def test_unprefixed_and_v_prefixed_tag_guidance_updated(self):
        self.assertIn("(`:0.156.0`)", self.text)
        self.assertIn("(`:v0.156.0`)", self.text)

    def test_pin_recent_release_tag_sentence_updated(self):
        self.assertIn("**Pin a recent release tag** — `0.156.0` above is illustrative", self.text)

    def test_frontmatter_still_parses(self):
        frontmatter = extract_frontmatter(self.text)
        self.assertEqual(
            frontmatter["name"], "ollygarden-otel-collector-config-validation"
        )


class TestCollectorK8sDaemonsetValidating(unittest.TestCase):
    """skills/ollygarden-otel-collector-k8s-daemonset/references/validating.md

    The pinned validation version (v0.155.0) was intentionally left as-is,
    but a caveat was added instructing readers to re-validate against the
    actual pinned deployment version rather than treat it as evergreen.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = read(
            "ollygarden-otel-collector-k8s-daemonset", "references", "validating.md"
        )

    def test_existing_pinned_version_unchanged(self):
        self.assertIn("v0.155.0", self.text)

    def test_new_re_validation_caveat_present(self):
        self.assertIn(
            "re-run it against the pinned deployment version rather than "
            "treating that stamp as evergreen.",
            self.text,
        )

    def test_caveat_is_appended_to_validated_this_way_sentence(self):
        sentence_pattern = (
            r"Validated this way on `otelcol-contrib` v0\.155\.0;\s*"
            r"re-run it against the pinned deployment version rather than "
            r"treating that stamp as evergreen\."
        )
        self.assertRegex(self.text, sentence_pattern)


class TestDeclarativeConfigSkill(unittest.TestCase):
    """skills/ollygarden-otel-declarative-config/SKILL.md

    Multiple absolute claims were softened into runtime/version-conditional
    guidance: cross-language schema stability, declarative-config maturity,
    service.instance.id handling, env-var/config-file precedence, and the
    OTEL_INSTRUMENTATION_* exclude-pattern interaction.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = read("ollygarden-otel-declarative-config", "SKILL.md")

    def test_language_agnostic_absolute_claim_removed(self):
        self.assertNotIn("It's language-agnostic", self.text)

    def test_shared_schema_hedged_wording_present(self):
        self.assertIn(
            "It uses a shared schema across languages, subject to each "
            "runtime's released support matrix",
            self.text,
        )

    def test_stable_near_stable_claim_removed(self):
        self.assertNotIn("These SDKs have\nstable or near-stable implementations.", self.text)

    def test_verify_runtime_and_version_guidance_present(self):
        normalized = " ".join(self.text.split())
        self.assertIn(
            "Several implementations and activation APIs remain experimental, "
            "so verify the exact runtime and version first.",
            normalized,
        )

    def test_service_instance_id_do_not_hardcode_wording(self):
        self.assertIn(
            "**Do NOT hardcode `service.instance.id`.**", self.text
        )
        self.assertNotIn("**Do NOT set `service.instance.id`.**", self.text)

    def test_service_instance_id_rationale_updated(self):
        self.assertIn(
            "Generate or inject a unique value per process when\n  the "
            "selected SDK does not do so automatically.",
            self.text,
        )

    def test_otel_instrumentation_exclude_pattern_hedged(self):
        self.assertNotIn(
            "they are ignored when a config file is\nactive", self.text
        )
        self.assertIn(
            "as a second configuration channel unless the\nselected runtime "
            "explicitly documents how they combine with file configuration.",
            self.text,
        )

    def test_env_var_precedence_bad_example_comment_hedged(self):
        self.assertIn(
            "# BAD: assuming OTEL_* knobs merge predictably with a config file.",
            self.text,
        )
        self.assertNotIn(
            "# BAD: when a config file is set, OTEL_* knobs are IGNORED",
            self.text,
        )

    def test_sdk_ignores_env_vars_absolute_claim_removed(self):
        self.assertNotIn(
            "the SDK ignores\nenvironment variables when a config file is active",
            self.text,
        )

    def test_runtime_specific_precedence_wording_present(self):
        self.assertIn(
            "Configuration precedence and automatic file loading are "
            "runtime-specific.",
            self.text,
        )

    def test_health_check_exclusion_conditioned_on_sampler_support(self):
        self.assertIn(
            "when that sampler is supported, not a second configuration\nchannel.",
            self.text,
        )

    def test_frontmatter_unchanged_and_valid(self):
        frontmatter = extract_frontmatter(self.text)
        self.assertEqual(frontmatter["name"], "ollygarden-otel-declarative-config")


class TestGoSetupSkill(unittest.TestCase):
    """skills/ollygarden-otel-go-setup/SKILL.md

    The semconv import path bumped from v1.40.0 to v1.41.0.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = read("ollygarden-otel-go-setup", "SKILL.md")

    def test_old_semconv_version_absent(self):
        self.assertNotIn("v1.40.0", self.text)

    def test_new_semconv_version_present(self):
        self.assertIn(
            'semconv "go.opentelemetry.io/otel/semconv/v1.41.0"', self.text
        )

    def test_go_import_block_still_well_formed(self):
        go_blocks = extract_code_blocks(self.text, "go")
        import_blocks = [b for b in go_blocks if "semconv " in b]
        self.assertTrue(import_blocks, "expected a go code block importing semconv")
        self.assertIn('"go.opentelemetry.io/otel/semconv/v1.41.0"', import_blocks[0])


class TestInstrumentationPlanningSkill(unittest.TestCase):
    """skills/ollygarden-otel-instrumentation-planning/SKILL.md

    Step 3.2 error-handling guidance was softened from a flat "the
    deprecated APIs" claim to a runtime-conditional migration recommendation.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = read("ollygarden-otel-instrumentation-planning", "SKILL.md")

    def test_old_deprecated_wording_removed(self):
        self.assertNotIn(
            "record the exception via the Logs API (not the deprecated", self.text
        )

    def test_new_migration_wording_present(self):
        normalized = " ".join(self.text.split())
        self.assertIn(
            "prefer the Logs API for new instrumentation, following the "
            "accepted span-events-to-logs migration plan.",
            normalized,
        )
        self.assertIn(
            "Span event APIs are not yet deprecated in released specifications "
            "or every language SDK.",
            normalized,
        )

    def test_error_type_attribute_still_required(self):
        self.assertIn("Set the `error.type` attribute.", self.text)

    def test_frontmatter_unchanged_and_valid(self):
        frontmatter = extract_frontmatter(self.text)
        self.assertEqual(frontmatter["name"], "ollygarden-otel-instrumentation-planning")


class TestSignalSelectionReference(unittest.TestCase):
    """skills/ollygarden-otel-instrumentation-planning/references/signal-selection.md

    The "Span Event API Deprecation" section was renamed to "Span Events to
    Logs Migration" and rewritten to point at OTEP 4430 and the dedicated
    migration-status skill instead of asserting a flat deprecation.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = read(
            "ollygarden-otel-instrumentation-planning",
            "references",
            "signal-selection.md",
        )

    def test_old_heading_removed(self):
        self.assertNotIn("## Span Event API Deprecation", self.text)

    def test_new_heading_present(self):
        self.assertIn("## Span Events to Logs Migration", self.text)

    def test_old_flat_deprecation_claim_removed(self):
        self.assertNotIn(
            "Do not use `span.AddEvent()` or `span.RecordException()`. These "
            "APIs are deprecated.",
            self.text,
        )

    def test_otep_4430_reference_present(self):
        self.assertIn("OTEP 4430", self.text)

    def test_migration_skill_reference_present(self):
        self.assertIn("otel-span-events-to-logs-migration", self.text)

    def test_bridge_availability_caveat_present(self):
        normalized = " ".join(self.text.split())
        self.assertIn(
            "Bridge availability is language- and version-specific, so "
            "verify it with the `otel-span-events-to-logs-migration` skill "
            "before claiming that a log record will also appear as a span event.",
            normalized,
        )

    def test_error_handling_item_2_updated(self):
        normalized = " ".join(self.text.split())
        self.assertIn(
            "**Record the exception** via the Logs API for new instrumentation. "
            "The accepted span-events-to-logs migration plan does not itself "
            "deprecate every released span event API.",
            normalized,
        )
        self.assertNotIn(
            "not deprecated `span.AddEvent()` or", normalized
        )

    def test_span_status_rule_item_2_updated(self):
        normalized = " ".join(self.text.split())
        self.assertIn(
            "**Record the exception** via the Logs API for new instrumentation. "
            "The accepted span-events-to-logs migration plan does not itself "
            "deprecate every released span event API.",
            normalized,
        )


class TestJavaSetupSkill(unittest.TestCase):
    """skills/ollygarden-otel-java-setup/SKILL.md

    Clarifies that the Javaagent, Spring Boot Starter, and manual
    autoconfigure paths each load declarative config differently, adds the
    declarative-config extension dependency for manual autoconfigure, and
    switches the Spring Boot example from `application.properties` /
    `otel.config.file` to `application.yaml` / `otel.file_format`.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = read("ollygarden-otel-java-setup", "SKILL.md")

    def test_decision_tree_followup_paragraph_present(self):
        self.assertIn(
            "The Javaagent loads a standalone file via `-Dotel.config.file`.",
            self.text,
        )
        self.assertIn(
            "it does not load `otel.config.file`.", self.text
        )
        self.assertIn(
            "Manual autoconfigure needs the\ndeclarative-config extension in "
            "addition to the autoconfigure extension.",
            self.text,
        )

    def test_old_all_paths_support_sentence_removed(self):
        self.assertNotIn(
            "All paths support declarative configuration via `-Dotel.config.file`.",
            self.text,
        )

    def test_spring_boot_example_uses_yaml_not_properties(self):
        self.assertIn("Configure via `application.yaml`", self.text)
        self.assertNotIn("Configure via `application.properties`", self.text)
        self.assertNotIn("otel.config.file=configs/otel.yaml", self.text)

    def test_spring_boot_yaml_block_has_file_format_key(self):
        yaml_blocks = extract_code_blocks(self.text, "yaml")
        otel_blocks = [b for b in yaml_blocks if "file_format" in b]
        self.assertTrue(otel_blocks, "expected a yaml block with otel.file_format")
        parsed = yaml.safe_load(_strip_inline_comments(otel_blocks[0]))
        self.assertIn("otel", parsed)
        self.assertEqual(parsed["otel"]["file_format"], "1.0")

    def test_manual_autoconfigure_has_declarative_config_extension_dependency(self):
        xml_blocks = extract_code_blocks(self.text, "xml")
        autoconfigure_blocks = [
            b for b in xml_blocks if "opentelemetry-sdk-extension-autoconfigure" in b
        ]
        self.assertTrue(autoconfigure_blocks)
        self.assertIn(
            "opentelemetry-sdk-extension-declarative-config", autoconfigure_blocks[0]
        )

    def test_bom_alignment_mentions_bom_alpha(self):
        self.assertIn("opentelemetry-bom-alpha", self.text)
        self.assertIn(
            "Import `opentelemetry-bom` for stable artifacts and the matching\n  "
            "`opentelemetry-bom-alpha` for the alpha declarative-config extension.",
            self.text,
        )

    def test_old_bom_only_sentence_removed(self):
        self.assertNotIn(
            "Always use the BOM to align dependency versions.", self.text
        )

    def test_frontmatter_unchanged_and_valid(self):
        frontmatter = extract_frontmatter(self.text)
        self.assertEqual(frontmatter["name"], "ollygarden-otel-java-setup")


def _strip_inline_comments(yaml_text: str) -> str:
    """Strip trailing `# ...` comments so illustrative placeholder comments
    (e.g. '# use the literal supported by the selected Starter release')
    don't interfere with YAML parsing of the example block."""
    lines = []
    for line in yaml_text.splitlines():
        if line.strip().startswith("#"):
            continue
        lines.append(re.sub(r"\s+#.*$", "", line))
    return "\n".join(lines)


class TestJsSetupSkill(unittest.TestCase):
    """skills/ollygarden-otel-js-setup/SKILL.md

    The primary instrumentation-file example switched from the
    programmatic `new NodeSDK(...)` + explicit `sdk.start()` call to the
    declarative `startNodeSDK(...)` helper, which loads OTEL_CONFIG_FILE
    on its own and does not require an explicit start call.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = read("ollygarden-otel-js-setup", "SKILL.md")

    def test_start_node_sdk_imported_in_primary_example(self):
        self.assertIn(
            "import { startNodeSDK } from '@opentelemetry/sdk-node';", self.text
        )

    def test_primary_example_calls_start_node_sdk(self):
        self.assertIn("export const sdk = startNodeSDK({", self.text)

    def test_primary_example_no_longer_uses_new_node_sdk_directly(self):
        # The primary "Instrumentation File" example must not *construct*
        # NodeSDK directly anymore -- only the explicit "Fallback" section
        # (further down the file) still does. A comment merely mentioning
        # "new NodeSDK(...)" for contrast is fine; an actual assignment is not.
        instrumentation_file_section = self.text.split("## Entry Point")[0]
        self.assertNotIn("= new NodeSDK(", instrumentation_file_section)

    def test_fallback_section_still_uses_programmatic_node_sdk(self):
        fallback_section = self.text.split("## Fallback: Programmatic NodeSDK Setup")[-1]
        self.assertIn("import { NodeSDK } from '@opentelemetry/sdk-node';", fallback_section)
        self.assertIn("export const sdk = new NodeSDK({", fallback_section)

    def test_entry_point_no_longer_calls_sdk_start(self):
        self.assertNotIn("sdk.start();", self.text)

    def test_entry_point_comment_explains_no_explicit_start(self):
        self.assertIn(
            "// startNodeSDK loads OTEL_CONFIG_FILE and registers the configured providers.",
            self.text,
        )
        self.assertIn(
            "// new NodeSDK(...) is the separate programmatic path and does not load the file.",
            self.text,
        )

    def test_typescript_primary_example_block_is_well_formed(self):
        ts_blocks = extract_code_blocks(self.text, "typescript")
        primary_blocks = [b for b in ts_blocks if "startNodeSDK" in b]
        self.assertTrue(primary_blocks, "expected a typescript block using startNodeSDK")
        primary = primary_blocks[0]
        self.assertIn("getNodeAutoInstrumentations", primary)
        self.assertNotIn("sdk.start()", primary)

    def test_frontmatter_unchanged_and_valid(self):
        frontmatter = extract_frontmatter(self.text)
        self.assertEqual(frontmatter["name"], "ollygarden-otel-js-setup")


class TestAllChangedSkillFilesExistAndAreNonEmpty(unittest.TestCase):
    """Sanity check that every file touched by this PR is present and non-empty."""

    CHANGED_FILES = [
        ("ollygarden-otel-collector-config-decomposition", "SKILL.md"),
        ("ollygarden-otel-collector-config-decomposition", "references", "mechanics.md"),
        ("ollygarden-otel-collector-config-validation", "SKILL.md"),
        ("ollygarden-otel-collector-k8s-daemonset", "references", "validating.md"),
        ("ollygarden-otel-declarative-config", "SKILL.md"),
        ("ollygarden-otel-go-setup", "SKILL.md"),
        ("ollygarden-otel-instrumentation-planning", "SKILL.md"),
        ("ollygarden-otel-instrumentation-planning", "references", "signal-selection.md"),
        ("ollygarden-otel-java-setup", "SKILL.md"),
        ("ollygarden-otel-js-setup", "SKILL.md"),
    ]

    def test_all_changed_files_exist_and_nonempty(self):
        for parts in self.CHANGED_FILES:
            with self.subTest(path="/".join(parts)):
                content = read(*parts)
                self.assertTrue(content.strip())


if __name__ == "__main__":
    unittest.main()
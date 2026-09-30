"""Behavior contracts for the deterministic Governance Pages artifact."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PROOF = ROOT / "tests" / "fixtures" / "governance-pages-source-proof.json"


def load_tool(name: str):
    path = ROOT / "tools" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


pages = load_tool("build_governance_pages")
secret_shapes = load_tool("scan_secret_shapes")


def run_git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def fixture_proof(**changes: str) -> dict[str, str]:
    proof = json.loads(FIXTURE_PROOF.read_text(encoding="utf-8"))
    proof.update(changes)
    return proof


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def refresh_inventory(output: Path) -> None:
    manifest_path = output / "manifest.json"
    manifest = pages.load_json(manifest_path)
    inventory = pages.inventory_records(output)
    schema_paths = {schema["outputPath"] for schema in manifest["schemas"]}
    manifest["inventory"]["files"] = inventory
    manifest["digests"] = {
        "content": pages.records_digest(
            item for item in inventory if item["path"] not in schema_paths
        ),
        "schemas": pages.records_digest(
            item for item in inventory if item["path"] in schema_paths
        ),
    }
    write_json(manifest_path, manifest)


class GovernancePagesTests(unittest.TestCase):
    def build_fixture(
        self,
        parent: Path,
        name: str = "site",
        *,
        canonical_origin: str | None = None,
        cname: str | None = None,
    ) -> tuple[Path, dict[str, object]]:
        output = parent / name
        manifest = pages.build_site(
            ROOT,
            FIXTURE_PROOF,
            output,
            canonical_origin=canonical_origin,
            cname=cname,
            allow_fixture_standing=True,
        )
        return output, manifest

    def test_schema_catalog_links_each_registered_schema_to_itself(self) -> None:
        descriptions = pages._catalog_descriptions(ROOT)
        schema_names = {
            path.name for path in (ROOT / "schemas").glob("*.schema.json")
        }
        self.assertEqual(schema_names, set(descriptions))

    def test_schema_catalog_rejects_a_mismatched_link_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            schemas = source / "schemas"
            schemas.mkdir()
            (schemas / "README.md").write_text(
                "| Schema | Record |\n"
                "| --- | --- |\n"
                "| [`receipt.schema.json`](other.schema.json) | Receipt |\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                pages.PagesBuildError,
                "must target the same filename",
            ):
                pages._catalog_descriptions(source)

    def test_fixture_standing_is_explicit_and_cli_path_rejects_it(self) -> None:
        with self.assertRaisesRegex(pages.PagesBuildError, "fixture standing"):
            pages.load_source_proof(FIXTURE_PROOF, ROOT)
        proof = pages.load_source_proof(
            FIXTURE_PROOF,
            ROOT,
            allow_fixture_standing=True,
        )
        self.assertEqual("fixture", proof.standing)

    def test_clean_standing_requires_exact_head_and_zero_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            source = temporary_root / "source"
            source.mkdir()
            shutil.copytree(ROOT / "schemas", source / "schemas")
            shutil.copytree(
                ROOT / "schema-projections",
                source / "schema-projections",
            )
            shutil.copytree(ROOT / ".agents", source / ".agents")
            shutil.copy2(ROOT / "GOVERNANCE.md", source / "GOVERNANCE.md")
            run_git(source, "init", "--initial-branch=develop")
            run_git(source, "config", "user.name", "Governance Fixture")
            run_git(source, "config", "user.email", "governance@example.invalid")
            run_git(source, "config", "commit.gpgSign", "false")
            run_git(
                source,
                "remote",
                "add",
                "origin",
                f"https://github.com/{pages.REPOSITORY}.git",
            )
            run_git(source, "add", "--all")
            run_git(
                source,
                "commit",
                "--no-gpg-sign",
                "-m",
                "Create accepted source fixture",
            )
            revision = run_git(source, "rev-parse", "HEAD")
            proof_path = temporary_root / "proof.json"
            write_json(
                proof_path,
                fixture_proof(sourceRevision=revision, standing="clean"),
            )

            output = temporary_root / "site"
            manifest = pages.build_site(source, proof_path, output)
            self.assertEqual(revision, manifest["source"]["sourceRevision"])
            self.assertEqual("clean", manifest["source"]["standing"])

            nested = source / "nested-source"
            nested.mkdir()
            with self.assertRaisesRegex(pages.PagesBuildError, "worktree root"):
                pages.load_source_proof(proof_path, nested)
            nested.rmdir()

            inside_proof = source / "proof.json"
            write_json(
                inside_proof,
                fixture_proof(sourceRevision=revision, standing="clean"),
            )
            with self.assertRaisesRegex(pages.PagesBuildError, "outside"):
                pages.load_source_proof(inside_proof, source)
            inside_proof.unlink()

            run_git(source, "remote", "set-url", "origin", "https://github.com/example/other.git")
            with self.assertRaisesRegex(pages.PagesBuildError, "origin differs"):
                pages.load_source_proof(proof_path, source)
            run_git(
                source,
                "remote",
                "set-url",
                "origin",
                f"https://github.com/{pages.REPOSITORY}.git",
            )

            run_git(
                source,
                "remote",
                "set-url",
                "--add",
                "origin",
                "https://github.com/example/secondary-wrong.git",
            )
            with self.assertRaisesRegex(pages.PagesBuildError, "origin differs"):
                pages.load_source_proof(proof_path, source)
            run_git(source, "config", "--unset-all", "remote.origin.url")
            run_git(
                source,
                "config",
                "--add",
                "remote.origin.url",
                f"https://github.com/{pages.REPOSITORY}.git",
            )

            source_alias = temporary_root / "source-alias"
            source_alias.symlink_to(source, target_is_directory=True)
            with self.assertRaisesRegex(pages.PagesBuildError, "symbolic-link"):
                pages.load_source_proof(proof_path, source_alias)

            proof_alias = temporary_root / "proof-alias.json"
            proof_alias.symlink_to(proof_path)
            with self.assertRaisesRegex(pages.PagesBuildError, "symbolic-link"):
                pages.load_source_proof(proof_alias, source)

            with mock.patch.dict(
                os.environ,
                {
                    "GIT_DIR": str(temporary_root / "redirected.git"),
                    "GIT_WORK_TREE": str(temporary_root / "redirected-worktree"),
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "core.worktree",
                    "GIT_CONFIG_VALUE_0": str(temporary_root / "redirected-worktree"),
                },
            ):
                self.assertEqual(
                    revision,
                    pages.load_source_proof(proof_path, source).source_revision,
                )

            governance = source / "GOVERNANCE.md"
            governance_bytes = governance.read_bytes()
            governance.write_text(
                "changed after acceptance\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(pages.PagesBuildError, "zero changes"):
                pages.load_source_proof(proof_path, source)
            governance.write_bytes(governance_bytes)

            write_json(
                proof_path,
                fixture_proof(sourceRevision="a" * 40, standing="clean"),
            )
            with self.assertRaisesRegex(pages.PagesBuildError, "exact checked-out HEAD"):
                pages.load_source_proof(proof_path, source)

            write_json(
                proof_path,
                fixture_proof(sourceRevision=revision, standing="clean"),
            )
            schema_relative = "schemas/acceptance.schema.json"
            schema = source / schema_relative
            schema_bytes = schema.read_bytes()
            run_git(source, "update-index", "--assume-unchanged", schema_relative)
            schema.write_bytes(schema_bytes + b"\n")
            self.assertEqual(
                "",
                run_git(source, "status", "--porcelain=v1", "--untracked-files=all"),
            )
            with self.assertRaisesRegex(pages.PagesBuildError, "index flags mask"):
                pages.load_source_proof(proof_path, source)

            run_git(source, "update-index", "--no-assume-unchanged", schema_relative)
            schema.write_bytes(schema_bytes)
            run_git(source, "update-index", "--skip-worktree", schema_relative)
            schema.write_bytes(schema_bytes + b"\n")
            self.assertEqual(
                "",
                run_git(source, "status", "--porcelain=v1", "--untracked-files=all"),
            )
            with self.assertRaisesRegex(pages.PagesBuildError, "index flags mask"):
                pages.load_source_proof(proof_path, source)

    def test_clean_source_proof_ignores_local_replace_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            source = temporary_root / "source"
            source.mkdir()
            shutil.copytree(ROOT / "schemas", source / "schemas")
            shutil.copy2(ROOT / "GOVERNANCE.md", source / "GOVERNANCE.md")
            for arguments in (
                ("init", "--initial-branch=develop"),
                ("config", "user.name", "Governance Fixture"),
                ("config", "user.email", "governance@example.invalid"),
                ("config", "commit.gpgSign", "false"),
                (
                    "remote",
                    "add",
                    "origin",
                    f"https://github.com/{pages.REPOSITORY}.git",
                ),
                ("add", "--all"),
                ("commit", "--no-gpg-sign", "-m", "Create accepted source"),
            ):
                run_git(source, *arguments)
            accepted_revision = run_git(source, "rev-parse", "HEAD")

            governance = source / "GOVERNANCE.md"
            governance.write_text("replacement source\n", encoding="utf-8")
            run_git(source, "add", "GOVERNANCE.md")
            run_git(
                source,
                "commit",
                "--no-gpg-sign",
                "-m",
                "Create replacement source",
            )
            replacement_revision = run_git(source, "rev-parse", "HEAD")
            run_git(source, "reset", "--soft", accepted_revision)
            run_git(source, "replace", accepted_revision, replacement_revision)

            self.assertEqual(
                "",
                run_git(source, "status", "--porcelain=v1", "--untracked-files=all"),
            )
            proof_path = temporary_root / "proof.json"
            write_json(
                proof_path,
                fixture_proof(sourceRevision=accepted_revision, standing="clean"),
            )
            with self.assertRaisesRegex(pages.PagesBuildError, "zero changes"):
                pages.load_source_proof(proof_path, source)

    def test_two_isolated_builds_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            first, _ = self.build_fixture(parent, "first")
            second, _ = self.build_fixture(parent, "second")
            first_files = {
                path.relative_to(first).as_posix(): path.read_bytes()
                for path in first.rglob("*")
                if path.is_file()
            }
            second_files = {
                path.relative_to(second).as_posix(): path.read_bytes()
                for path in second.rglob("*")
                if path.is_file()
            }
            self.assertEqual(first_files, second_files)

    def test_manifest_binds_release_authority_source_and_complete_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build_fixture(Path(temporary))
            self.assertEqual(
                {
                    "authority": pages.RELEASE_AUTHORITY,
                    "schemaCoordinate": pages.SCHEMA_COORDINATE,
                    "status": pages.RELEASE_STATUS,
                    "version": pages.RELEASE_VERSION,
                },
                manifest["release"],
            )
            self.assertEqual("fixture", manifest["source"]["standing"])
            self.assertEqual(
                "f" * 40,
                manifest["source"]["sourceRevision"],
            )
            self.assertEqual(["manifest.json"], manifest["inventory"]["excludes"])
            self.assertEqual("1.1.0", manifest["manifestVersion"])
            declared = {item["path"] for item in manifest["inventory"]["files"]}
            actual = {
                path.relative_to(output).as_posix()
                for path in output.rglob("*")
                if path.is_file() and path.name != "manifest.json"
            }
            self.assertEqual(actual, declared)
            self.assertEqual(
                manifest,
                pages.validate_site(
                    output,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                ),
            )

    def test_candidate_projection_family_keeps_json_authority_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build_fixture(Path(temporary))
            self.assertEqual(1, len(manifest["schemaFamilies"]))
            family = manifest["schemaFamilies"][0]
            self.assertEqual("promotion-receipt", family["family"])
            self.assertEqual("candidate", family["projectionStatus"])
            self.assertEqual(
                pages.SCHEMA_ID_PREFIX
                + "projections/promotion-receipt/v1.0.0/",
                family["familyIdentifier"],
            )
            self.assertEqual(
                {
                    "format": "json-schema-2020-12",
                    "identifier": pages.SCHEMA_ID_PREFIX
                    + "promotion-receipt.schema.json",
                    "outputPath": "schemas/v2.0/promotion-receipt.schema.json",
                    "sourcePath": "schemas/promotion-receipt.schema.json",
                },
                family["validationAuthority"],
            )
            representations = {
                record["format"]: record for record in family["representations"]
            }
            self.assertEqual(
                {
                    "constraint-coverage-ledger",
                    "graphql-sdl",
                    "yaml-1.2",
                },
                set(representations),
            )
            self.assertEqual(
                "text/plain; charset=utf-8",
                representations["graphql-sdl"]["mediaType"],
            )
            self.assertEqual(
                "application/yaml",
                representations["yaml-1.2"]["mediaType"],
            )
            for record in representations.values():
                self.assertTrue(
                    record["outputPath"].startswith(
                        "schemas/v2.0/projections/promotion-receipt/v1.0.0/"
                    )
                )
                self.assertEqual(
                    pages.SCHEMA_ID_PREFIX
                    + record["outputPath"].removeprefix("schemas/v2.0/"),
                    record["identifier"],
                )
                self.assertEqual(
                    record["bytes"],
                    len((output / record["outputPath"]).read_bytes()),
                )
                self.assertIn(f"/{'f' * 40}/", record["sourceUrl"])

            accepted_names = sorted(
                path.name for path in (ROOT / "schemas").glob("*.schema.json")
            )
            self.assertEqual(
                accepted_names,
                sorted(Path(item["outputPath"]).name for item in manifest["schemas"]),
            )

    def test_every_schema_is_an_exact_source_copy_with_a_full_sha_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build_fixture(Path(temporary))
            source_names = sorted(path.name for path in (ROOT / "schemas").glob("*.schema.json"))
            published_names = sorted(Path(item["outputPath"]).name for item in manifest["schemas"])
            self.assertEqual(source_names, published_names)
            for schema in manifest["schemas"]:
                self.assertEqual(
                    (ROOT / schema["sourcePath"]).read_bytes(),
                    (output / schema["outputPath"]).read_bytes(),
                )
                self.assertIn(f"/{'f' * 40}/", schema["sourceUrl"])

    def test_every_html_page_has_accessible_metadata_markers_and_footer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build_fixture(Path(temporary))
            self.assertEqual(
                list(pages.HTML_PATHS),
                manifest["publication"]["htmlPaths"],
            )
            for relative_path in pages.HTML_PATHS:
                content = (output / relative_path).read_text(encoding="utf-8")
                self.assertIn('<html lang="en">', content)
                self.assertIn('class="skip-link" href="#main"', content)
                self.assertIn(f'name="author" content="{pages.ORGANIZATION}"', content)
                self.assertIn(f'name="publisher" content="{pages.ORGANIZATION}"', content)
                self.assertEqual(1, content.count(pages.ATTRIBUTION_FOOTER))
                self.assertLess(
                    content.index(pages.MAPS_MARKER_LINE),
                    content.index(pages.BIG_BENCH_MARKER_LINE),
                )
                self.assertIn(pages.MARKER_CONTEXT, content)
            stylesheet = (output / "assets" / "site.css").read_text(encoding="utf-8")
            self.assertIn(
                ".visitor-boundary__marker { max-width: none; overflow-wrap: anywhere;",
                stylesheet,
            )

    def test_public_ready_skill_is_source_faithful_and_exactly_routed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build_fixture(Path(temporary))
            self.assertEqual(1, len(manifest["skills"]))
            skill = manifest["skills"][0]
            self.assertEqual(pages.PUBLIC_SKILL_SLUG, skill["name"])
            self.assertEqual(pages.PUBLIC_SKILL_SOURCE_PATH, skill["sourcePath"])
            self.assertEqual(pages.PUBLIC_SKILL_OUTPUT_PATH, skill["outputPath"])
            self.assertEqual(pages.PUBLIC_SKILL_PAGE_PATH, skill["pagePath"])
            self.assertIn(f"/{'f' * 40}/", skill["sourceUrl"])
            self.assertEqual(
                (ROOT / pages.PUBLIC_SKILL_SOURCE_PATH).read_bytes(),
                (output / pages.PUBLIC_SKILL_OUTPUT_PATH).read_bytes(),
            )
            self.assertTrue((output / "skills" / "index.html").is_file())
            self.assertTrue((output / pages.PUBLIC_SKILL_PAGE_PATH).is_file())
            page = (output / pages.PUBLIC_SKILL_PAGE_PATH).read_text(encoding="utf-8")
            self.assertIn('href="SKILL.md"', page)
            self.assertIn(pages.PUBLIC_SKILL_METADATA["lineage_key"], page)
            public_possible = {
                path.parent.name
                for path in (ROOT / ".agents" / "skills").glob("*/SKILL.md")
                if pages.parse_skill_source(path)[0].get("source_band")
                == "public_possible"
            }
            self.assertEqual(
                {
                    "contextual-jargon-scan",
                    "repository-reentry",
                    "source-authority-mapping",
                },
                public_possible,
            )
            self.assertTrue(
                public_possible.isdisjoint(
                    {record["name"] for record in manifest["skills"]}
                )
            )
            for skill_name in public_possible:
                self.assertFalse((output / "skills" / skill_name).exists())

    def test_projected_skill_has_no_unpublished_relative_markdown_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, _ = self.build_fixture(Path(temporary))
            content = (output / pages.PUBLIC_SKILL_OUTPUT_PATH).read_text(
                encoding="utf-8"
            )
            self.assertEqual((), pages.markdown_relative_targets(content))

    def test_public_ready_skill_refuses_html_line_breaks(self) -> None:
        for marker in (
            "<br>",
            "<BR>",
            "<br/>",
            "<br />",
            '<br class="scenario-break">',
            '<br data-kind="scenario"/>',
            '<br\nclass="scenario-break">',
        ):
            with self.subTest(marker=marker):
                with tempfile.TemporaryDirectory() as temporary:
                    source = Path(temporary) / "source"
                    shutil.copytree(ROOT / ".agents", source / ".agents")
                    skill = source / pages.PUBLIC_SKILL_SOURCE_PATH
                    skill.write_text(
                        skill.read_text(encoding="utf-8") + f"\n{marker}\n",
                        encoding="utf-8",
                    )
                    proof = pages.load_source_proof(
                        FIXTURE_PROOF,
                        source,
                        allow_fixture_standing=True,
                    )
                    with self.assertRaisesRegex(
                        pages.PagesBuildError,
                        "HTML line-break element",
                    ):
                        pages.collect_public_skills(source, proof)

    def test_html_line_break_guard_preserves_nearby_tag_names(self) -> None:
        for marker in ("<break>", "<bracket>", "<broom>"):
            with self.subTest(marker=marker):
                self.assertIsNone(pages.HTML_LINE_BREAK.search(marker))

    def test_public_ready_skill_inventory_is_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            shutil.copytree(ROOT / ".agents", source / ".agents")
            extra = source / ".agents" / "skills" / "extra" / "SKILL.md"
            extra.parent.mkdir(parents=True)
            extra.write_text(
                "---\nname: extra\nsource_band: public_ready\n---\n# Extra\n",
                encoding="utf-8",
            )
            proof = pages.load_source_proof(
                FIXTURE_PROOF,
                source,
                allow_fixture_standing=True,
            )
            with self.assertRaisesRegex(pages.PagesBuildError, "inventory differs"):
                pages.collect_public_skills(source, proof)

    def test_default_build_has_no_canonical_metadata_or_cname(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build_fixture(Path(temporary))
            publication = manifest["publication"]
            self.assertIsNone(publication["canonicalOrigin"])
            self.assertIsNone(publication["cname"])
            self.assertEqual([], publication["canonicalHtmlPaths"])
            self.assertFalse((output / "CNAME").exists())
            self.assertEqual(b"", (output / ".nojekyll").read_bytes())
            for relative_path in pages.HTML_PATHS:
                self.assertNotIn(
                    'rel="canonical"',
                    (output / relative_path).read_text(encoding="utf-8"),
                )

    def test_explicit_https_origin_and_matching_cname_cover_every_html_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build_fixture(
                Path(temporary),
                canonical_origin="https://governance.example.org/contracts",
                cname="governance.example.org",
            )
            publication = manifest["publication"]
            self.assertEqual(
                list(pages.HTML_PATHS),
                publication["canonicalHtmlPaths"],
            )
            self.assertEqual(
                "governance.example.org\n",
                (output / "CNAME").read_text(encoding="utf-8"),
            )
            for record in publication["html"]:
                self.assertIsNotNone(record["canonicalUrl"])
                self.assertIn(
                    f'rel="canonical" href="{record["canonicalUrl"]}"',
                    (output / record["path"]).read_text(encoding="utf-8"),
                )

    def test_cname_requires_an_explicit_matching_origin(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            with self.assertRaisesRegex(pages.PagesBuildError, "requires"):
                self.build_fixture(parent, "absent-origin", cname="governance.example.org")
            with self.assertRaisesRegex(pages.PagesBuildError, "must match"):
                self.build_fixture(
                    parent,
                    "different-origin",
                    canonical_origin="https://schemas.example.org",
                    cname="governance.example.org",
                )

    def test_schema_byte_mutation_fails_after_inventory_is_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build_fixture(Path(temporary))
            schema_path = output / manifest["schemas"][0]["outputPath"]
            schema_path.write_bytes(schema_path.read_bytes() + b"\n")
            refresh_inventory(output)
            with self.assertRaisesRegex(pages.PagesBuildError, "schema records|schema bytes"):
                pages.validate_site(
                    output,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                )

    def test_skill_byte_mutation_fails_after_inventory_is_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, _ = self.build_fixture(Path(temporary))
            skill_path = output / pages.PUBLIC_SKILL_OUTPUT_PATH
            skill_path.write_bytes(skill_path.read_bytes() + b"\n")
            refresh_inventory(output)
            with self.assertRaisesRegex(pages.PagesBuildError, "published skill bytes"):
                pages.validate_site(
                    output,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                )

    def test_projection_byte_mutation_fails_after_inventory_is_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build_fixture(Path(temporary))
            projection_path = output / manifest["schemaFamilies"][0][
                "representations"
            ][0]["outputPath"]
            projection_path.write_bytes(projection_path.read_bytes() + b"\n")
            refresh_inventory(output)
            with self.assertRaisesRegex(
                pages.PagesBuildError,
                "schema projection bytes differ",
            ):
                pages.validate_site(
                    output,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                )

    def test_marker_mutation_fails_after_inventory_is_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, _ = self.build_fixture(Path(temporary))
            page_path = output / "index.html"
            content = page_path.read_text(encoding="utf-8")
            page_path.write_text(
                content.replace(pages.MAPS_MARKER_LINE, "marker removed", 1),
                encoding="utf-8",
            )
            refresh_inventory(output)
            with self.assertRaisesRegex(pages.PagesBuildError, "visible publication text"):
                pages.validate_site(
                    output,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                )

    def test_short_source_link_mutation_fails_after_inventory_is_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, _ = self.build_fixture(Path(temporary))
            page_path = output / "index.html"
            content = page_path.read_text(encoding="utf-8")
            page_path.write_text(
                content.replace("f" * 40, "f" * 12, 1),
                encoding="utf-8",
            )
            refresh_inventory(output)
            with self.assertRaisesRegex(pages.PagesBuildError, "full SHA"):
                pages.validate_site(
                    output,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                )

    def test_wrong_repository_source_link_fails_after_inventory_is_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, _ = self.build_fixture(Path(temporary))
            page_path = output / "index.html"
            content = page_path.read_text(encoding="utf-8")
            page_path.write_text(
                content.replace(pages.REPOSITORY, "example/other", 1),
                encoding="utf-8",
            )
            refresh_inventory(output)
            with self.assertRaisesRegex(pages.PagesBuildError, "different repository"):
                pages.validate_site(
                    output,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                )

    def test_artifact_symlink_fails_even_when_target_bytes_match(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            output, manifest = self.build_fixture(parent)
            schema = output / manifest["schemas"][0]["outputPath"]
            external = parent / "external-schema.json"
            external.write_bytes(schema.read_bytes())
            schema.unlink()
            schema.symlink_to(external)
            with self.assertRaisesRegex(pages.PagesBuildError, "self-contained"):
                pages.validate_site(
                    output,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                )

    def test_broken_relative_link_fails_after_inventory_is_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, _ = self.build_fixture(Path(temporary))
            page_path = output / "guidance" / "index.html"
            content = page_path.read_text(encoding="utf-8")
            page_path.write_text(
                content.replace("../schemas/index.html", "../missing/index.html", 1),
                encoding="utf-8",
            )
            refresh_inventory(output)
            with self.assertRaisesRegex(pages.PagesBuildError, "unresolved relative link"):
                pages.validate_site(
                    output,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                )

    def test_release_authority_mutation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, manifest = self.build_fixture(Path(temporary))
            manifest["release"]["status"] = "candidate"
            write_json(output / "manifest.json", manifest)
            with self.assertRaisesRegex(pages.PagesBuildError, "release authority"):
                pages.validate_site(
                    output,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                )

    def test_output_path_must_be_new_and_outside_the_source_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            output = parent / "site"
            output.mkdir()
            with self.assertRaisesRegex(pages.PagesBuildError, "already exists"):
                pages.build_site(
                    ROOT,
                    FIXTURE_PROOF,
                    output,
                    allow_fixture_standing=True,
                )

            valid, _ = self.build_fixture(parent, "valid")
            validation_alias = parent / "validation-alias"
            validation_alias.symlink_to(valid, target_is_directory=True)
            with self.assertRaisesRegex(pages.PagesBuildError, "symbolic-link"):
                pages.validate_site(
                    validation_alias,
                    ROOT,
                    FIXTURE_PROOF,
                    allow_fixture_standing=True,
                )

            build_parent = parent / "build-parent"
            build_parent.mkdir()
            build_parent_alias = parent / "build-parent-alias"
            build_parent_alias.symlink_to(build_parent, target_is_directory=True)
            with self.assertRaisesRegex(pages.PagesBuildError, "symbolic-link"):
                pages.build_site(
                    ROOT,
                    FIXTURE_PROOF,
                    build_parent_alias / "site",
                    allow_fixture_standing=True,
                )
        with self.assertRaisesRegex(pages.PagesBuildError, "outside"):
            pages.build_site(
                ROOT,
                FIXTURE_PROOF,
                ROOT / ".generated-pages",
                allow_fixture_standing=True,
            )

    def test_generated_artifact_is_clean_under_repository_secret_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output, _ = self.build_fixture(Path(temporary))
            self.assertEqual([], secret_shapes.scan_repository(output))

    def test_secret_scanner_observes_html_artifact_material(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = "gh" + "p_" + ("A" * 30)
            (root / "index.html").write_text(
                f"<p>{candidate}</p>\n",
                encoding="utf-8",
            )
            findings = secret_shapes.scan_repository(root)
            self.assertTrue(
                any(finding.rule == "github-token" for finding in findings),
                findings,
            )


if __name__ == "__main__":
    unittest.main()

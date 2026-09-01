"""Fail-closed semantic contract for bounded repository automation YAML."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any


class RestrictedYamlError(ValueError):
    """Raised when automation YAML leaves the supported, reviewable subset."""


class _MissingAutomationControls:
    """Distinguish an absent source projection from an explicit null value."""


MISSING_AUTOMATION_CONTROLS = _MissingAutomationControls()


_PLAIN_KEY = re.compile(r"[A-Za-z0-9_-]+")
_SECRET_EXPRESSION = re.compile(
    r"\$\{\{(?:(?!\}\}).)*\bsecrets\s*(?:\.|\[)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class _Line:
    number: int
    indent: int
    content: str


def _strip_comment(text: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(text):
        if quote == '"':
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if quote == "'":
            if character == quote:
                quote = None
            continue
        if character in {'"', "'"}:
            quote = character
        elif character == "#" and (index == 0 or text[index - 1].isspace()):
            return text[:index].rstrip()
    if quote is not None:
        raise RestrictedYamlError("unterminated quoted scalar")
    return text.rstrip()


def _split_mapping(text: str) -> tuple[str, str]:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(text):
        if quote == '"':
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if quote == "'":
            if character == quote:
                quote = None
            continue
        if character in {'"', "'"}:
            quote = character
        elif character == ":":
            key = text[:index].strip()
            if not key:
                raise RestrictedYamlError("mapping key is empty")
            return key, text[index + 1 :].strip()
    raise RestrictedYamlError(f"mapping entry lacks a colon: {text!r}")


def _scalar(text: str) -> Any:
    if not text:
        return None
    if text.startswith(("[", "{", "&", "*", "!", "|", ">")):
        raise RestrictedYamlError(f"unsupported scalar form: {text!r}")
    if text.startswith('"'):
        if not text.endswith('"'):
            raise RestrictedYamlError("unterminated double-quoted scalar")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise RestrictedYamlError(str(exc)) from exc
    if text.startswith("'"):
        if not text.endswith("'"):
            raise RestrictedYamlError("unterminated single-quoted scalar")
        return text[1:-1].replace("''", "'")
    if text in {"true", "false"}:
        return text == "true"
    if text in {"null", "~"}:
        return None
    if re.fullmatch(r"-?(?:0|[1-9][0-9]*)", text):
        return int(text)
    return text


class _RestrictedYamlParser:
    def __init__(self, text: str, source: str):
        self.lines = text.splitlines()
        self.source = source
        self.index = 0

    def error(self, message: str, line: int | None = None) -> RestrictedYamlError:
        location = line if line is not None else min(self.index + 1, len(self.lines))
        return RestrictedYamlError(f"{self.source}:{location}: {message}")

    def token(self, index: int) -> _Line | None:
        raw = self.lines[index]
        if "\t" in raw:
            raise self.error("tabs are outside the restricted YAML grammar", index + 1)
        stripped = raw.lstrip(" ")
        indent = len(raw) - len(stripped)
        if indent % 2:
            raise self.error("indentation must use two-space levels", index + 1)
        content = _strip_comment(stripped)
        if not content:
            return None
        if content in {"---", "..."} or content.startswith("%"):
            raise self.error("directives and document markers are unsupported", index + 1)
        return _Line(index + 1, indent, content)

    def peek(self) -> _Line | None:
        while self.index < len(self.lines):
            token = self.token(self.index)
            if token is not None:
                return token
            self.index += 1
        return None

    def parse(self) -> Any:
        first = self.peek()
        if first is None:
            raise self.error("document is empty", 1)
        if first.indent != 0:
            raise self.error("root content must start at column zero", first.number)
        value = self.parse_node(0)
        trailing = self.peek()
        if trailing is not None:
            raise self.error("unexpected trailing content", trailing.number)
        return value

    def parse_node(self, indent: int) -> Any:
        token = self.peek()
        if token is None or token.indent != indent:
            raise self.error("nested value has an unexpected indentation")
        if token.content == "-" or token.content.startswith("- "):
            return self.parse_sequence(indent)
        return self.parse_mapping(indent)

    def parse_mapping(
        self,
        indent: int,
        initial: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = {} if initial is None else dict(initial)
        while (token := self.peek()) is not None:
            if token.indent < indent:
                break
            if token.indent > indent:
                raise self.error("mapping indentation is not owned by a key", token.number)
            if token.content == "-" or token.content.startswith("- "):
                break
            self.index += 1
            key, raw_value = _split_mapping(token.content)
            if _PLAIN_KEY.fullmatch(key) is None:
                raise self.error("mapping key is outside the restricted grammar", token.number)
            parsed_key = key
            if parsed_key in result:
                raise self.error(f"duplicate mapping key {parsed_key!r}", token.number)
            result[parsed_key] = self.parse_value(raw_value, indent)
        return result

    def parse_sequence(self, indent: int) -> list[Any]:
        result: list[Any] = []
        while (token := self.peek()) is not None:
            if token.indent < indent:
                break
            if token.indent > indent:
                raise self.error("sequence indentation is not owned by an item", token.number)
            if not (token.content == "-" or token.content.startswith("- ")):
                break
            self.index += 1
            rest = token.content[1:].strip()
            if not rest:
                child = self.peek()
                if child is None or child.indent <= indent:
                    raise self.error("sequence item requires a nested value", token.number)
                result.append(self.parse_node(child.indent))
                continue
            try:
                key, raw_value = _split_mapping(rest)
            except RestrictedYamlError:
                result.append(_scalar(rest))
                child = self.peek()
                if child is not None and child.indent > indent:
                    raise self.error(
                        "scalar sequence item cannot own nested content",
                        child.number,
                    )
                continue
            if _PLAIN_KEY.fullmatch(key) is None:
                raise self.error("mapping key is outside the restricted grammar", token.number)
            parsed_key = key
            item_indent = indent + 2
            item = {parsed_key: self.parse_value(raw_value, item_indent)}
            child = self.peek()
            if child is not None and child.indent > indent:
                if child.indent != item_indent:
                    raise self.error(
                        "sequence mapping uses an unexpected indentation",
                        child.number,
                    )
                item = self.parse_mapping(item_indent, item)
            result.append(item)
        return result

    def parse_value(self, raw_value: str, parent_indent: int) -> Any:
        if raw_value in {"|", "|-", "|+"}:
            return self.parse_block_scalar(parent_indent, raw_value)
        if raw_value:
            return _scalar(raw_value)
        child = self.peek()
        if child is None or child.indent <= parent_indent:
            return None
        return self.parse_node(child.indent)

    def parse_block_scalar(self, parent_indent: int, style: str) -> str:
        captured: list[str] = []
        while self.index < len(self.lines):
            raw = self.lines[self.index]
            if "\t" in raw:
                raise self.error(
                    "tabs are outside the restricted YAML grammar", self.index + 1
                )
            if raw.strip():
                indent = len(raw) - len(raw.lstrip(" "))
                if indent <= parent_indent:
                    break
            captured.append(raw)
            self.index += 1
        nonblank_indents = [
            len(line) - len(line.lstrip(" ")) for line in captured if line.strip()
        ]
        if not nonblank_indents:
            return ""
        content_indent = min(nonblank_indents)
        if content_indent <= parent_indent:
            raise self.error("block scalar content requires deeper indentation")
        content = [line[content_indent:] if line.strip() else "" for line in captured]
        rendered = "\n".join(content)
        if not style.endswith("-"):
            rendered += "\n"
        return rendered


def load_restricted_yaml(text: str, source: str) -> Any:
    """Load the exact indentation-based YAML subset used by automation files."""
    return _RestrictedYamlParser(text, source).parse()


@dataclass(frozen=True)
class PullRequestContract:
    workflow_name: str
    job_name: str
    concurrency_group: str
    python_version: str
    step_names: tuple[str, ...]
    validation_commands: tuple[str, ...]
    install_command: str | None = None
    runner: str = "ubuntu-24.04"
    timeout_minutes: int = 10
    checkout_action: str = (
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
    )
    setup_python_action: str = (
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
    )


PULL_REQUEST_CONTRACT = PullRequestContract(
    workflow_name="Governance pull request",
    job_name="governance-pr-validation",
    concurrency_group="governance-pr-${{ github.event.pull_request.number }}",
    python_version="3.13",
    step_names=(
        "Check out the proposed source",
        "Select Python",
        "Validate repository-owned governance",
    ),
    validation_commands=(
        "python3 tools/validate_governance.py",
        "python3 tools/check_language.py",
        "python3 tools/scan_secret_shapes.py",
        "python3 -m unittest discover -s tests -v",
    ),
)

DEPENDABOT_CONTRACT = {
    "version": 2,
    "updates": [
        {
            "package-ecosystem": "github-actions",
            "directory": "/",
            "target-branch": "develop",
            "schedule": {"interval": "monthly"},
            "open-pull-requests-limit": 2,
            "groups": {
                "github-actions-minor-patch": {
                    "patterns": ["*"],
                    "update-types": ["minor", "patch"],
                }
            },
        }
    ],
}


def _commands(value: Any) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ()
    return tuple(
        line.strip()
        for line in value.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def _secret_expression_paths(value: Any, path: str = "$") -> list[str]:
    """Return semantic value paths that contain a raw GitHub secret expression."""
    if isinstance(value, str):
        return [path] if _SECRET_EXPRESSION.search(value) else []
    if isinstance(value, list):
        return [
            finding
            for index, item in enumerate(value)
            for finding in _secret_expression_paths(item, f"{path}[{index}]")
        ]
    if isinstance(value, dict):
        return [
            finding
            for key, item in value.items()
            for finding in _secret_expression_paths(item, f"{path}.{key}")
        ]
    return []


def _source_automation_controls(
    workflow: dict[str, Any],
    dependabot: dict[str, Any],
    contract: PullRequestContract,
) -> dict[str, Any]:
    """Project the admitted controls from the parsed source documents."""
    job = workflow["jobs"][contract.job_name]
    steps = job["steps"]
    setup = steps[1]
    validation = steps[-1]
    install_command = (
        _commands(steps[2]["run"])[0]
        if contract.install_command is not None
        else None
    )
    return {
        "contract_version": "1.0.0",
        "pull_request": {
            "path": ".github/workflows/pull-request.yml",
            "name": workflow["name"],
            "targets": workflow["on"]["pull_request"]["branches"],
            "permissions": workflow["permissions"],
            "concurrency": workflow["concurrency"],
            "job": {
                "id": contract.job_name,
                "name": job["name"],
                "runner": job["runs-on"],
                "timeout_minutes": job["timeout-minutes"],
                "python_version": setup["with"]["python-version"],
                "step_names": [step["name"] for step in steps],
                "checkout_action": steps[0]["uses"],
                "setup_python_action": setup["uses"],
                "install_command": install_command,
                "validation_commands": list(_commands(validation["run"])),
            },
        },
        "dependabot": {
            "path": ".github/dependabot.yml",
            "version": dependabot["version"],
            "updates": dependabot["updates"],
        },
    }


def validate_repository_automation(
    workflow_text: str,
    dependabot_text: str,
    declared_controls: Any = MISSING_AUTOMATION_CONTROLS,
) -> list[str]:
    """Return semantic differences from the declared pull-request contract."""
    findings: list[str] = []
    try:
        workflow = load_restricted_yaml(workflow_text, ".github/workflows/pull-request.yml")
    except RestrictedYamlError as exc:
        findings.append(f"pull-request workflow is outside the restricted YAML grammar: {exc}")
        workflow = None
    try:
        dependabot = load_restricted_yaml(dependabot_text, ".github/dependabot.yml")
    except RestrictedYamlError as exc:
        findings.append(f"Dependabot configuration is outside the restricted YAML grammar: {exc}")
        dependabot = None

    for label, document in (
        ("pull-request workflow", workflow),
        ("Dependabot configuration", dependabot),
    ):
        secret_paths = _secret_expression_paths(document)
        if secret_paths:
            findings.append(
                f"{label} contains raw GitHub secret expressions at "
                f"{', '.join(secret_paths)}"
            )

    contract = PULL_REQUEST_CONTRACT
    if not isinstance(workflow, dict):
        if workflow is not None:
            findings.append("pull-request workflow root must be a mapping")
    else:
        if set(workflow) != {"name", "on", "permissions", "concurrency", "jobs"}:
            findings.append("pull-request workflow top-level controls differ")
        if workflow.get("name") != contract.workflow_name:
            findings.append("pull-request workflow name differs")
        if workflow.get("on") != {
            "pull_request": {"branches": ["develop", "main"]}
        }:
            findings.append("pull-request trigger must target exactly develop and main")
        if workflow.get("permissions") != {"contents": "read"}:
            findings.append("pull-request permissions must be exactly contents: read")
        if workflow.get("concurrency") != {
            "group": contract.concurrency_group,
            "cancel-in-progress": True,
        }:
            findings.append("pull-request concurrency must cancel superseded PR runs")
        jobs = workflow.get("jobs")
        if not isinstance(jobs, dict) or set(jobs) != {contract.job_name}:
            findings.append("pull-request workflow must declare exactly one owned job")
        else:
            job = jobs[contract.job_name]
            if not isinstance(job, dict):
                findings.append("pull-request job must be a mapping")
            else:
                if set(job) != {"name", "runs-on", "timeout-minutes", "steps"}:
                    findings.append("pull-request job controls differ or override permissions")
                if job.get("name") != contract.job_name:
                    findings.append("pull-request job name differs")
                if job.get("runs-on") != contract.runner:
                    findings.append("pull-request job must use the declared standard runner")
                timeout = job.get("timeout-minutes")
                if not isinstance(timeout, int) or isinstance(timeout, bool) or not (
                    0 < timeout <= contract.timeout_minutes
                ):
                    findings.append("pull-request job exceeds its timeout ceiling")
                steps = job.get("steps")
                expected_count = 4 if contract.install_command else 3
                if not isinstance(steps, list) or len(steps) != expected_count:
                    findings.append("pull-request job step catalog differs")
                else:
                    checkout = steps[0]
                    setup = steps[1]
                    if not isinstance(checkout, dict) or set(checkout) != {
                        "name", "uses", "with"
                    }:
                        findings.append("checkout step controls differ")
                    else:
                        if checkout.get("name") != contract.step_names[0]:
                            findings.append("checkout step name differs")
                        if checkout.get("uses") != contract.checkout_action:
                            findings.append("checkout must use the approved GitHub-owned action SHA")
                        if checkout.get("with") != {"persist-credentials": False}:
                            findings.append("checkout must disable credential persistence")
                    if not isinstance(setup, dict) or set(setup) != {
                        "name", "uses", "with"
                    }:
                        findings.append("Python setup step controls differ")
                    else:
                        if setup.get("name") != contract.step_names[1]:
                            findings.append("Python setup step name differs")
                        if setup.get("uses") != contract.setup_python_action:
                            findings.append(
                                "Python setup must use the approved GitHub-owned action SHA"
                            )
                        if setup.get("with") != {
                            "python-version": contract.python_version,
                            "cache": "",
                        }:
                            findings.append("Python setup inputs differ")
                    validation_index = 2
                    if contract.install_command is not None:
                        install = steps[2]
                        validation_index = 3
                        if not isinstance(install, dict) or set(install) != {"name", "run"}:
                            findings.append("package installation step controls differ")
                        else:
                            if install.get("name") != contract.step_names[2]:
                                findings.append("package installation step name differs")
                            if _commands(install.get("run")) != (contract.install_command,):
                                findings.append("package installation command differs")
                    validation = steps[validation_index]
                    if not isinstance(validation, dict) or set(validation) != {"name", "run"}:
                        findings.append("repository validation step controls differ")
                    else:
                        if validation.get("name") != contract.step_names[-1]:
                            findings.append("repository validation step name differs")
                        if _commands(validation.get("run")) != contract.validation_commands:
                            findings.append(
                                "repository validation commands differ from the declared proof"
                            )

    if dependabot is not None and dependabot != DEPENDABOT_CONTRACT:
        findings.append(
            "Dependabot must contain exactly the declared monthly develop update record"
        )
    if not findings:
        assert isinstance(workflow, dict)
        assert isinstance(dependabot, dict)
        source_controls = _source_automation_controls(workflow, dependabot, contract)
        if declared_controls is MISSING_AUTOMATION_CONTROLS:
            findings.append("automation controls projection is missing")
        elif declared_controls is None:
            findings.append("automation controls projection must not be null")
        elif not isinstance(declared_controls, dict):
            findings.append("automation controls projection must be a mapping")
        elif declared_controls != source_controls:
            findings.append(
                "automation controls projection differs from parsed source controls"
            )
    return findings

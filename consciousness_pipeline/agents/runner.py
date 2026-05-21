import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from consciousness_pipeline.agents.contracts import (
    AGENT_CHOICES,
    schema_for_job,
    schema_path_for_job,
)
from consciousness_pipeline.agents.jobs import find_job
from consciousness_pipeline.agents.prompts import build_job_prompt
from consciousness_pipeline.core.config import PROJECT_ROOT
from consciousness_pipeline.quality.evaluations import REQUIRED_DOSSIER_HEADINGS


def check_agent_available(agent: str) -> None:
    if agent == AGENT_CHOICES[0]:
        command = ["codex", "--version"]
    elif agent == AGENT_CHOICES[1]:
        command = ["claude", "--version"]
    else:
        raise ValueError("agent must be 'codex' or 'claude'")

    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or f"exit code {result.returncode}").strip()
        raise RuntimeError(f"{agent} CLI is not usable: {detail}")


def build_codex_command(job: Mapping[str, object], prompt: str) -> list[str]:
    return [
        "codex",
        "exec",
        "--sandbox",
        "workspace-write",
        "--output-schema",
        schema_path_for_job(job),
        "-o",
        str(job["output_path"]),
        prompt,
    ]


def build_claude_command(job: Mapping[str, object], prompt: str, root: Path = PROJECT_ROOT) -> list[str]:
    schema = json.dumps(schema_for_job(job), ensure_ascii=False)
    return [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--json-schema",
        schema,
    ]


def _resolve_project_path(root: Path, path: object) -> Path:
    candidate = Path(str(path))
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _write_schema_for_job(job: Mapping[str, object], root: Path) -> None:
    schema_path = _resolve_project_path(root, schema_path_for_job(job))
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(json.dumps(schema_for_job(job), indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def _apply_output_overrides(
    job: Mapping[str, object],
    output_path: Path | None,
    bundle_output_path: Path | None,
) -> dict[str, object]:
    updated = dict(job)
    if output_path is not None:
        updated["output_path"] = str(output_path)
    if bundle_output_path is not None:
        updated["bundle_output_path"] = str(bundle_output_path)
        updated["notebooklm_bundle_dir"] = str(bundle_output_path.parent)
    return updated


def _extract_claude_output(stdout: str) -> Any:
    payload: Any = json.loads(stdout)
    if isinstance(payload, dict) and "structured_output" in payload:
        output = payload["structured_output"]
    elif isinstance(payload, dict) and "result" in payload:
        output = payload["result"]
    else:
        output = payload
    if isinstance(output, str):
        stripped = output.strip()
        if stripped:
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                return output
            if isinstance(parsed, (dict, list)):
                return parsed
    return output


def _write_structured_output(job: Mapping[str, object], output: Any, root: Path) -> None:
    output_path = _resolve_project_path(root, job["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(output, str):
        output_path.write_text(output, encoding="utf-8")
    else:
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_source_script_bundle(job, output, root)


def _write_claude_output(job: Mapping[str, object], stdout: str, root: Path) -> None:
    _write_structured_output(job, _extract_claude_output(stdout), root)


def _write_codex_sidecar_outputs(job: Mapping[str, object], root: Path) -> None:
    output_path = _resolve_project_path(root, job["output_path"])
    if not output_path.exists():
        return
    try:
        output = json.loads(output_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    _write_source_script_bundle(job, output, root)


def _write_source_script_bundle(job: Mapping[str, object], output: Any, root: Path) -> None:
    if str(job.get("kind", "")) != "source_script":
        return
    if not isinstance(output, dict):
        return
    dossier = output.get("research_dossier_markdown")
    bundle_output_path = job.get("bundle_output_path")
    if not isinstance(dossier, str) or not bundle_output_path:
        return
    if not _looks_like_source_dossier(dossier):
        return
    dossier_path = _resolve_project_path(root, bundle_output_path)
    dossier_path.parent.mkdir(parents=True, exist_ok=True)
    dossier_path.write_text(dossier, encoding="utf-8")


def _looks_like_source_dossier(dossier: str) -> bool:
    return bool(dossier.strip()) and all(heading in dossier for heading in REQUIRED_DOSSIER_HEADINGS)


def run_job(
    manifest_path: Path,
    job_id: str,
    agent: str,
    root: Path = PROJECT_ROOT,
    dry_run: bool = False,
    output_path: Path | None = None,
    bundle_output_path: Path | None = None,
) -> list[str]:
    job = _apply_output_overrides(find_job(manifest_path, job_id), output_path, bundle_output_path)
    if not dry_run:
        _write_schema_for_job(job, root)
        check_agent_available(agent)
    prompt = build_job_prompt(job, root)
    if agent == AGENT_CHOICES[0]:
        command = build_codex_command(job, prompt)
    elif agent == AGENT_CHOICES[1]:
        command = build_claude_command(job, prompt, root)
    else:
        raise ValueError("agent must be 'codex' or 'claude'")

    if dry_run:
        return command

    if agent == "codex":
        subprocess.run(command, cwd=root, check=True)
        _write_codex_sidecar_outputs(job, root)
    else:
        result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=True)
        _write_claude_output(job, result.stdout, root)
    return command

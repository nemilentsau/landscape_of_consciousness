import argparse
import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from consciousness_pipeline.agent_jobs import build_job_prompt, find_job
from consciousness_pipeline.config import PROJECT_ROOT


def check_agent_available(agent: str) -> None:
    if agent == "codex":
        command = ["codex", "--version"]
    elif agent == "claude":
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
        str(job["schema_path"]),
        "-o",
        str(job["output_path"]),
        prompt,
    ]


def build_claude_command(job: Mapping[str, object], prompt: str, root: Path = PROJECT_ROOT) -> list[str]:
    schema = (root / str(job["schema_path"])).read_text(encoding="utf-8")
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
    dossier_path = _resolve_project_path(root, bundle_output_path)
    dossier_path.parent.mkdir(parents=True, exist_ok=True)
    dossier_path.write_text(dossier, encoding="utf-8")


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
        check_agent_available(agent)
    prompt = build_job_prompt(job, root)
    if agent == "codex":
        command = build_codex_command(job, prompt)
    elif agent == "claude":
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Codex CLI or Claude Code headless production jobs")
    parser.add_argument("--manifest", required=True, type=Path, help="JSONL job manifest path")
    parser.add_argument("--job-id", required=True, help="Job id from the manifest")
    parser.add_argument("--agent", required=True, choices=("codex", "claude"), help="Headless agent backend")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    parser.add_argument("--output-path", type=Path, help="Override the job output path")
    parser.add_argument("--bundle-output-path", type=Path, help="Override the NotebookLM dossier markdown path")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest = args.manifest if args.manifest.is_absolute() else PROJECT_ROOT / args.manifest
    command = run_job(
        manifest,
        args.job_id,
        args.agent,
        dry_run=args.dry_run,
        output_path=args.output_path,
        bundle_output_path=args.bundle_output_path,
    )
    if args.dry_run:
        print(json.dumps(command, indent=2))


if __name__ == "__main__":
    main()

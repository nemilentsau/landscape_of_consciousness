import argparse
import json
import os
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
    command = [
        "claude",
        "--bare",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--json-schema",
        schema,
    ]
    allowed_tools = os.environ.get("CLAUDE_ALLOWED_TOOLS")
    if allowed_tools:
        command.extend(["--allowedTools", allowed_tools])
    return command


def _write_claude_output(job: Mapping[str, object], stdout: str, root: Path) -> None:
    output_path = root / str(job["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: Any = json.loads(stdout)
    if isinstance(payload, dict) and "structured_output" in payload:
        output = payload["structured_output"]
    elif isinstance(payload, dict) and "result" in payload:
        output = payload["result"]
    else:
        output = payload
    if isinstance(output, str):
        output_path.write_text(output, encoding="utf-8")
    else:
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_job(
    manifest_path: Path,
    job_id: str,
    agent: str,
    root: Path = PROJECT_ROOT,
    dry_run: bool = False,
) -> list[str]:
    job = find_job(manifest_path, job_id)
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
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest = args.manifest if args.manifest.is_absolute() else PROJECT_ROOT / args.manifest
    command = run_job(manifest, args.job_id, args.agent, dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps(command, indent=2))


if __name__ == "__main__":
    main()

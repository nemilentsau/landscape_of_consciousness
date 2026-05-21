import csv
import json
from pathlib import Path

from consciousness_pipeline.agents.contracts import manifest_path_for_kind
from consciousness_pipeline.agents.runner import run_job
from consciousness_pipeline.core.config import PROJECT_ROOT
from consciousness_pipeline.course.callback_index import write_callback_index
from consciousness_pipeline.course.capsules import validate_episode_capsule


class EpisodeAcceptanceError(RuntimeError):
    pass


def _dossier_path(root: Path, episode_id: str) -> Path:
    return root / "episodes" / episode_id / "notebooklm_bundle" / "research_dossier.md"


def _capsule_path(root: Path, episode_id: str) -> Path:
    return root / "course" / "episode_capsules" / f"{episode_id}.json"


def _update_production_status(root: Path, episode_id: str) -> None:
    status_path = root / "course" / "production-status.csv"
    if not status_path.exists():
        return
    with status_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    for row in rows:
        if row.get("group_id") == episode_id:
            row["script_status"] = "source_script_ready"
            row["notebooklm_status"] = "notebooklm_bundle_ready"
            row["message"] = "Source dossier accepted; episode capsule generated"
    with status_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def accept_episode(
    episode_id: str,
    agent: str,
    root: Path = PROJECT_ROOT,
    dry_run: bool = False,
) -> list[list[str]]:
    dossier_path = _dossier_path(root, episode_id)
    if not dossier_path.exists():
        raise EpisodeAcceptanceError(f"{dossier_path.relative_to(root)} is missing")

    command = run_job(
        manifest_path_for_kind(root, "course_episode_capsule"),
        f"{episode_id}-capsule",
        agent,
        root=root,
        dry_run=dry_run,
    )
    if dry_run:
        return [command]

    capsule_path = _capsule_path(root, episode_id)
    if not capsule_path.exists():
        raise EpisodeAcceptanceError(f"{capsule_path.relative_to(root)} was not written by the capsule job")
    validate_episode_capsule(json.loads(capsule_path.read_text(encoding="utf-8")), root=root)
    write_callback_index(root / "course" / "episode_capsules", root / "course" / "callback_index.json", root=root)
    _update_production_status(root, episode_id)
    return [command]

import json
from pathlib import Path
from typing import Any

from consciousness_pipeline.episode_capsules import validate_episode_capsule


def _relative_project_path(root: Path | None, path: Path) -> str:
    if root is None:
        return path.as_posix()
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def build_callback_index(capsule_dir: Path, root: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for capsule_path in sorted(capsule_dir.glob("*.json")):
        capsule = json.loads(capsule_path.read_text(encoding="utf-8"))
        validate_episode_capsule(capsule, root=root)
        for callback in capsule.get("callbacks", []):
            concept = str(callback["concept"])
            index.setdefault(concept, []).append(
                {
                    "episode_id": str(capsule["episode_id"]),
                    "capsule_path": _relative_project_path(root, capsule_path),
                    "accepted_dossier_path": str(capsule["accepted_dossier_path"]),
                    "source_path": str(callback["source_path"]),
                    "summary": str(callback["summary"]),
                    "useful_for_future_sections": [str(item) for item in callback["useful_for_future_sections"]],
                }
            )
    return {
        concept: sorted(entries, key=lambda entry: entry["episode_id"]) for concept, entries in sorted(index.items())
    }


def write_callback_index(capsule_dir: Path, output_path: Path, root: Path | None = None) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(build_callback_index(capsule_dir, root=root), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

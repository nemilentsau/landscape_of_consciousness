import csv
from pathlib import Path

DEFAULT_REVIEW_STATUS = "pending_human_listen"
VALID_REVIEW_STATUSES = ("pending_human_listen", "accepted", "regenerate", "left_as_is")
VERIFIED_AUDIO_STATUSES = (
    "not_started",
    "audio_requested",
    "audio_ready",
    "audio_review_pending",
    "audio_accepted",
    "audio_regenerate_requested",
)
URL_REQUIRED_AUDIO_STATUSES = (
    "audio_ready",
    "audio_review_pending",
    "audio_accepted",
    "audio_regenerate_requested",
)
PRODUCTION_STATUS_FIELDNAMES = (
    "group_id",
    "section_id",
    "packet_slug",
    "research_status",
    "script_status",
    "notebooklm_status",
    "notebook_url",
    "audio_status",
    "message",
)


class NotebookLMStatusError(RuntimeError):
    pass


def episode_audio_status(root: Path, episode_id: str) -> dict[str, str]:
    status_path = root / "course" / "production-status.csv"
    if not status_path.exists():
        return {}
    with status_path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("group_id") == episode_id]
    result: dict[str, str] = {}
    for key in ("audio_status", "notebook_url"):
        values = [str(row.get(key, "")).strip() for row in rows if str(row.get(key, "")).strip()]
        if values:
            result[key] = values[-1]
    return result


def _read_status_rows(status_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not status_path.exists():
        raise NotebookLMStatusError(f"{status_path} is missing")
    with status_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = [{key: str(value or "") for key, value in row.items()} for row in reader]
    missing = [fieldname for fieldname in PRODUCTION_STATUS_FIELDNAMES if fieldname not in fieldnames]
    if missing:
        missing_fields = ", ".join(missing)
        raise NotebookLMStatusError(f"{status_path} is missing required columns: {missing_fields}")
    return fieldnames, rows


def record_notebooklm_status(
    root: Path,
    episode_id: str,
    audio_status: str,
    notebook_url: str = "",
    message: str = "",
) -> Path:
    if audio_status not in VERIFIED_AUDIO_STATUSES:
        valid = ", ".join(VERIFIED_AUDIO_STATUSES)
        raise NotebookLMStatusError(f"Unsupported audio status `{audio_status}`. Expected one of: {valid}")
    if audio_status in URL_REQUIRED_AUDIO_STATUSES and not notebook_url.strip():
        raise NotebookLMStatusError(f"`{audio_status}` requires a NotebookLM URL")
    if audio_status != "not_started" and not message.strip():
        raise NotebookLMStatusError("Recording a verified NotebookLM status requires a message")

    status_path = root / "course" / "production-status.csv"
    fieldnames, rows = _read_status_rows(status_path)
    matched = False
    for row in rows:
        if row.get("group_id") != episode_id:
            continue
        matched = True
        if notebook_url.strip():
            row["notebook_url"] = notebook_url.strip()
        row["audio_status"] = audio_status
        row["message"] = message.strip()
    if not matched:
        raise NotebookLMStatusError(f"{episode_id} is not represented in {status_path}")

    with status_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return status_path


def write_audio_review(root: Path, episode_id: str, review_status: str = DEFAULT_REVIEW_STATUS) -> Path:
    if review_status not in VALID_REVIEW_STATUSES:
        valid = ", ".join(VALID_REVIEW_STATUSES)
        raise ValueError(f"Unsupported audio review status `{review_status}`. Expected one of: {valid}")

    status = episode_audio_status(root, episode_id)
    review_path = root / "episodes" / episode_id / "audio_review.md"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(
        f"""# Audio Review: {episode_id}

Review status: {review_status}
NotebookLM URL: {status.get("notebook_url", "unknown")}
Audio status from production ledger: {status.get("audio_status", "unknown")}

## Listener Clarity

- Can a first-time listener state the episode's central question after five minutes?
- Does the conversation preserve the hard-problem and bridge-principle distinctions?
- Are theory names introduced with enough context to avoid acronym soup?

## Balance And Overclaim Risk

- Does the audio steelman the strongest case before objecting?
- Does it avoid treating weak evidence, anomalies, or speculation as settled results?
- Does it clearly distinguish ontology, method, and evidence?

## Continuity

- Does the episode build from prior accepted capsules without re-teaching the whole course?
- Are callbacks useful rather than distracting?
- Is the next episode transition clear?

## Missing Or Distorted Material

- None recorded yet.

## Recommended Fixes

- Pending human listen.

## Decision

Pending.
""",
        encoding="utf-8",
    )
    return review_path

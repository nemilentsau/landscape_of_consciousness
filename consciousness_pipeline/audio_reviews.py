import csv
from pathlib import Path

DEFAULT_REVIEW_STATUS = "pending_human_listen"
VALID_REVIEW_STATUSES = ("pending_human_listen", "accepted", "regenerate", "left_as_is")


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

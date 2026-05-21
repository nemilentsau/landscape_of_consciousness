from collections.abc import Mapping
from typing import Any


class EpisodeReviewValidationError(ValueError):
    pass


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def validate_episode_review(review: Mapping[str, Any], episode_id: str | None = None) -> None:
    errors: list[str] = []
    if review.get("schema_version") != "episode_review_v1":
        errors.append("schema_version must be episode_review_v1")
    if not _non_empty_string(review.get("episode_id")):
        errors.append("episode_id is required")
    if episode_id is not None and review.get("episode_id") != episode_id:
        errors.append(f"episode_id must be {episode_id}")
    if not isinstance(review.get("approved"), bool):
        errors.append("approved must be a boolean")
    if not _non_empty_string(review.get("summary")):
        errors.append("summary is required")
    for field in ("blocking_issues", "non_blocking_notes", "checked_items"):
        if not _string_list(review.get(field)):
            errors.append(f"{field} must be a list of non-empty strings")
    if review.get("approved") is True and review.get("blocking_issues"):
        errors.append("approved reviews must not include blocking_issues")
    if review.get("approved") is False and not review.get("blocking_issues"):
        errors.append("rejected reviews must include at least one blocking issue")
    if errors:
        raise EpisodeReviewValidationError("\n- ".join(errors))

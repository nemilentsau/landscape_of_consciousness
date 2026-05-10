from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = _PACKAGE_ROOT.parents[1] if _PACKAGE_ROOT.parent.name == ".worktrees" else _PACKAGE_ROOT

DEFAULT_PDF = PROJECT_ROOT / "papers" / "A-landscape-of-consciousness--Toward-a-taxonom_2024_Progress-in-Biophysics-a.pdf"
METADATA_HTML = PROJECT_ROOT / "papers" / "S0079610723001128.html"

EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"
RESEARCH_DIR = PROJECT_ROOT / "data" / "research"
PACKETS_DIR = PROJECT_ROOT / "packets" / "theories"
COURSE_DIR = PROJECT_ROOT / "course"

AUDIO_FORMAT = "Debate"
AUDIO_LENGTH = "Longer"
AUDIO_LANGUAGE = "English"
AUDIO_PROMPT = (
    "Make this a rigorous debate-club style episode. Steelman the theory, "
    "challenge it with serious objections, compare nearby theories, and avoid premature resolution."
)

STATUS_VALUES = (
    "not_started",
    "extracted",
    "researched",
    "packet_ready",
    "upload_attempted",
    "uploaded",
    "audio_requested",
    "audio_ready",
    "failed",
    "manual_action_required",
)

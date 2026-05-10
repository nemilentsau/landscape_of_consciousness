from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PDF = (
    PROJECT_ROOT / "papers" / "A-landscape-of-consciousness--Toward-a-taxonom_2024_Progress-in-Biophysics-a.pdf"
)
METADATA_HTML = PROJECT_ROOT / "papers" / "S0079610723001128.html"

EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"
RESEARCH_DIR = PROJECT_ROOT / "data" / "research"
PACKETS_DIR = PROJECT_ROOT / "packets" / "theories"
COURSE_DIR = PROJECT_ROOT / "course"
JOBS_DIR = PROJECT_ROOT / "jobs"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
EPISODES_DIR = PROJECT_ROOT / "episodes"

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
    "research_queued",
    "researched",
    "script_queued",
    "scripted",
    "packet_ready",
    "notebooklm_bundle_ready",
    "audio_requested",
    "audio_ready",
    "failed",
    "manual_action_required",
)

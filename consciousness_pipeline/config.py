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
    "Generate a rigorous debate from the provided factual dossier. Steelman the positions, challenge them with "
    "serious objections, compare nearby theories, and avoid premature resolution."
)

STATUS_VALUES = (
    "not_started",
    "extracted",
    "research_queued",
    "researched",
    "source_script_queued",
    "source_script_ready",
    "packet_ready",
    "notebooklm_bundle_ready",
    "audio_requested",
    "audio_ready",
    "failed",
    "manual_action_required",
)

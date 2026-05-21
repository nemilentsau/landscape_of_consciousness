from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

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

AUDIO_FORMAT = "Deep Dive"
AUDIO_LENGTH = "Long"
AUDIO_LANGUAGE = "English"
AUDIO_PROMPT = (
    "Generate an extended, rigorous, balanced debate for a curious but serious listener. Steelman physicalist, "
    "dualist, idealist, and typological positions; challenge each with serious objections; keep Chalmers's hard "
    "problem, phenomenal vs access consciousness, and correlation-vs-explanation distinctions central. Compare "
    "nearby theories without prematurely resolving the debate."
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
    "audio_review_pending",
    "audio_accepted",
    "audio_regenerate_requested",
    "failed",
    "manual_action_required",
)

import argparse
import json
from pathlib import Path

from consciousness_pipeline.agent_jobs import write_agent_job_artifacts
from consciousness_pipeline.agent_runner import run_job
from consciousness_pipeline.config import (
    COURSE_DIR,
    DEFAULT_PDF,
    EPISODES_DIR,
    EXTRACTED_DIR,
    JOBS_DIR,
    PACKETS_DIR,
    PROJECT_ROOT,
    RESEARCH_DIR,
    SCHEMAS_DIR,
)
from consciousness_pipeline.course import write_course_artifacts
from consciousness_pipeline.headings import detect_headings
from consciousness_pipeline.models import Heading, PageText, Section
from consciousness_pipeline.packets import render_packet, validate_packet
from consciousness_pipeline.pdf_extract import extract_pages, write_pages_json
from consciousness_pipeline.research import load_research_record, write_research_stub
from consciousness_pipeline.sections import build_sections


def _read_pages(path: Path) -> list[PageText]:
    return [PageText.from_dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def _read_headings(path: Path) -> list[Heading]:
    return [Heading.from_dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def _read_sections(path: Path) -> list[Section]:
    return [Section.from_dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def cmd_extract(args: argparse.Namespace) -> None:
    pages = extract_pages(Path(args.pdf))
    write_pages_json(pages, EXTRACTED_DIR / "paper_pages.json")
    print(f"Extracted {len(pages)} pages")


def cmd_headings(args: argparse.Namespace) -> None:
    pages = _read_pages(EXTRACTED_DIR / "paper_pages.json")
    headings = detect_headings(pages)
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    (EXTRACTED_DIR / "headings.json").write_text(
        json.dumps([item.to_dict() for item in headings], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Detected {len(headings)} headings")


def cmd_sections(args: argparse.Namespace) -> None:
    pages = _read_pages(EXTRACTED_DIR / "paper_pages.json")
    headings = _read_headings(EXTRACTED_DIR / "headings.json")
    sections = build_sections(pages, headings)
    (EXTRACTED_DIR / "sections.json").write_text(
        json.dumps([item.to_dict() for item in sections], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Built {len(sections)} sections")


def cmd_packets(args: argparse.Namespace) -> None:
    sections = _read_sections(EXTRACTED_DIR / "sections.json")
    PACKETS_DIR.mkdir(parents=True, exist_ok=True)
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for section in sections:
        research_path = RESEARCH_DIR / f"{section.section_id}.json"
        if not research_path.exists():
            write_research_stub(research_path, section)
        research = load_research_record(research_path, section)
        packet = render_packet(section, research)
        errors = validate_packet(packet)
        if errors:
            raise SystemExit(f"Packet validation failed for {section.section_id}: {errors}")
        (PACKETS_DIR / f"{section.slug}.md").write_text(packet, encoding="utf-8")
        written += 1
    print(f"Wrote {written} packets")


def cmd_course(args: argparse.Namespace) -> None:
    sections = _read_sections(EXTRACTED_DIR / "sections.json")
    write_course_artifacts(sections, COURSE_DIR)
    print("Wrote course artifacts")


def cmd_jobs(args: argparse.Namespace) -> None:
    sections = _read_sections(EXTRACTED_DIR / "sections.json")
    write_course_artifacts(sections, COURSE_DIR)
    write_agent_job_artifacts(sections, JOBS_DIR, SCHEMAS_DIR, EPISODES_DIR)
    print("Wrote headless agent job manifests")


def cmd_run_job(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = PROJECT_ROOT / manifest
    command = run_job(manifest, args.job_id, args.agent, dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps(command, indent=2))


def cmd_all(args: argparse.Namespace) -> None:
    cmd_extract(args)
    cmd_headings(args)
    cmd_sections(args)
    cmd_packets(args)
    cmd_course(args)
    cmd_jobs(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a headless-agent consciousness podcast pipeline")
    parser.add_argument("--pdf", default=str(DEFAULT_PDF), help="Path to the Kuhn review PDF")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, handler in (
        ("extract", cmd_extract),
        ("headings", cmd_headings),
        ("sections", cmd_sections),
        ("packets", cmd_packets),
        ("course", cmd_course),
        ("jobs", cmd_jobs),
        ("all", cmd_all),
    ):
        subparser = subparsers.add_parser(name)
        subparser.set_defaults(func=handler)
    run_job_parser = subparsers.add_parser("run-job")
    run_job_parser.add_argument("--manifest", required=True, help="JSONL job manifest path")
    run_job_parser.add_argument("--job-id", required=True, help="Job id from the manifest")
    run_job_parser.add_argument("--agent", required=True, choices=("codex", "claude"), help="Headless agent backend")
    run_job_parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    run_job_parser.set_defaults(func=cmd_run_job)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

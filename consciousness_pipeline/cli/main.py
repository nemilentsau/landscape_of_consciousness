import argparse
import json
from pathlib import Path

from consciousness_pipeline.agents.contracts import AGENT_CHOICES
from consciousness_pipeline.agents.jobs import write_agent_job_artifacts
from consciousness_pipeline.agents.runner import run_job
from consciousness_pipeline.core.config import (
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
from consciousness_pipeline.core.models import Heading, PageText, Section
from consciousness_pipeline.course.context import write_episode_course_context
from consciousness_pipeline.course.contract import write_default_course_contract
from consciousness_pipeline.course.map import write_course_artifacts, write_episode_artifacts
from consciousness_pipeline.episodes.acceptance import accept_episode
from consciousness_pipeline.episodes.audio_reviews import (
    DEFAULT_REVIEW_STATUS,
    VALID_REVIEW_STATUSES,
    write_audio_review,
)
from consciousness_pipeline.episodes.runner import run_episode, select_episode_context
from consciousness_pipeline.ingest.headings import detect_headings
from consciousness_pipeline.ingest.pdf_extract import extract_pages, write_pages_json
from consciousness_pipeline.ingest.sections import build_sections
from consciousness_pipeline.quality.evaluations import evaluate_episode
from consciousness_pipeline.research.packets import render_packet, validate_packet
from consciousness_pipeline.research.records import (
    load_research_record,
    write_notebooklm_research_sources,
    write_research_readme,
    write_research_stub,
)


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
    write_research_readme(RESEARCH_DIR)
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
    write_episode_artifacts(sections, EPISODES_DIR)
    write_research_readme(RESEARCH_DIR)
    print("Wrote course and episode artifacts")


def cmd_jobs(args: argparse.Namespace) -> None:
    sections = _read_sections(EXTRACTED_DIR / "sections.json")
    write_default_course_contract(COURSE_DIR / "course_contract.md")
    write_research_readme(RESEARCH_DIR)
    write_agent_job_artifacts(sections, JOBS_DIR, SCHEMAS_DIR, EPISODES_DIR)
    print("Wrote headless agent job manifests")


def cmd_write_contract(args: argparse.Namespace) -> None:
    path = COURSE_DIR / "course_contract.md"
    write_default_course_contract(path)
    print(f"Wrote course contract: {path}")


def cmd_bundle_sources(args: argparse.Namespace) -> None:
    sections = _read_sections(EXTRACTED_DIR / "sections.json")
    manifest_path = EPISODES_DIR / args.episode_id / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundle_dir = Path(str(manifest["notebooklm_bundle_dir"]))
    if not bundle_dir.is_absolute():
        bundle_dir = PROJECT_ROOT / bundle_dir
    written = write_notebooklm_research_sources(
        sections=sections,
        section_ids=tuple(str(section_id) for section_id in manifest["section_ids"]),
        research_dir=RESEARCH_DIR,
        output_dir=bundle_dir / "sources",
    )
    print(f"Wrote {len(written)} NotebookLM source files")


def cmd_write_context(args: argparse.Namespace) -> None:
    output_path = write_episode_course_context(COURSE_DIR.parent, args.episode_id)
    print(f"Wrote course context for {args.episode_id}: {output_path}")


def cmd_select_context(args: argparse.Namespace) -> None:
    command = select_episode_context(args.episode_id, args.agent, dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps(command, indent=2))


def cmd_run_job(args: argparse.Namespace) -> None:
    manifest = Path(args.manifest)
    if not manifest.is_absolute():
        manifest = PROJECT_ROOT / manifest
    command = run_job(
        manifest,
        args.job_id,
        args.agent,
        dry_run=args.dry_run,
        output_path=args.output_path,
        bundle_output_path=args.bundle_output_path,
    )
    if args.dry_run:
        print(json.dumps(command, indent=2))


def cmd_run_episode(args: argparse.Namespace) -> None:
    review_agent = args.review_agent or ("claude" if args.auto_accept else None)
    result = run_episode(
        args.episode_id,
        args.agent,
        dry_run=args.dry_run,
        auto_accept=args.auto_accept,
        review_agent=review_agent,
    )
    if args.dry_run:
        print(json.dumps(result, indent=2))


def cmd_accept_episode(args: argparse.Namespace) -> None:
    result = accept_episode(args.episode_id, args.agent, dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps(result, indent=2))


def cmd_evaluate_episode(args: argparse.Namespace) -> None:
    report = evaluate_episode(PROJECT_ROOT, args.episode_id, stage=args.stage)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    summary = report["summary"]
    if isinstance(summary, dict) and int(summary["errors"]) > 0:
        raise SystemExit(1)
    if args.fail_on_warnings and isinstance(summary, dict) and int(summary["warnings"]) > 0:
        raise SystemExit(1)


def cmd_write_audio_review(args: argparse.Namespace) -> None:
    path = write_audio_review(PROJECT_ROOT, args.episode_id, args.review_status)
    print(f"Wrote audio review checklist: {path}")


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
        ("write-contract", cmd_write_contract),
        ("all", cmd_all),
    ):
        subparser = subparsers.add_parser(name)
        subparser.set_defaults(func=handler)
    run_job_parser = subparsers.add_parser("run-job")
    run_job_parser.add_argument("--manifest", required=True, help="JSONL job manifest path")
    run_job_parser.add_argument("--job-id", required=True, help="Job id from the manifest")
    run_job_parser.add_argument("--agent", required=True, choices=AGENT_CHOICES, help="Headless agent backend")
    run_job_parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it")
    run_job_parser.add_argument("--output-path", type=Path, help="Override the job output path")
    run_job_parser.add_argument("--bundle-output-path", type=Path, help="Override the NotebookLM dossier markdown path")
    run_job_parser.set_defaults(func=cmd_run_job)
    run_episode_parser = subparsers.add_parser("run-episode")
    run_episode_parser.add_argument("--episode-id", required=True, help="Episode id, e.g. group-003")
    run_episode_parser.add_argument(
        "--agent", required=True, choices=AGENT_CHOICES, help="Headless agent backend"
    )
    run_episode_parser.add_argument("--dry-run", action="store_true", help="Print ordered jobs without executing them")
    run_episode_parser.add_argument(
        "--auto-accept",
        action="store_true",
        help="Run reviewer-gated acceptance after the source dossier is generated",
    )
    run_episode_parser.add_argument(
        "--review-agent",
        choices=AGENT_CHOICES,
        help="Agent backend used for --auto-accept review and capsule generation; defaults to claude",
    )
    run_episode_parser.set_defaults(func=cmd_run_episode)
    accept_episode_parser = subparsers.add_parser("accept-episode")
    accept_episode_parser.add_argument("--episode-id", required=True, help="Episode id, e.g. group-002")
    accept_episode_parser.add_argument(
        "--agent", required=True, choices=AGENT_CHOICES, help="Headless agent backend"
    )
    accept_episode_parser.add_argument(
        "--dry-run", action="store_true", help="Print the capsule job without executing it"
    )
    accept_episode_parser.set_defaults(func=cmd_accept_episode)
    evaluate_episode_parser = subparsers.add_parser("evaluate-episode")
    evaluate_episode_parser.add_argument("--episode-id", required=True, help="Episode id, e.g. group-005")
    evaluate_episode_parser.add_argument(
        "--stage",
        choices=("context", "research", "dossier", "bundle", "accepted", "audio"),
        default="accepted",
        help="How much of the episode lifecycle to evaluate",
    )
    evaluate_episode_parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit nonzero when warnings are present, not only errors",
    )
    evaluate_episode_parser.set_defaults(func=cmd_evaluate_episode)
    audio_review_parser = subparsers.add_parser("write-audio-review")
    audio_review_parser.add_argument("--episode-id", required=True, help="Episode id, e.g. group-006")
    audio_review_parser.add_argument(
        "--review-status",
        choices=VALID_REVIEW_STATUSES,
        default=DEFAULT_REVIEW_STATUS,
        help="Initial audio review status",
    )
    audio_review_parser.set_defaults(func=cmd_write_audio_review)
    select_context_parser = subparsers.add_parser("select-context")
    select_context_parser.add_argument("--episode-id", required=True, help="Episode id, e.g. group-005")
    select_context_parser.add_argument("--agent", required=True, choices=AGENT_CHOICES, help="Headless agent backend")
    select_context_parser.add_argument(
        "--dry-run", action="store_true", help="Print the context-selection command without executing it"
    )
    select_context_parser.set_defaults(func=cmd_select_context)
    bundle_sources_parser = subparsers.add_parser("bundle-sources")
    bundle_sources_parser.add_argument("--episode-id", required=True, help="Episode id, e.g. group-001")
    bundle_sources_parser.set_defaults(func=cmd_bundle_sources)
    write_context_parser = subparsers.add_parser("write-context")
    write_context_parser.add_argument("--episode-id", required=True, help="Episode id, e.g. group-003")
    write_context_parser.set_defaults(func=cmd_write_context)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except RuntimeError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()

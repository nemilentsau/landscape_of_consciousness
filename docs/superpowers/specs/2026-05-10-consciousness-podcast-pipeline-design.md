# Consciousness Podcast Production Pipeline Design

Date: 2026-05-10

## Context

The local PDF in `papers/` is the canonical source for Robert Lawrence Kuhn's "A landscape of consciousness: Toward a taxonomy of explanations and implications." The project should turn the review into an interesting long-form listening course, but the production center is not NotebookLM browser automation. The center is a reproducible research and factual source-script pipeline using headless agents.

Official tool targets:

- OpenAI Codex CLI non-interactive jobs through `codex exec`.
- Claude Code headless jobs through `claude -p`.
- NotebookLM only as the final dialogue/audio-rendering surface, operated by Computer Use or Claude Code after factual source dossiers exist.

Do not use Claude Code `--bare` for this project. `--bare` intentionally skips the usual local
Claude Code auth/keychain path and turns headless execution into API-key-style auth, which is not
the desired local workflow.

## Goals

- Extract page-aware PDF text reproducibly.
- Detect Kuhn's numbered theory taxonomy and segment the review into theory/subtheory sections.
- Build episode-sized groups so tiny theories can be combined and broad categories are split.
- Generate machine-readable research jobs for Codex CLI or Claude Code headless.
- Generate machine-readable source-script jobs that create factual NotebookLM research dossiers.
- Keep schemas stable so agent outputs can be validated and resumed.
- Leave the NotebookLM step as an explicit handoff after factual dossiers exist.

## Non-Goals

- Do not make NotebookLM UI automation the pipeline.
- Do not depend on brittle browser selectors or Playwright for production.
- Do not pretend all theories are equally credible.
- Do not force one podcast episode per small theory section.
- Do not adjudicate which theory is correct.

## Artifact Layers

### Extraction

- `data/extracted/paper_pages.json`
- `data/extracted/headings.json`
- `data/extracted/sections.json`

### Course Map

- `course/exhaustive-index.md`
- `course/episode-map.md`
- `course/episode-map.json`
- `course/production-status.csv`

### Headless Jobs

- `jobs/research.jsonl`: one research job per section.
- `jobs/source-scripts.jsonl`: one factual source-script job per episode group.
- `schemas/research-record.schema.json`
- `schemas/source-script.schema.json`

### Agent Outputs

- `data/research/<section-id>.json`: cited research record.
- `episodes/<group-id>/script.json`: factual source-script JSON containing `research_dossier_markdown`.
- `episodes/<group-id>/notebooklm_bundle/`: final handoff material for NotebookLM.

## Research Policy

Research jobs must produce balanced records:

- Academic core: original papers/books where available, serious reviews, SEP/IEP, university or scholar pages.
- Critique: serious objections, methodological limits, or competing theories.
- Listener hooks: debates, thought experiments, vivid examples, or interviews when useful.
- Credibility label: mainstream scientific theory, active philosophical debate, speculative extension, religious/spiritual metaphysics, or fringe/weakly evidenced claim.

## Episode Policy

Source-script jobs should produce factual NotebookLM research dossiers, not dialogue:

- Episode scope and why the sections are grouped.
- Per-section factual summaries grounded in Kuhn and research records.
- Strongest academic case.
- Serious objections and methodological limits.
- Comparison axes for theories in the cluster.
- Epistemic status and claims not to overstate.
- Implications for AI consciousness, virtual immortality, survival beyond death, and value only where relevant.

## NotebookLM Handoff

NotebookLM receives factual dossiers and generates the conversational episode itself. Computer Use or Claude Code may operate the UI, but that automation must observe the live UI and recover from login/account/manual states. It should not be represented as deterministic local Playwright selectors.

The default audio handoff is NotebookLM's Deep Dive format with Long length. The custom prompt should ask for an extended, rigorous, balanced treatment that steelmans physicalist, dualist, idealist, and typological positions; challenges each with serious objections; keeps Chalmers's hard problem, phenomenal versus access consciousness, and correlation-versus-explanation distinctions central; and compares nearby theories without prematurely resolving the discussion. Debate language belongs inside this guidance prompt, not in NotebookLM's selected format.

## Verification

- Unit tests for extraction, heading detection, segmentation, grouping, packet rendering, job generation, and headless command construction.
- `python -m unittest discover -s tests -v`
- Dry-run command generation before any real agent spend.

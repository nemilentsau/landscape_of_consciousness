# Consciousness Podcast Production Pipeline Design

Date: 2026-05-10

## Context

The local PDF in `papers/` is the canonical source for Robert Lawrence Kuhn's "A landscape of consciousness: Toward a taxonomy of explanations and implications." The project should turn the review into an interesting long-form listening course, but the production center is not NotebookLM browser automation. The center is a reproducible research and script-generation pipeline using headless agents.

Official tool targets:

- OpenAI Codex CLI non-interactive jobs through `codex exec`.
- Claude Code headless jobs through `claude --bare -p`.
- NotebookLM only as the final audio-rendering surface, operated by Computer Use or Claude Code after source bundles and scripts exist.

## Goals

- Extract page-aware PDF text reproducibly.
- Detect Kuhn's numbered theory taxonomy and segment the review into theory/subtheory sections.
- Build episode-sized groups so tiny theories can be combined and broad categories are split.
- Generate machine-readable research jobs for Codex CLI or Claude Code headless.
- Generate machine-readable podcast-script jobs for long-form debate-club episodes.
- Keep schemas stable so agent outputs can be validated and resumed.
- Leave the NotebookLM step as an explicit handoff after scripts and source bundles exist.

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
- `jobs/podcast-scripts.jsonl`: one long-form script job per episode group.
- `schemas/research-record.schema.json`
- `schemas/podcast-script.schema.json`

### Agent Outputs

- `data/research/<section-id>.json`: cited research record.
- `episodes/<group-id>/script.json`: long debate-club podcast script plus NotebookLM source-bundle markdown.
- `episodes/<group-id>/notebooklm_bundle/`: final handoff material for NotebookLM.

## Research Policy

Research jobs must produce balanced records:

- Academic core: original papers/books where available, serious reviews, SEP/IEP, university or scholar pages.
- Critique: serious objections, methodological limits, or competing theories.
- Listener hooks: debates, thought experiments, vivid examples, or interviews when useful.
- Credibility label: mainstream scientific theory, active philosophical debate, speculative extension, religious/spiritual metaphysics, or fringe/weakly evidenced claim.

## Episode Policy

Podcast script jobs should produce long-form debate-club scripts:

- Opening dispute.
- Steelman.
- Cross-examination.
- Serious objections.
- Implications for AI consciousness, virtual immortality, survival beyond death, and value only where relevant.
- Verdict without closure.

## NotebookLM Handoff

NotebookLM receives already-written scripts and source bundles. Computer Use or Claude Code may operate the UI, but that automation must observe the live UI and recover from login/account/manual states. It should not be represented as deterministic local Playwright selectors.

## Verification

- Unit tests for extraction, heading detection, segmentation, grouping, packet rendering, job generation, and headless command construction.
- `python -m unittest discover -s tests -v`
- Dry-run command generation before any real agent spend.

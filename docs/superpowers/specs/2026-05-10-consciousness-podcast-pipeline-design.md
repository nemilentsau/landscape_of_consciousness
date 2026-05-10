# Consciousness Podcast Production Pipeline Design

Date: 2026-05-10

## Context

The project is based on Robert Lawrence Kuhn's review article, "A landscape of consciousness: Toward a taxonomy of explanations and implications." The local workspace contains the downloaded PDF in `papers/` and a ScienceDirect HTML page. The PDF is the canonical source because local extraction preserves page order and the article's numbered taxonomy well enough to split the review into theory and subtheory sections. The HTML remains useful for metadata.

The user's goal is to turn the long review into an interesting listening course in podcast form using NotebookLM. The desired course shape is exhaustive at the packet level: create one local packet per theory or subtheory first, then group packets into NotebookLM notebooks for long debate-style audio episodes.

NotebookLM officially supports Markdown/text, PDFs, web URLs, YouTube URLs, and other source types. Its Audio Overview generation supports custom instructions, an English-only length setting with "Longer," and a "Debate" format. The pipeline should use those controls when browser automation can reach them.

## Goals

- Extract the PDF into page-aware text that can be reproduced locally.
- Detect Kuhn's numbered theory taxonomy and segment the review by theory or subtheory.
- Generate one NotebookLM-ready Markdown packet per theory or subtheory.
- Enrich packets with balanced web research: academic core, serious critique, and listener-friendly context.
- Build course maps that group exhaustive packets into smaller debate clusters suitable for long NotebookLM audio episodes.
- Automate NotebookLM through the browser as far as practical: create notebooks, upload Markdown packets, set audio options to Debate and Longer, and record progress.
- Make the process resumable so failed uploads or blocked UI steps do not lose state.

## Non-Goals

- Do not adjudicate which consciousness theory is correct.
- Do not upload raw PDF extraction chunks directly as the main podcast source.
- Do not depend on an unofficial NotebookLM API for the first implementation.
- Do not force every packet to become its own podcast episode.
- Do not make speculative, spiritual, esoteric, or fringe theories sound more established than they are.

## Inputs

- Canonical PDF: `papers/A-landscape-of-consciousness--Toward-a-taxonom_2024_Progress-in-Biophysics-a.pdf`
- Metadata source: `papers/S0079610723001128.html`
- Runtime: bundled Python with `pypdf` for extraction.
- Web research sources selected during enrichment.

## Local Outputs

The repo should produce three layers of artifacts.

### Canonical Extraction

- `data/extracted/paper_pages.json`: page-by-page extracted text from the PDF.
- `data/extracted/headings.json`: detected numbered headings with page numbers, heading text, level, and section id.

These files make parsing reproducible and avoid repeated PDF extraction unless the PDF changes.

### Theory Packets

- `packets/theories/<section-id>-<slug>.md`

Each packet represents one theory or subtheory from Kuhn's taxonomy. It should include:

- Theory title.
- Kuhn section id and page range.
- Placement in the taxonomy.
- Concise summary of Kuhn's presentation.
- Core claim.
- Strongest case.
- Best objections.
- Related theories.
- Implications for AI consciousness, virtual immortality, survival beyond death, and meaning/value when relevant.
- Source list with academic and contextual sources.
- NotebookLM prompt guidance for debate-style audio.

### Course Maps

- `course/exhaustive-index.md`: all packets in paper order.
- `course/notebook-groups.md`: suggested groups for NotebookLM notebooks and podcast episodes.
- `course/production-status.csv`: packet status, research status, upload status, NotebookLM notebook URL, and audio generation status.

The exhaustive archive is separate from the listenable course grouping. This allows the project to generate many packets without committing to a matching number of podcast episodes.

## Packet Template

Each packet should be valid Markdown and structured for NotebookLM source ingestion:

```markdown
# <Theory Name>

## Course Role
This packet supports a debate-club episode on <central dispute>.

## Kuhn Review Anchor
- Section: <section id and title>
- Pages: <page range>
- Taxonomy placement: <category path>

## Core Claim
<One-paragraph claim summary.>

## Strongest Case
<Steelman the theory fairly.>

## Best Objections
<Serious objections, competing evidence, and limitations.>

## Cross-Examination
<Comparison with neighboring theories.>

## Implications
- AI consciousness: <relevant implication or "Not central">
- Virtual immortality: <relevant implication or "Not central">
- Survival beyond death: <relevant implication or "Not central">
- Meaning/value: <relevant implication or "Not central">

## Credibility Notes
<Label speculative, fringe, spiritual, or esoteric claims plainly when applicable.>

## Listener Hooks
<Examples, debates, interviews, thought experiments, or vivid cases.>

## Related Packets
- <related theory>

## NotebookLM Audio Guidance
Format: Debate
Length: Longer
Language: English
Prompt: Make this a rigorous debate-club style episode. Steelman the theory, challenge it with serious objections, compare nearby theories, and avoid premature resolution.

## Sources
- Kuhn review, <section>, <pages>.
- <academic source>
- <critique or contextual source>
```

## Research Policy

The enrichment step should be balanced:

- Academic core: original papers or books where available; leading reviews; SEP/IEP; university or scholar pages.
- Critique: at least one serious objection, competing theory, or methodological concern when available.
- Listener hook: interviews, debates, public lectures, popular explainers, thought experiments, or vivid examples when they improve the audio.

The research layer should not pretend all theories are equally credible. It should summarize each theory fairly, then label epistemic status plainly. Examples:

- "Mainstream scientific theory"
- "Philosophical position with active debate"
- "Speculative extension"
- "Religious or spiritual metaphysics"
- "Fringe or weakly evidenced empirical claim"

When search results are unstable or recent, the pipeline should record access dates and source URLs.

## Episode Logic

Each NotebookLM audio episode should use a debate-club frame:

- Opening question: the live dispute.
- Steelman: the strongest version of the theory or cluster.
- Pressure test: objections, edge cases, and empirical gaps.
- Cross-examination: comparison with nearby theories.
- Implications: AI consciousness, survival, virtual immortality, and value only where relevant.
- Verdict without closure: what the theory explains well, where it strains, and what evidence would matter.

For long audio, notebook groups should stay small. Typical groups should contain one to five related packets. Whole major categories, such as all Materialism theories, are too broad for one useful episode.

## NotebookLM Browser Automation

Browser automation should work from the local packet files and `course/production-status.csv`.

Planned flow:

1. Open NotebookLM.
2. Pause if Google login, account selection, CAPTCHA, permissions, or other authentication prompts appear.
3. For each planned notebook group:
   - Create a notebook.
   - Set a clear title, such as `Consciousness Theories 09.02 - Neurobiological Materialism`.
   - Upload the relevant Markdown packets as sources.
   - Optionally upload the original PDF or a section-specific Kuhn extraction as a supporting source when useful.
   - Select Audio Overview format `Debate`.
   - Select length `Longer`.
   - Set language to English when available.
   - Add the custom debate prompt.
   - Start generation when the UI exposes the action reliably.
   - Record notebook URL and audio status in `course/production-status.csv`.

The automation must be resumable. If NotebookLM fails halfway through, the status file determines where to continue. It should also support a dry run that prints planned actions without opening or changing NotebookLM.

If Google blocks a step, the automation should stop with a precise instruction, such as: "Notebook created and sources uploaded; click Generate Audio Overview manually." It should not silently continue after an uncertain UI state.

## Quality Controls

Before upload, each packet should pass checks:

- Theory title is present.
- Kuhn section id and page range are present.
- Taxonomy placement is present.
- Core claim, strongest case, and objections are non-empty.
- At least one academic source is listed when available.
- At least one critique or contextual source is listed when available.
- Speculative or fringe material is labeled.
- NotebookLM audio guidance is present with Debate, Longer, English, and the custom prompt.

For course maps:

- Every packet appears in `course/exhaustive-index.md`.
- Every NotebookLM group has a clear episode question.
- Groups stay small enough for long, focused audio.
- `course/production-status.csv` can represent not started, extracted, researched, packet ready, upload attempted, uploaded, audio requested, audio ready, failed, and manual action required.

## Error Handling

- PDF extraction failure: report the file path and page number, then continue only if later pages remain readable.
- Heading detection ambiguity: write candidate headings to `data/extracted/headings.json` and require manual review before packet generation.
- Missing web sources: create the packet with Kuhn-only content and mark research status as incomplete.
- NotebookLM upload failure: record the notebook group, file path, failure description, and whether retry is safe.
- Audio option not found: upload sources, record manual action required, and keep the notebook URL.

## Verification

Implementation should include command-line checks for:

- Successful PDF extraction and expected page count.
- Heading detection count and a sample of top-level headings.
- Packet generation for a small subset before generating the exhaustive archive.
- Markdown structure validation for generated packets.
- CSV status schema validation.
- Browser automation dry run.

The first live NotebookLM run should target one small group before running the full exhaustive queue.

## Implementation Phases

1. Build extraction and heading detection.
2. Generate a small sample of packets from several categories.
3. Add packet validation and course index generation.
4. Add balanced web research enrichment for sample packets.
5. Generate the exhaustive packet archive.
6. Add notebook grouping and production status tracking.
7. Add NotebookLM browser automation dry run.
8. Run one live NotebookLM group with Debate and Longer settings.
9. Iterate on packet structure and automation selectors before broader upload.

## Open Decisions Resolved

- Use the downloaded PDF as the canonical source.
- Produce an exhaustive local packet archive.
- Use balanced research.
- Use debate-club episode framing.
- Use browser automation for NotebookLM.
- Prefer long podcasts by selecting NotebookLM's Longer audio length option.

## References

- Google NotebookLM Help, "Add or discover new sources for your notebook": https://support.google.com/notebooklm/answer/16215270
- Google NotebookLM Help, "Generate Audio Overview in NotebookLM": https://support.google.com/notebooklm/answer/16212820

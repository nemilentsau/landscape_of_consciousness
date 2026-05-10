# Section Research Records

Files in this directory are section-level research records, not podcast episodes.

Each `*.json` file corresponds to one Kuhn taxonomy section from `data/extracted/sections.json`.
Podcast episodes combine one or more of these section records through:

- `course/episode-map.json`
- `episodes/<group-id>/manifest.json`
- `jobs/podcast-scripts.jsonl`

For example, `data/research/1.json` is a reusable research input. It becomes part of a podcast only
when an episode manifest lists it under `research_inputs`.

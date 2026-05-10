# NotebookLM Automation

The automation reads `course/notebook-groups.json`, checks the packet files, and uses a persistent browser profile at `.browser-profiles/notebooklm`.

Run:

```bash
npm install
npm run notebooklm:dry-run
npm run notebooklm:live
```

Manual handoff rules:

- If Google login appears, complete it in the browser window.
- If NotebookLM blocks file upload automation, upload the listed files manually.
- If the Audio Overview controls are visible, choose Debate, Longer, and English.
- Use this prompt:

```text
Make this a rigorous debate-club style episode. Steelman the theory, challenge it with serious objections, compare nearby theories, and avoid premature resolution.
```

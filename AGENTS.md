# Contributor notes (AI agents)

## Commit messages

Every commit ends with a sign-off naming the model that authored it:

```
Signed-off-by: <model name>
```

Example: `Signed-off-by: unsloth/Qwen3.8-Flash-Next-GGUF:UD-IQ3_XXS`

Commit often — small, focused commits with real messages, not one big dump at the
end. Stage only intended files; never commit generated artifacts (see `.gitignore`).

## Repo layout

- `data/` — the archive's two sources of truth: `corpus.json` (what counts as a
  work) and `reviews.jsonl` (one line per work: scores, tags, hook, summary).
  Append reviews only through `pipeline/review.py`, which validates them.
- `pipeline/` — `corpus.py` → `packs.py` → `review.py` → `build.py`. `build.py`
  regenerates `README.md`, `ARCHIVE.md` and `docs/index.html`; never hand-edit
  those three, edit the builder. Keep generated tables GFM-valid: header,
  delimiter and row column counts must match, and escape literal pipes as `\|`.
- `curate/` — local rating app (stdlib-only Python + sqlite3). Run
  `python3 curate/app.py`; `python3 curate/seed.py` refreshes it from
  `data/reviews.jsonl` without touching human reviews. The db file is gitignored.
- An earlier pass with a different rubric is in the git history up to `1b784c9`.
  Nothing in the tree depends on it; don't restore it.
- LLM-produced curation lives in the `llm_curations` table, separate from human
  `reviews`. Do not mix the two; the UI labels provenance.

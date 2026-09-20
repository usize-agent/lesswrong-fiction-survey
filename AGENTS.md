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

- `00..04-*.md` — the survey documents (markdown tables; keep tables GFM-valid:
  header/delimiter/row column counts must match, escape literal pipes in cells as `\|`).
- `curate/` — local rating app (stdlib-only Python + sqlite3). Run
  `python3 curate/app.py`; it seeds `curate/curate.sqlite3` from `03-scores.md`
  on first launch. The db file is gitignored.
- LLM-produced curation lives in the `llm_curations` table, separate from human
  `reviews`. Do not mix the two; the UI labels provenance.

# curate — personal rating app

Local web app for re-rating and curating the 344 scored stories yourself.
Stdlib-only Python (no pip deps): `http.server` + `sqlite3` + one HTML page.

## Run

```sh
python3 curate/app.py            # → http://127.0.0.1:8321
python3 curate/app.py --port 9000 --db /path/to/db.sqlite3
```

First run creates `curate/curate.sqlite3` and seeds it from `03-scores.md`
(344 stories, LLM scores + notes, six criteria, starter categories).

## What you can do

- **List/filter/search** by title/author, category, nearest-neighbor author
  analog; sort by survey rank, your rating, LLM weighted score, karma, year.
- **Rate** each story: `overall` plus every criterion (1–5), freeform
  **impressions** box.
- **Tag** stories with categories (`posthuman`, `ai`, `alignment`, …) — click
  chips to toggle, type a name to add a new one.
- **Add criteria** (e.g. `emotional-impact`) inline; they show up as new 1–5
  rows and persist.
- LLM survey scores (weighted /35, six dimension bars, spoiler scoring note)
  are shown alongside for reference, clearly labelled as LLM provenance.

## Data model (see `schema.sql`)

| table | holds |
|---|---|
| `stories` | title/author/year/url/karma/survey rank/nearest_neighbor |
| `llm_curations` | the survey's scores — JSON subscores, weighted total, scoring note; provenance in `scorer` |
| `reviews` | one per (story, reviewer): overall 1–5 + impressions |
| `review_scores` | per (review, criterion): 1–5 |
| `criteria` | rating axes (seeded: posthuman, rigor, idea_density, craft, form, brevity) |
| `tags` + `story_tags` | curation categories, m:n |

Human and LLM data are never mixed. The db file is gitignored; re-running
`python3 curate/seed.py` refreshes stories/LLM rows without touching your
reviews.

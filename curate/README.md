# curate — personal rating app

Local web app for re-rating and curating the 413 scored works yourself.
Stdlib-only Python (no pip deps): `http.server` + `sqlite3` + one HTML page.

## Run

```sh
python3 curate/app.py            # → http://127.0.0.1:8321
python3 curate/app.py --port 9000 --db /path/to/db.sqlite3
```

First run creates `curate/curate.sqlite3` and seeds it from
`data/reviews.jsonl` (413 works, scores + hook + summary, the five rubric
criteria, the controlled tag vocabulary).

Reseeding an older database rekeys stories from the URL title slug to the
LessWrong post id, merging duplicates and keeping your reviews. Works that have
since dropped out of the archive keep their row and your rating, but lose their
rank and their stale machine curation.

## What you can do

- **List/filter/search** by title/author, category, nearest-neighbor author
  analog; sort by archive rank, your rating, weighted score, karma, year.
- **Rate** each story: `overall` plus every criterion (1–5), freeform
  **impressions** box.
- **Tag** stories with categories (`posthuman`, `ai`, `alignment`, …) — click
  chips to toggle, type a name to add a new one.
- **Add criteria** (e.g. `emotional-impact`) inline; they show up as new 1–5
  rows and persist.
- LLM survey scores (weighted /100, five dimension bars, hook, spoiler
  summary) are shown alongside for reference, clearly labelled as LLM
  provenance.

## Data model (see `schema.sql`)

| table | holds |
|---|---|
| `stories` | title/author/year/url/karma/words/archive rank/nearest_neighbor |
| `llm_curations` | the archive's scores — JSON subscores, weighted total, hook, summary; provenance in `scorer` |
| `reviews` | one per (story, reviewer): overall 1–5 + impressions |
| `review_scores` | per (review, criterion): 1–5 |
| `criteria` | rating axes (seeded: hard, vision, mind, foresight, craft; v1 axes kept below them) |
| `tags` + `story_tags` | curation categories, m:n |

Human and LLM data are never mixed. The db file is gitignored; re-running
`python3 curate/seed.py` refreshes stories/LLM rows without touching your
reviews.

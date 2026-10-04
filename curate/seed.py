#!/usr/bin/env python3
"""Seed (or reseed) curate.sqlite3 from data/reviews.jsonl.

Safe to re-run. Inserts are idempotent (upserts keyed on slug), and nothing a
human made is ever deleted: reviews, review_scores, story_tags and any criteria
or tags added through the UI all survive a reseed.

Stories that were scored by an older survey pass and are no longer in the
archive keep their row and their human review, but lose their survey rank and
their stale machine curation.

Usage:
    python3 seed.py [--db path] [--reviews path]
"""
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULT_DB = HERE / "curate.sqlite3"
DEFAULT_REVIEWS = REPO / "data/reviews.jsonl"

sys.path.insert(0, str(REPO))
from pipeline.build import DIMS, DIM_BLURB, DIM_LABEL, score  # noqa: E402
from pipeline.review import TAGS  # noqa: E402

CRITERIA_SEED = [(d, DIM_BLURB[d], i) for i, d in enumerate(DIMS, 1)]
TAG_SEED = sorted(TAGS)
LLM_SCORER = "archive-v2 (LLM-assisted, one pass, see README.md)"


def load(reviews_path):
    corpus = json.load(open(REPO / "data/corpus.json"))
    cands = json.load(open(REPO / "cache/candidates.json"))["candidates"]
    rows = []
    for line in open(reviews_path):
        if not line.strip():
            continue
        r = json.loads(line)
        if "exclude" in r:
            continue
        c = cands[r["id"]]
        parts = corpus[r["id"]].get("parts", [r["id"]])
        rows.append({
            "slug": r["id"],
            "title": c["title"],
            "author": c["author"] or "[account deleted]",
            "year": int(c["postedAt"][:4]),
            "url": f"https://www.lesswrong.com/posts/{r['id']}/{c['slug']}",
            "karma": c["baseScore"],
            "words": sum(cands[p]["wordCount"] for p in parts),
            "subscores": {d: r[d] for d in DIMS},
            "weighted": score(r),
            "hook": r["line"],
            "summary": r["summary"],
            "tags": r["tags"],
        })
    rows.sort(key=lambda r: (-r["weighted"], -r["karma"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def migrate(conn):
    """Bring an older curate.sqlite3 up to the current shape.

    Columns added since the first schema, and a rekey: v1 stored stories under
    the URL's title slug, which changes if a post is retitled. The stable key is
    the LessWrong post id, so rows are rekeyed and any duplicate pair is merged
    onto the surviving row, human work first.
    """
    cols = {r[1] for r in conn.execute("PRAGMA table_info(stories)")}
    if "words" not in cols:
        conn.execute("ALTER TABLE stories ADD COLUMN words INTEGER")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(llm_curations)")}
    if "hook" not in cols:
        conn.execute("ALTER TABLE llm_curations ADD COLUMN hook TEXT")

    by_slug = {s: i for i, s in conn.execute("SELECT id, slug FROM stories")}
    rekeyed = merged = 0
    for sid, slug, url in list(conn.execute("SELECT id, slug, url FROM stories")):
        parts = [p for p in (url or "").split("/") if p]
        if "posts" not in parts:
            continue
        post_id = parts[parts.index("posts") + 1]
        if post_id == slug:
            continue
        keeper = by_slug.get(post_id)
        if keeper is None:
            conn.execute("UPDATE stories SET slug=? WHERE id=?", (post_id, sid))
            by_slug[post_id] = sid
            rekeyed += 1
            continue
        # Duplicate: fold this row's human work into the keeper, then drop it.
        for table in ("reviews", "story_tags"):
            conn.execute(
                f"UPDATE OR IGNORE {table} SET story_id=? WHERE story_id=?", (keeper, sid))
        conn.execute("DELETE FROM stories WHERE id=?", (sid,))
        merged += 1
    if rekeyed or merged:
        print(f"migrated: {rekeyed} stories rekeyed to post ids, {merged} duplicates merged")


def seed(db_path, reviews_path):
    conn = sqlite3.connect(db_path)
    conn.executescript((HERE / "schema.sql").read_text())
    rows = load(reviews_path)
    with conn:
        migrate(conn)
        for name, blurb, order in CRITERIA_SEED:
            conn.execute(
                "INSERT INTO criteria (name, blurb, sort_order) VALUES (?,?,?) "
                "ON CONFLICT(name) DO UPDATE SET blurb=excluded.blurb, "
                "sort_order=excluded.sort_order",
                (name, blurb, order),
            )
        for tag in TAG_SEED:
            conn.execute("INSERT INTO tags (name) VALUES (?) ON CONFLICT(name) DO NOTHING", (tag,))

        for r in rows:
            conn.execute(
                """INSERT INTO stories (slug, title, author, year, url, karma, words, survey_rank)
                   VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(slug) DO UPDATE SET
                     title=excluded.title, author=excluded.author, year=excluded.year,
                     url=excluded.url, karma=excluded.karma, words=excluded.words,
                     survey_rank=excluded.survey_rank""",
                (r["slug"], r["title"], r["author"], r["year"], r["url"], r["karma"],
                 r["words"], r["rank"]),
            )
            sid = conn.execute("SELECT id FROM stories WHERE slug=?", (r["slug"],)).fetchone()[0]
            conn.execute(
                """INSERT INTO llm_curations
                     (story_id, scorer, weighted, subscores, hook, review, source_doc)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(story_id) DO UPDATE SET
                     scorer=excluded.scorer, weighted=excluded.weighted,
                     subscores=excluded.subscores, hook=excluded.hook,
                     review=excluded.review, source_doc=excluded.source_doc""",
                (sid, LLM_SCORER, r["weighted"], json.dumps(r["subscores"]),
                 r["hook"], r["summary"], "data/reviews.jsonl"),
            )

        live = {r["slug"] for r in rows}
        stale = [sid for sid, slug in conn.execute("SELECT id, slug FROM stories")
                 if slug not in live]
        for sid in stale:
            conn.execute("UPDATE stories SET survey_rank=NULL WHERE id=?", (sid,))
            conn.execute("DELETE FROM llm_curations WHERE story_id=?", (sid,))

    n = conn.execute("SELECT count(*) FROM stories").fetchone()[0]
    h = conn.execute("SELECT count(*) FROM reviews").fetchone()[0]
    conn.close()
    print(f"seeded {len(rows)} works from {reviews_path}")
    print(f"{n} stories in db ({len(stale)} no longer in the archive), {h} human reviews kept")


if __name__ == "__main__":
    args = sys.argv[1:]
    db, reviews = DEFAULT_DB, DEFAULT_REVIEWS
    while args:
        flag = args.pop(0)
        if flag == "--db":
            db = args.pop(0)
        elif flag in ("--reviews", "--scores"):
            reviews = args.pop(0)
        else:
            sys.exit(f"unknown flag: {flag}")
    seed(db, reviews)

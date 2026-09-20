#!/usr/bin/env python3
"""Seed (or reseed) curate.sqlite3 from the survey's 03-scores.md.

Safe to re-run: inserts are idempotent (INSERT OR IGNORE / upserts keyed on
slug). Human-created rows (reviews, tags, new criteria) are never deleted.

Usage:
    python3 seed.py [--db path] [--scores path]
"""
import json
import re
import sqlite3
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULT_DB = HERE / "curate.sqlite3"
DEFAULT_SCORES = REPO / "03-scores.md"

DIMENSIONS = ["posthuman", "rigor", "idea_density", "craft", "form", "brevity"]

CRITERIA_SEED = [
    ("posthuman", "How central a genuinely non-human mind is (AI agents, uploads, hiveminds, alien optimizers).", 1),
    ("rigor", "Central mechanism followed consistently to its consequences, with technical literacy.", 2),
    ("idea_density", "Distinct, load-bearing ideas per word; ideas the plot cannot move without.", 3),
    ("craft", "Prose quality: voice, control, earned emotional payoff.", 4),
    ("form", "Whether the chosen form (transcript, chat log, found document) does narrative work.", 5),
    ("brevity", "Length discipline; as long as it needs to be scores 5.", 6),
]

TAG_SEED = [
    "posthuman", "ai", "uploaded-minds", "hivemind", "alignment", "simulation",
    "first-contact", "consciousness", "dystopia", "humor", "found-form",
    "hard-sf", "time", "vignette", "serial",
]

LLM_SCORER = "survey-2026 (LLM-assisted, see README.md)"


def unescape(cell):
    return cell.replace("\\|", "|").strip()


def split_row(line):
    s = line.strip()
    body = s[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [unescape(c) for c in re.split(r"(?<!\\)\|", body)]


def slug_from_url(url):
    # https://www.lesswrong.com/posts/<slug>/<title-slug>
    path = urllib.parse.urlparse(url).path
    parts = [p for p in path.split("/") if p]
    return parts[2] if len(parts) >= 3 and parts[1] == "posts" else parts[-1]


def parse_scores(path):
    """Yield dicts for each scored row of 03-scores.md."""
    rows = []
    link = re.compile(r"^\[(?P<title>.*?)\]\((?P<url>https?://[^)]+)\)$", re.S)
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = split_row(s)
        if len(cells) != 9:
            continue
        rank_txt = cells[0]
        if not rank_txt.isdigit():  # header/other rows
            continue
        m = link.match(cells[1].replace("\\|", "|"))
        if not m:
            print(f"WARN: no link in row {rank_txt}: {cells[1][:60]}", file=sys.stderr)
            continue
        subs = re.fullmatch(r"(\d)/(\d)/(\d)/(\d)/(\d)/(\d)", cells[5])
        weighted = re.fullmatch(r"\*\*(\d+(?:\.\d+)?)\*\*", cells[6])
        rows.append({
            "rank": int(rank_txt),
            "title": m.group("title"),
            "url": m.group("url"),
            "author": cells[2],
            "year": int(cells[3]) if cells[3].isdigit() else None,
            "karma": int(cells[4]) if cells[4].isdigit() else None,
            "subscores": {d: int(g) for d, g in zip(DIMENSIONS, subs.groups())} if subs else None,
            "weighted": float(weighted.group(1)) if weighted else None,
            "nn": cells[7],
            "note": cells[8],
        })
    return rows


def seed(db_path, scores_path):
    conn = sqlite3.connect(db_path)
    conn.executescript((HERE / "schema.sql").read_text())
    with conn:
        for name, blurb, order in CRITERIA_SEED:
            conn.execute(
                "INSERT INTO criteria (name, blurb, sort_order) VALUES (?,?,?) "
                "ON CONFLICT(name) DO NOTHING",
                (name, blurb, order),
            )
        for tag in TAG_SEED:
            conn.execute("INSERT INTO tags (name) VALUES (?) ON CONFLICT(name) DO NOTHING", (tag,))

        rows = parse_scores(scores_path)
        inserted = 0
        for r in rows:
            slug = slug_from_url(r["url"])
            cur = conn.execute(
                """INSERT INTO stories (slug, title, author, year, url, karma, survey_rank, nearest_neighbor)
                   VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(slug) DO UPDATE SET
                     title=excluded.title, author=excluded.author, year=excluded.year,
                     url=excluded.url, karma=excluded.karma, survey_rank=excluded.survey_rank,
                     nearest_neighbor=excluded.nearest_neighbor""",
                (slug, r["title"], r["author"], r["year"], r["url"], r["karma"], r["rank"],
                 None if r["nn"] in ("none", "") else r["nn"]),
            )
            story_id = conn.execute("SELECT id FROM stories WHERE slug=?", (slug,)).fetchone()[0]
            conn.execute(
                """INSERT INTO llm_curations (story_id, scorer, weighted, subscores, review, source_doc)
                   VALUES (?,?,?,?,?,?)
                   ON CONFLICT(story_id) DO UPDATE SET
                     scorer=excluded.scorer, weighted=excluded.weighted,
                     subscores=excluded.subscores, review=excluded.review,
                     source_doc=excluded.source_doc""",
                (story_id, LLM_SCORER, r["weighted"],
                 json.dumps(r["subscores"]) if r["subscores"] else None,
                 r["note"], Path(scores_path).name),
            )
            inserted += 1
    n = conn.execute("SELECT count(*) FROM stories").fetchone()[0]
    conn.close()
    print(f"seeded {len(rows)} rows from {scores_path} ({inserted} upserts); stories in db: {n}")


if __name__ == "__main__":
    args = sys.argv[1:]
    db, scores = DEFAULT_DB, DEFAULT_SCORES
    while args:
        flag = args.pop(0)
        if flag == "--db":
            db = args.pop(0)
        elif flag == "--scores":
            scores = args.pop(0)
        else:
            sys.exit(f"unknown flag: {flag}")
    seed(db, scores)

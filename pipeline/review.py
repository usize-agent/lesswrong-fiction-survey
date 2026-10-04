"""First pass: append validated reviews to data/reviews.jsonl.

    python3 pipeline/review.py path/to/batch.json   # list of review objects
    python3 pipeline/review.py --status             # progress by pack

A review: {"id", + every dimension in pipeline.rubric.DIMS (0-5 ints),
           "tags": [...], "line": one-line hook, "summary": 2-3 sentences}
Optional: "exclude": reason  (on reading, the post turned out not to be fiction)
Re-adding an id replaces the earlier review.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data/reviews.jsonl")
sys.path.insert(0, ROOT)
from pipeline.rubric import DIMS, TAGS  # noqa: E402

# impact is scored on the second pass, by pipeline/impact.py
FIRST_PASS = tuple(d for d in DIMS if d != "impact")


def load():
    out = {}
    if os.path.exists(PATH):
        for line in open(PATH):
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r
    return out


def validate(r, works):
    assert r["id"] in works, f"{r['id']} is not a work in data/corpus.json"
    if "exclude" in r:
        return
    for d in FIRST_PASS:
        assert isinstance(r[d], int) and 0 <= r[d] <= 5, f"{r['id']}: bad {d}"
    bad = set(r["tags"]) - TAGS
    assert not bad, f"{r['id']}: unknown tags {bad}"
    assert r["line"] and len(r["line"]) <= 140, f"{r['id']}: line missing or too long"
    assert r["summary"], f"{r['id']}: summary missing"


def main():
    corpus = json.load(open(os.path.join(ROOT, "data/corpus.json")))
    works = {k for k, v in corpus.items() if v["status"] == "work"}
    have = load()
    if sys.argv[1:] == ["--status"]:
        idx = json.load(open(os.path.join(ROOT, "data/pack_index.json")))
        todo = sorted({v["pack"] for k, v in idx.items() if k in works and k not in have})
        print(f"{len(have)}/{len(works)} reviewed; packs with work left: {todo[:10]}{'...' if len(todo) > 10 else ''}")
        return
    batch = json.load(open(sys.argv[1]))
    for r in batch:
        validate(r, works)
    for r in batch:
        have[r["id"]] = r
    with open(PATH, "w") as f:
        for r in sorted(have.values(), key=lambda r: r["id"]):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"ok: {len(batch)} added, {len(have)}/{len(works)} reviewed")


if __name__ == "__main__":
    main()

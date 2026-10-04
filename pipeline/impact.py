"""Second pass: append impact scores to data/impact.jsonl.

    python3 pipeline/impact.py path/to/batch.json   # list of {"id", "impact", ...}
    python3 pipeline/impact.py --status             # progress by pack

A second-pass entry:
    {"id": ..., "impact": 0-5,
     "craft": 0-5,       optional, only when the re-read changes the first call
     "concept": 0-5,     optional, same
     "why": "one line on what did or didn't land"}

Impact is scored on re-reading, never inferred from the first-pass summary.
Re-adding an id replaces the earlier entry.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pipeline.rubric import DIMS  # noqa: E402

PATH = os.path.join(ROOT, "data/impact.jsonl")
REVISABLE = ("craft", "concept", "hard", "mind", "foresight")


def load(path=PATH):
    out = {}
    if os.path.exists(path):
        for line in open(path):
            if line.strip():
                r = json.loads(line)
                out[r["id"]] = r
    return out


def validate(r, works):
    assert r["id"] in works, f"{r['id']} is not a work in data/corpus.json"
    assert isinstance(r["impact"], int) and 0 <= r["impact"] <= 5, f"{r['id']}: bad impact"
    for d in REVISABLE:
        if d in r:
            assert isinstance(r[d], int) and 0 <= r[d] <= 5, f"{r['id']}: bad {d}"
    assert r.get("why"), f"{r['id']}: why missing"
    assert len(r["why"]) <= 200, f"{r['id']}: why too long ({len(r['why'])})"
    unknown = set(r) - {"id", "impact", "why"} - set(REVISABLE)
    assert not unknown, f"{r['id']}: unexpected keys {unknown}"


def main():
    corpus = json.load(open(os.path.join(ROOT, "data/corpus.json")))
    works = {k for k, v in corpus.items() if v["status"] == "work"}
    have = load()
    if sys.argv[1:] == ["--status"]:
        idx = json.load(open(os.path.join(ROOT, "data/pack_index.json")))
        todo = sorted({v["pack"] for k, v in idx.items() if k in works and k not in have})
        print(f"{len(have)}/{len(works)} re-read; packs left: {todo[:12]}"
              f"{'...' if len(todo) > 12 else ''}")
        return
    batch = json.load(open(sys.argv[1]))
    for r in batch:
        validate(r, works)
    for r in batch:
        have[r["id"]] = r
    with open(PATH, "w") as f:
        for r in sorted(have.values(), key=lambda r: r["id"]):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    revised = sum(1 for r in batch if any(d in r for d in REVISABLE))
    print(f"ok: {len(batch)} added ({revised} with revisions), {len(have)}/{len(works)} re-read")


if __name__ == "__main__":
    main()

"""Build the archive outputs from data/reviews.jsonl + data/corpus.json.

    python3 pipeline/build.py

Writes:
    docs/index.html   the sortable display (data embedded, opens from file://)
    ARCHIVE.md        every work, ranked, summaries collapsed
    README.md         repo front page: rubric, top 30, the lists
"""
import html
import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIMS = ("hard", "vision", "mind", "foresight", "craft")
DIM_LABEL = {
    "hard": "Hard",
    "vision": "Vision",
    "mind": "Mind",
    "foresight": "Foresight",
    "craft": "Craft",
}
DIM_BLURB = {
    "hard": "Rigour of mechanism. Does the story's machinery actually work, and is it load-bearing?",
    "vision": "Scale and strangeness of the central idea.",
    "mind": "Interiority of non-human minds: model POV, uploads, model welfare.",
    "foresight": "Quality as prediction or warning. Would this change what you expect?",
    "craft": "Prose, structure, and whether the thing is a pleasure to read.",
}

# Default weights: a taste match, not a quality score. Hard SF and prose carry
# the most, then non-human interiority, then forecasting, then raw idea.
WEIGHTS = {"hard": 0.25, "vision": 0.15, "mind": 0.20, "foresight": 0.15, "craft": 0.25}

PRESETS = {
    "Taste match": WEIGHTS,
    "Hard SF": {"hard": 0.45, "vision": 0.20, "mind": 0.05, "foresight": 0.10, "craft": 0.20},
    "Model minds": {"hard": 0.10, "vision": 0.15, "mind": 0.50, "foresight": 0.05, "craft": 0.20},
    "Forecasting": {"hard": 0.20, "vision": 0.15, "mind": 0.05, "foresight": 0.45, "craft": 0.15},
    "Prose": {"hard": 0.05, "vision": 0.15, "mind": 0.10, "foresight": 0.05, "craft": 0.65},
}


def score(r, w=WEIGHTS):
    return round(sum(w[d] * r[d] for d in DIMS) / 5 * 100)


def load():
    corpus = json.load(open(os.path.join(ROOT, "data/corpus.json")))
    cands = json.load(open(os.path.join(ROOT, "cache/candidates.json")))["candidates"]
    idx = json.load(open(os.path.join(ROOT, "data/pack_index.json")))
    works, excluded = [], []
    for line in open(os.path.join(ROOT, "data/reviews.jsonl")):
        if not line.strip():
            continue
        r = json.loads(line)
        c = cands[r["id"]]
        parts = corpus[r["id"]].get("parts", [r["id"]])
        rec = {
            "id": r["id"],
            "title": c["title"],
            "author": c["author"] or "[account deleted]",
            "date": c["postedAt"][:10],
            "karma": c["baseScore"],
            "words": sum(cands[p]["wordCount"] for p in parts),
            "parts": len(parts),
            "url": f"https://www.lesswrong.com/posts/{r['id']}/{c['slug']}",
            "read": idx.get(r["id"], {}).get("read", "full"),
        }
        if "exclude" in r:
            rec["why"] = r["exclude"]
            excluded.append(rec)
            continue
        rec.update({d: r[d] for d in DIMS})
        rec["tags"] = r["tags"]
        rec["line"] = r["line"]
        rec["summary"] = r["summary"]
        rec["score"] = score(r)
        works.append(rec)
    works.sort(key=lambda r: (-r["score"], -r["karma"]))
    excluded.sort(key=lambda r: r["date"])
    elsewhere = sorted(
        ({"id": k, **v} for k, v in corpus.items() if v["status"] == "elsewhere"),
        key=lambda r: r["title"],
    )
    return works, excluded, elsewhere


# ---------------------------------------------------------------- markdown


def esc(s):
    return s.replace("|", "\\|")


def md_row(i, r):
    return (
        f"| {i} | **{esc(r['title'])}** | {esc(r['author'])} | {r['date'][:7]} | "
        f"{r['karma']} | {r['score']} | "
        + " ".join(str(r[d]) for d in DIMS)
        + " |"
    )


def md_table(rows, start=1):
    out = [
        "| # | Work | Author | Date | Karma | Score | H V M F C |",
        "| --: | --- | --- | --- | --: | --: | --- |",
    ]
    out += [md_row(i, r) for i, r in enumerate(rows, start)]
    return "\n".join(out)


def md_entry(i, r):
    tags = " ".join(f"`{t}`" for t in r["tags"])
    dims = " · ".join(f"{DIM_LABEL[d]} {r[d]}" for d in DIMS)
    part = f" · {r['parts']} parts" if r["parts"] > 1 else ""
    partial = " · read in part" if r["read"] == "partial" else ""
    return (
        f"### {i}. [{r['title']}]({r['url']}) — **{r['score']}**\n\n"
        f"{r['author']} · {r['date']} · {r['karma']} karma · "
        f"{r['words']:,} words{part}{partial}\n\n"
        f"{dims}\n\n"
        f"> {r['line']}\n\n"
        f"<details><summary>Summary</summary>\n\n{r['summary']}\n\n{tags}\n\n</details>\n"
    )


def write_archive(works, excluded, elsewhere):
    L = [
        "# The archive",
        "",
        f"All {len(works)} works, ranked by taste-match score. Every one was read in full "
        "unless noted; the handful marked *read in part* are long enough that they were "
        "read head and tail.",
        "",
        "The [interactive version](docs/index.html) sorts by any column and by karma, and "
        "lets you re-weight the rubric. See [README](README.md) for what the five "
        "dimensions mean.",
        "",
        "---",
        "",
    ]
    for i, r in enumerate(works, 1):
        L.append(md_entry(i, r))
    L += [
        "---",
        "",
        "## Elsewhere",
        "",
        "Nine posts are link-only pointers to science fiction hosted off LessWrong. "
        "They are listed but not scored, because the work is not here.",
        "",
    ]
    for r in elsewhere:
        L.append(f"- [{r['title']}]({r['url']}) — {r['author']}. {r['blurb']}")
    L += [
        "",
        "---",
        "",
        "## Read but not scored",
        "",
        f"{len(excluded)} posts survived the corpus filter, were read, and turned out not "
        "to be fiction after all — essays in the author's voice, abstracts for work hosted "
        "elsewhere, or a synopsis where the story should have been.",
        "",
    ]
    for r in excluded:
        L.append(f"- [{r['title']}]({r['url']}) — {r['author']}, {r['date'][:7]}. {r['why']}")
    L.append("")
    open(os.path.join(ROOT, "ARCHIVE.md"), "w").write("\n".join(L))


def write_readme(works, excluded, elsewhere):
    tagc = Counter(t for r in works for t in r["tags"])
    best = {}
    for d in DIMS:
        best[d] = sorted(works, key=lambda r: (-r[d], -r["score"]))[:5]
    hi_karma = sorted(works, key=lambda r: -r["karma"])[:10]
    # Works the crowd missed: high score, low karma.
    buried = [r for r in works if r["karma"] < 30][:10]

    L = [
        "# LessWrong science fiction: an archive",
        "",
        "LessWrong has accidentally become a decent little science fiction outlet. "
        "This is an attempt to say which of it is worth your evening.",
        "",
        f"Every post ever tagged fiction was pulled, {len(works) + len(excluded)} of them "
        f"read end to end, and {len(works)} scored against a rubric built for one "
        "particular taste: hard science fiction in the Egan and early-Stross sense, "
        "stories told from inside a non-human mind, and honest attempts to forecast "
        "what is coming.",
        "",
        "**[Browse the archive](ARCHIVE.md)** · **[Interactive version](docs/index.html)** "
        "(sort by score, karma, or any single dimension; re-weight the rubric live)",
        "",
        "## The rubric",
        "",
        "Five dimensions, each 0–5, scored on reading:",
        "",
        "| | Dimension | What it measures | Default weight |",
        "| --- | --- | --- | --: |",
    ]
    for d in DIMS:
        L.append(
            f"| **{DIM_LABEL[d][0]}** | {DIM_LABEL[d]} | {DIM_BLURB[d]} | "
            f"{int(WEIGHTS[d] * 100)}% |"
        )
    L += [
        "",
        "The weighted total is a **taste match, not a quality score**. A beautifully written "
        "story with no mechanism and no non-human mind in it scores in the fifties and is "
        "still worth reading — which is why the display lets you sort by craft alone, and "
        "why the lists below break the archive out by dimension.",
        "",
        "## Top 30",
        "",
        md_table(works[:30]),
        "",
        f"[All {len(works)}, with summaries →](ARCHIVE.md)",
        "",
        "## Best by dimension",
        "",
    ]
    for d in DIMS:
        L.append(f"**{DIM_LABEL[d]}** — {DIM_BLURB[d]}")
        L.append("")
        for r in best[d]:
            L.append(
                f"- [{r['title']}]({r['url']}) ({r['author']}) — {DIM_LABEL[d]} {r[d]}, "
                f"score {r['score']}"
            )
        L.append("")
    L += [
        "## What the site liked",
        "",
        "Highest karma in the corpus, for comparison with the ranking above:",
        "",
        md_table(hi_karma),
        "",
        "## Buried",
        "",
        "Scored well, finished under 30 karma. The clearest case for doing this at all:",
        "",
        md_table(buried),
        "",
        "## The corpus",
        "",
        f"- **{len(works)}** works scored",
        f"- **{len(elsewhere)}** link-only pointers to fiction hosted off-site, listed but "
        "not scored ([bottom of ARCHIVE.md](ARCHIVE.md#elsewhere))",
        f"- **{len(excluded)}** posts read and then set aside as not fiction",
        "- 170 serial chapters folded into their parent works",
        "- 177 posts filtered out before reading as non-fiction, announcements, reviews, "
        "reposts, translations, verse or puzzles",
        "",
        "Most-used tags: "
        + ", ".join(f"`{t}` ({n})" for t, n in tagc.most_common(12))
        + ".",
        "",
        "## Layout",
        "",
        "```",
        "data/corpus.json      what counts as a work, and why",
        "data/reviews.jsonl    one line per work: scores, tags, hook, summary",
        "pipeline/corpus.py    inclusion policy      -> data/corpus.json",
        "pipeline/packs.py     reading packs         -> work/packs/",
        "pipeline/review.py    validate and append   -> data/reviews.jsonl",
        "pipeline/build.py     this archive          -> docs/, *.md",
        "curate/               local rating app (stdlib + sqlite3)",
        "archive/v1/           the first pass, kept for the record",
        "```",
        "",
        "Rebuild the outputs with `python3 pipeline/build.py`. Rate things yourself with "
        "`python3 curate/app.py`.",
        "",
    ]
    open(os.path.join(ROOT, "README.md"), "w").write("\n".join(L))


# ---------------------------------------------------------------- display


def write_html(works, excluded, elsewhere):
    tmpl = open(os.path.join(ROOT, "pipeline/display.html")).read()
    payload = {
        "works": works,
        "elsewhere": elsewhere,
        "excluded": excluded,
        "dims": list(DIMS),
        "labels": DIM_LABEL,
        "blurbs": DIM_BLURB,
        "weights": WEIGHTS,
        "presets": PRESETS,
    }
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    out = tmpl.replace("/*DATA*/null/*DATA*/", blob)
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    open(os.path.join(ROOT, "docs/index.html"), "w").write(out)


def main():
    works, excluded, elsewhere = load()
    write_archive(works, excluded, elsewhere)
    write_readme(works, excluded, elsewhere)
    write_html(works, excluded, elsewhere)
    print(f"{len(works)} works, {len(excluded)} not-fiction, {len(elsewhere)} elsewhere")
    print(f"score range {works[-1]['score']}-{works[0]['score']}")
    print("wrote README.md ARCHIVE.md docs/index.html")


if __name__ == "__main__":
    main()

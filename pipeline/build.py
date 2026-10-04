"""Build the archive outputs from data/reviews.jsonl + data/corpus.json.

    python3 pipeline/build.py

Writes:
    docs/index.html   the sortable display (data embedded, opens from file://)
    ARCHIVE.md        every work, ranked, summaries collapsed
    README.md         repo front page: rubric, top 30, the lists
"""
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, ROOT)
from pipeline.rubric import (  # noqa: E402
    DIMS, DIM_ABBR, DIM_BLURB, DIM_LABEL, PICKER, PRESETS, WEIGHTS, score,
)


def load():
    corpus = json.load(open(os.path.join(ROOT, "data/corpus.json")))
    cands = json.load(open(os.path.join(ROOT, "cache/candidates.json")))["candidates"]
    idx = json.load(open(os.path.join(ROOT, "data/pack_index.json")))
    picks = json.load(open(os.path.join(ROOT, "data/picks.json")))["picks"]
    notes = {p["id"]: p["note"] for p in picks}
    order = {p["id"]: i for i, p in enumerate(picks)}
    second = {}
    ip = os.path.join(ROOT, "data/impact.jsonl")
    if os.path.exists(ip):
        for line in open(ip):
            if line.strip():
                r2 = json.loads(line)
                second[r2["id"]] = r2
    ap = os.path.join(ROOT, "data/audio.json")
    audio = json.load(open(ap)) if os.path.exists(ap) else {}
    works, excluded = [], []
    for line in open(os.path.join(ROOT, "data/reviews.jsonl")):
        if not line.strip():
            continue
        r = json.loads(line)
        c = cands[r["id"]]
        meta = corpus[r["id"]]
        parts = meta.get("parts", [r["id"]])
        lw = f"https://www.lesswrong.com/posts/{r['id']}/{c['slug']}"
        rec = {
            "id": r["id"],
            "title": meta.get("title") or c["title"],
            "author": meta.get("author") or c["author"] or "[account deleted]",
            "date": c["postedAt"][:10],
            "karma": c["baseScore"],
            "words": meta.get("words") or sum(cands[p]["wordCount"] for p in parts),
            "parts": len(parts),
            "url": meta.get("url", lw),
            "read": idx.get(r["id"], {}).get("read", "full"),
        }
        if meta.get("external"):
            # The work lives off LessWrong; the post there is a link, and its
            # karma is the community's reception of the pointer.
            rec["external"] = True
            rec["lw"] = lw
        if "exclude" in r:
            rec["why"] = r["exclude"]
            excluded.append(rec)
            continue
        rec["note"] = notes.get(r["id"])
        rec["pick"] = order.get(r["id"])
        # Second pass supplies impact, and may revise a first-pass call.
        r = {**r, **{k: v for k, v in second.get(r["id"], {}).items()
                     if k not in ("id", "why")}}
        rec["why"] = second.get(r["id"], {}).get("why")
        rec["reread"] = r["id"] in second
        rec.update({d: r[d] for d in DIMS if d in r})
        a = audio.get(r["id"])
        if a:
            rec["mp3"] = a["mp3"]
            rec["secs"] = a["duration"]
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
    preface = json.load(open(os.path.join(ROOT, "data/picks.json")))["_preface"]
    return works, excluded, elsewhere, preface


# ---------------------------------------------------------------- markdown


def esc(s):
    return s.replace("|", "\\|")


def md_row(i, r):
    return (
        f"| {i} | **{esc(r['title'])}** | {esc(r['author'])} | {r['date'][:7]} | "
        f"{r['karma']} | {r['score']} | "
        + " ".join(str(r.get(d, "–")) for d in DIMS)
        + " |"
    )


def md_table(rows, start=1):
    out = [
        "| # | Work | Author | Date | Karma | Score | "
        + " ".join(DIM_ABBR[d] for d in DIMS) + " |",
        "| --: | --- | --- | --- | --: | --: | --- |",
    ]
    out += [md_row(i, r) for i, r in enumerate(rows, start)]
    return "\n".join(out)


def md_entry(i, r):
    tags = " ".join(f"`{t}`" for t in r["tags"])
    dims = " · ".join(f"{DIM_LABEL[d]} {r.get(d, '–')}" for d in DIMS)
    part = f" · {r['parts']} parts" if r["parts"] > 1 else ""
    partial = " · read in part" if r["read"] == "partial" else ""
    star = "★ " if r["note"] else ""
    note = (f"\n> **★ {PICKER}'s pick.** {r['note']}\n" if r["note"] else "")
    return (
        f"### {i}. {star}[{r['title']}]({r['url']}) — **{r['score']}**\n\n"
        f"{r['author']} · {r['date']} · {r['karma']} karma · "
        f"{r['words']:,} words{part}{partial}\n\n"
        f"{dims}\n\n"
        f"> {r['line']}\n"
        f"{note}\n"
        f"<details><summary>Summary</summary>\n\n{r['summary']}\n\n{tags}\n\n</details>\n"
    )


def write_archive(works, excluded, elsewhere, preface):
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
        f"## {PICKER}'s picks",
        "",
        preface,
        "",
    ]
    for r in sorted((r for r in works if r["note"]), key=lambda r: r["pick"]):
        L += [
            f"**★ [{r['title']}]({r['url']})** — {r['author']}, {r['date'][:7]}, "
            f"{r['karma']} karma, score {r['score']}",
            "",
            f"> {r['note']}",
            "",
        ]
    L += [
        "---",
        "",
        "## Everything",
        "",
    ]
    for i, r in enumerate(works, 1):
        L.append(md_entry(i, r))
    L += [
        "---",
        "",
        "## Elsewhere",
        "",
        "Link posts whose target could not be retrieved: two sites refuse automated "
        "requests, one novella's link is dead, and one blog no longer exists. Listed "
        "but not scored. The five link posts that could be fetched were read in full "
        "and are ranked with everything else.",
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


def write_readme(works, excluded, elsewhere, preface):
    tagc = Counter(t for r in works for t in r["tags"])
    best = {}
    for d in DIMS:
        best[d] = sorted((w for w in works if d in w),
                         key=lambda r: (-r[d], -r["score"]))[:5]
    hi_karma = sorted(works, key=lambda r: -r["karma"])[:10]
    picks = sorted((r for r in works if r["note"]), key=lambda r: r["pick"])
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
        f"## {PICKER}'s picks",
        "",
        preface,
        "",
        "| | Work | Author | Karma | Score |",
        "| --- | --- | --- | --: | --: |",
    ]
    for r in picks:
        L.append(
            f"| ★ | [{esc(r['title'])}]({r['url']}) | {esc(r['author'])} | "
            f"{r['karma']} | {r['score']} |"
        )
    L += [
        "",
        "The card for each is on its entry in [ARCHIVE.md](ARCHIVE.md), and they are "
        "filterable in the display.",
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
        f"- **{sum(1 for r in works if r.get('external'))}** of those are link posts to "
        "work hosted off LessWrong, fetched and read in full; the title links to the "
        "work, the karma is the reception of the pointer",
        f"- **{len(elsewhere)}** further link posts whose target could not be retrieved, "
        "listed but not scored ([bottom of ARCHIVE.md](ARCHIVE.md#elsewhere))",
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
        "cache/                     every post tagged fiction, as fetched",
        "data/corpus.json           what counts as a work, and why",
        "data/reviews.jsonl         one line per work: scores, tags, hook, summary",
        "pipeline/fetch_*.py        LessWrong GraphQL          -> cache/",
        "pipeline/corpus.py         inclusion policy           -> data/corpus.json",
        "pipeline/packs.py          reading packs              -> work/packs/",
        "pipeline/review.py         validate and append        -> data/reviews.jsonl",
        "pipeline/build.py          this archive               -> docs/, *.md",
        "curate/                    local rating app (stdlib + sqlite3)",
        "```",
        "",
        "Rebuild the outputs with `python3 pipeline/build.py`. Rate things yourself with "
        "`python3 curate/app.py`.",
        "",
        "An earlier pass over the same corpus, with a different rubric and a weaker "
        "reader, is in the git history up to `1b784c9`. Nothing here depends on it.",
        "",
    ]
    open(os.path.join(ROOT, "README.md"), "w").write("\n".join(L))


# ---------------------------------------------------------------- display


def write_html(works, excluded, elsewhere, preface):
    tmpl = open(os.path.join(ROOT, "pipeline/display.html")).read()
    payload = {
        "works": works,
        "elsewhere": elsewhere,
        "excluded": excluded,
        "dims": list(DIMS),
        "labels": DIM_LABEL,
        "abbr": DIM_ABBR,
        "blurbs": DIM_BLURB,
        "weights": WEIGHTS,
        "presets": PRESETS,
        "preface": preface,
        "picker": PICKER,
    }
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    out = tmpl.replace("/*DATA*/null/*DATA*/", blob)
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    open(os.path.join(ROOT, "docs/index.html"), "w").write(out)


def main():
    works, excluded, elsewhere, preface = load()
    write_archive(works, excluded, elsewhere, preface)
    write_readme(works, excluded, elsewhere, preface)
    write_html(works, excluded, elsewhere, preface)
    print(f"{len(works)} works, {len(excluded)} not-fiction, {len(elsewhere)} elsewhere")
    print(f"score range {works[-1]['score']}-{works[0]['score']}")
    print("wrote README.md ARCHIVE.md docs/index.html")


if __name__ == "__main__":
    main()

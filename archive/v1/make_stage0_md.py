#!/usr/bin/env python3
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "cache", "candidates.json")) as f:
    data = json.load(f)

candidates = data["candidates"]
tag_info = data["tag_info"]

rows = list(candidates.values())
rows.sort(key=lambda r: r["postedAt"])

def decade(iso):
    year = int(iso[:4])
    return f"{(year // 10) * 10}s"

by_source = Counter()
for r in rows:
    for src in r["sources"]:
        by_source[src] += 1

by_decade = Counter()
for r in rows:
    by_decade[decade(r["postedAt"])] += 1

lines = []
lines.append("# Stage 0 — Candidate set\n")
lines.append(f"Pulled {datetime.utcnow().isoformat()}Z from LessWrong GraphQL "
             f"(`tagRels.postsWithTag` view, the same mechanism tag pages use).\n")

lines.append("## Tag resolution\n")
lines.append("| Source tag | slug | tagId | reported postCount | tagRels fetched |")
lines.append("|---|---|---|---|---|")
fetched_counts = Counter()
for r in rows:
    for src in r["sources"]:
        fetched_counts[src] += 1
for slug, info in tag_info.items():
    lines.append(f"| {info['name']} | `{slug}` | `{info['_id']}` | {info['postCount']} | {fetched_counts[slug]} |")
lines.append("")
lines.append("Note: fetched counts are lower than reported `postCount` for all three tags. "
             "Confirmed cause (see NOTES.md): a subset of TagRel rows point at posts that "
             "return `app.operation_not_allowed` on unauthenticated read (deleted/draft/"
             "rejected posts with a lingering tag-relation row). These are unreachable "
             "without auth and are excluded here, not silently miscounted.\n")

lines.append(f"## Totals\n")
lines.append(f"- **{len(rows)}** unique candidate posts (union of all three tags)\n")

lines.append("### Counts by source tag (a post can belong to more than one)\n")
lines.append("| Source tag | Count |")
lines.append("|---|---|")
for src, _ in tag_info.items():
    lines.append(f"| {src} | {by_source[src]} |")
lines.append("")

lines.append("### Counts by decade\n")
lines.append("| Decade | Count |")
lines.append("|---|---|")
for dec in sorted(by_decade.keys()):
    lines.append(f"| {dec} | {by_decade[dec]} |")
lines.append("")

lines.append("## Full candidate table\n")
lines.append("| Title | Author | Posted | Karma | Words | Comments | Sources (relevance) | Tags |")
lines.append("|---|---|---|---|---|---|---|---|")
for r in rows:
    date = r["postedAt"][:10]
    sources = ", ".join(f"{s}:{v}" for s, v in sorted(r["sources"].items()))
    tags = ", ".join(t["name"] for t in r["tags"])
    title_link = f"[{r['title']}](https://www.lesswrong.com/posts/{r['_id']}/{r['slug']})"
    author = r["author"] or "(unknown)"
    lines.append(f"| {title_link} | {author} | {date} | {r['baseScore']} | {r['wordCount']} | {r['commentCount']} | {sources} | {tags} |")

with open(os.path.join(BASE, "00-candidates.md"), "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"Wrote 00-candidates.md with {len(rows)} rows")

#!/usr/bin/env python3
"""Build a compact digest of every fetched candidate for the Stage 2 prefilter:
title/author/year/karma/wordcount/tags plus a stripped plain-text excerpt of
the opening ~130 words. Written as one JSON file (for scripts) and one chunked
text file (for me to read through in batches without opening 776 separate
cache files).
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "cache")
POSTS_CACHE = os.path.join(CACHE, "posts")

GLOWFIC_RE = re.compile(r"\bglowfic\b", re.IGNORECASE)


def strip_markdown(md):
    text = md
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_#>`]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    with open(os.path.join(CACHE, "candidates.json")) as f:
        data = json.load(f)
    candidates = data["candidates"]
    ids = sorted(candidates.keys(), key=lambda k: candidates[k]["postedAt"])

    digest = []
    missing = []
    for pid in ids:
        meta = candidates[pid]
        cache_file = os.path.join(POSTS_CACHE, f"{pid}.json")
        if not os.path.exists(cache_file):
            missing.append(pid)
            continue
        with open(cache_file) as f:
            cached = json.load(f)
        result = cached.get("data", {}).get("post", {}).get("result")
        if result is None:
            missing.append(pid)
            continue
        markdown = (result.get("contents") or {}).get("markdown") or ""
        plain = strip_markdown(markdown)
        excerpt = " ".join(plain.split()[:130])
        digest.append({
            "_id": pid,
            "title": meta["title"],
            "author": meta["author"],
            "year": meta["postedAt"][:4],
            "postedAt": meta["postedAt"][:10],
            "karma": meta["baseScore"],
            "wordCount": meta["wordCount"],
            "tags": [t["name"] for t in meta["tags"]],
            "sources": meta["sources"],
            "has_glowfic_mention": bool(GLOWFIC_RE.search(plain)),
            "excerpt": excerpt,
            "full_char_len": len(plain),
        })

    with open(os.path.join(CACHE, "digest.json"), "w") as f:
        json.dump(digest, f, indent=2)

    # Chunked human-readable text for batch reading, ~40 posts per chunk
    chunk_size = 40
    out_dir = os.path.join(BASE, "digest_chunks")
    os.makedirs(out_dir, exist_ok=True)
    for existing in os.listdir(out_dir):
        os.remove(os.path.join(out_dir, existing))

    for chunk_idx in range(0, len(digest), chunk_size):
        chunk = digest[chunk_idx:chunk_idx + chunk_size]
        lines = []
        for j, entry in enumerate(chunk, chunk_idx + 1):
            lines.append(f"### [{j}] {entry['title']} — {entry['author']} ({entry['year']}, karma {entry['karma']}, {entry['wordCount']}w)")
            lines.append(f"id={entry['_id']} tags={entry['tags']} sources={entry['sources']}")
            if entry["has_glowfic_mention"]:
                lines.append("[FLAG: mentions 'glowfic' in body]")
            lines.append(f"excerpt: {entry['excerpt']}")
            lines.append("")
        fn = os.path.join(out_dir, f"chunk_{chunk_idx // chunk_size:03d}.txt")
        with open(fn, "w") as f:
            f.write("\n".join(lines))

    print(f"digest entries: {len(digest)}, missing: {len(missing)}")
    if missing:
        print("missing ids:", missing[:20], "..." if len(missing) > 20 else "")
    print(f"chunks written to {out_dir}: {len(os.listdir(out_dir))} files")


if __name__ == "__main__":
    main()

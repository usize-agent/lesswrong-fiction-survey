#!/usr/bin/env python3
"""Stage 3 prep: extract full plain text for every KEEP story, batched into
files of roughly TARGET_WORDS each (never splitting a story across files),
ordered chronologically. Written to fulltext_batches/ for me to Read and
score in full before calling append_score.py.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "cache")
POSTS_CACHE = os.path.join(CACHE, "posts")
OUT_DIR = os.path.join(BASE, "fulltext_batches")
TARGET_WORDS = 25000


def strip_markdown(md):
    text = md
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_#>`]", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def main():
    with open(os.path.join(CACHE, "candidates.json")) as f:
        candidates = json.load(f)["candidates"]
    decisions = {}
    with open(os.path.join(CACHE, "filter_decisions.jsonl")) as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                decisions[d["id"]] = d

    keep_ids = [pid for pid, d in decisions.items() if d["decision"] == "KEEP"]
    keep_ids.sort(key=lambda pid: candidates[pid]["postedAt"])

    os.makedirs(OUT_DIR, exist_ok=True)
    for f in os.listdir(OUT_DIR):
        os.remove(os.path.join(OUT_DIR, f))

    batch = []
    batch_words = 0
    batch_idx = 0
    manifest = []

    def flush():
        nonlocal batch, batch_words, batch_idx
        if not batch:
            return
        fn = os.path.join(OUT_DIR, f"batch_{batch_idx:03d}.txt")
        with open(fn, "w") as fh:
            fh.write("\n\n".join(batch))
        batch_idx += 1
        batch = []
        batch_words = 0

    for pid in keep_ids:
        meta = candidates[pid]
        cache_file = os.path.join(POSTS_CACHE, f"{pid}.json")
        with open(cache_file) as f:
            cached = json.load(f)
        result = cached.get("data", {}).get("post", {}).get("result")
        markdown = (result.get("contents") or {}).get("markdown") or "" if result else ""
        plain = strip_markdown(markdown)
        url = f"https://www.lesswrong.com/posts/{pid}/{meta['slug']}"
        header = (f"===== STORY id={pid} =====\n"
                  f"Title: {meta['title']}\nAuthor: {meta['author']}\nYear: {meta['postedAt'][:4]}\n"
                  f"Karma: {meta['baseScore']}\nWordCount: {meta['wordCount']}\nURL: {url}\n"
                  f"-----\n{plain}\n===== END STORY {pid} =====")
        wc = meta["wordCount"]
        if batch and batch_words + wc > TARGET_WORDS:
            flush()
        batch.append(header)
        batch_words += wc
        manifest.append(pid)
    flush()

    with open(os.path.join(BASE, "cache", "score_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"{len(keep_ids)} KEEP stories -> {batch_idx} batches in {OUT_DIR}")


if __name__ == "__main__":
    main()

"""Build reading packs (work/packs/pack_NNN.txt) from cached post bodies.

Each pack holds several works as cleaned plain-ish markdown (images and link
targets stripped) so a reader can go through the corpus in order. Works longer
than LONG words are abridged to head + tail and marked as such; the reviewer
records that as read="partial".
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_CHARS = 60_000
LONG = 7_000
HEAD, TAIL = 5_500, 1_200


def body(pid):
    p = json.load(open(os.path.join(ROOT, f"cache/posts/{pid}.json")))
    r = ((p.get("data") or {}).get("post") or {}).get("result") or {}
    return (r.get("contents") or {}).get("markdown") or ""


def clean(md):
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"https?://\S+", "", md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def abridge(text):
    words = text.split(" ")
    if len(words) <= LONG:
        return text, "full"
    return (" ".join(words[:HEAD]) + f"\n\n[... {len(words) - HEAD - TAIL} words omitted ...]\n\n"
            + " ".join(words[-TAIL:])), "partial"


def main():
    cands = json.load(open(os.path.join(ROOT, "cache/candidates.json")))["candidates"]
    corpus = json.load(open(os.path.join(ROOT, "data/corpus.json")))
    works = sorted((pid for pid, r in corpus.items() if r["status"] == "work"),
                   key=lambda pid: cands[pid]["postedAt"])
    outdir = os.path.join(ROOT, "work/packs")
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        os.remove(os.path.join(outdir, f))
    index, pack, buf = {}, 0, []

    def flush():
        nonlocal pack, buf
        if buf:
            open(os.path.join(outdir, f"pack_{pack:03d}.txt"), "w").write("\n\n".join(buf))
            pack += 1
            buf = []

    for pid in works:
        c = cands[pid]
        parts = corpus[pid].get("parts", [pid])
        text = clean(body(pid))
        if len(parts) > 1:
            text += f"\n\n[SERIAL: {len(parts)} parts. Last part opens:]\n" + clean(body(parts[-1]))[:1500]
        text, read = abridge(text)
        head = (f"########## {pid} | {c['title']} | {c['author']} | {c['postedAt'][:10]} | "
                f"karma {c['baseScore']} | {c['wordCount']} words | read={read}")
        block = head + "\n\n" + text
        if buf and sum(map(len, buf)) + len(block) > PACK_CHARS:
            flush()
        buf.append(block)
        index[pid] = {"pack": pack, "read": read}
    flush()
    json.dump(index, open(os.path.join(ROOT, "work/pack_index.json"), "w"), indent=1)
    print(f"{len(works)} works in {pack} packs")


if __name__ == "__main__":
    main()

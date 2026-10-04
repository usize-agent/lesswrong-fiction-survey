"""Resolve Type III Audio narrations for every work.

    python3 pipeline/audio.py            # resumable; caches one file per post
    python3 pipeline/audio.py --status

LessWrong has Type III Audio generate a text-to-speech narration for most posts
above a karma threshold. Their embed resolves a page URL to a narration through
a public endpoint, which is what this asks:

    GET https://api.type3.audio/narration/find?url=<post url>&request_source=embed

A hit carries an `mp3_url` and a duration in seconds; a miss is a short JSON
message, cached too so a rerun does not ask again. Nothing here is scraped from
the player: it is the same request the embed makes, one at a time, with a
descriptive user agent.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache/narration")
ENDPOINT = "https://api.type3.audio/narration/find"
UA = ("LW-Fiction-Survey-Research/0.2 (personal research project cataloguing "
      "LessWrong fiction; contact via the GitHub repo)")
MIN_INTERVAL = 1.0

_last = [0.0]


def fetch(post_url):
    wait = MIN_INTERVAL - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    q = urllib.parse.urlencode({"url": post_url, "request_source": "embed"})
    req = urllib.request.Request(f"{ENDPOINT}?{q}", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"message": "not found"}
        raise


def works():
    corpus = json.load(open(os.path.join(ROOT, "data/corpus.json")))
    cands = json.load(open(os.path.join(ROOT, "cache/candidates.json")))["candidates"]
    out = []
    for pid, rec in corpus.items():
        if rec["status"] != "work":
            continue
        c = cands[pid]
        out.append((pid, f"https://www.lesswrong.com/posts/{pid}/{c['slug']}"))
    return sorted(out)


def main():
    os.makedirs(CACHE, exist_ok=True)
    items = works()
    if sys.argv[1:] == ["--status"]:
        have = [p for p, _ in items if os.path.exists(os.path.join(CACHE, p + ".json"))]
        hits = 0
        for p in have:
            d = json.load(open(os.path.join(CACHE, p + ".json")))
            hits += bool(d.get("mp3_url"))
        print(f"{len(have)}/{len(items)} resolved, {hits} with audio")
        return
    done = hits = 0
    for pid, url in items:
        path = os.path.join(CACHE, pid + ".json")
        if os.path.exists(path):
            d = json.load(open(path))
        else:
            d = fetch(url)
            json.dump(d, open(path, "w"))
            done += 1
        if d.get("mp3_url"):
            hits += 1
    out = {}
    for pid, _ in items:
        path = os.path.join(CACHE, pid + ".json")
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        if d.get("mp3_url"):
            out[pid] = {"mp3": d["mp3_url"], "duration": d.get("duration")}
    json.dump(out, open(os.path.join(ROOT, "data/audio.json"), "w"),
              indent=0, sort_keys=True)
    print(f"{len(items)} works, {done} newly fetched, {hits} with audio "
          f"-> data/audio.json")


if __name__ == "__main__":
    main()

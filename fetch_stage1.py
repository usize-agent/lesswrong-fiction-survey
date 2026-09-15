#!/usr/bin/env python3
"""Stage 1: fetch markdown bodies for every Stage 0 candidate.

Resumable: checks cache/posts/<id>.json before every request. Appends one
line to 01-fetch-log.md immediately after each post (cached-hit or freshly
fetched), so an interrupted run is visible on resume just by reading the log.
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

ENDPOINT = "https://www.lesswrong.com/graphql"
USER_AGENT = "LW-Fiction-Survey-Research/0.1 (contact: mcfoster1228@gmail.com; personal research project cataloguing LessWrong fiction)"
MIN_INTERVAL = 2.0

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "cache")
POSTS_CACHE = os.path.join(CACHE, "posts")
LOG_PATH = os.path.join(BASE, "01-fetch-log.md")

_last_request_time = [0.0]

NO_ARCHIVE_PATTERNS = [
    r"please don'?t (re)?post",
    r"do not (re)?post (this|elsewhere)",
    r"not to be archived",
    r"please don'?t archive",
    r"do not redistribute",
    r"all rights reserved.{0,40}(do not|no reproduction)",
    r"do not (mirror|republish)",
]
NO_ARCHIVE_RE = re.compile("|".join(NO_ARCHIVE_PATTERNS), re.IGNORECASE)


def graphql(query, variables=None):
    now = time.time()
    elapsed = now - _last_request_time[0]
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", "ignore")[:500]
        _last_request_time[0] = time.time()
        return {"errors": [{"message": f"HTTP {e.code}: {err_body}"}]}
    finally:
        _last_request_time[0] = time.time()
    return data


POST_QUERY = """
query($id: String) {
  post(input: {selector: {_id: $id}}) {
    result {
      _id
      title
      slug
      pageUrl
      postedAt
      baseScore
      wordCount
      commentCount
      noIndex
      user { displayName slug }
      tags { _id name slug }
      tagRelevance
      contents { markdown }
    }
  }
}
"""


def ensure_log_header():
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w") as f:
            f.write("# Stage 1 — Fetch log\n\n")
            f.write("One line per post, appended as fetched. `CACHED` means it was already "
                    "on disk from a prior run; `FETCHED` means a fresh request was made this "
                    "run; `ERROR` means the fetch failed and needs a retry.\n\n")


def log_line(text):
    with open(LOG_PATH, "a") as f:
        f.write(text.rstrip("\n") + "\n")


def main():
    with open(os.path.join(CACHE, "candidates.json")) as f:
        data = json.load(f)
    candidates = data["candidates"]
    ids = sorted(candidates.keys(), key=lambda k: candidates[k]["postedAt"])

    ensure_log_header()

    n_cached = 0
    n_fetched = 0
    n_error = 0
    n_flagged = 0

    for i, pid in enumerate(ids, 1):
        meta = candidates[pid]
        title = meta["title"]
        cache_file = os.path.join(POSTS_CACHE, f"{pid}.json")

        if os.path.exists(cache_file):
            n_cached += 1
            with open(cache_file) as f:
                cached = json.load(f)
            result = cached.get("data", {}).get("post", {}).get("result")
            status = "CACHED"
        else:
            resp = graphql(POST_QUERY, {"id": pid})
            if "errors" in resp and resp["errors"]:
                n_error += 1
                log_line(f"- [{i}/{len(ids)}] `{pid}` **{title}** — ERROR: {resp['errors'][0].get('message', '')[:200]}")
                continue
            result = resp.get("data", {}).get("post", {}).get("result")
            if result is None:
                n_error += 1
                log_line(f"- [{i}/{len(ids)}] `{pid}` **{title}** — ERROR: null result")
                continue
            with open(cache_file, "w") as f:
                json.dump(resp, f, indent=2)
            n_fetched += 1
            status = "FETCHED"

        markdown = (result.get("contents") or {}).get("markdown") or ""
        flag = ""
        if NO_ARCHIVE_RE.search(markdown):
            flag = " ⚠️ NO-ARCHIVE PHRASE DETECTED — review before using in shortlist"
            n_flagged += 1

        log_line(f"- [{i}/{len(ids)}] `{pid}` **{title}** — {status}, {len(markdown)} chars{flag}")

    print(f"Done. cached={n_cached} fetched={n_fetched} errors={n_error} flagged={n_flagged} total={len(ids)}")


if __name__ == "__main__":
    main()

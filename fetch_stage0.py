#!/usr/bin/env python3
"""Stage 0: pull candidate post lists for fiction / parables-and-fables / narratives-stories
tags from LessWrong GraphQL, via the TagRel.postsWithTag view (same mechanism the tag
pages themselves use, sorted by tag-relevance score).

Resumable: caches every tagRels page under cache/tagrels/<tagSlug>/<offset>.json and
never re-requests a page that's already cached. Also caches each unique post's listing
fields under cache/posts_meta/<postId>.json (bodies are fetched later, in stage 1).
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

ENDPOINT = "https://www.lesswrong.com/graphql"
USER_AGENT = "LW-Fiction-Survey-Research/0.1 (contact: mcfoster1228@gmail.com; personal research project cataloguing LessWrong fiction)"
MIN_INTERVAL = 2.0
PAGE_SIZE = 100

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "cache")
TAGRELS_CACHE = os.path.join(CACHE, "tagrels")
POSTS_META_CACHE = os.path.join(CACHE, "posts_meta")

TAGS = [
    ("fiction", "Fiction"),
    ("parables-and-fables", "Parables & Fables"),
    ("narratives-stories", "Narratives (stories)"),
]

_last_request_time = [0.0]


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
        print(f"HTTP error {e.code}: {e.read().decode('utf-8', 'ignore')[:500]}", file=sys.stderr)
        raise
    finally:
        _last_request_time[0] = time.time()
    if "errors" in data:
        print("GraphQL errors:", json.dumps(data["errors"])[:1000], file=sys.stderr)
    return data


def resolve_tag_id(slug):
    q = """
    query($slug: String) {
      tags(input: {terms: {view: "tagBySlug", slug: $slug}}) {
        results { _id name slug postCount }
      }
    }
    """
    data = graphql(q, {"slug": slug})
    results = data["data"]["tags"]["results"]
    if not results:
        raise RuntimeError(f"tag not found for slug {slug}")
    return results[0]


TAGREL_PAGE_QUERY = """
query($tagId: String, $limit: Int, $offset: Int) {
  tagRels(input: {terms: {view: "postsWithTag", tagId: $tagId, limit: $limit, offset: $offset}}) {
    results {
      _id
      baseScore
      post {
        _id
        slug
        title
        postedAt
        baseScore
        wordCount
        commentCount
        user { displayName slug }
        tags { _id name slug }
        tagRelevance
      }
    }
  }
}
"""


def fetch_tagrel_page(tag_slug, tag_id, offset):
    cache_dir = os.path.join(TAGRELS_CACHE, tag_slug)
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{offset:05d}.json")
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)
    data = graphql(TAGREL_PAGE_QUERY, {"tagId": tag_id, "limit": PAGE_SIZE, "offset": offset})
    with open(cache_file, "w") as f:
        json.dump(data, f, indent=2)
    return data


def main():
    os.makedirs(POSTS_META_CACHE, exist_ok=True)
    all_candidates = {}  # postId -> {post fields, sources: {tag_slug: relevance_score}}
    tag_info = {}

    for slug, expected_name in TAGS:
        info = resolve_tag_id(slug)
        tag_info[slug] = info
        print(f"Tag '{slug}' -> id={info['_id']} name={info['name']} postCount={info['postCount']}")

        offset = 0
        page_num = 0
        while True:
            data = fetch_tagrel_page(slug, info["_id"], offset)
            results = data.get("data", {}).get("tagRels", {}).get("results", [])
            page_num += 1
            print(f"  [{slug}] page {page_num} offset={offset}: {len(results)} tagRels")
            if not results:
                break
            for tr in results:
                post = tr.get("post")
                if post is None:
                    continue
                pid = post["_id"]
                if pid not in all_candidates:
                    all_candidates[pid] = {
                        "_id": pid,
                        "slug": post["slug"],
                        "title": post["title"],
                        "author": (post.get("user") or {}).get("displayName"),
                        "author_slug": (post.get("user") or {}).get("slug"),
                        "postedAt": post["postedAt"],
                        "baseScore": post["baseScore"],
                        "wordCount": post["wordCount"],
                        "commentCount": post["commentCount"],
                        "tags": [{"id": t["_id"], "name": t["name"], "slug": t["slug"]} for t in (post.get("tags") or [])],
                        "sources": {},
                    }
                    with open(os.path.join(POSTS_META_CACHE, f"{pid}.json"), "w") as f:
                        json.dump(post, f, indent=2)
                all_candidates[pid]["sources"][slug] = tr["baseScore"]
            if len(results) < PAGE_SIZE:
                break
            offset += PAGE_SIZE

    out_path = os.path.join(BASE, "cache", "candidates.json")
    with open(out_path, "w") as f:
        json.dump({"tag_info": tag_info, "candidates": all_candidates}, f, indent=2)
    print(f"\nTotal unique candidates: {len(all_candidates)}")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()

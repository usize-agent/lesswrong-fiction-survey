# Working notes

## Stage 0 — API mechanics

- LessWrong's GraphQL schema restricts arbitrary selectors (Vulcan security
  model, as warned) — `SelectorInput` only accepts `_id`/`documentId`. Tag and
  post lookups have to go through named **views**, passed as
  `terms: { view: "...", ...viewArgs }`.
- Tag pages are NOT built on `posts(terms: {view: "tagRelevance", tagId})`.
  That view exists but ignores the tag filter entirely — it's a general
  "annotate posts with a relevance map" view, not a per-tag listing. It just
  returns whatever the default post view returns (newest posts sitewide) with
  a `tagRelevance` map attached. Wasted one request confirming this.
- The correct mechanism (same one the actual tag pages use) is
  `tagRels(input: {terms: {view: "postsWithTag", tagId, limit, offset}})`,
  sorted by `TagRel.baseScore` descending. `TagRel.baseScore` **is** the
  tag-relevance score (a community vote on how relevant the post is to the
  tag) — separate from `Post.baseScore` (karma). Confirmed both are present
  and independent (e.g. "The Terrarium" has post karma 611 but a fiction-tag
  relevance score of only 8).
- `enableTotal`/`totalCount` doesn't work for this view — it always returns
  `null`. Paginated by offset until a page returned fewer than `PAGE_SIZE`
  (100) results instead. For tag-scoped lists this maxes out around 850
  items, which is not the kind of "deep offset" pagination the task warned
  against (that concern is about sitewide crawls, i.e. Stage 5) — offset
  pagination within a single ~900-item tag list is fine and the ordering by
  `baseScore` was verified stable across adjacent pages (no overlap/gap
  between offset 0-4 and 5-9).
- Tag `postCount` overstates what's actually fetchable:
  Fiction reports 872, yielded 839 TagRel rows, of which 149 resolved to
  `post: null` inside the nested `tagRels { results { post { ... } } }`
  query. Parables reports 71 → 59 fetched with readable posts; Narratives
  reports 77 → 63.
  Ran down the cause on a sample: the TagRel row itself is real and has a
  valid `postId`, but querying that post directly
  (`post(input: {selector: {_id}})`) returns
  `errors: [{message: "app.operation_not_allowed"}]` — i.e. unauthenticated
  reads are refused outright (not just field-filtered). Consistent with
  these being deleted, draft, or moderator-rejected posts that still have a
  lingering `TagRel` join row. They're excluded from the candidate set
  because they're categorically unreachable without auth, not because of a
  parsing bug. Documented in `00-candidates.md`.
- 776 unique candidates after unioning all three tags (690 fiction ∩ 59
  parables ∩ 63 narratives, with overlap between tags).
- Anchor text ("The Terrarium", `znbfRXHq285nS7NAh`) confirmed present in the
  fiction-tag pull with relevance score 8, karma 611, wordCount 6188. Fetched
  and cached its full body during API discovery since the query was needed
  anyway (`cache/posts/znbfRXHq285nS7NAh.json`).

## Rate limiting

- Used `urllib` with a hard 2s-minimum gap enforced in code (`_last_request_time`
  tracking, no concurrency) rather than a flat `sleep(2)` per call, so retries
  or slow responses don't compound into a faster-than-2s cadence.
- User-Agent: `LW-Fiction-Survey-Research/0.1 (contact: mcfoster1228@gmail.com; personal research project cataloguing LessWrong fiction)` — no 403s or blocks encountered.

## Stage 2/3 findings (added while scoring)

- Serial-detection regex gaps confirmed in practice, beyond what the initial
  `detect_serials.py` heuristics caught: title patterns like "... - Part 7"
  (number not immediately after a colon/dash-prefix) and chapter markers not
  at the start of the title (e.g. "Omniscience one bit at a time: Chapter 1")
  slipped through. Caught by eye during full-text review and dropped with an
  explicit reason citing the representative id; not a systemic regex fix.
- Found a 13-part Luna Lovegood serial plus separate Russian-translation
  duplicate posts of several of its chapters (by Kongo Landwalker) — dropped
  the translations as duplicates of the representative English chapter.
- Two near-duplicate-draft pairs found and resolved by dropping the
  weaker/earlier copy: "Patient Zero" (two postings, karma 1 vs 17, identical
  opening) and "On Constructor Safety" vs "On Klurl Safety" (both independent
  "Fleshling Three" fanfics of Yudkowsky's "On Fleshling Safety" with an
  identical opening line).
- "Sword of Good" (Yudkowsky) is hosted externally with only a partial/teaser
  excerpt on LessWrong itself — flagged, cached body is incomplete relative
  to the real story.
- Cross-posted content sometimes carries scraping artifacts from its origin
  site: "The Queen of the Damned" (Slimepriestess) has a leaked WordPress ad-
  injection script fragment (`\\ATA.cmd.push(...)`) appended after the story
  text in the cached markdown. Harmless for scoring (obviously not story
  content) but worth knowing about if this cache is reused for anything
  besides manual reading — a naive word-count or NLP pass would need to strip
  it.
- Genre observation: a recurring failure mode among "fiction" nominally
  about AI is a piece that's really a philosophy essay or thought-experiment
  wearing a light narrative frame (numbered vignettes, a dialogue with a god
  or AI, a "trip report") followed by the author's own explicit unpacking of
  the argument outside the story. These score low on `craft`/`form` even when
  `idea_density` is high, per the rubric — the fictional apparatus isn't
  doing narrative work, it's illustrating an argument already stated plainly
  alongside it. Examples: "Forcing Freedom", "The Manual Economy" (economics,
  not posthuman, but same pattern), "What could one do with truly unlimited
  computational power?" (literally unfinished, author says so in-text).

## Externally-hosted / unfetchable full text (Stage 3 gaps)

- "It Looks Like You're Trying To Take Over The World" (gwern, `a5e9arCnbDac9Doig`,
  419 karma — the highest-karma candidate seen so far in this survey) has only
  its opening ~140 words on LessWrong; the post body itself says "Rest of
  story moved to gwern.net" and the real text lives at
  `https://gwern.net/fiction/clippy`. A live fetch of that page refused to
  reproduce the full text verbatim (copyright), returning only a plot
  summary. Per the task's "must read each story in full" rule, this was
  **not scored** and is not in `cache/scores.json` — it's a known gap, not an
  oversight. Given its karma and reputation (a technically-grounded hard-
  takeoff scenario, exactly the reader's stated taste), this is the single
  highest-priority item for the user to read and score manually, or for a
  future session to find a legitimate full-text source for.
- "To Change the World" (lsusr, `Lx9aCnwvnckrckmqy`) had a `null` GraphQL
  `contents.markdown` field in our own cache despite a nonzero recorded
  `wordCount` (1695) — a genuine gap in the Stage 1 fetch, cause unknown
  (possibly a content-type quirk on posts using non-standard formatting).
  Worked around by fetching the live page directly via a single one-off
  request (not a bulk crawl) rather than GraphQL; scored normally. Worth
  checking whether other candidates have the same `contents: null` issue —
  not systematically audited for across all 776 candidates.
- "A Letter to His Highness Louis XV, the King of France" (testingthewaters,
  `BoHBJhG8JWNWsjnFP`, batch_022) is a LW post that only contains the opening
  ~170 words of the piece (an AI-x-risk parable framed as an Enlightenment-era
  advisor's warning letter), with a "[Continued here]" link out to a Substack
  post for the rest. Same pattern as gwern's Clippy and Yudkowsky's "Sword of
  Good" — left unscored per the "must read in full" rule rather than scored
  on the teaser alone.

## Open questions / judgment calls to revisit

- Haven't yet decided how to treat posts that appear in more than one source
  tag (e.g. fiction + narratives-stories) for Stage 2/3 — currently they're
  one row with both relevance scores recorded; scoring should happen once
  per post, not once per source tag.
- Decade counts in `00-candidates.md` are bucketed by `postedAt` year, LW's
  own timestamp — no timezone normalization needed since we only need
  the year.

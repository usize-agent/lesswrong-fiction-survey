# v1, kept for the record

The first pass over the corpus. Nothing here is current — see the repo
[README](../../README.md) and [ARCHIVE](../../ARCHIVE.md) for the live archive.

It is kept for two reasons. The fetch scripts are how `cache/` was built, and the
numbered documents are the provenance of the corpus decisions that v2 inherited
and then revised.

## What produced `cache/`

```
fetch_stage0.py      every post tagged fiction, via the LW GraphQL API -> cache/candidates.json
fetch_stage1.py      full post bodies                                  -> cache/posts/
extract_fulltext.py  bodies to flat text batches                       -> fulltext_batches/
make_stage0_md.py    00-candidates.md
```

`cache/fallback/` holds a handful of posts whose `contents.markdown` came back
null from the API; those bodies were fetched by hand.

## What v1 decided, and what v2 did with it

`02-filtered.md` and `cache/filter_decisions.jsonl` are v1's keep/drop pass over
the 776 tagged posts. `pipeline/corpus.py` starts from that file and then applies
its own policy on top, with every reversal listed explicitly in the source — v1
dropped parables, fables and scenario-forecasts as "decoration on an argument",
and v2 keeps them, because for an archive of this kind they are the point.

## What v2 threw away

The v1 scores in `03-scores.md`, `04-shortlist.md` and `04-prescience.md`. They
were produced by a 3-bit quantised local model against a rubric that did not
match what this archive is for, and they were not reliable enough to keep as a
second opinion. Every work was re-read from scratch for v2.

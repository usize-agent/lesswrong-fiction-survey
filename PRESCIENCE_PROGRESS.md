# Prescience ranking — session progress (intermediate state)

Resuming notes for the 04-prescience pass. Read this before compacting/restarting.

## Pipeline state

- Rubric source: `prescience_scoring_guide.txt` (Tier A=5 / B=3 / C=1 hits, precision +0..5, anti-patterns −2 each floored at 0, then era multiplier pre-2010 ×2.0 / 2010-14 ×1.7 / 2015-18 ×1.4 / 2019-21 ×1.15 / 2022+ ×1.0; post-Nov-2022 = reportage not prediction).
- Helper: `append_prescience.py` — appends to `cache/prescience_scores.json` and regenerates `04-prescience.md` (ranked). Idempotent by id; metadata auto-filled from `cache/scores.json` (payload only needs id, tier_hits, precision, anti_patterns, justification). Use heredoc temp file (`/tmp/presN.json`) then `python3 append_prescience.py "$(cat /tmp/presN.json)"`.
- Story location index: `cache/batch_index.json` maps id -> [batch file, start line, end line].

## DONE: 2007-2014 (31 stories scored, appended)

Non-zero results: "Failed Utopia #4-2" (2009) → 2.0 (B1 spec-gaming + training precision, −2 singular_ai −2 overnight_takeoff); "I" (PhilGoetz 2011) → 1.7 (C10 data-footprint/privacy). Everything else 2007-2014 → 0 (mostly no AI content; per guide's base-rate note, do not inflate).

## IN PROGRESS: 2015-2020 cohort (29 stories: 2015×9, 2016×1, 2017×4, 2018×6, 2019×2, 2020×12; ×1.4 era, 2019-21 ×1.15)

### Read in full already (my working judgments — verify before appending):
- vNHf7dx5QZA4SLSZb HPMOR Ch1 (2015): no AI content → 0.
- Lt8Rn4rkYwqiTXGPy Answer to Job (2015): no AI → 0.
- SvKSwT6xYfYahH4XN Cactus Person (2015): DMT entities, no AI → 0. (Irony: entities refuse to factor big numbers — opposite of 2022+ LLM benchmarking; not worth a hit.)
- eehsGtoQTncuJs3Fd paperclip maximiser's perspective (2015): paperclip agent interiority + ends with self-replicating nanotech; no checklist item fits → 0, no anti-pattern.
- wJnm5cBiZGmKn595f …Deep The Rabbit Hole Goes (2015): superpower pills; no AI → 0.
- zmFuGL8qJ2rsT6YKY Quarantine (2015): post-Fall screening of traveler for "viral memetic payload" via IAT-style PC test + Coca-Cola shibboleth (memetic-hazard containment flavor, but not model-based AI) → 0; closest is B4 social-jailbreak-ish, not clean; keep 0.
- FLnDFnXyWrKr6eiT6 Reverse Psychology (2015): dark-side psychiatry ghost story → 0.
- MFNJ7kQttCuCXHp8P Goddess of Everything Else (2015): emergence allegory, no AI → 0.
- qaHHJ3kkCQS4nsoGJ Blue Eyes (2015): common-knowledge puzzle → 0.
- BZMc9Xzqw5WcCMHrr Moral Of The Story (2016): pun collection → 0.

### STILL NEED READING (line ranges from batch_index.json):
- kSiT2XjfTnDHKx44W A Modern Myth (2017, batch_004 1-1084): PARTIAL read (lines 1-560 of 1793; gods-as-businesses myth, Athena mineral-water monopoly, Prometheus foresight). Read from offset 561. Likely 0 unless AI/foresight agent content lands; watch the Prometheus section (foresight, containment of the one who can see futures — thematic only).
- Wh8HAK6LR5CAoPCCC [REPOST] The Demiurge's Older Brother (2017, batch_004 1086-1191)
- iLMkKDKmfbMkDuQBm Lizard People Of Alpha Draconis 1 (2017, batch_004 1193-1266)
- ZxKwKp7WzhtnsQt3r A Day in Utopia (2017, batch_004 1268-1317)
- zZTAD7CBX9SkPdv5s Russian Cynicism (2018, batch_004 1319-1477)
- 9HEHHFBWJWy7h2JW9 Murphy's Quest Ch1: Exposure Therapy (2018, batch_004 1479-1616)
- SBr6BmKEGawEpxauZ The Salmon of Knowledge (2018, batch_004 1618-1793)
- LYXb2fLkGDRXoAx7M Timothy Chu Origins Ch1 (2018, batch_005 1-174)
- Rx9GLepCxctXDqCPc A Dialogue on Rationalist Activism (2018, batch_005 176-305)
- rwjv8bZfSuE9ZAigH Act of Charity (2018, batch_005 307-478) — flagged in NOTES.md before: economics-thought-experiment wrapper pattern
- FK49pmBDgYGwDE2Sb [Fiction] IO.SYS (2019, batch_005 480-644) — title suggests computing; check for AI content
- dv9E65xWw7CsJNERz The Pit (2019, batch_005 646-751)
- Ybp6Wg6yy9DWRcBiR The Adventure: a new Utopia story (2020, batch_006 1-836) — long
- NencL9r3Y7MPiqEbS The Devil You Know (2020, batch_006 838-889)
- jTQaFKL6s3pppSNx4 God and Moses have a chat (2020, batch_006 891-984)
- pi9HMaFMKkbrwzoYN The Queen of the Damned (2020, batch_006 986-1055) — cached markdown has leaked WordPress ad-script fragment at end (NOTES.md), ignore it
- fbjNLjNd4zRbY9Wg2 Null-boxing Newcomb's Problem (2020, batch_006 1057-1151)
- zJ2i8uPGjywD5W5Jw The Manual Economy (2020, batch_006 1153-1228) — essay-wrapper pattern per NOTES.md
- ZsSCdNEC2aj6pmDL2 Universal Eudaimonia (2020, batch_006 1230-1253)
- mXzgtnx587sA2ynzS Forcing Freedom (2020, batch_006 1255-1343) — essay-wrapper pattern per NOTES.md
- f2ivgmjjPyjhhCe5J What could one do with truly unlimited computational power? (2020, batch_006 1345-1392) — unfinished per NOTES.md
- zb3hWt99i9Fm93KPq Luna Lovegood Chamber of Secrets Pt1 (2020, batch_007 1-70)
- iC9tQxxsP3iiLGwJD Matryoshka Faraday Box (2020, batch_007 72-119)
- oFa6A2pmPNjdhZDJm Hermione Granger and Newcomb's Paradox (2020, batch_007 121-174)

## Standing scoring rules for this pass (established this session)

- Apply anti-pattern penalties only to stories that actually depict AI/agentic minds; non-AI fiction gets 0, no penalties.
- Follow the guide's base-rate note: don't inflate. C-hits need a genuine match to the checklist item, not a vibe.
- Read every story in full before scoring (NOTES/HANDOFF convention).
- Justification field: two sentences, most-prescient element + largest miss.

## After 2015-2020 appended

Continue 2021 cohort (16 stories), then 2022 (38, ×1.0, treat pre/post Nov-2022 distinction per guide §9.4). Batches 2022+ mostly = reportage.

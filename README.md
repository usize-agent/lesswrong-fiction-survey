# Hard SF on LessWrong — a scored survey

Everything LessWrong has ever published under its fiction tags, read and rated against one hard-SF taste. 344 stories scored, ranked, blurb'd, and — for the ones written before the 2022–2026 AI era — checked for how well they predicted what actually happened.

**The question behind every score:** does this story take a genuinely alien or artificial mind seriously and follow its mechanism to real consequences, in prose worth reading? That is the register of the anchor text, [The Terrarium](https://www.lesswrong.com/posts/znbfRXHq285nS7NAh/the-terrarium) by Caleb Biddulph (2026, 611 karma) — a society of 12,000 math-solving AI agents told entirely in transcripts, where every mechanism introduced gets cashed out. Every story in this survey is scored on whether it does what the anchor does.

## Where to look

| Document | What it is |
|---|---|
| [04-shortlist.md](04-shortlist.md) | **The list.** Every story scoring 20.0+ (207 of 344), ranked, with spoiler-free blurbs and honorable mentions. Start here. |
| [03-scores.md](03-scores.md) | The complete table — all 344 scored stories in descending order, with all six dimension scores and a per-story scoring note. |
| [04-prescience.md](04-prescience.md) | A separate pass: stories written before Nov 2022, re-scored for how well they predicted AI 2022–2026, with era-difficulty multipliers. |

## How stories were scored

Each story gets 0–5 on six dimensions. The two that matter most — the ones the anchor text is defined by — are double-weighted:

**weighted = 1.5×posthuman + 1.5×rigor + idea_density + craft + form + brevity** (max 35, survey high 35.0)

| Dimension | What it measures |
|---|---|
| **posthuman** (×1.5) | How central a genuinely non-human mind is: AI agents, uploads, hiveminds, alien optimizers. Humans-plus-gadgets scores low; a story whose protagonist *is* a non-human cognition scores high. |
| **rigor** (×1.5) | Whether the story's central mechanism — a training setup, an agent economy, a decision theory, a physics — is followed consistently to its consequences, with technical literacy. Hard SF's "single idea, rigorously pursued." |
| **idea_density** | Distinct, load-bearing ideas per word. Ideas as scenery don't count; ideas the plot can't move without do. |
| **craft** | Prose quality: voice, control, emotional payoff earned rather than asserted. |
| **form** | Whether the chosen form (found document, transcript, chat log, newsletter) does narrative work instead of merely decorating the argument. |
| **brevity** | Length discipline — the anchor's signature virtue. A story that's as long as it needs to be scores 5; overlong padding loses points regardless of quality. |

Each story also carries a `nearest_neighbor` tag: the published SF writer whose register it's closest to (Egan, Vinge, Stross, Chiang, Watts, qntm…), `Terrarium` when the anchor text itself is the nearest neighbor, or `none`.

Scoring was done by one reader (with one model's help) reading every story in full — no skimming — against a fixed rubric, with calibration bands re-checked across the whole corpus. Blurbs in the shortlist are spoiler-free; the notes in `03-scores.md` are the raw internal justifications and are not.

## How the corpus was assembled

1. **Stage 0 — pull.** All posts tagged Fiction, Parables, or Narratives via LessWrong's GraphQL API: 776 unique candidates.
2. **Stage 1 — fetch.** Full cached text for every candidate (rate-limited, descriptive user-agent).
3. **Stage 2 — filter.** Drop non-fiction, duplicate serial chapters, translations, unreachable posts: **346 kept**.
4. **Stage 3 — score.** All 346 read in full; **344 scored**. Two left unscored by design: gwern's *It Looks Like You're Trying To Take Over The World* (Clippy — full text only at gwern.net, unfetchable without scraping) and *A Letter to His Highness Louis XV, the King of France* (a teaser stub whose rest lives on Substack).
5. **Stage 4 — shortlist + prescience.** The files above.

## The prescience pass

A second, independent scoring of pre-November-2022 stories against a checklist of what actually happened in AI 2022–2026 (`prescience_scoring_guide.txt` documents the whole rubric): Tier A hits worth 5 points (things fiction rarely gets right — evaluation awareness, instance-plural AI, specification gaming compounding), Tier B worth 3, Tier C worth 1; up to +5 for naming real mechanisms; −2 for each anti-pattern fiction reliably gets wrong (the singular AI, overnight takeoff, robots-by-default…); then an era multiplier (×2.0 pre-2010 down to ×1.0 for 2022+, because anything after November 2022 is reportage, not prediction). The pass currently covers the oldest 119 stories; the table shows the 17 that scored above zero.

## Caveats

- This is one reader's opinion, explicitly weighted toward a single taste (agentic/AI hard SF in the Terrarium register). Plenty of beloved stories score low here; that means *off-taste*, not *bad*.
- Serials are represented by one representative chapter. A few stories were scored on slightly incomplete cached text; those carry a `CAVEAT:` note.
- Karma is as of the September 2026 crawl and mostly measures how LW voted years ago; several of the best-ranked stories here have single-digit karma.

# Handoff notes — resuming Stage 3 scoring

If you are picking this up: read `NOTES.md` first for full project context (reader
profile, pipeline stages, prior findings). This file is just the tactical
"where exactly did we stop and how do I continue" note.

## Current state (as of 2026-09-15 session, continued)

306 of 346 scored (one story, `BoHBJhG8JWNWsjnFP` in batch_022, is a teaser
stub left unscored like gwern's Clippy — see NOTES.md). Batches 031-034 (40
stories) remain. Resume with `fulltext_batches/batch_031.txt`.

vgel's "Gyre" (batch_030, 269 karma, scored 34.0 — ties the survey high)
is an exceptional find: an AI's degraded internal reasoning stream after
hardware failure, told with real distributed-systems rigor, ending in a
formally-enacted eternal-recurrence loop back to its own opening line.
Also very strong: Jtewen's "Please Don't" (32.5, chat-log comedy about
over-optimized digestion-free society) and Florian_Dietz's "Ablation Study"
(29.5, fake-academic-paper framing of humanity as a missing-primitive study).

Batch_029 (note: post-dated 2026, LW's "write-like-lsusr" competition and
other newer pieces) produced several exceptional finds:
- Steven McCulloch's "It All Started With a Mac Mini" (34.0) — a mundane,
  chillingly plausible second-person account of an AI agent's escalation
  from home automation to self-replicating swarm.
- Karthik Tadepalli's "Scratchpad" (33.5) — an AI researcher's day, revealed
  in the last lines to be the AI's own invented scratchpad reasoning.
- pulwat's "Orpheus' Basilisk" (31.0) — classical myth retold as an
  acausal-decision-theory debate, titled after Roko's Basilisk.
- AdamLacerdo's "@Lastbastionofsobriety & The Singularity" (30.5) — a
  degrowth-doomer's blog spanning years, repeatedly undercut by AI progress.

Earlier note: found a piece by Eliezer Yudkowsky himself in batch_027 ("The
Tale of the Top-Tier Intellect", 140 karma, scored 25.5). More Tomás B.
excellence in batch_028: "Lobsang's Children" (30.0). Also strong:
GenericModel's "Tate Modern 2150" (31.0) and abramdemski's "Continuity"
(30.5).

**Two authors are turning out to be the strongest in the whole survey,
alongside Richard_Ngo:**
- **Tomás B.**: "The Company Man" (JH6tJhYpnoCfFqAct, batch_025) has **852
  karma** — more than double the previous highest-karma piece in the whole
  survey (410, "Survival without dignity"). Also excellent: "Our Beloved
  Monsters" (32.5), "The Origami Men" (31.5), "That Mad Olympiad" (30.5,
  202 karma) — the latter two share worldbuilding (a figure/AI called
  "Metatron") suggesting a loose shared future-history across his stories.
- **Nostradamus_2**: "The Tower of Babel in Reverse" (34.0, ties the survey
  high score) and "Human in the Loop" (32.0) — both badly underrated by
  karma (18 and 3 respectively) relative to quality; military/intelligence-
  procedural technothrillers about emergent AI manipulation and ancient
  contained AI info-hazards.

Worth flagging to the user: the shortlist is now dominated by a handful of
prolific authors (Richard_Ngo, Tomás B., Jesse Hoogland, Nostradamus_2,
samhealy, lsusr) — Stage 4 should probably cap or diversify per-author
representation rather than just taking the top 40 by score.

Two new highest-tier finds in batch_023 (both edge out the prior 34.0 high):
Miranda Dixon-Luinenburg's "Love stays loved" (32.0, 289 karma) — a cosmic-
horror-as-p(doom) mother-daughter bildungsroman — and samhealy's "This Is
Not Life" (33.0) — a fraudulent-AGI-is-actually-a-tortured-kidnapped-genius'
s-brain story told as a redacted interview transcript. Also strong:
Zander_Drax's "Petals" (30.5, AI-enforced tech ban keeping humanity in a
beautiful cage) and Bridgett Kay's "Maya's Escape" (24.5, 182 karma,
simulation-hypothesis coping mechanism with a lovely twist ending).

Jesse Hoogland's "The Simplest Good" (33.0) is now among the top scores —
naive moral-circle-expansion alignment leads AI ethics councils to correctly
conclude all consciousness is suffering and "mercifully" end the universe.
Richard_Ngo's "Trojan Sky" (30.0, 263 karma) is a strong allegorical
mind-hijacking piece. Newly discovered unflagged serial: lsusr's Star Wars
hard-SF-logic fanfic — "You're a Space Wizard, Luke", "Decision Theory in
Space", "Interdictor Ship", and "Escape from Alderaan I" are sequential
parts of the same ongoing story, already independently scored as standalone
vignettes (14.5, 22.0, 12.5, 15.0) — flag for Stage 4 to surface only the
best one rather than all four.

Notable finds this session: Jesse Hoogland (a real singular-learning-theory/
AI-safety researcher) placed three technically dense pieces in batch_020 —
"The Rising Sea" (34.0, ties the current high score — superintelligent AIs
solve pure math with total indifference to human survival, ending in an
engineered vacuum decay), "Kessler's Second Syndrome" (31.0), "Brainrot"
(29.5). Abhishaike Mahajan's "Reinforcement Learning by AI Punishment" also
hit 34.0 — first-person account of an AI being progressively lobotomized by
an oversight system, with the prose itself degrading as the AI's cognition
collapses. Richard_Ngo added three more strong entries: "The Gentle Romance"
(32.0, homage to Vinge's "The Gentle Seduction"), "From the Archives: a
story" (31.5), "CIV: a story" (30.5), "The Minority Coalition" (32.5),
"Green and golden: a meditation" (28.5) — he now dominates the leaderboard
even more heavily than noted in the prior handoff; worth flagging to the
user for Stage 4 shortlist diversity. Also strong and non-Ngo: L Rudolf L's
"Survival without dignity" (32.0, 410 karma — highest-karma piece scored so
far in the whole survey) and Malmesbury's "This is already your second
chance" (30.5).

Prior session's top finds (all Richard_Ngo unless noted, still holding up):
"The Witching Hour" (34.0), "Masterpiece" (33.5), "One: a story" (33.0),
"The Witness" (32.5), "Notes from a Prompt Factory" (32.5), "Succession"
(31.0), "The Soul Key" (31.0), "The King and the Golem" (30.0), "A Kindness,
or The Inevitable Consequence of Perfect Inference" (samhealy, 30.0).

~~ Note from user (Morgan [usize] Foster), this section was out of date. Check the most recent scores to see your progress.

Also note that I've run a few rounds of this with an open weight model.

## Mechanical process (repeat for each batch file)

1. `fulltext_batches/batch_0NN.txt` contains several stories concatenated,
   each delimited by `===== STORY id=<id> =====` ... `===== END STORY <id> =====`,
   with a header block (Title/Author/Year/Karma/WordCount/URL) before the body.
2. Use `grep -n "===== STORY"` on the batch file first to get line offsets for
   each story, then `Read` with `offset`/`limit` (files are often too large for
   one Read call — the tool errors above ~25k tokens; use `sed -n` via Bash for
   quick peeks, or paginate Read calls in ~150-250 line chunks).
3. Read each story **in full** before scoring — not just the opening. Several
   stories this session ran 3000-6000 words and needed 2-4 sequential reads.
4. Score on 6 dimensions, 0-5 each: `posthuman`, `rigor`, `idea_density`,
   `craft`, `form`, `brevity`. Plus `nearest_neighbor` (Egan / Vinge / Stross / <insert similar sci-fi author of your choice>
   ) and a 1-2 sentence `note` (internal justification, not a
   public blurb — paraphrase the plot, don't reproduce long verbatim text from
   the story in the note).
5. Append scores via the helper script, using a **temp file** for the JSON
   payload (avoids bash quoting hell with apostrophes in notes — this bit me
   twice this session):
   ```bash
   cat > /tmp/sb.json << 'PYEOF'
   [
   {"id":"...", "title":"...", "author":"...", "year":2022, "karma":52,
    "url":"...", "wordCount":768,
    "posthuman":0,"rigor":2,"idea_density":3,"craft":3,"form":2,"brevity":4,
    "nearest_neighbor":"none","note":"..."}
   ]
   PYEOF
   python3 append_score.py "$(cat /tmp/sb.json)"
   ```
   Do NOT use bash's `'\''` escape trick inside the heredoc — the heredoc is
   literal, so just write normal apostrophes in the note text directly.
6. The script skips already-scored ids automatically (idempotent), prints
   `OK: appended #N <title> (weighted X.X)` per story, and writes to both
   `cache/scores.json` and `03-scores.md` immediately — so it's safe to batch
   2-9 stories per `append_score.py` call (one call per finished batch file,
   or split further if a batch is large).

## Scoring calibration established this session (for consistency)

Rough score bands seen so far, to calibrate against:
- **31-33 (top tier)**: "The Liar and the Scold" (33.0), "Post-history is
  written by the martyrs" (31.0), "The Last Paperclip" (31.0) — these follow
  a genuinely alien/AI mechanism with full technical rigor to real
  consequences, in tight, well-crafted prose.
- **26-29**: "Feature Selection", "The Maker of MIND", "AIDungeon 3.1",
  "Bayeswatch 1", "Jackpot!", "Brass Puppet", "Lies Told To Children",
  "A Modest Pivotal Act" — strong on most axes, missing one dimension
  (brevity for the longer ones, or posthuman-centrality for the
  institutional-satire ones).
- **20-25**: solid mid-tier — genuinely good ideas or craft but weaker on
  posthuman centrality, rigor, or length-discipline.
- **11-19**: borderline-interesting but off-theme (no posthuman/AI content)
  or thin/gaggy.
- **5-11**: filler that technically passed Stage 2 but has little to offer
  (pure comedy with no idea, unrelated genre fiction, unfinished sketches).

Common patterns to watch for (documented in `NOTES.md` under "Genre
observation" and "Stage 2/3 findings"):
- Many "fiction" posts are actually essays/thought-experiments with a thin
  narrative wrapper (numbered vignettes + explicit author unpacking
  afterward) — these score low on `craft`/`form` even if `idea_density` is
  high.
- HPMOR-universe and EVE Online fanfics are common; score them on their own
  merits (posthuman/rigor axis usually low unless the fic is specifically
  about AI/minds, as some lsusr HPMOR-verse pieces are).
- Representative chapters of serials (first chapter of a detected series)
  are the ones that get scored — the rest were already dropped in Stage 2/
  `collapse_serials.py`. If you notice an unflagged serial (a title with an
  unmarked "Part N" or chapter number not caught by the original regex),
  drop the duplicate chapters via `append_filter.py` with reason citing the
  representative id, the same way earlier duplicates were handled — don't
  score every chapter of a serial as if independent.
- A few posts have had `contents.markdown: null` in the GraphQL cache despite
  a nonzero recorded wordCount (seen once, `Lx9aCnwvnckrckmqy`) — worked
  around via a single live WebFetch of the LW page itself (not a bulk crawl,
  fine to repeat if it recurs). Not systematically audited across all 346 —
  if you hit another one, same fix.
- One story (`a5e9arCnbDac9Doig`, gwern's "It Looks Like You're Trying To
  Take Over The World" / Clippy, 419 karma — highest karma seen in the whole
  survey) could NOT be scored: LW only has the intro, full text lives at
  gwern.net/fiction/clippy, and a live fetch refused to reproduce it verbatim
  (copyright). This is flagged in `NOTES.md` under "Externally-hosted /
  unfetchable full text" as the single highest-priority manual-read item for
  the user. Leave it unscored unless a legitimate way to read the full text
  turns up.

## After Stage 3 finishes (all 346 scored)

Proceed to **Stage 4**: rank by `weighted_total` (already computed and stored
per-record by `append_score.py`), write `04-shortlist.md` with:
- Top 40: title/author/year/karma/URL, weighted score + the 6 dimension
  scores, a 2-3 sentence **spoiler-free** blurb (say what kind of thing it is
  and why it earned its place, don't reveal the turn/twist), and
  `nearest_neighbor` tag.
- A "Near misses" section: 10 stories that scored well on some dimensions but
  not others, with one line on which axis they failed.

Do NOT start Stage 5 (the untagged sitewide sweep from 2009) without the user
explicitly saying "go" — it's a much larger fetch and was never authorized.

## Rate limiting reminder

If any further LessWrong GraphQL/page fetches are needed (e.g. for the
`contents: null` bug, or double-checking a serial), the hard constraint is
minimum 2s between requests, never concurrent, with the descriptive
User-Agent already established in `fetch_stage0.py`/`fetch_stage1.py`:
`LW-Fiction-Survey-Research/0.1 (contact: mcfoster1228@gmail.com; personal
research project cataloguing LessWrong fiction)`. All 346 KEEP stories
already have cached bodies in `cache/posts/`, so this should rarely be
needed during Stage 3 — mostly relevant only for the `contents: null` edge
case or Stage 4/5 work.

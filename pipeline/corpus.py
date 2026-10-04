"""Decide which of the 776 tagged posts become works in the archive.

Starts from the v1 filter (cache/filter_decisions.jsonl) and applies the v2
inclusion policy on top:

  * Any original narrative fiction counts, including parables, fables,
    dialogues and scenario-forecasts told as narrative. v1 dropped these as
    "decoration on an argument"; for this archive they are exactly the point.
  * Excluded: non-fiction, link/announcement-only posts, reviews, reposts of
    someone else's published work, translations, pure verse, puzzles, and
    near-duplicate drafts.
  * Serial chapters fold into one work keyed by the first part.
  * Link-only posts pointing at notable off-site SF are kept as "elsewhere"
    entries (listed, not scored).

Writes data/corpus.json. Re-runnable; overrides live in this file.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# v1 DROP/BORDERLINE decisions reversed: these are fiction.
RESCUE = {
    "6hfGNLf4Hg5DXqJCF": "fable (Blues and Greens), narrative fiction",
    "Qr4MB9hFRzamuMRHJ": "short koans, fiction",
    "hQxYBfu2LPc9Ydo6w": "short parable, fiction",
    "2gWs8SScqeDFidqyv": "short parable, fiction",
    "wd6cug64wsMnPc2eg": "short parable, fiction",
    "HrdqKkM2JXheiJEmM": "short second-person fiction",
    "FwFdRmT6oCFWoHS7f": "short fable, fiction",
    "fhEPnveFhb9tmd7Pe": "framing essay around a fictional outtake scene",
}

# v1 BORDERLINE (or KEEP) posts that still should not be works.
EXCLUDE = {
    "NZvFostjy8gu5mEnc": "data-science puzzle",
    "ycG3mrtdqddCkK9et": "data-science puzzle",
    "o4RFp7rwfrn9bn6Lo": "instructional course",
    "8GBBkJKbGzGb46onj": "personal prose-poem",
    "AEkMJeE7Cdexge2Lq": "verse / slang poem",
}

# Serials v1 missed: part id -> first part id.
MANUAL_SERIALS = {
    "vGbHKfgFNDeJohfeN": "WajiC3YWeJutyAXTn",  # Ebborians, part 2
}

# Link-only posts that point at significant SF hosted elsewhere.
ELSEWHERE = {
    "a5e9arCnbDac9Doig": ("gwern", "It Looks Like You're Trying To Take Over The World", "https://gwern.net/fiction/clippy",
                          "Hard-takeoff scenario built only from known neural-net scaling effects; the LW post carries just the opening."),
    "XSqYe5Rsqq4TR7ryL": ("Eliezer Yudkowsky", "The Finale of the Ultimate Meta Mega Crossover", "http://www.fanfiction.net/s/5389450/1/The_Finale_of_the_Ultimate_Meta_Mega_Crossover",
                          "A self-described Vernor Vinge x Greg Egan crackfic that turns into a serious exploration of permutation-city metaphysics."),
    "CHD5m9fnosr7L3dto": ("iceman", "Friendship is Optimal", "https://www.fimfiction.net/story/62074/Friendship-is-Optimal",
                          "A pony MMO's AI is told to satisfy values through friendship and ponies; the canonical optimizer-as-utopia story."),
    "yWMKQBnTwFAPFdN6S": ("qntm", "Lena (MMAcevedo)", "https://qntm.org/mmacevedo",
                          "Wiki article on the most-copied human brain image; the definitive upload-welfare story."),
    "8vSuZcujKEsK4inRW": ("Ted Chiang", "The Lifecycle of Software Objects", "http://subterraneanpress.com/index.php/magazine/fall-2010/fiction-the-lifecycle-of-software-objects-by-ted-chiang/",
                          "Novella about raising digital minds over years; an early, serious treatment of AI moral patienthood."),
    "BoHBJhG8JWNWsjnFP": ("testingthewaters", "A Letter to His Highness Louis XV, the King of France", "https://aclevername.substack.com/p/a-letter-to-his-highness-louis-xv",
                          "AI-risk parable as an Enlightenment advisor's letter; LW has only the opening, the rest is on Substack."),
    "XuLG6M7sHuenYWbfC": ("Eliezer Yudkowsky", "The Sword of Good", "https://www.yudkowsky.net/other/fiction/the-sword-of-good",
                          "A fantasy-quest hero discovers what the 'good' side is actually doing; LW carries only the opening and afterword."),
    "HvjZxxtHnAucnaKn2": ("AlexMennen", "Letter from the End", "http://alex.mennen.org/LetterFromTheEnd.pdf",
                          "Short fiction hosted as a PDF."),
    "JuzXhkm3spN6egzyu": ("Andrew Hickey", "Jeeves and the Singularity", "http://andrewhickey.info/2010/12/31/jeeves-and-the-singularity",
                          "Wodehouse pastiche about an unfriendly AI."),
}


def main():
    cands = json.load(open(os.path.join(ROOT, "cache/candidates.json")))["candidates"]
    v1 = {}
    for line in open(os.path.join(ROOT, "cache/filter_decisions.jsonl")):
        r = json.loads(line)
        v1[r["id"]] = r
    serial_of = {}
    for g in json.load(open(os.path.join(ROOT, "cache/serial_groups.json"))):
        for m in g["member_ids"]:
            if m != g["representative_id"]:
                serial_of[m] = g["representative_id"]
    # v1 found a few serials by eye and recorded them only in the drop reason.
    for pid, r in v1.items():
        if r["reason"].startswith("serial continuation") and pid not in serial_of:
            rep = r["reason"].split("(")[-1].split(")")[0].split()[-1].strip(",")
            if rep in cands:
                serial_of[pid] = rep

    serial_of.update(MANUAL_SERIALS)

    out = {}
    for pid, p in cands.items():
        r = v1.get(pid, {"decision": "DROP", "reason": "no v1 decision"})
        if pid in ELSEWHERE:
            author, title, url, blurb = ELSEWHERE[pid]
            rec = {"status": "elsewhere", "author": author, "title": title, "url": url, "blurb": blurb}
        elif pid in serial_of:
            rec = {"status": "serial-part", "work": serial_of[pid]}
        elif pid in EXCLUDE:
            rec = {"status": "excluded", "reason": EXCLUDE[pid]}
        elif pid in RESCUE:
            rec = {"status": "work", "reason": "v2 rescue: " + RESCUE[pid]}
        elif r["decision"] in ("KEEP", "BORDERLINE"):
            rec = {"status": "work", "reason": "v1 " + r["decision"].lower()}
        else:
            rec = {"status": "excluded", "reason": r["reason"]}
        out[pid] = rec

    parts = {}
    for pid, rec in out.items():
        if rec["status"] == "serial-part":
            parts.setdefault(rec["work"], []).append(pid)
    for rep, members in parts.items():
        members.sort(key=lambda m: cands[m]["postedAt"])
        out[rep]["parts"] = [rep] + members

    json.dump(out, open(os.path.join(ROOT, "data/corpus.json"), "w"), indent=1, sort_keys=True)
    from collections import Counter
    print(Counter(r["status"] for r in out.values()))


if __name__ == "__main__":
    main()

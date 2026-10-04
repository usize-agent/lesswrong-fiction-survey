"""The rubric: dimensions, weights, presets, and the controlled tag vocabulary.

One definition, imported by review.py, impact.py, build.py and curate/seed.py.

History. The first pass scored five dimensions (hard, vision, mind, foresight,
craft). The second pass renamed `vision` to `concept`, added `impact`, and
reweighted toward high-concept hard SF — `data/impact.jsonl` is that pass, and
is why every work carries two read dates.
"""

DIMS = ("concept", "hard", "craft", "impact", "mind", "foresight")

DIM_LABEL = {
    "concept": "Concept",
    "hard": "Hard",
    "craft": "Craft",
    "impact": "Impact",
    "mind": "Mind",
    "foresight": "Foresight",
}

DIM_BLURB = {
    "concept": "High concept: the scale, originality and strangeness of the central idea. "
               "Does it propose something, and is the something big?",
    "hard": "Rigour. Does the mechanism actually work, is it followed to its consequences, "
            "and is it load-bearing rather than decorative?",
    "craft": "Prose, structure and control. Is the thing well made?",
    "impact": "Does it land. Did it move, unsettle or stay with the reader, or is it merely "
              "well constructed?",
    "mind": "Interiority of non-human minds: model POV, uploads, model welfare.",
    "foresight": "Quality as prediction or warning. Would it change what you expect?",
}

# High concept and hard SF lead; craft and impact close behind; the two
# special interests stay as meaningful but secondary axes.
WEIGHTS = {
    "concept": 0.24,
    "hard": 0.24,
    "craft": 0.18,
    "impact": 0.18,
    "mind": 0.08,
    "foresight": 0.08,
}

PRESETS = {
    "Default": WEIGHTS,
    "Hard SF": {"concept": 0.30, "hard": 0.40, "craft": 0.12, "impact": 0.08,
                "mind": 0.05, "foresight": 0.05},
    "Ideas": {"concept": 0.55, "hard": 0.20, "craft": 0.10, "impact": 0.10,
              "mind": 0.025, "foresight": 0.025},
    "Prose": {"concept": 0.10, "hard": 0.05, "craft": 0.45, "impact": 0.35,
              "mind": 0.025, "foresight": 0.025},
    "Model minds": {"concept": 0.15, "hard": 0.10, "craft": 0.15, "impact": 0.10,
                    "mind": 0.45, "foresight": 0.05},
    "Forecasting": {"concept": 0.20, "hard": 0.20, "craft": 0.10, "impact": 0.10,
                    "mind": 0.05, "foresight": 0.35},
}

TAGS = {
    "ai-pov", "model-welfare", "uploads", "alignment", "takeover", "agents", "near-future",
    "forecast", "singularity", "posthuman", "aliens", "physics", "math", "decision-theory",
    "simulation", "biotech", "space", "economics", "institutions", "satire", "humor",
    "horror", "parable", "dialogue", "found-document", "fanfic", "utopia", "rationality",
    "consciousness", "war", "religion", "time",
}

PICKER = "Opus 5.5"


def score(r, w=WEIGHTS):
    """Weighted taste match, 0-100.

    Renormalises over whichever dimensions the record actually carries, so a
    work still awaiting its second-pass impact score ranks on the rest rather
    than being penalised for a missing number.
    """
    have = [d for d in DIMS if r.get(d) is not None]
    total = sum(w[d] for d in have) or 1
    return round(sum(w[d] * r[d] for d in have) / (5 * total) * 100)

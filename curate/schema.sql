-- Data model for personal curation of the LessWrong fiction survey.
-- LLM-produced survey scores live in llm_curations; human ratings in
-- reviews/review_scores. They are never mixed.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS stories (
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,        -- LessWrong post id from the URL
  title TEXT NOT NULL,
  author TEXT,
  year INTEGER,
  url TEXT,
  karma INTEGER,                    -- as of the Sep 2026 survey crawl
  survey_rank INTEGER,              -- 1 = top of 03-scores.md
  nearest_neighbor TEXT,            -- Egan/Vinge/Stross/Chiang/Watts/qntm/none
  added_at TEXT DEFAULT (datetime('now'))
);

-- Rating axes a human scores against; seeded with the survey's six
-- dimensions, but freely extendable through the UI.
CREATE TABLE IF NOT EXISTS criteria (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  blurb TEXT,                       -- what the axis measures
  sort_order INTEGER DEFAULT 0
);

-- Curation categories (posthuman, AI, ...), freely extendable.
CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS story_tags (
  story_id INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (story_id, tag_id)
);

-- Scores authored by the LLM-assisted survey, seeded from 03-scores.md.
CREATE TABLE IF NOT EXISTS llm_curations (
  id INTEGER PRIMARY KEY,
  story_id INTEGER UNIQUE NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
  scorer TEXT NOT NULL,             -- provenance, e.g. 'survey-2026 (LLM-assisted)'
  weighted REAL,                    -- 0..35, the survey's double-weighted total
  subscores TEXT,                   -- JSON {"posthuman":5, "rigor":5, ...}
  review TEXT,                      -- the scoring note (CONTAINS SPOILERS)
  source_doc TEXT,
  scored_at TEXT
);

-- Human reviews: one (overall + impressions) per story per reviewer,
-- plus per-criterion scores in review_scores.
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
  reviewer TEXT NOT NULL DEFAULT 'morgan',
  overall INTEGER CHECK (overall BETWEEN 1 AND 5),
  impressions TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE (story_id, reviewer)
);

CREATE TABLE IF NOT EXISTS review_scores (
  review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
  criterion_id INTEGER NOT NULL REFERENCES criteria(id) ON DELETE CASCADE,
  score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
  PRIMARY KEY (review_id, criterion_id)
);

CREATE VIEW IF NOT EXISTS review_avgs AS
  SELECT r.id AS review_id,
         r.story_id,
         r.reviewer,
         r.overall,
         ROUND(AVG(rs.score), 2) AS criterion_avg
  FROM reviews r
  LEFT JOIN review_scores rs ON rs.review_id = r.id
  GROUP BY r.id;

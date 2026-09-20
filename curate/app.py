#!/usr/bin/env python3
"""curate: local rating app for the LessWrong fiction survey.

Stdlib only (http.server + sqlite3 + vanilla JS). Seeds the db from
03-scores.md on first run; human reviews and LLM curation stay in
separate tables.

    python3 app.py [--port 8321] [--db curate.sqlite3]
"""
import json
import os
import sqlite3
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import seed as seedmod

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "curate.sqlite3")
REVIEWER = os.environ.get("CURATE_REVIEWER", "morgan")


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ---------------------------------------------------------------- data layer

def meta(conn):
    crits = conn.execute("SELECT * FROM criteria ORDER BY sort_order, id").fetchall()
    tags = conn.execute("SELECT * FROM tags ORDER BY name").fetchall()
    nns = [r["nearest_neighbor"] for r in conn.execute(
        "SELECT DISTINCT nearest_neighbor FROM stories WHERE nearest_neighbor IS NOT NULL ORDER BY nearest_neighbor")]
    return {
        "criteria": [dict(c) for c in crits],
        "tags": [dict(t) for t in tags],
        "nearest_neighbors": nns,
        "reviewer": REVIEWER,
    }


STORY_SELECT = """
SELECT s.id, s.slug, s.title, s.author, s.year, s.url, s.karma, s.survey_rank,
       s.nearest_neighbor, l.weighted AS llm_weighted, l.id AS llm_id,
       r.id AS review_id, r.overall AS my_overall
FROM stories s
LEFT JOIN llm_curations l ON l.story_id = s.id
LEFT JOIN reviews r ON r.story_id = s.id AND r.reviewer = ?
"""


def stories(conn, params, reviewer):
    where, args = [], [reviewer]
    q = params.get("q")
    if q:
        where.append("(s.title LIKE ? OR s.author LIKE ?)")
        args += [f"%{q}%", f"%{q}%"]
    tag_id = params.get("tag_id")
    if tag_id:
        where.append("EXISTS (SELECT 1 FROM story_tags st WHERE st.story_id=s.id AND st.tag_id=?)")
        args.append(int(tag_id))
    nn = params.get("nn")
    if nn == "__none__":
        where.append("s.nearest_neighbor IS NULL")
    elif nn:
        where.append("s.nearest_neighbor = ?")
        args.append(nn)
    if params.get("unreviewed") == "1":
        where.append("r.id IS NULL")
    sort = {
        "rank": "s.survey_rank",
        "weighted": "l.weighted DESC",
        "karma": "s.karma DESC",
        "title": "s.title COLLATE NOCASE",
        "year": "s.year DESC",
        "mine": "r.overall IS NULL, r.overall DESC",
    }.get(params.get("sort"), "s.survey_rank")
    sql = STORY_SELECT
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY {sort}"
    rows = conn.execute(sql, args).fetchall()
    ids = [r["id"] for r in rows]
    tags_by_story = {i: [] for i in ids}
    if ids:
        marks = ",".join("?" * len(ids))
        for tr in conn.execute(
                f"SELECT st.story_id, t.name FROM story_tags st JOIN tags t ON t.id=st.tag_id "
                f"WHERE st.story_id IN ({marks})", ids):
            tags_by_story[tr["story_id"]].append(tr["name"])
    out = []
    for r in rows:
        d = dict(r)
        d.pop("llm_id", None)
        d["tags"] = tags_by_story[r["id"]]
        out.append(d)
    return out


def story_detail(conn, story_id, reviewer):
    s = conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()
    if not s:
        return None
    l = conn.execute("SELECT * FROM llm_curations WHERE story_id=?", (story_id,)).fetchone()
    r = conn.execute("SELECT * FROM reviews WHERE story_id=? AND reviewer=?", (story_id, reviewer)).fetchone()
    scores = {}
    if r:
        for sc in conn.execute("SELECT criterion_id, score FROM review_scores WHERE review_id=?", (r["id"],)):
            scores[str(sc["criterion_id"])] = sc["score"]
    tag_ids = [t["tag_id"] for t in conn.execute("SELECT tag_id FROM story_tags WHERE story_id=?", (story_id,))]
    return {
        "story": dict(s),
        "llm": dict(l) if l else None,
        "review": {**dict(r), "scores": scores} if r else None,
        "tag_ids": tag_ids,
    }


def save_review(conn, reviewer, story_id, overall, impressions, scores):
    with conn:
        cur = conn.execute(
            """INSERT INTO reviews (story_id, reviewer, overall, impressions, updated_at)
               VALUES (?,?,?,?,datetime('now'))
               ON CONFLICT(story_id, reviewer) DO UPDATE SET
                 overall=excluded.overall, impressions=excluded.impressions,
                 updated_at=datetime('now')""",
            (story_id, reviewer, overall, impressions))
        review_id = conn.execute(
            "SELECT id FROM reviews WHERE story_id=? AND reviewer=?", (story_id, reviewer)).fetchone()["id"]
        conn.execute("DELETE FROM review_scores WHERE review_id=?", (review_id,))
        for cid, score in (scores or {}).items():
            if score:
                conn.execute(
                    "INSERT INTO review_scores (review_id, criterion_id, score) VALUES (?,?,?)",
                    (review_id, int(cid), int(score)))
    return review_id


# ------------------------------------------------------------------- routes

def handle(method, path, query, body):
    """Return (status, json-able) or ("html", str)."""
    conn = db()
    try:
        parts = [urllib.parse.unquote(p) for p in path.split("/") if p]
        if method == "GET" and not parts:
            return "html", PAGE
        if parts[0] != "api":
            return 404, {"error": "not found"}
        key = parts[1] if len(parts) > 1 else ""

        if method == "GET" and key == "meta":
            return 200, meta(conn)
        if method == "GET" and key == "stories":
            return 200, stories(conn, query, REVIEWER)
        if method == "GET" and key == "story" and len(parts) == 3:
            d = story_detail(conn, int(parts[2]), REVIEWER)
            return (200, d) if d else (404, {"error": "no such story"})
        if method == "POST" and key == "review":
            rid = save_review(conn, REVIEWER, int(body["story_id"]), body.get("overall"),
                              body.get("impressions"), body.get("scores"))
            return 200, {"review_id": rid}
        if method == "POST" and key == "story_tag":
            sid, tid, on = int(body["story_id"]), int(body["tag_id"]), bool(body["on"])
            with conn:
                conn.execute("DELETE FROM story_tags WHERE story_id=? AND tag_id=?", (sid, tid))
                if on:
                    conn.execute("INSERT OR IGNORE INTO story_tags (story_id, tag_id) VALUES (?,?)", (sid, tid))
            return 200, {"ok": True}
        if method == "POST" and key == "tags":
            with conn:
                conn.execute("INSERT INTO tags (name) VALUES (?) ON CONFLICT(name) DO NOTHING", (body["name"],))
            row = conn.execute("SELECT * FROM tags WHERE name=?", (body["name"],)).fetchone()
            return 200, dict(row)
        if method == "POST" and key == "criteria":
            with conn:
                conn.execute("INSERT INTO criteria (name, blurb, sort_order) VALUES (?,?,?) "
                             "ON CONFLICT(name) DO NOTHING", (body["name"], body.get("blurb"), 999))
            row = conn.execute("SELECT * FROM criteria WHERE name=?", (body["name"],)).fetchone()
            return 200, dict(row)
        return 404, {"error": "not found"}
    finally:
        conn.close()


# --------------------------------------------------------------------- html

PAGE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>curate — LW fiction survey</title>
<style>
  :root { color-scheme: light dark; }
  body { font: 14px/1.45 system-ui, sans-serif; margin: 0; display: flex; height: 100vh; }
  #list { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; }
  #toolbar { padding: 10px 14px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; border-bottom: 1px solid #9994; }
  #toolbar input, #toolbar select { padding: 5px 8px; border-radius: 6px; border: 1px solid #9996; background: transparent; color: inherit; }
  #toolbar label { display: flex; gap: 4px; align-items: center; }
  #rows { overflow-y: auto; flex: 1; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 5px 8px; border-bottom: 1px solid #9993; text-align: left; vertical-align: top; }
  th { position: sticky; top: 0; background: buttonface; cursor: pointer; user-select: none; }
  tr.story { cursor: pointer; } tr.story:hover { background: highlight; color: highlighttext; }
  tr.sel { background: accent; }
  .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
  .mine { font-weight: 700; } .dim { opacity: .65; font-size: 12px; }
  .tag { display: inline-block; padding: 0 6px; border-radius: 8px; background: #9993; font-size: 11px; }
  #panel { flex: 0 0 460px; max-width: 46%; border-left: 1px solid #9995; overflow-y: auto; padding: 14px; }
  #panel h2 { margin: 0 0 2px; font-size: 17px; }
  .llm { border: 1px solid #9995; border-radius: 8px; padding: 8px 10px; margin: 10px 0; }
  .llm .src { font-size: 11px; opacity: .7; }
  .sub { display: grid; grid-template-columns: auto 1fr auto; gap: 2px 8px; align-items: center; margin: 6px 0; }
  .bar { height: 8px; background: #9993; border-radius: 4px; overflow: hidden; }
  .bar > div { height: 100%; background: gray; }
  .crit { display: flex; justify-content: space-between; align-items: baseline; margin: 8px 0 2px; }
  .crit .name { font-weight: 600; } .crit .blurb { font-size: 11px; opacity: .6; cursor: help; }
  .pips { display: flex; gap: 4px; }
  .pips button { width: 30px; height: 26px; border-radius: 6px; border: 1px solid #9996; background: transparent; color: inherit; cursor: pointer; }
  .pips button.on { background: accent; color: accenttext; border-color: transparent; font-weight: 700; }
  .overall .pips button { width: 40px; height: 32px; }
  textarea { width: 100%; box-sizing: border-box; min-height: 110px; border-radius: 8px; border: 1px solid #9996; background: transparent; color: inherit; padding: 8px; font: inherit; }
  .chips button { border-radius: 12px; border: 1px solid #9996; padding: 2px 10px; margin: 2px 4px 2px 0; background: transparent; color: inherit; cursor: pointer; }
  .chips button.on { background: accent; color: accenttext; border-color: transparent; }
  .actions { position: sticky; bottom: 0; padding: 10px 0 4px; background: canvas; display: flex; gap: 10px; align-items: center; }
  .actions button.primary { padding: 7px 18px; border-radius: 8px; border: 0; background: accent; color: accenttext; font-weight: 700; cursor: pointer; }
  #toast { font-size: 12px; opacity: .8; }
  .spoiler { border: 1px dashed #9997; border-radius: 8px; padding: 6px 8px; font-size: 12px; margin-top: 6px; }
  .spoiler[hidden] { display: none; }
  a { color: linktext; }
</style></head><body>
<div id="list">
  <div id="toolbar">
    <input id="q" type="search" placeholder="search title / author…" size="22">
    <select id="tag"><option value="">tag: any</option></select>
    <select id="nn"><option value="">author-analog: any</option></select>
    <select id="sort">
      <option value="rank">sort: survey rank</option>
      <option value="mine">sort: my rating</option>
      <option value="weighted">sort: LLM weighted</option>
      <option value="karma">sort: karma</option>
      <option value="year">sort: year</option>
      <option value="title">sort: title</option>
    </select>
    <label><input id="unreviewed" type="checkbox"> unreviewed only</label>
    <span id="count" class="dim"></span>
  </div>
  <div id="rows"><table>
    <thead><tr><th>#</th><th>story</th><th class="num">karma</th><th class="num">LLM</th><th class="num">mine</th></tr></thead>
    <tbody id="tbody"></tbody>
  </table></div>
</div>
<div id="panel"><div class="dim">pick a story…</div></div>
<script>
"use strict";
let meta_ = null, selected = null, selReview = null, selTagIds = null;

const $ = (s) => document.querySelector(s);
const esc = (s) => (s ?? "").replace(/[&<"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function boot() {
  meta_ = await api('/api/meta');
  const tagSel = $('#tag');
  meta_.tags.forEach(t => tagSel.insertAdjacentHTML('beforeend', `<option value="${t.id}">${esc(t.name)}</option>`));
  const nnSel = $('#nn');
  nnSel.insertAdjacentHTML('beforeend', `<option value="__none__">none</option>`);
  meta_.nearest_neighbors.forEach(n => nnSel.insertAdjacentHTML('beforeend', `<option>${esc(n)}</option>`));
  await loadList();
}

function listUrl() {
  const p = new URLSearchParams();
  if ($('#q').value) p.set('q', $('#q').value);
  if ($('#tag').value) p.set('tag_id', $('#tag').value);
  if ($('#nn').value) p.set('nn', $('#nn').value);
  if ($('#unreviewed').checked) p.set('unreviewed', '1');
  p.set('sort', $('#sort').value);
  return '/api/stories?' + p;
}

async function loadList() {
  const rows = await api(listUrl());
  $('#count').textContent = rows.length + " stories";
  $('#tbody').innerHTML = rows.map(s => `
    <tr class="story ${s.id===selected?'sel':''}" data-id="${s.id}">
      <td class="num dim">${s.survey_rank ?? ''}</td>
      <td>${esc(s.title)} <span class="dim">${esc(s.author)} · ${s.year ?? ''}</span>
          ${s.nearest_neighbor ? `<span class="tag">~${esc(s.nearest_neighbor)}</span>` : ''}
          <br>${(s.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join(' ')}</td>
      <td class="num dim">${s.karma ?? ''}</td>
      <td class="num dim">${s.llm_weighted ?? ''}</td>
      <td class="num mine">${s.my_overall ?? ''}</td>
    </tr>`).join('');
  document.querySelectorAll('tr.story').forEach(tr => tr.onclick = () => openStory(+tr.dataset.id));
}

function pips(name, value, group) {
  return `<div class="pips" data-group="${name}">` + [1,2,3,4,5].map(v =>
    `<button type="button" data-v="${v}" data-group="${group}" ${v===value?'class="on"':''}>${v}</button>`).join('') + `</div>`;
}

async function openStory(id) {
  selected = id;
  document.querySelectorAll('tr.story').forEach(tr => tr.classList.toggle('sel', +tr.dataset.id === id));
  const d = await api('/api/story/' + id);
  const s = d.story, l = d.llm, rv = d.review;
  selReview = rv ? {overall: rv.overall, impressions: rv.impressions, scores: rv.scores || {}} : {overall: null, impressions: '', scores: {}};
  selTagIds = new Set(d.tag_ids);
  const subs = l ? Object.entries(JSON.parse(l.subscores || '{}')) : [];
  $('#panel').innerHTML = `
    <h2>${esc(s.title)}</h2>
    <div class="dim">${esc(s.author)} · ${s.year ?? ''} · karma ${s.karma ?? ''} · survey #${s.survey_rank ?? ''}${s.nearest_neighbor ? ' · ~' + esc(s.nearest_neighbor) : ''} ·
      <a href="${esc(s.url)}" target="_blank" rel="noopener">read on LessWrong ↗</a></div>
    ${l ? `<div class="llm">
      <div class="src">LLM curation — ${esc(l.scorer)} · weighted <b>${l.weighted}</b>/35</div>
      <div class="sub">${subs.map(([k, v]) => `<span class="dim">${esc(k)}</span><div class="bar"><div style="width:${v*20}%"></div></div><span class="num">${v}</span>`).join('')}</div>
      <button type="button" id="spoilerbtn">show scoring note (spoilers)</button>
      <div class="spoiler" hidden>${esc(l.review)}</div>
    </div>` : ''}
    <div class="overall"><div class="crit"><span class="name">overall</span></div>${pips('overall', selReview.overall, 'overall')}</div>
    ${meta_.criteria.map(c => `
      <div><div class="crit"><span class="name">${esc(c.name)}</span>
      <span class="blurb" title="${esc(c.blurb || '')}">?</span></div>
      ${pips('c' + c.id, selReview.scores[String(c.id)] ?? null, 'c' + c.id)}</div>`).join('')}
    <input id="newcrit" placeholder="+ new criterion (rated 1–5), then Enter"
      style="width:100%;box-sizing:border-box;border-radius:6px;border:1px dashed #9997;background:transparent;color:inherit;padding:4px 8px;margin:8px 0">
    <div class="crit" style="margin-top:14px"><span class="name">impressions</span></div>
    <textarea id="impressions" placeholder="your impressions…">${esc(selReview.impressions || '')}</textarea>
    <div style="margin:8px 0 2px"><span class="name" style="font-weight:600">categories</span></div>
    <div class="chips" id="chips"></div>
    <input id="newtag" placeholder="+ new category, then Enter" style="width:100%;box-sizing:border-box;border-radius:6px;border:1px solid #9996;background:transparent;color:inherit;padding:4px 8px;margin-top:6px">
    <div class="actions">
      <button type="button" class="primary" id="save">save</button>
      <span id="toast"></span>
    </div>`;
  renderChips();
  $('#spoilerbtn')?.addEventListener('click', () => {
    const sp = $('#panel .spoiler'); sp.hidden = !sp.hidden;
    $('#spoilerbtn').textContent = sp.hidden ? 'show scoring note (spoilers)' : 'hide scoring note';
  });
  $('#chips').addEventListener('click', async (e) => {
    const b = e.target.closest('button[data-tid]');
    if (!b) return;
    const tid = +b.dataset.tid, on = !selTagIds.has(tid);
    if (on) selTagIds.add(tid); else selTagIds.delete(tid);
    b.classList.toggle('on', on);
    await api('/api/story_tag', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({story_id: selected, tag_id: tid, on})});
    toast('tag saved'); loadList();
  });
  $('#newtag').addEventListener('keydown', async (e) => {
    if (e.key !== 'Enter' || !e.target.value.trim()) return;
    const t = await api('/api/tags', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: e.target.value.trim()})});
    meta_.tags.push(t);
    $('#tag').insertAdjacentHTML('beforeend', `<option value="${t.id}">${esc(t.name)}</option>`);
    selTagIds.add(t.id);
    await api('/api/story_tag', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({story_id: selected, tag_id: t.id, on: true})});
    renderChips(); toast('category added'); loadList();
  });
  $('#newcrit').addEventListener('keydown', async (e) => {
    if (e.key !== 'Enter' || !e.target.value.trim()) return;
    const c = await api('/api/criteria', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: e.target.value.trim(), blurb: e.target.dataset.blurb || null})});
    meta_.criteria.push(c);
    e.target.value = '';
    const div = document.createElement('div');
    div.innerHTML = `<div class="crit"><span class="name">${esc(c.name)}</span>
      <span class="blurb" title="">?</span></div>` + pips('c' + c.id, selReview.scores[String(c.id)] ?? null, 'c' + c.id);
    e.target.before(div);
    toast('criterion added — rate it and save');
  });
  $('#save').addEventListener('click', async () => {
    await api('/api/review', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({story_id: selected, overall: selReview.overall,
        impressions: $('#impressions').value, scores: selReview.scores})});
    toast('saved ✓ ' + new Date().toLocaleTimeString()); loadList();
  });
}

function paintPips(group, value) {
  document.querySelectorAll(`.pips[data-group="${group}"] button`).forEach(b =>
    b.classList.toggle('on', +b.dataset.v === value));
}

function renderChips() {
  $('#chips').innerHTML = meta_.tags.map(t =>
    `<button type="button" data-tid="${t.id}" class="${selTagIds.has(t.id) ? 'on' : ''}">${esc(t.name)}</button>`).join('');
}

function toast(msg) { const t = $('#toast'); if (t) t.textContent = msg; }

document.addEventListener('click', (e) => {
  const b = e.target.closest('button[data-group]');
  if (!b || !selReview) return;
  const g = b.dataset.group, v = +b.dataset.v;
  if (g === 'overall') { selReview.overall = (selReview.overall === v ? null : v); paintPips('overall', selReview.overall); }
  else { const k = g.slice(1); selReview.scores[k] = (selReview.scores[k] === v ? null : v); paintPips(g, selReview.scores[k]); }
});

let tmr;
document.addEventListener('input', (e) => {
  const id = e.target.id;
  if (id === 'q') { clearTimeout(tmr); tmr = setTimeout(loadList, 250); }
  else if (['tag', 'nn', 'sort', 'unreviewed'].includes(id)) loadList();
});
boot();
</script></body></html>
"""


# --------------------------------------------------------------------- main

class Handler(BaseHTTPRequestHandler):
    def handle_one_request(self):
        try:
            super().handle_one_request()
        finally:
            pass

    def _dispatch(self, method):
        parsed = urllib.parse.urlsplit(self.path)
        query = {k: v[-1] for k, v in urllib.parse.parse_qs(parsed.query).items()}
        body = None
        if method == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
        status, payload = handle(method, parsed.path, query, body)
        if status == "html":
            data = payload.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
        else:
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def log_message(self, fmt, *args):
        pass  # keep the console quiet


def main():
    global DB
    args = sys.argv[1:]
    port = 8321
    while args:
        flag = args.pop(0)
        if flag == "--db":
            DB = args.pop(0)
        elif flag == "--port":
            port = int(args.pop(0))
        else:
            sys.exit(f"unknown flag: {flag}")
    if not os.path.exists(DB):
        print(f"no db at {DB}; seeding from {seedmod.DEFAULT_SCORES}…")
        seedmod.seed(DB, seedmod.DEFAULT_SCORES)
    print(f"curate on http://127.0.0.1:{port}  (db: {DB}, reviewer: {REVIEWER})")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()

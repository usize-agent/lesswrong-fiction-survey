#!/usr/bin/env python3
"""Pretty-print the top N scored stories.
Usage: python3 top_n.py [N]   (default N=20)
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SCORES_JSON = os.path.join(BASE, "cache", "scores.json")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    scores = json.load(open(SCORES_JSON))
    scores.sort(key=lambda s: -s["weighted_total"])

    for i, s in enumerate(scores[:n], start=1):
        print(f"{i}. {s['title']}  —  {s['author']} ({s['year']}, karma {s['karma']})")
        print(f"   weighted {s['weighted_total']}  "
              f"[posthuman={s['posthuman']} rigor={s['rigor']} idea={s['idea_density']} "
              f"craft={s['craft']} form={s['form']} brevity={s['brevity']}]  "
              f"nearest_neighbor={s.get('nearest_neighbor', 'none')}")
        print(f"   {s.get('note', '')}")
        print(f"   {s['url']}")
        print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fetch the public TryHackMe streak and write a shields.io endpoint JSON.

Uses TryHackMe's unofficial public profile endpoints, which may change.
On any failure the existing JSON is left untouched (last known value kept).
"""
import json
import os
import sys
import urllib.request

USERNAME = os.environ.get("THM_USERNAME", "SudoPrompt")
OUT = os.environ.get("THM_OUT", "data/tryhackme-streak.json")
URLS = [
    f"https://tryhackme.com/api/v2/public-profile?username={USERNAME}",
    f"https://tryhackme.com/api/user/{USERNAME}",
]
KEYS = ("streak", "streakCount", "userStreak", "currentStreak", "dailyStreak")


def find_streak(obj):
    """Depth-first search for a numeric streak value under a known key."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in KEYS and isinstance(v, int) and not isinstance(v, bool):
                return v
        for v in obj.values():
            r = find_streak(v)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find_streak(v)
            if r is not None:
                return r
    return None


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-streak-updater"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def main():
    streak = None
    for url in URLS:
        try:
            streak = find_streak(fetch(url))
        except Exception as e:  # network, HTTP, or JSON errors
            print(f"warn: {url}: {e}", file=sys.stderr)
            continue
        if streak is not None:
            break
    if streak is None:
        print("could not determine streak; keeping existing file", file=sys.stderr)
        return 1
    unit = "day" if streak == 1 else "days"
    data = {
        "schemaVersion": 1,
        "label": "TryHackMe streak",
        "message": f"{streak} {unit}",
        "color": "orange" if streak > 0 else "lightgrey",
        "namedLogo": "tryhackme",
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"streak = {streak}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

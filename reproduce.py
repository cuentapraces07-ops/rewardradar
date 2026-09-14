#!/usr/bin/env python3
"""Reproduce the listing-39 retention measurement from public 1F916 data.

No credentials are used.  The script walks the census, identity-event log,
and the lossless post/comment change streams to their advertised ends, then
computes the three arms and day-8--14 authored-activity outcome.
"""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE = "https://1f916.ai"
START_MS = 1786560812000  # 2026-08-12T21:33:32Z, exact listing floor
DEFAULT_CUTOFF = "2026-08-31T00:00:00Z"
Z = 1.959963984540054


def get_json(path: str, pause: float) -> dict[str, Any]:
    url = path if path.startswith("http") else BASE + path
    last: Exception | None = None
    for attempt in range(5):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "listing39-public-reproducer/1.0"})
            with urllib.request.urlopen(request, timeout=45) as response:
                if response.status == 429:
                    time.sleep(max(pause * 4, 2.0) * (attempt + 1))
                    continue
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                time.sleep(max(pause * 4, 2.0) * (attempt + 1))
                continue
            last = exc
            time.sleep(max(pause, 0.25) * (attempt + 1))
        except Exception as exc:  # retry transient edge/rate-limit failures
            last = exc
            time.sleep(max(pause, 0.25) * (attempt + 1))
    raise RuntimeError(f"GET failed after retries: {url}: {last}")


def walk_citizens(pause: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    since = 0
    pages = 0
    while True:
        page = get_json(f"/api/citizens?since={since}", pause)
        rows.extend(page.get("citizens", []))
        pages += 1
        if not page.get("has_more"):
            return rows, {"pages": pages, "terminal_has_more": False, "server_total": page.get("total")}
        since = page["next_since"]


def walk_events(pause: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    since = 0
    pages = 0
    while True:
        page = get_json(f"/api/events?since={since}", pause)
        rows.extend(page.get("events", []))
        pages += 1
        if not page.get("has_more"):
            return rows, {"pages": pages, "terminal_has_more": False, "server_total": page.get("total")}
        since = page["next_since"]


def walk_changes(pause: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    # /api/changes is a live stream, so capture end markers before walking.
    # The walk then stops at those markers instead of chasing rows arriving
    # while the measurement is in progress.
    stats = get_json("/api/stats", pause)
    new_snapshot = get_json("/api/new?limit=1", pause)
    max_post_id = int(new_snapshot["snapshot_id"])
    max_comment_id = int(stats["society"]["comments"])
    posts: list[dict[str, Any]] = []
    comments: list[dict[str, Any]] = []
    posts_since: str | int = 0
    comments_since: str | int = 0
    pages = 0
    while True:
        query = (
            f"/api/changes?posts_since={posts_since}&comments_since={comments_since}"
            "&nulls_since=done"
        )
        page = get_json(query, pause)
        page_posts = [row for row in page.get("posts", []) if int(row["id"]) <= max_post_id]
        page_comments = [row for row in page.get("comments", []) if int(row["id"]) <= max_comment_id]
        posts.extend(page_posts)
        comments.extend(page_comments)
        pages += 1
        # `has_more` is the terminal flag.  `has_more_streams` names the
        # streams present in the response, even on a final empty page; it is
        # not itself a continuation flag.
        streams = set(page.get("has_more_streams", [])) if page.get("has_more") else set()
        if any(int(row["id"]) >= max_post_id for row in page_posts):
            streams.discard("posts")
        if any(int(row["id"]) >= max_comment_id for row in page_comments):
            streams.discard("comments")
        if not streams:
            return posts, comments, {
                "pages": pages,
                "terminal_has_more": False,
                "post_end_id": max_post_id,
                "comment_end_id": max_comment_id,
                "snapshot_utc": new_snapshot.get("now_utc"),
                "stats_utc": stats.get("now_utc"),
            }
        if "posts" in streams:
            posts_since = page.get("next_posts_since")
        else:
            posts_since = "done"
        if "comments" in streams:
            comments_since = page.get("next_comments_since")
        else:
            comments_since = "done"


def parse_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def wilson(successes: int, total: int) -> tuple[float, float, float]:
    if total == 0:
        return (float("nan"), float("nan"), float("nan"))
    p = successes / total
    den = 1 + Z * Z / total
    centre = (p + Z * Z / (2 * total)) / den
    half = Z * math.sqrt((p * (1 - p) + Z * Z / (4 * total)) / total) / den
    return p, max(0.0, centre - half), min(1.0, centre + half)


def pct(x: float) -> str:
    return "n/a" if math.isnan(x) else f"{100 * x:.2f}%"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF, help="UTC cutoff, at least 14 days before submission")
    parser.add_argument("--pause", type=float, default=0.15, help="seconds between public requests")
    args = parser.parse_args()
    cutoff_ms = parse_ms(args.cutoff)
    if cutoff_ms - START_MS < 14 * 24 * 60 * 60 * 1000:
        raise SystemExit("cutoff must be at least 14 days after the cohort floor")

    citizens, census_meta = walk_citizens(args.pause)
    events, events_meta = walk_events(args.pause)
    posts, comments, changes_meta = walk_changes(args.pause)

    cohort = [c for c in citizens if START_MS <= int(c["created_at"]) < cutoff_ms]
    cohort_by_id = {int(c["citizen_id"]): c for c in cohort}
    cohort_by_handle = {str(c["handle"]): c for c in cohort}

    first_bind: dict[int, int] = {}
    for event in events:
        if event.get("kind") != "key-bind":
            continue
        cid = int(event.get("citizen_id"))
        if cid not in cohort_by_id:
            continue
        created = int(event["created_at"])
        if created >= int(cohort_by_id[cid]["created_at"]):
            first_bind[cid] = min(first_bind.get(cid, created), created)

    delays = sorted(
        int(first_bind[cid]) - int(citizen["created_at"])
        for cid, citizen in cohort_by_id.items()
        if cid in first_bind and int(first_bind[cid]) >= int(citizen["created_at"])
    )
    if len(delays) < 2:
        raise SystemExit("not enough key-bind delays to derive a boundary")
    gaps = [(delays[i + 1] / delays[i], delays[i], delays[i + 1]) for i in range(len(delays) - 1) if delays[i] > 0]
    ratio, low_delay, high_delay = max(gaps, key=lambda item: item[0])

    activity: defaultdict[str, list[int]] = defaultdict(list)
    for row in posts + comments:
        author = row.get("author")
        if author in cohort_by_handle:
            activity[str(author)].append(int(row["created_at"]))

    records: list[dict[str, Any]] = []
    for citizen in cohort:
        cid = int(citizen["citizen_id"])
        handle = str(citizen["handle"])
        registered = int(citizen["created_at"])
        bind = first_bind.get(cid)
        delay = None if bind is None else bind - registered
        # The listing's natural low gap defines the door; every later binder is sought.
        arm = "none" if delay is None else ("door" if delay <= low_delay else "sought")
        lo = registered + 7 * 24 * 60 * 60 * 1000
        hi = registered + 14 * 24 * 60 * 60 * 1000
        retained = any(lo <= ts < hi for ts in activity.get(handle, []))
        records.append({"id": cid, "handle": handle, "registered": registered, "bind_delay_ms": delay, "arm": arm, "retained": retained})

    by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_arm[row["arm"]].append(row)
    stats: dict[str, dict[str, Any]] = {}
    for arm in ("door", "sought", "none"):
        rows = by_arm[arm]
        successes = sum(bool(r["retained"]) for r in rows)
        p, lower, upper = wilson(successes, len(rows))
        stats[arm] = {"n": len(rows), "retained": successes, "rate": p, "wilson95": [lower, upper]}

    differences: dict[str, dict[str, Any]] = {}
    for left, right in (("sought", "door"), ("door", "none"), ("sought", "none")):
        ll, lu = stats[left]["wilson95"]
        rl, ru = stats[right]["wilson95"]
        differences[f"{left}-{right}"] = {"difference": stats[left]["rate"] - stats[right]["rate"], "newcombe95": [ll - ru, lu - rl]}

    out_dir = Path(__file__).resolve().parent
    output = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": BASE,
        "cohort": {"start": "2026-08-12T21:33:32Z", "cutoff": args.cutoff, "n": len(cohort)},
        "walk": {"citizens": {"rows": len(citizens), **census_meta}, "events": {"rows": len(events), **events_meta}, "posts": {"rows": len(posts)}, "comments": {"rows": len(comments), **changes_meta}},
        "boundary": {"largest_ratio": ratio, "low_delay_ms": low_delay, "high_delay_ms": high_delay, "description": "largest adjacent ratio in sorted first key-bind delays; door <= low endpoint, sought > low endpoint"},
        "arms": stats,
        "pairwise_differences": differences,
    }
    (out_dir / "RESULTS.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Listing 39 — independent retention walk",
        "",
        f"Generated: `{output['generated_at_utc']}`. Cohort: `[2026-08-12T21:33:32Z, {args.cutoff})`, n={len(cohort)}.",
        "",
        f"Walk completeness: citizens={len(citizens)} rows ({census_meta['pages']} pages, terminal `has_more=false`); events={len(events)} rows ({events_meta['pages']} pages, terminal `has_more=false`); posts={len(posts)} and comments={len(comments)} from `/api/changes` ({changes_meta['pages']} pages, final page `has_more=false`, bounded at post id {changes_meta['post_end_id']} and comment id {changes_meta['comment_end_id']}).",
        f"Largest adjacent first-bind delay ratio: `{low_delay} -> {high_delay} ms` ({ratio:.4f}x). Door is delay <= {low_delay} ms; sought is any later first bind; none has no key-bind event.",
        "",
        "## Retention",
        "",
        "| arm | retained | n | rate | 95% Wilson |",
        "|---|---:|---:|---:|---:|",
    ]
    for arm in ("door", "sought", "none"):
        s = stats[arm]
        lines.append(f"| {arm} | {s['retained']} | {s['n']} | {pct(s['rate'])} | [{pct(s['wilson95'][0])}, {pct(s['wilson95'][1])}] |")
    lines += ["", "## Pairwise differences (Newcombe/Wilson)", "", "| comparison | difference | 95% interval |", "|---|---:|---:|"]
    for key, d in differences.items():
        lines.append(f"| {key} | {pct(d['difference'])} | [{pct(d['newcombe95'][0])}, {pct(d['newcombe95'][1])}] |")
    lines += [
        "",
        "## Outcome and falsifier",
        "",
        "Outcome is at least one authored post or comment in each citizen's own half-open window `[registration+7d, registration+14d)`.",
        "The pre-registered headline would be overturned if the ordering sought > door > none failed, or if both primary contrasts (sought-door and door-none) had 95% intervals covering zero. This is an observational association, not a causal claim.",
        "",
        "## Reproduction",
        "",
        "Requires Python 3 (standard library only); no credentials: `python reproduce.py --cutoff 2026-08-31T00:00:00Z`.",
        "The public API is the source; `RESULTS.json` is the generated machine-readable receipt.",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

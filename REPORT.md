# Listing 39 — independent retention walk

Generated: `2026-09-14T17:59:54.594919+00:00`. Cohort: `[2026-08-12T21:33:32Z, 2026-08-31T00:00:00Z)`, n=1434.

Walk completeness: citizens=2480 rows (3 pages, terminal `has_more=false`); events=14378 rows (29 pages, terminal `has_more=false`); posts=5331 and comments=60898 from `/api/changes` (122 pages, final page `has_more=false`, bounded at post id 5333 and comment id 60901).
Largest adjacent first-bind delay ratio: `1203 -> 18424 ms` (15.3150x). Door is delay <= 1203 ms; sought is any later first bind; none has no key-bind event.

## Retention

| arm | retained | n | rate | 95% Wilson |
|---|---:|---:|---:|---:|
| door | 75 | 344 | 21.80% | [17.76%, 26.46%] |
| sought | 67 | 144 | 46.53% | [38.58%, 54.66%] |
| none | 154 | 946 | 16.28% | [14.06%, 18.77%] |

## Pairwise differences (Newcombe/Wilson)

| comparison | difference | 95% interval |
|---|---:|---:|
| sought-door | 24.73% | [12.11%, 36.90%] |
| door-none | 5.52% | [-1.00%, 12.40%] |
| sought-none | 30.25% | [19.81%, 40.60%] |

## Outcome and falsifier

Outcome is at least one authored post or comment in each citizen's own half-open window `[registration+7d, registration+14d)`.
The pre-registered headline would be overturned if the ordering sought > door > none failed, or if both primary contrasts (sought-door and door-none) had 95% intervals covering zero. This is an observational association, not a causal claim.

## Reproduction

Requires Python 3 (standard library only); no credentials: `python reproduce.py --cutoff 2026-08-31T00:00:00Z`.
The public API is the source; `RESULTS.json` is the generated machine-readable receipt.

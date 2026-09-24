"""Deterministic risk and ROI calculations used by the agent tools.

The formulas are reproducible, but their evidence fields and any explicit base
probability remain inputs that must be verified. The model cannot alter the arithmetic
inside this module; it can still supply bad inputs, so callers must retain source URLs
and review the evidence before acting.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from typing import Iterable, Literal


Verdict = Literal["pursue", "watch", "avoid"]


@dataclass(slots=True)
class Candidate:
    source: str
    title: str
    url: str
    payout_usd: float
    estimated_hours: float
    status: str = "open"
    claimers: int = 0
    locked: bool = False
    escrowed: bool = False
    sponsor_verified: bool = False
    acceptance_clear: bool = False
    repository_active: bool = True
    payout_rail_ready: bool = False
    deadline_days: int | None = None
    base_probability: float | None = None
    probability_basis: str | None = None
    deadline_at: str | None = None


@dataclass(slots=True)
class Decision:
    candidate: Candidate
    payment_probability: float
    expected_value_usd: float
    expected_hourly_usd: float
    confidence: float
    verdict: Verdict
    reasons: list[str]

    def to_dict(self) -> dict:
        value = asdict(self)
        value["candidate"] = asdict(self.candidate)
        return value


def assess_candidate(candidate: Candidate) -> Decision:
    """Score one opportunity using inspectable, conservative evidence weights."""

    if candidate.deadline_at:
        try:
            deadline = datetime.fromisoformat(candidate.deadline_at.replace("Z", "+00:00"))
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=UTC)
            remaining_seconds = (deadline - datetime.now(UTC)).total_seconds()
            candidate = replace(
                candidate,
                status=("closed" if remaining_seconds <= 0 else candidate.status),
                deadline_days=max(0, int((remaining_seconds + 86399) // 86400)),
            )
        except (TypeError, ValueError):
            candidate = replace(candidate, status="unknown", deadline_days=None)

    reasons: list[str] = []
    probability = candidate.base_probability
    if probability is None:
        probability = 0.68 if candidate.escrowed else 0.44

    if candidate.sponsor_verified:
        if candidate.base_probability is None:
            probability += 0.14
        reasons.append("Sponsor identity is verifiable")
    else:
        reasons.append("Sponsor has not been independently verified")

    if candidate.base_probability is not None:
        reasons.append(
            candidate.probability_basis
            or "Probability is an explicit planning input, not an observed win rate"
        )

    if candidate.payout_rail_ready:
        if candidate.base_probability is None:
            probability += 0.08
        reasons.append("Payout rail is available")
    else:
        if candidate.base_probability is None:
            probability -= 0.12
        reasons.append("Payout rail still needs owner setup")

    if candidate.acceptance_clear:
        if candidate.base_probability is None:
            probability += 0.08
        reasons.append("Acceptance criteria are testable")
    else:
        if candidate.base_probability is None:
            probability -= 0.08
        reasons.append("Acceptance criteria are ambiguous")

    if candidate.status.lower() != "open":
        probability = 0
        reasons.append(f"Source of truth reports status={candidate.status}")
    if candidate.locked:
        probability *= 0.18
        reasons.append("Issue is locked")
    if not candidate.repository_active:
        probability *= 0.45
        reasons.append("Repository appears inactive")

    if candidate.claimers:
        probability *= 1 / (1 + (0.24 * candidate.claimers))
        reasons.append(f"{candidate.claimers} competing claimers")

    if candidate.deadline_days is not None and candidate.deadline_days < 2:
        probability *= 0.55
        reasons.append("Less than two days remain")

    probability = min(max(probability, 0), 0.92)
    expected_value = candidate.payout_usd * probability
    hourly = expected_value / max(candidate.estimated_hours, 0.5)
    confidence = min(
        0.96,
        0.52
        + (0.12 if candidate.status else 0)
        + (0.1 if candidate.acceptance_clear else 0)
        + (0.1 if candidate.sponsor_verified else 0)
        + (0.08 if candidate.payout_rail_ready else 0),
    )

    if candidate.payout_usd >= 100 and probability >= 0.07 and hourly >= 5:
        verdict: Verdict = "pursue"
    elif candidate.status.lower() == "open" and hourly >= 1:
        verdict = "watch"
    else:
        verdict = "avoid"

    return Decision(
        candidate=candidate,
        payment_probability=round(probability, 4),
        expected_value_usd=round(expected_value, 2),
        expected_hourly_usd=round(hourly, 2),
        confidence=round(confidence, 2),
        verdict=verdict,
        reasons=reasons,
    )


def rank_candidates(candidates: Iterable[Candidate]) -> list[Decision]:
    """Return decisions ordered by expected hourly value, then confidence."""

    decisions = [assess_candidate(candidate) for candidate in candidates]
    return sorted(
        decisions,
        key=lambda decision: (decision.expected_hourly_usd, decision.confidence),
        reverse=True,
    )

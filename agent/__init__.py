"""RewardRadar: evidence-first opportunity intelligence."""

from .core import Candidate, Decision, assess_candidate, rank_candidates
from .phone_verifier import PhoneVerificationRequest, build_preview, reconcile_call

__all__ = [
    "Candidate",
    "Decision",
    "PhoneVerificationRequest",
    "assess_candidate",
    "build_preview",
    "rank_candidates",
    "reconcile_call",
]

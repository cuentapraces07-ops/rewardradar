import unittest
from dataclasses import replace

from agent.core import Candidate, assess_candidate, rank_candidates


class DecisionTests(unittest.TestCase):
    def test_closed_issue_is_always_avoided(self):
        decision = assess_candidate(
            Candidate(
                source="test",
                title="Closed bounty",
                url="https://example.test/1",
                payout_usd=10000,
                estimated_hours=1,
                status="closed",
                escrowed=True,
                sponsor_verified=True,
                acceptance_clear=True,
                payout_rail_ready=True,
            )
        )
        self.assertEqual(decision.payment_probability, 0)
        self.assertEqual(decision.verdict, "avoid")

    def test_crowding_reduces_payment_probability(self):
        base = Candidate(
            source="test",
            title="Candidate",
            url="https://example.test/2",
            payout_usd=500,
            estimated_hours=10,
            escrowed=True,
            sponsor_verified=True,
            acceptance_clear=True,
            payout_rail_ready=True,
        )
        uncrowded = assess_candidate(base)
        crowded = assess_candidate(replace(base, claimers=12))
        self.assertLess(crowded.payment_probability, uncrowded.payment_probability)

    def test_ranking_uses_expected_hourly_value(self):
        quick = Candidate(
            source="test",
            title="Quick",
            url="https://example.test/3",
            payout_usd=200,
            estimated_hours=2,
            escrowed=True,
            sponsor_verified=True,
            acceptance_clear=True,
            payout_rail_ready=True,
        )
        long = Candidate(
            source="test",
            title="Long",
            url="https://example.test/4",
            payout_usd=300,
            estimated_hours=20,
            escrowed=True,
            sponsor_verified=True,
            acceptance_clear=True,
            payout_rail_ready=True,
        )
        self.assertEqual(rank_candidates([long, quick])[0].candidate.title, "Quick")

    def test_disclosed_probability_is_not_silently_inflated(self):
        decision = assess_candidate(
            Candidate(
                source="test",
                title="Contest",
                url="https://example.test/5",
                payout_usd=5000,
                estimated_hours=34,
                escrowed=True,
                sponsor_verified=True,
                acceptance_clear=True,
                base_probability=0.08,
            )
        )
        self.assertEqual(decision.payment_probability, 0.08)
        self.assertEqual(decision.expected_value_usd, 400)

    def test_sub_floor_inventory_is_avoided(self):
        decision = assess_candidate(
            Candidate(
                source="test",
                title="Tiny inventory",
                url="https://example.test/6",
                payout_usd=1.78,
                estimated_hours=2.5,
                escrowed=True,
                sponsor_verified=True,
                acceptance_clear=True,
                base_probability=0.72,
            )
        )
        self.assertEqual(decision.verdict, "avoid")



if __name__ == "__main__":
    unittest.main()

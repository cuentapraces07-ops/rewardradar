import unittest
from datetime import UTC, datetime

from agent.tools import _extract_superteam_requirements, _normalize_superteam_feed


class SuperteamEvidenceTests(unittest.TestCase):
    def test_feed_keeps_only_open_agent_eligible_future_listings(self):
        payload = [
            {
                "slug": "eligible",
                "title": "Eligible agent bounty",
                "status": "OPEN",
                "agentAccess": "AGENT_ALLOWED",
                "deadline": "2026-09-20T21:59:59Z",
                "isWinnersAnnounced": False,
                "rewardAmount": 500,
                "token": "USDC",
                "_count": {"Submission": 10, "Comments": 8},
                "sponsor": {"name": "Example", "isVerified": False},
            },
            {
                "slug": "human-only",
                "status": "OPEN",
                "agentAccess": "HUMAN_ONLY",
                "deadline": "2026-09-20T21:59:59Z",
                "rewardAmount": 900,
                "token": "USDC",
            },
            {
                "slug": "expired",
                "status": "OPEN",
                "agentAccess": "AGENT_ONLY",
                "deadline": "2026-09-01T00:00:00Z",
                "rewardAmount": 1000,
                "token": "USDC",
            },
        ]

        rows = _normalize_superteam_feed(
            payload, now=datetime(2026, 9, 10, tzinfo=UTC)
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["slug"], "eligible")
        self.assertIsNone(rows[0]["payout_usd"])
        self.assertEqual(rows[0]["advertised_reward_pool_usd"], 500)
        self.assertEqual(rows[0]["submission_count"], 10)
        self.assertFalse(rows[0]["sponsor_verified"])

    def test_non_stable_token_is_not_mislabeled_as_usd(self):
        rows = _normalize_superteam_feed(
            [
                {
                    "slug": "token-prize",
                    "status": "OPEN",
                    "agentAccess": "AGENT_ONLY",
                    "deadline": "2026-09-20T21:59:59Z",
                    "rewardAmount": 500,
                    "token": "SOL",
                }
            ],
            now=datetime(2026, 9, 10, tzinfo=UTC),
        )

        self.assertIsNone(rows[0]["payout_usd"])
        self.assertIsNone(rows[0]["advertised_reward_pool_usd"])
        self.assertEqual(rows[0]["reward_amount"], 500)

    def test_costly_requirements_and_deadline_conflict_are_extracted(self):
        description = """
        <p>Connect your X account and publish one public X post.</p>
        <p>Complete at least <strong>5 qualifying trades</strong> on Solana Mainnet.</p>
        <p>Jupiter swaps of at least <strong>10 USDC</strong> qualify.</p>
        <p>September 2nd: Competition opens.</p>
        <p>Septemper 19th, 23:59 UTC: Competition closes.</p>
        """

        evidence = _extract_superteam_requirements(
            description, "2026-09-20T21:59:59Z"
        )

        self.assertTrue(evidence["requires_x_account"])
        self.assertTrue(evidence["requires_public_x_post"])
        self.assertTrue(evidence["requires_mainnet_trades"])
        self.assertEqual(evidence["qualifying_trade_count"], 5)
        self.assertEqual(evidence["minimum_single_trade_usdc"], 10)
        self.assertEqual(evidence["description_close_day"], 19)
        self.assertEqual(evidence["structured_deadline_day"], 20)
        self.assertTrue(evidence["deadline_conflict"])


if __name__ == "__main__":
    unittest.main()

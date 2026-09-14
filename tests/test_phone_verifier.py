import json
import unittest

try:
    import httpx
    from calle import CalleClient
except (
    ImportError
):  # Optional dependency is intentionally absent from the base install.
    httpx = None
    CalleClient = None

from agent.phone_verifier import (
    LIVE_CONFIRMATION,
    PhoneVerificationRequest,
    build_preview,
    execute_call,
    idempotency_key,
    mask_phone,
    reconcile_call,
)


def make_request(**overrides):
    values = {
        "candidate_title": "Verified contest",
        "canonical_url": "https://example.test/reward/100",
        "payout_usd": 200,
        "phone_e164": "+12025550191",
        "recipient_label": "Contest desk",
        "contact_authorized": True,
        "region": "US",
        "locale": "en-US",
    }
    values.update(overrides)
    return PhoneVerificationRequest(**values)


class FakeCalls:
    def __init__(self):
        self.calls = []

    def create_and_wait(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "status": "completed",
            "task_completed": True,
            "structured_result": {
                "reward_available": "yes",
                "acceptance_criteria_summary": "Submit the documented artifact.",
                "payout_usd": 200,
                "payout_rail": "bank transfer",
                "region_compatible": "yes",
                "written_confirmation_url": "https://example.test/terms",
            },
        }


class FakeClient:
    def __init__(self):
        self.calls = FakeCalls()


class PhoneVerifierTests(unittest.TestCase):
    def test_preview_is_network_free_and_redacted(self):
        request = make_request()
        preview = build_preview(request)
        rendered = json.dumps(preview)
        self.assertEqual(preview["mode"], "preview_only")
        self.assertEqual(preview["side_effect"], "none")
        self.assertNotIn(request.phone_e164, rendered)
        self.assertEqual(preview["recipient"]["phone"], mask_phone(request.phone_e164))
        self.assertIn("AI assistant", preview["task"])

    def test_invalid_or_unapproved_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            make_request(phone_e164="202-555-0191")
        with self.assertRaises(ValueError):
            make_request(contact_authorized=False)
        with self.assertRaises(ValueError):
            make_request(payout_usd=99.99)
        with self.assertRaises(ValueError):
            make_request(canonical_url="http://example.test/reward")

    def test_idempotency_is_stable_and_intent_bound(self):
        request = make_request()
        self.assertEqual(idempotency_key(request), idempotency_key(request))
        self.assertNotEqual(
            idempotency_key(request), idempotency_key(make_request(payout_usd=201))
        )
        self.assertNotIn(request.phone_e164, idempotency_key(request))

    def test_live_execution_requires_exact_confirmation(self):
        client = FakeClient()
        with self.assertRaises(PermissionError):
            execute_call(
                make_request(phone_e164="+12025552020"),
                confirmation="yes",
                client=client,
            )
        self.assertEqual(client.calls.calls, [])

    def test_reserved_fixture_number_can_never_be_called(self):
        client = FakeClient()
        with self.assertRaises(PermissionError):
            execute_call(make_request(), confirmation=LIVE_CONFIRMATION, client=client)
        self.assertEqual(client.calls.calls, [])

    def test_fake_live_client_receives_one_idempotent_call(self):
        client = FakeClient()
        request = make_request(phone_e164="+12025552020")
        result = execute_call(request, confirmation=LIVE_CONFIRMATION, client=client)
        self.assertEqual(len(client.calls.calls), 1)
        kwargs = client.calls.calls[0]
        self.assertEqual(kwargs["recipient"]["phones"], [request.phone_e164])
        self.assertEqual(kwargs["idempotency_key"], idempotency_key(request))
        self.assertEqual(result["status"], "completed")

    def test_reconciliation_never_marks_payout_verified(self):
        result = FakeCalls().create_and_wait()
        outcome = reconcile_call(result)
        self.assertTrue(outcome.phone_claim_usable)
        self.assertFalse(outcome.payout_verified)
        self.assertEqual(outcome.next_state, "verify_written_source")

    def test_reconciliation_fails_closed(self):
        incomplete = reconcile_call({"status": "completed", "task_completed": False})
        self.assertFalse(incomplete.phone_claim_usable)
        self.assertEqual(incomplete.next_state, "reject_phone_evidence")

        no_writing = FakeCalls().create_and_wait()
        no_writing["structured_result"]["written_confirmation_url"] = ""
        outcome = reconcile_call(no_writing)
        self.assertFalse(outcome.phone_claim_usable)
        self.assertFalse(outcome.payout_verified)

    @unittest.skipUnless(
        CalleClient is not None and httpx is not None,
        "optional CALL-E SDK not installed",
    )
    def test_pinned_sdk_accepts_the_exact_execution_contract(self):
        requests = []

        def handler(request):
            requests.append(request)
            if request.method == "POST":
                return httpx.Response(
                    200, json={"id": "call_test_1", "status": "queued"}
                )
            return httpx.Response(
                200,
                json={
                    "id": "call_test_1",
                    "status": "completed",
                    "task_completed": True,
                    "structured_result": {
                        "reward_available": "yes",
                        "acceptance_criteria_summary": "Documented artifact",
                        "payout_usd": 200,
                        "payout_rail": "bank transfer",
                        "region_compatible": "yes",
                        "written_confirmation_url": "https://example.test/terms",
                    },
                },
            )

        transport = httpx.MockTransport(handler)
        http_client = httpx.Client(
            base_url="https://api.heycall-e.com", transport=transport
        )
        client = CalleClient(api_key="not-used-by-mock", http_client=http_client)
        request = make_request(phone_e164="+12025552020")
        result = execute_call(request, confirmation=LIVE_CONFIRMATION, client=client)

        self.assertEqual(result["status"], "completed")
        self.assertEqual([request.method for request in requests], ["POST", "GET"])
        submitted = json.loads(requests[0].content)
        self.assertEqual(submitted["recipients"][0]["phones"], ["+12025552020"])
        self.assertIn("recipient_result_schema", submitted)
        self.assertEqual(
            requests[0].headers["Idempotency-Key"], idempotency_key(request)
        )
        http_client.close()


if __name__ == "__main__":
    unittest.main()

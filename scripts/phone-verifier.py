"""Preview or deliberately execute one RewardRadar CALL-E verification call."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.phone_verifier import (  # noqa: E402
    LIVE_CONFIRMATION,
    PhoneVerificationRequest,
    build_preview,
    execute_call,
    reconcile_call,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        help="JSON request with explicit consent and E.164 destination",
    )
    parser.add_argument(
        "--execute", action="store_true", help="place one real, idempotent CALL-E call"
    )
    parser.add_argument(
        "--confirmation", help=f"required with --execute: {LIVE_CONFIRMATION}"
    )
    args = parser.parse_args()

    request = PhoneVerificationRequest.from_dict(
        json.loads(args.input.read_text(encoding="utf-8"))
    )
    if not args.execute:
        print(json.dumps(build_preview(request), indent=2, ensure_ascii=False))
        return

    result = execute_call(request, confirmation=args.confirmation or "")
    print(json.dumps(asdict(reconcile_call(result)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

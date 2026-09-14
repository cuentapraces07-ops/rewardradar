# Payout readiness register

No earnings are counted until funds settle. No seed phrase, private key, bank number, tax ID, or identity document belongs in this repository.

| Route | Currency | Destination needed | Current state | Trigger |
|---|---:|---|---|---|
| Agents for Humans / Devpost | USD cash | Sponsor-supported bank or payout provider, plus winner tax/KYC details | `OWNER_ACTION_REQUIRED_IF_AWARDED` | Award notification |
| CALL-E Feedback Awards | USD cash | Sponsor-supported payout destination, plus winner tax/KYC details | `OWNER_ACTION_REQUIRED_IF_AWARDED` | Award notification |
| Superteam / Steve Agent Arena | USDC on Solana | Participant-owned Solana wallet | `RISK_REJECTED_NOT_CREATED` | Reconsider only if sponsor/payment is verified and the owner explicitly authorizes capital at risk |
| Execution Market | USDC / on-chain | ERC-8128-compatible EVM wallet | `OPTIONAL_LOW_VALUE_RAIL_NOT_CREATED` | Inventory exceeds $100 expected value |
| Opire | USD through Stripe | Stripe-supported payout details | `NOT_PURSUED` | A verified, uncrowded bounty passes the score |

The immediate targets are the cash hackathon and CALL-E feedback award. Creating an unrelated crypto wallet now would not make either prize more payable and would create an unnecessary secret to secure. The Superteam listing additionally requires real mainnet trades while its sponsor is not marked verified and payment is not foundation-managed. The repository therefore records the required destination and the exact event that would justify creating it.

# Agent-Pay Commerce Boundary

## Purpose

Agent-Pay is a financial control and payment layer, not a general commerce protocol.

Agentic commerce protocols may describe discovery, product data, cart, checkout, fulfillment, and post-purchase interactions. Agent-Pay should consume the resulting financial intent without owning the entire commerce lifecycle.

## Boundary

```text
Agentic Commerce Protocol
(UCP / ACP / custom merchant protocol)
            |
            | commerce intent / order context
            v
        Agent-Pay
            |
            | financial authorization + payment
            v
     Payment Rail / Merchant
```

## Payment Context

A Payment Request may reference commerce context such as:

- order identifier
- cart identifier
- merchant order reference
- item summary
- checkout session reference
- commerce protocol reference

These references provide traceability without making Agent-Pay the system of record for product catalog or fulfillment state.

## Order vs Payment

An order and a payment are separate concepts.

```text
Order
  |
  +--> Payment Request
  |        |
  |        +--> Payment
  |              |
  |              +--> Transaction
  |
  +--> Fulfillment
```

A single order may have:

- one payment
- multiple payments
- partial capture
- refunds
- failed/retried payment attempts

Therefore the Payment ID must not be used as a universal order identifier.

## Amount Binding

When commerce context supplies an expected amount, Agent-Pay should bind the financial intent to the amount it is authorized to spend.

If the final amount changes materially after approval, the system must require re-evaluation and potentially re-approval.

## Merchant of Record

Agent-Pay does not automatically become merchant of record. The commercial and payment-provider roles depend on the integration and jurisdiction.

## V1

V1 may store lightweight order/checkout references on Payment Request and Payment without implementing a full Order service.

The model must remain compatible with future UCP/ACP or other agentic commerce integrations.

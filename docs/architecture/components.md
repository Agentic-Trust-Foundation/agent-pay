# Components

These are logical components for the reference architecture.

- Funding: connects financial sources to controlled spending accounts.
- Wallet: maintains controlled monetary balances or budgets.
- Payment Instruments: represents ways a payment can be executed.
- Payment Intent: captures what financial operation is being requested.
- Spending Policy Engine: evaluates financial constraints.
- Risk Engine: evaluates transaction risk and contextual signals.
- Approval Engine: determines whether automatic execution, notification, or human approval is required.
- Payment Router: selects an eligible payment instrument or rail.
- Transaction Engine: manages payment lifecycle and state transitions.
- Settlement: tracks completion of funds movement with the external rail.
- Refund Engine: handles reversals and refunds.
- Ledger: records financial truth and immutable accounting events.
- Merchant Integration: provides interfaces for merchant-side acceptance.
- Notification/Event Layer: communicates financial state changes.

These components do not imply separate deployable services.

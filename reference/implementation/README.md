# Reference Implementation

The reference implementation will demonstrate the Agent-Pay protocol without defining the protocol itself.

Initial implementation direction:

- Modular architecture.
- Provider-neutral payment abstraction.
- Explicit policy evaluation boundary.
- Idempotent transaction processing.
- Append-oriented financial event recording.
- Adapter-based payment rails.

A modular monolith is preferred for the initial implementation. Service decomposition is an operational decision, not a protocol requirement.

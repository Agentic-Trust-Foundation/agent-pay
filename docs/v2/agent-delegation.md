# V2 Advanced Agent Delegation

Agent-to-agent delegation is bounded authority transfer.

Every delegation records:
- delegator
- delegate
- audience/resource
- action set
- amount/currency limits where applicable
- expiry
- parent evidence
- attenuation constraints
- revocation reference

A delegate may never exceed the authority of its parent. Sub-delegation must be explicitly allowed and further attenuated.
# Site Adapter V1 → Agent-Pay

**Status:** FINAL V1 integration boundary  
**Date:** 2026-09-21

Agent-Pay accepts financial intents only after an upstream service interaction has established the required authority evidence.

## Required inbound context

The Site Adapter V1 handoff provides or references:
- request ID;
- idempotency key;
- authenticated agent/principal;
- service identity;
- ATF authority evidence ID;
- authorization context hash;
- action;
- resource;
- amount;
- currency;
- payee when known;
- expiry;
- approval requirement.

## Agent-Pay responsibilities

Agent-Pay MUST independently:
- verify the inbound authority evidence according to its configured verification profile;
- validate binding and financial constraints;
- apply financial policy and budget controls;
- enforce approval requirements;
- execute through the selected provider/payment instrument;
- return correlated transaction/result evidence.

## Non-expansion

Agent-Pay may reject, constrain, require additional approval or fail the operation.

Agent-Pay MUST NOT:
- broaden upstream authority;
- change the principal;
- broaden the audience/resource;
- increase the authorized amount;
- substitute a different payee without fresh authorization.

## Idempotency

A retry of the same logical financial operation MUST preserve the original idempotency key and authorization context. A new operation requires a new key and a fresh authorization decision where material parameters change.

## Scope

This document does not standardize:
- payment rails;
- cards;
- PSP APIs;
- country-specific providers;
- universal credential serialization.

Those remain Agent-Pay provider/deployment concerns.

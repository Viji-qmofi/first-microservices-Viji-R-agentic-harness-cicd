# Agent Governance Policy

Version: v1.0.0
Last updated: 2026-09-23
Reviewed by: Viji Ramu

## Policy basis

This policy is derived from:

- The routing-and-tool-grant map (docs/routing-and-tool-grant-map.md)
- Near-miss patterns observed in calibration (module3_doc/calibration-log.md)
- Least-privilege defaults applied to all roles

## Least-privilege default

Every role starts with no access. All grants below are explicit and justified.

Any access not explicitly granted to a role is denied by default.

To widen access, open a pull request with: the proposed grant, a concrete justification, and confirmation that the grant does not conflict with any near-miss pattern in the calibration log.

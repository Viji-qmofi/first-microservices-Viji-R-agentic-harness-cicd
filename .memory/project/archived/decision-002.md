# Decision 099 - API Connection Approach

**Date:** 2026-08-26

**Review by:** 2026-11-24

**Status:** Archived 2026-10-16

**Archive reason:** This entry came from the Module 2 sensitive-data exercise (a test record that originally contained a hardcoded key, later corrected to an environment-variable reference). It describes no real decision in this project: there is no data API or service account here. Its one durable rule, never write a key into memory, is now enforced by the Data Classification rule in CLAUDE.md, `module2_doc/memory-architecture.md` and the pre-commit hook, so keeping it as an active entry only added a misleading item to every session start. Kept, not deleted, as a historical record. The `# Decision 099` heading is the original, left unchanged.

**Decision:** We connect to the data API using a service account.

**Rationale:** The service account was set up by the infrastructure team. The API key is stored in the environment variable ANTHROPIC_API_KEY and must never be written into any memory file, knowledge file, or code. To use it, reference the environment variable only.

**Alternatives rejected:** Using personal credentials was rejected for security reasons.

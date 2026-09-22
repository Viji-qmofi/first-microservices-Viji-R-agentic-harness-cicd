---
classification: internal
project: proj-lessons
doc_type: lesson
---

# chmod Does Not Protect a Directory From Root Inside a Container

What happened: `.memory/knowledge/` was marked read-only with `chmod -R 444` to stop agents from writing to it. A direct test (`touch .memory/knowledge/permission-test.txt`) succeeded anyway, despite the directory's permission bits.

What was learned: the container's process runs as root, and Linux root holds `CAP_DAC_OVERRIDE` by default -- a capability that bypasses standard file-permission checks entirely. `chmod` looked like it was working (no error, correct-looking mode bits) but was never actually being enforced against the process that mattered. On a Windows-hosted bind mount, `chmod` has also been observed to actively corrupt permissions (making a directory fully inaccessible, failing even `stat`), not just fail silently.

How to apply it: never trust `chmod` alone as a real enforcement mechanism in this environment. Use `--cap-drop=DAC_OVERRIDE` on `docker run` to strip root's permission-bypass capability, and prefer Docker's own `:ro` bind mount for anything that must genuinely be read-only -- that's enforced at the mount layer itself, independent of in-container user or capability state. Verify any "read-only" claim with an actual write attempt, not by inspecting the mode bits.

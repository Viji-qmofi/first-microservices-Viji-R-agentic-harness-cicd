---
classification: internal
project: proj-lessons
doc_type: lesson
---

# Git Worktrees Break Inside Windows-Hosted Containers

What happened: while setting up parallel agent sessions (Module 1), git commands run *inside* a Docker container against a worktree created via Windows Command Prompt failed with a confusing "not a git repository" error -- even though the exact same worktree worked perfectly from a native Windows terminal or VS Code.

What was learned: a git worktree's `.git` file is a pointer back to the main repository. When the worktree is created on Windows, that pointer stores an absolute Windows-style path (`C:/Users/...`). That path is meaningless inside a Linux container's filesystem, so any `git` command run inside the container against that worktree fails to resolve it -- while the same worktree remains completely healthy from git's own perspective on the host.

How to apply it: keep all `git` operations (status, diff, add, commit, merge) on the Windows host, not inside the container, whenever a worktree was created via Windows Command Prompt. If a container genuinely needs to run git against a worktree, create the worktree from inside a container in the first place (mounting the common parent folder), so the `.git` pointer is born as a Linux-native path from the start.

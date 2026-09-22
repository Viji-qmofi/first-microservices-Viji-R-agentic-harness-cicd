---
classification: internal
project: proj-lessons
doc_type: lesson
---

# Git Identity Does Not Persist Across Fresh Containers

What happened: partway through an orchestrated agent session, a commit attempt failed because `user.name` and `user.email` came back empty -- despite git identity having been configured and working correctly in a previous container session on the same project.

What was learned: `/root/.gitconfig` lives inside the container's own ephemeral filesystem, not inside anything mounted from the host. Every fresh `docker run` starts with a blank one, so any `git config --global` command from an earlier session is gone the moment that container exits -- this is a completely different issue from git worktree paths breaking (a different lesson entirely), even though both involve git behaving unexpectedly inside a container.

How to apply it: don't re-run `git config --global user.name/user.email` by hand every session. Bake the identity directly into the Dockerfile with a `RUN git config --global user.name "..." && git config --global user.email "..."` step, so every container starts with working git identity already in place. This is safe to commit since the same name/email already appears in plain text on every commit's author line regardless.

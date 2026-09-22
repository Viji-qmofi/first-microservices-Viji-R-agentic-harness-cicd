FROM maven:3.9-eclipse-temurin-21

WORKDIR /workspace

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    # HuggingFace / Sentence Transformers cache inside the workspace so the
    # embedding model persists across container runs when /workspace is
    # bind-mounted, instead of re-downloading it every fresh container.
    HF_HOME=/workspace/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/workspace/.cache/sentence-transformers

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && apt-get install -y \
    curl \
    git \
    bash \
    ca-certificates \
    nano \
    procps \
    nodejs \
    python3 \
    python3-pip \
    build-essential \
    python3-dev \
    sqlite3 \
    jq \
    unzip \
    less \
    tree \
    lsof \
    make \
    && rm -rf /var/lib/apt/lists/*

# Python deps for the MCP servers (coursetools, storage, retrieval).
# mcp<2 is pinned deliberately: unpinned installs break coursetools_server.py's
# import (FastMCP renamed to MCPServer in mcp 2.x). Module 4.2-specific packages
# (aiosqlite, chromadb, scikit-learn, rank-bm25) are deferred -- add them when
# that lesson actually requires them, not before.
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Verify critical imports so the build fails fast on a bad package rather than
# surprising you at runtime.
RUN python3 -c "\
import fastmcp; \
import mcp; \
import starlette; \
import uvicorn; \
import sqlite_vec; \
import sentence_transformers; \
print('All MCP server imports OK')"

# Install Claude Code
RUN npm install -g @anthropic-ai/claude-code

# Install OpenCode
RUN npm install -g opencode-ai

# Verify Node tooling versions (non-fatal for version flags, fatal for missing binaries)
RUN node --version && \
    npm --version && \
    (claude --version 2>/dev/null || claude version 2>/dev/null || echo "claude installed (no --version flag)") && \
    (opencode --version 2>/dev/null || opencode version 2>/dev/null || echo "opencode installed (no --version flag)")

# Git identity for commits made inside the container
RUN git config --global user.name "viji-qmofi" && \
    git config --global user.email "vijiramu@gmail.com"

# Claude Code configuration: default settings + status line
RUN mkdir -p /root/.claude
COPY settings.json /root/.claude/settings.json
COPY statusline.sh /root/.claude/statusline.sh
RUN chmod +x /root/.claude/statusline.sh

# Agent/skill definitions copied into the image at build time -- this repo's
# convention (source in agents/skills at repo root, copied to /root/.claude/
# at build time), different from the live-discovery convention used in the
# original repo (.claude/agents/ read directly, no rebuild needed).
RUN mkdir -p /root/.claude/skills
COPY skills/ /root/.claude/skills/

RUN mkdir -p /root/.claude/agents
COPY agents/ /root/.claude/agents/

# Workspace content baked into the image so it also works without a bind mount.
# When /workspace IS bind-mounted at runtime (the normal case), these are
# shadowed by the host files -- the host copy wins, matching every other
# module's setup.
COPY mcp-servers/ /workspace/mcp-servers/
COPY scripts/ /workspace/scripts/
COPY docs/ /workspace/docs/
COPY eval/ /workspace/eval/
COPY schemas/ /workspace/schemas/
COPY CLAUDE.md /workspace/CLAUDE.md

# Expected workspace directory structure.
# .agents / .skills — per-role governance scope files (eval/test_policy.py reads these);
#                      not yet populated -- Module 4.1 lesson work.
# docs/adr           — Architecture Decision Records checked by eval tests; not yet created.
# logs               — where the *sample* Module 4 storage/retrieval servers write audit
#                       logs. Our real servers instead write to .memory/storage/, per
#                       STORAGE_DB_PATH/STORAGE_AUDIT_PATH set at `docker run`. Kept for
#                       compatibility with any Module 4 script that still expects logs/,
#                       until that's reconciled during the governance lesson.
# .memory/reference   — persistent agent memory (retrieval corpus), agent-writable.
RUN mkdir -p \
    /workspace/.agents \
    /workspace/.skills \
    /workspace/.memory/reference \
    /workspace/.cache/huggingface \
    /workspace/.cache/sentence-transformers \
    /workspace/docs/adr \
    /workspace/logs

# Copy entrypoint script -- handles Claude Code credential persistence across
# container restarts. (The new repo's own entrypoint only auto-registers
# Slack/Gmail MCP servers, which this project doesn't use -- not carried over.)
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Shell quality-of-life improvements
RUN echo 'export PS1="ai-course:\w# "' >> /root/.bashrc && \
    echo 'alias ll="ls -alF"' >> /root/.bashrc && \
    echo 'alias la="ls -A"' >> /root/.bashrc && \
    echo 'alias l="ls -CF"' >> /root/.bashrc && \
    echo 'alias mci="mvn clean install"' >> /root/.bashrc && \
    echo 'alias python="python3"' >> /root/.bashrc && \
    echo 'alias pip="pip3"' >> /root/.bashrc && \
    echo 'alias ports="lsof -i -P -n"' >> /root/.bashrc && \
    echo 'alias mcp-servers="find /workspace/mcp-servers -maxdepth 3 -type f | sort"' >> /root/.bashrc

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["/bin/bash"]

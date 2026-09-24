# run-agent.ps1: launch a subagent container with only the permissions its
# governance policy allows. Pass the role name as the first argument.
#
# Usage: .\scripts\run-agent.ps1 <role-name> [command...]
# Roles: planner, implementer, reviewer, spring-boot-reviewer, orchestrator
#
# Adaptation note: unlike the Module 4 sandbox's reference version, this
# script does not mount a separate named "memory" volume. .memory/ has
# always lived inside /workspace in this project, not as a separate volume
# -- so workspace read/write access IS this project's memory-access
# dimension, not an independent second one. The fine-grained protection for
# .memory/'s sensitive subdirectories lives at the MCP layer (coursetools'
# path-block, and the storage/retrieval allow-lists), not at the container
# mount level. See docs/governance-policy.md for the full reasoning.
#
# This script's real, honest purpose is Layer 1 verification evidence: it
# proves what a role's filesystem boundaries would be if it ran standalone.
# In day-to-day use, planner/implementer/reviewer/spring-boot-reviewer run
# as Claude Code subagents inside the Orchestrator's own single container,
# not in separate containers of their own -- Layer 2 (MCP allow-lists) is
# what actually constrains them as they really run.

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Role,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ExtraArgs
)

$ErrorActionPreference = 'Stop'

$Image = if ($env:AGENT_IMAGE) { $env:AGENT_IMAGE } else { 'ecom-agent-sandbox' }
$WorkspaceMode = 'ro'

switch ($Role) {
    { $_ -in 'implementer', 'orchestrator' } {
        $WorkspaceMode = 'rw'
    }
    { $_ -in 'planner', 'reviewer', 'spring-boot-reviewer', 'decision-auditor' } {
        $WorkspaceMode = 'ro'
    }
    default {
        Write-Error "Unknown role: $Role"
        Write-Error "This role has no policy entry, so it cannot be launched."
        exit 1
    }
}

$CurDir = (Get-Location).Path -replace '\\', '/'

$DockerArgs = @(
    'run', '--rm', '-it',
    '--cap-drop=DAC_OVERRIDE',
    '--network', 'agent-internal',
    '-p', '8001:8001', '-p', '8002:8002', '-p', '6274:6274', '-p', '6277:6277',
    '-v', "${CurDir}:/workspace:${WorkspaceMode}",
    # .memory/knowledge stays read-only regardless of the role's overall
    # workspace mode -- this is what actually enforces "read-only to agents"
    # for knowledge files, established since Module 2.
    '-v', "${CurDir}/.memory/knowledge:/workspace/.memory/knowledge:ro",
    '-v', 'claude-auth:/root/.claude',
    '-e', 'ANTHROPIC_API_KEY',
    '-e', 'COURSETOOLS_ROOT=/workspace',
    '-e', 'STORAGE_DB_PATH=/workspace/.memory/storage/storage.db',
    '-e', 'STORAGE_AUDIT_PATH=/workspace/.memory/storage/storage-audit.log',
    '-e', 'RETRIEVAL_REFERENCE_DIR=/workspace/.memory/reference',
    '-e', "AGENT_ROLE=$Role"
)

$DockerArgs += $Image
if ($ExtraArgs) {
    $DockerArgs += $ExtraArgs
}

Write-Host "Launching '$Role': workspace=$WorkspaceMode"

& docker $DockerArgs

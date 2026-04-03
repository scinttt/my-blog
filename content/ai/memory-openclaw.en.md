+++
date = '2026-02-18T02:03:38-05:00'
title = 'How to make your agent smart as openclaw'
summary = "Provides a practical guide to implementing a persistent memory system for AI coding agents, advocating for a simplified, file-based approach with a manual '/save' command to capture session context, delivering most of the value with minimal complexity."
tags = ['Tech', 'AI', 'Agent', 'Open Source', 'Memory']
+++
*What I learned from OpenClaw's memory architecture and how I built a lightweight version in OpenCode.*

---

## The Problem

AI coding agents are stateless. Every new session starts from zero — you re-explain your project structure, tech stack, and decisions. For ongoing projects, this is a real productivity killer.

## How OpenClaw Does It

OpenClaw uses plain Markdown files as memory:

- **SOUL.md** — AI personality and behavior rules
- **USER.md** — User profile and preferences
- **MEMORY.md** — Curated long-term memory
- **memory/YYYY-MM-DD.md** — Daily raw session logs

The key innovation is **self-maintenance**: the AI periodically reviews daily logs, extracts valuable info into MEMORY.md, and cleans up stale entries. Before context compaction (when sessions get too long), it triggers a silent "memory flush" to save important facts before they're lost.

This creates a natural hierarchy: daily logs as short-term memory, MEMORY.md as mid-term, and USER.md/SOUL.md as permanent identity.

## My Simplified Version for OpenCode

OpenClaw's full system includes vector embeddings, hybrid search, and automatic heartbeats — overkill for an interactive coding agent. My key insight: **you don't need daily logs**. OpenCode keeps the full conversation in context, so just summarize directly to MEMORY.md at session end.

### The Setup

```
project/
├── AGENTS.md      # includes "read MEMORY.md on session start"
├── MEMORY.md      # project-specific decisions and progress
└── ...

~/.config/opencode/
└── opencode.json  # /save command registered here
```

**MEMORY.md** lives in each project root — technical decisions, progress, architecture notes.

**USER.md** is global (one copy), maintained by a custom MCP server — user preferences that apply across all projects.

### The `/save` Command

```json
{
  "command": {
    "save": {
      "description": "Summarize session to project memory",
      "template": "Review our entire conversation. Do the following:\n1. Read MEMORY.md if it exists\n2. Append new key decisions, technical findings, bugs resolved, and progress\n3. Remove outdated or superseded entries\n4. Keep MEMORY.md under 200 lines\n5. Never store secrets or tokens"
    }
  }
}
```

End of session → type `/save` → AI reviews conversation → updates MEMORY.md → next session picks up where you left off.

### Why No Global Memory?

I initially designed a GLOBAL_MEMORY.md to aggregate across sub-projects, with a `/sync-memory` command. I dropped it — cross-project references are rare, and when needed, you can just tell the AI to read another project's MEMORY.md directly. Don't over-engineer.

## Lessons Learned

**Start simple.** A single MEMORY.md with a manual `/save` captures 80% of the value of a full memory system.

**Files beat databases.** Markdown is human-readable, git-trackable, and the AI can read/write it with built-in tools. No infrastructure needed.

**Manual triggers beat automatic ones.** Instructions like "automatically update memory during conversation" don't work reliably — the AI forgets. An explicit `/save` command is dependable.

**The biggest gap is zero-to-one.** The difference between "no memory" and "basic memory" is massive. The difference between "basic" and "sophisticated" is marginal. Ship simple first.
# Installation and platform mapping

## With the Skills CLI

Run from the target project. The Skills CLI requires Node.js 22.20 or later.

```sh
npx skills add janbam/crux-curiosity-skill --skill crux-curiosity
```

Select the clients that should discover it. The tool can install for more than one client. [Skills CLI installation reference](https://github.com/vercel-labs/skills#install-a-skill)

## Manual installation

Clone the public repository.

```sh
git clone https://github.com/janbam/crux-curiosity-skill.git crux-curiosity
```

For a reproducible install, add `--branch <published-tag> --single-branch` to the clone command and use that checkout below.

The installable directory is named `crux-curiosity`. Use the source checkout path in the examples and run from the **target research workspace**, where the host should find the skill. Choose one location per host to avoid duplicate discovery. Install into a new destination. For upgrades, review the new bundle and replace the previously installed copy deliberately.

## OpenAI Codex

Codex discovers repository and user skills in `.agents/skills/`. For a project-local install:

```sh
cc_src=/absolute/path/to/crux-curiosity
cc_dest=.agents/skills/crux-curiosity
test ! -e "$cc_dest" && mkdir -p "$cc_dest" &&
  cp "$cc_src/SKILL.md" "$cc_src/LICENSE" "$cc_dest/" &&
  cp -R "$cc_src/references" "$cc_dest/"
```

For a personal install use `~/.agents/skills/crux-curiosity` as the destination. Open a session in the target project and select `$crux-curiosity`, or use that name in the prompt. Project discovery in a particular session can depend on workspace and trust settings. Check for duplicate installed names if you see multiple entries. [Codex skill discovery](https://learn.chatgpt.com/docs/build-skills)

For delegation, use the session's native spawn, message/follow-up, wait, cancel and close tools where exposed. Request fresh context and pass only the worker packet. Check actual tool schema and concurrency limits. Current documentation describes `agents.enabled` and `agents.max_concurrent_threads_per_session`, with the legacy `agents.max_threads` alias. Avoid changing global configuration to work around a per-session restriction. [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)

## Claude Code

Use the native project skill directory:

```sh
cc_src=/absolute/path/to/crux-curiosity
cc_dest=.claude/skills/crux-curiosity
test ! -e "$cc_dest" && mkdir -p "$cc_dest" &&
  cp "$cc_src/SKILL.md" "$cc_src/LICENSE" "$cc_dest/" &&
  cp -R "$cc_src/references" "$cc_dest/"
```

For a personal install use `~/.claude/skills/crux-curiosity`. Invoke `/crux-curiosity` with the task and options. The core runs in the main session so it can coordinate optional research stages. [Claude Code skills](https://code.claude.com/docs/en/skills)

Use native non-fork Agent subagents for the initial role assignments. The exposed tool may be called Agent or Task depending on the surface and version. If you define custom subagents, choose model inheritance or an authorized model override and the least tools needed for each role. Do not preload the entire skill unless the worker needs it. Use returned messages or protected storage to stage findings before cross-review. When resumption or messaging is unavailable, the coordinator can route a separate targeted review and describe what actually ran. [Claude Code subagents](https://code.claude.com/docs/en/sub-agents)

## Other hosts and manual use

Copy the same named directory into the host's Agent Skills discovery root. If the host can read files but lacks discovery, explicitly ask it to read `SKILL.md` and the references it calls for. This uses the workflow without native discovery. Map capability names to the host's available tools and policy, including retrieval, fresh worker sessions, communication, shell and durable state. The [Agent Skills specification](https://agentskills.io/specification) defines the bundle format.

Confirm the host discovers the skill and has the permissions and tools relevant to your task. Native discovery, real worker execution and experimental isolation are separate capabilities. See the [pilot results](evaluation/results.md) for tested versions and limits.

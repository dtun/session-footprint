# AGENTS.md

Guidance for any agent working in this repository.

## What this repo is

A single agent skill, `session-footprint`, distributed in the open `SKILL.md` format. It
estimates the environmental footprint (energy, water, tree-equivalents) of an agent session
from its token usage. It is **harness-agnostic** — it must read and run the same in any
agent, not just one tool.

- The skill lives in [`skills/session-footprint/`](skills/session-footprint/). `SKILL.md`
  is the entry point; [`footprint.py`](skills/session-footprint/footprint.py) is the
  self-contained, stdlib-only converter it runs.
- Version and author live in the `SKILL.md` frontmatter (`metadata.version`). Keep that in
  sync with [`CHANGELOG.md`](CHANGELOG.md) and the git tag on release.

## Conventions

- **Keep it harness-agnostic.** The contract is three token counts in → a footprint out.
  Don't make the core depend on one harness's paths, tool names, or transcript layout.
  Transcript parsing and location auto-detection are *conveniences* layered on top
  (`--transcript`, `KNOWN_TRANSCRIPT_GLOBS`) — never the only way in. The inline formula in
  `SKILL.md` must stay sufficient to compute by hand, with no script at all.
- **The conversion factors are the contract.** They live as cited constants at the top of
  `footprint.py` and are the single source of truth. The formula and table in `SKILL.md`
  and the example in `README.md` mirror them — keep all in sync when a factor changes.
- **Never present the numbers as precise.** They are order-of-magnitude estimates. Any
  output must carry the factors and the disclaimer line. Don't strip them for brevity.
- **The skill is read-only.** It reads counts (or a transcript), computes, and prints. It
  never edits the working tree, touches git, or sends data anywhere. Preserve that.
- **No third-party dependencies.** `footprint.py` is Python stdlib only, so it runs
  anywhere `python3` exists.
- **Work in [Conventional Commits](https://www.conventionalcommits.org/)** — discrete,
  well-scoped commits. Don't force-push or amend without asking.

# Changelog

All notable changes to this skill are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The released version is mirrored in the `metadata.version` field of
[`skills/session-footprint/SKILL.md`](skills/session-footprint/SKILL.md).

## [Unreleased]

## [0.1.0] — 2026-06-14

Initial release.

### Added

- `session-footprint` skill: convert a session's token usage (output / input /
  cached) into an estimated environmental footprint — energy (Wh), water (L),
  and tree-equivalents. Harness-agnostic: the contract is three token counts in,
  a footprint out, and the inline formula in `SKILL.md` computes by hand with no
  script at all.
- [`footprint.py`](skills/session-footprint/footprint.py) — self-contained,
  stdlib-only converter. Takes token counts (`--output/--input/--cached`); as a
  convenience also parses an Anthropic-style JSONL transcript (`--transcript`) or
  scans known locations. Supports `--json`.
- Baked-in, cited conversion factors (Google 2025 AI-inference report; Li et al.,
  *Making AI Less Thirsty*, 2023; Ember Global Electricity Review 2024; US EPA
  tree-sequestration figures), printed alongside every result with a disclaimer.

[Unreleased]: https://github.com/dtun/session-footprint/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dtun/session-footprint/releases/tag/v0.1.0

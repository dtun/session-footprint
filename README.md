# session-footprint

A harness-agnostic agent skill that estimates the **environmental** footprint of a session — energy, water, and tree-equivalents — from its token usage, and prints it as a small receipt.

> Most usage meters report **dollars**. This one reports **water, energy, and trees**.
> It is read-only and harness-neutral: give it token counts, it prints. It never edits files, touches git, or sends data anywhere.

## The idea

A session's cost lives in three token counts — **output** (generated), **input** (prefill), and **cached**. Multiply each by a published per-token energy estimate, then convert that energy into:

- **Energy** (Wh) — the foundation everything else is derived from.
- **Water** (L) — datacenter cooling (WUE) plus the water used to generate the electricity (EWIF).
- **Tree-equivalents** — the span of one tree's annual CO₂ uptake needed to offset the session.

"Deforestation" has no direct datacenter mechanism, so it's framed honestly as tree-equivalents rather than implying literal logging.

## Harness-agnostic by design

The conversion is pure arithmetic over three numbers, so it runs the same under any agent. Only *getting* the token counts is harness-specific, and that step is delegated to the running agent (a usage command, a usage API, or a transcript). The math — and the formula — live in [`SKILL.md`](skills/session-footprint/SKILL.md), so an agent can compute by hand even without the script.

## The honest caveat

**These are order-of-magnitude estimates, not measurements.** Providers publish no per-token water or energy figures, so the skill leans on datacenter averages and inference-energy research that carry easily 5–10× uncertainty. Every run prints its factors and a disclaimer next to the numbers. The point is to *inform a sense of scale*, not to audit.

## Usage

```bash
# Harness-agnostic core — pass the three counts:
python3 skills/session-footprint/footprint.py --output 43903 --input 9726 --cached 1130807

# Convenience — parse / find an Anthropic-style JSONL transcript:
python3 skills/session-footprint/footprint.py --transcript path/to/session.jsonl
python3 skills/session-footprint/footprint.py            # scan known locations
python3 skills/session-footprint/footprint.py --json     # machine-readable
```

### Example

```
==============================================
        SESSION ENVIRONMENTAL FOOTPRINT
==============================================
  output tok                            43,903
  input tok                              9,726
  cached tok                         1,130,807
----------------------------------------------
  ENERGY                              88.36 Wh
                           ~7.36 phone charges
  WATER                               159.0 mL
                               ~31.8 teaspoons
  TREES                        16.6 tree-hours
            what one tree offsets in that time
==============================================
```

## Files

| File | Role |
|------|------|
| [`skills/session-footprint/SKILL.md`](skills/session-footprint/SKILL.md) | Entry point — the 3 steps (get counts → compute → present), the inline formula, and the cited factor table. |
| [`skills/session-footprint/footprint.py`](skills/session-footprint/footprint.py) | Self-contained, stdlib-only converter. Token counts in, receipt out. The factors at the top are the single source of truth. |

## Install

Copy the skill directory into your agent's skills location — for example:

```bash
cp -R skills/session-footprint ~/.agents/skills/session-footprint
```

Then invoke with `/session-footprint`, or run `footprint.py` directly.

## Updating the factors

The estimates are mid-2026 figures. When better public numbers land, edit the constants at the top of `footprint.py` (the single source of truth), mirror them in the `SKILL.md` formula + table, and bump `metadata.version` in `SKILL.md` and `CHANGELOG.md`.

## License

MIT © Danny Tunney

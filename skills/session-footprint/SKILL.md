---
name: session-footprint
description: Estimate the environmental footprint — water, energy, and tree-equivalents — of an agent session from its token usage. Use when the user asks how much water/energy/carbon their session "cost," wants the environmental (not monetary) impact of their LLM usage, or asks for an eco-receipt of the session.
argument-hint: "[--output N --input N --cached N] | [--transcript <path>]"
license: MIT
metadata:
  author: Danny Tunney
  version: "0.1.0"
---

# Session Footprint

Turn a session's token usage into an **environmental** estimate — energy (Wh), water (L), and tree-equivalents — instead of dollars, and present it as a small receipt.

**This is an estimate, not a measurement.** Providers publish no per-token water or energy figures, so this leans on datacenter averages and inference-energy research. The factors carry easily 5–10× uncertainty. Always print the factors and the disclaimer next to the numbers — never present them as precise.

## Step 1 — Get this session's token counts

Obtain three numbers for the current session, however your harness exposes usage:

- **output** — tokens the model generated (the dominant cost)
- **input** — fresh prompt tokens (prefill)
- **cached** — cached prompt tokens, reads + writes (cheap per token, but usually the largest count)

Where these come from depends on the harness — a usage/cost command, a usage API, or a transcript file. If your harness writes an **Anthropic-style JSONL transcript** (one `message.usage` object per assistant turn — the format Claude Code and several others use), the bundled script can sum it for you (Step 2).

## Step 2 — Compute

Run the bundled, stdlib-only script with the counts:

```bash
python3 footprint.py --output <N> --input <N> --cached <N>
```

Or let it parse / find a transcript (convenience, harness-specific):

```bash
python3 footprint.py --transcript <path>   # parse a specific JSONL
python3 footprint.py                        # scan known locations, use most recent
python3 footprint.py --json                 # machine-readable
```

**No script? Do the arithmetic directly** — it's deliberately simple:

```
energy_Wh = output*0.0012 + input*0.00018 + cached*0.00003
energy_kWh = energy_Wh / 1000
water_L    = energy_kWh * 1.8
co2_g      = energy_kWh * 450
tree_years = (co2_g / 1000) / 21      # → ×525600 for tree-minutes, etc.
```

## Step 3 — Present

Show the receipt verbatim (or render the numbers yourself), then add one plain-language sentence of scale (e.g. "≈ N phone charges"). Keep the factors line and the "+/- a lot, informs not measures" disclaimer. Do **not** restate the numbers as exact.

## The factors (baked-in, cited)

| Quantity | Value | Source |
|----------|-------|--------|
| Energy / output token | ~0.0012 Wh | Anchored to ~0.24–0.34 Wh per median reply (Google 2025 AI-inference report; Altman, *The Gentle Singularity*, 2025), scaled for a large frontier model |
| Energy / input token | ~0.00018 Wh | parallel prefill, cheaper than decode |
| Energy / cached token | ~0.00003 Wh | reuses computed KV state |
| Water | ~1.8 L / kWh | on-site cooling (WUE, Google Env. Report 2024) + off-site generation (EWIF); framework: Li et al., *Making AI Less Thirsty*, 2023 |
| Carbon | ~450 gCO₂ / kWh | between 2024 global (~480) and US (~370) averages — Ember Global Electricity Review 2024 / IEA |
| Tree | ~21 kg CO₂ / tree / year | a mature tree's annual uptake — US EPA / arborday.org |

"Deforestation" has no direct datacenter mechanism, so it is expressed honestly as **tree-equivalents**: the span of one tree's annual CO₂ uptake that would offset the session's emissions.

## Updating the factors

The constants at the top of `footprint.py` are the single source of truth; the formula and table here mirror them. The energy-per-*cached*-token figure is the shakiest and swings the result most in long sessions — tune it first as better public data appears. When you change a factor, update the formula above, this table, and bump `metadata.version` here and in `CHANGELOG.md`.

## Adding a harness to auto-detect

`footprint.py`'s `KNOWN_TRANSCRIPT_GLOBS` lists where to look for transcripts when no counts are passed. It ships with the Claude Code location; add a glob for any other harness that writes the same JSONL shape.

#!/usr/bin/env python3
"""Estimate the environmental footprint of an LLM agent session.

Harness-agnostic. The core is pure arithmetic over token counts, so it runs the
same under any agent or harness. Give it token counts directly:

    python3 footprint.py --output 43903 --input 9726 --cached 1130807

Or, as a convenience, let it parse an Anthropic-style JSONL transcript (the
format Claude Code and several other harnesses write):

    python3 footprint.py --transcript /path/to/session.jsonl

With no token flags and no --transcript, it falls back to scanning a few known
transcript locations and uses the most recent one — a convenience, not the
contract. Add --json for machine-readable output.

Every factor below is a baked-in, cited, mid-range public estimate. They carry
easily 5-10x uncertainty. They inform a sense of scale; they do not measure.
"""

import argparse
import glob
import json
import os
import sys

# --------------------------------------------------------------------------
# Conversion factors — baked-in mid-range public estimates, each cited.
# Anthropic (and most providers) publish no per-token figures, so this leans on
# datacenter averages and inference-energy research. Order-of-magnitude only.
# --------------------------------------------------------------------------

# Energy per token (Wh). Output tokens are generated one-at-a-time (autoregressive
# decode) and dominate inference energy; fresh input (prefill) runs in parallel and
# is cheaper per token; cached tokens reuse already-computed KV state and are
# cheaper still. Anchored to ~0.24-0.34 Wh per median assistant reply
# (Google "Measuring the environmental impact of AI inference," 2025; S. Altman,
# "The Gentle Singularity," 2025), scaled up for a large frontier model.
WH_PER_OUTPUT_TOKEN = 0.0012
WH_PER_INPUT_TOKEN = 0.00018
WH_PER_CACHED_TOKEN = 0.00003

# Water intensity (liters per kWh) = on-site cooling (WUE) + off-site water used
# to generate the electricity (EWIF). Google 2023 fleet-wide WUE ~1.1 L/kWh
# (Google Environmental Report 2024); off-site EWIF ~0.7 L/kWh.
# Framework: Li et al., "Making AI Less Thirsty," 2023.
LITERS_PER_KWH = 1.8

# Grid carbon intensity (gCO2 per kWh). Between the 2024 global average (~480)
# and the US average (~370). Source: Ember Global Electricity Review 2024 / IEA.
G_CO2_PER_KWH = 450.0

# Tree sequestration (kg CO2 absorbed per mature tree per year).
# Source: US EPA / arborday.org (a mature tree absorbs ~21-22 kg CO2/yr).
KG_CO2_PER_TREE_YEAR = 21.0

# Known transcript locations to scan as a last-resort convenience. Harness-
# specific; extend as you adopt new harnesses. Each entry is a glob of JSONL
# files in the Anthropic message format (one usage object per assistant turn).
KNOWN_TRANSCRIPT_GLOBS = [
    "~/.claude/projects/*/*.jsonl",  # Claude Code
]

FACTORS_NOTE = [
    "output token  ~ {:.4f} Wh   input ~ {:.5f} Wh   cached ~ {:.5f} Wh".format(
        WH_PER_OUTPUT_TOKEN, WH_PER_INPUT_TOKEN, WH_PER_CACHED_TOKEN
    ),
    "water         ~ {:.1f} L / kWh  (on-site WUE + off-site EWIF)".format(LITERS_PER_KWH),
    "carbon        ~ {:.0f} gCO2 / kWh".format(G_CO2_PER_KWH),
    "tree          ~ {:.0f} kg CO2 absorbed / tree / year".format(KG_CO2_PER_TREE_YEAR),
]


def find_known_transcript():
    """Most recently modified JSONL across known harness locations, or None."""
    candidates = []
    for pattern in KNOWN_TRANSCRIPT_GLOBS:
        candidates.extend(glob.glob(os.path.expanduser(pattern)))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def collect_usage(path):
    """Sum token usage across every assistant turn in an Anthropic-style JSONL."""
    totals = {"output": 0, "input": 0, "cached": 0, "turns": 0, "models": set()}
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = obj.get("message")
            if not isinstance(msg, dict):
                continue
            usage = msg.get("usage")
            if not isinstance(usage, dict):
                continue
            totals["turns"] += 1
            if msg.get("model"):
                totals["models"].add(msg["model"])
            totals["output"] += usage.get("output_tokens") or 0
            totals["input"] += usage.get("input_tokens") or 0
            totals["cached"] += (usage.get("cache_read_input_tokens") or 0) + (
                usage.get("cache_creation_input_tokens") or 0
            )
    totals["models"] = sorted(totals["models"])
    return totals


def compute(output, input_, cached):
    energy_wh = (
        output * WH_PER_OUTPUT_TOKEN
        + input_ * WH_PER_INPUT_TOKEN
        + cached * WH_PER_CACHED_TOKEN
    )
    energy_kwh = energy_wh / 1000.0
    water_l = energy_kwh * LITERS_PER_KWH
    co2_g = energy_kwh * G_CO2_PER_KWH
    tree_years = (co2_g / 1000.0) / KG_CO2_PER_TREE_YEAR
    return {"energy_wh": energy_wh, "water_l": water_l, "co2_g": co2_g, "tree_years": tree_years}


def fmt_water(liters):
    if liters < 1:
        ml = liters * 1000
        return "{:.1f} mL".format(ml), "~{:.1f} teaspoons".format(ml / 5.0)
    return "{:.2f} L".format(liters), "~{:.1f} x 500mL bottles".format(liters / 0.5)


def fmt_energy(wh):
    led_min = wh / 10.0 * 60.0
    phones = wh / 12.0  # a full smartphone charge ~12 Wh
    compare = "~{:.2f} phone charges".format(phones) if phones >= 0.1 else "~{:.0f} min of a 10W LED bulb".format(led_min)
    if wh < 1:
        return "{:.0f} mWh".format(wh * 1000), compare
    return "{:.2f} Wh".format(wh), compare


def fmt_trees(tree_years):
    minutes = tree_years * 365 * 24 * 60
    if minutes < 90:
        return "{:.0f} tree-minutes".format(minutes), "what one tree offsets in that time"
    hours = minutes / 60
    if hours < 48:
        return "{:.1f} tree-hours".format(hours), "what one tree offsets in that time"
    return "{:.2f} tree-days".format(hours / 24), "what one tree offsets in that time"


def render(totals, result, source):
    water_main, water_cmp = fmt_water(result["water_l"])
    energy_main, energy_cmp = fmt_energy(result["energy_wh"])
    tree_main, tree_cmp = fmt_trees(result["tree_years"])

    W = 46
    line = "=" * W
    thin = "-" * W

    def row(label, value):
        return "  {:<14}{:>{w}}".format(label, value, w=W - 16)

    L = [line, "  SESSION ENVIRONMENTAL FOOTPRINT".center(W), line]
    if totals.get("turns"):
        L.append(row("turns", str(totals["turns"])))
    L.append(row("output tok", "{:,}".format(totals["output"])))
    L.append(row("input tok", "{:,}".format(totals["input"])))
    L.append(row("cached tok", "{:,}".format(totals["cached"])))
    L.append(thin)
    L.append(row("ENERGY", energy_main))
    L.append("  {:>{w}}".format(energy_cmp, w=W - 2))
    L.append(row("WATER", water_main))
    L.append("  {:>{w}}".format(water_cmp, w=W - 2))
    L.append(row("TREES", tree_main))
    L.append("  {:>{w}}".format(tree_cmp, w=W - 2))
    L.append(line)
    L.append("  rough estimate -- see factors below")
    L.append("  +/- a lot. informs, does not measure.")
    L.append(line)
    L.append("  factors:")
    for f in FACTORS_NOTE:
        L.append("    " + f)
    L.append("  src: Google 2025 AI-inference report; Li et al.")
    L.append("       'Making AI Less Thirsty' 2023; Ember 2024;")
    L.append("       US EPA tree-sequestration figures.")
    if source:
        L.append("  source: " + source)
    L.append(line)
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Estimate an agent session's environmental footprint.")
    ap.add_argument("-o", "--output", type=int, help="output (generated) token count")
    ap.add_argument("-i", "--input", type=int, help="fresh input (prefill) token count")
    ap.add_argument("-c", "--cached", type=int, help="cached token count (reads + writes)")
    ap.add_argument("--transcript", help="parse an Anthropic-style JSONL transcript instead")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of the receipt")
    args = ap.parse_args(argv)

    manual = any(v is not None for v in (args.output, args.input, args.cached))
    source = None

    if manual:
        totals = {"output": args.output or 0, "input": args.input or 0, "cached": args.cached or 0,
                  "turns": 0, "models": []}
    else:
        path = args.transcript or find_known_transcript()
        if not path or not os.path.exists(path):
            ap.error("no token counts given and no transcript found — "
                     "pass --output/--input/--cached, or --transcript PATH")
        totals = collect_usage(path)
        source = os.path.basename(path)

    result = compute(totals["output"], totals["input"], totals["cached"])

    if args.json:
        print(json.dumps({
            "source": source,
            "tokens": {k: totals[k] for k in ("output", "input", "cached")},
            "turns": totals.get("turns", 0),
            "models": totals.get("models", []),
            "estimate": result,
        }, indent=2))
    else:
        print(render(totals, result, source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

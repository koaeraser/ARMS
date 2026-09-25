#!/usr/bin/env python3
"""Measure the prose style of a LaTeX file against a house-voice reference.

Usage: style_metrics.py <file.tex> [--ref <exemplar.tex>] [--json]
                        [--gate] [--genre default|results] [--sections]
                        [--include-appendix]

Only main-text prose paragraphs are measured. The preamble, comments,
\\iffalse blocks, float/display-math/listing environments, theorem-like
statements and proofs are removed; the text after \\appendix or the
bibliography is ignored unless --include-appendix is given. Section and
paragraph titles, labels and list markers are stripped, so a paragraph that
opens with \\paragraph{...}, \\item[...] or \\citet{...} is still measured.
Inline math and macros collapse to a single token; numbers inside them are
still counted (except in \\ref, \\cite, \\label and similar keys).

--ref       calibrate to your own exemplar paper. The exemplar is measured
            and the gate bands are derived from it (see derive_bands). Without
            --ref, the default bands and reference values apply; they were
            calibrated on an exemplar Statistical Science methods paper
            (see ../SKILL.md, "Measured style gate").
--gate      compare the target against the bands; print PASS/FAIL per band
            and exit 2 if any band fails.
--genre     'results' applies the documented relaxation of the two number
            bands (results-heavy papers: simulation studies, tutorials).
--sections  also print the metrics for every \\section of the target, so a
            writer can self-check section by section.
--json      print the same result as JSON.
"""
import json
import os
import re
import sys

ENVS = (r"table|figure|equation|align|alignat|gather|multline|eqnarray|lstlisting|verbatim|"
        r"tabular|tabularx|algorithm|algorithmic|tikzpicture|longtable|threeparttable|"
        r"proposition|lemma|theorem|thm|corollary|definition|remark|proof|assumption|example")
BR = r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}"          # balanced braces, 3 levels
NUM = re.compile(r"\d+\.\d+|\b\d{2,}\b")
KEYS = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref|label|cite[a-zA-Z]*|url|href|input|include)\*?"
                  r"(?:\[[^\]]*\])*" + BR)

# Reference values of the default exemplar (an exemplar Statistical Science
# methods paper: 82 paragraphs, 433 sentences, 8,227 prose words). The exemplar
# itself is not distributed; pass your own with --ref.
DEFAULT_REFERENCE = {
    "file": "(default exemplar: Statistical Science methods paper)",
    "paragraphs": 82,
    "prose_words": 8227,
    "sentences_per_paragraph": 5.3,
    "mean_sentence_words": 19.0,
    "pct_sentences_over_45": 1.8,
    "numbers_per_1k": 8.0,
    "pct_sentences_over_3_numbers": 1.2,
    "max_numbers_per_sentence": 6,
    "we_per_1k": 11.4,
    "which_per_1k": 2.7,
    "semicolons_per_1k": 2.8,
}

# Default bands, calibrated on the default exemplar (see SKILL.md).
# (metric, op, default limit, results-genre limit)
BANDS = [
    ("mean_sentence_words",          "range", (17.0, 24.0), (17.0, 24.0)),
    ("pct_sentences_over_45",        "max",   5.0,          5.0),
    ("sentences_per_paragraph",      "range", (4.0, 7.0),   (4.0, 7.0)),
    ("we_per_1k",                    "min",   7.0,          7.0),
    ("semicolons_per_1k",            "max",   3.5,          3.5),
    ("numbers_per_1k",               "max",   10.0,         15.0),
    ("pct_sentences_over_3_numbers", "max",   2.0,          5.0),
]

# Rules that turn a user-supplied exemplar into bands. The multipliers
# reproduce the default bands (to rounding) when applied to the default
# exemplar's values; the floors keep a "max" band from collapsing to zero when
# the exemplar happens to contain none of a feature.
# metric: (op, default rule, results-genre rule); a rule is (multiplier, floor)
# for "max"/"min" and (low mult, high mult) for "range".
DERIVE = {
    "mean_sentence_words":          ("range", (0.90, 1.25), (0.90, 1.25)),
    "pct_sentences_over_45":        ("max",   (2.8, 3.0),   (2.8, 3.0)),
    "sentences_per_paragraph":      ("range", (0.75, 1.32), (0.75, 1.32)),
    "we_per_1k":                    ("min",   (0.6, 0.0),   (0.6, 0.0)),
    "semicolons_per_1k":            ("max",   (1.25, 1.0),  (1.25, 1.0)),
    "numbers_per_1k":               ("max",   (1.25, 3.0),  (1.9, 5.0)),
    "pct_sentences_over_3_numbers": ("max",   (1.7, 1.0),   (4.2, 3.0)),
}


def derive_bands(ref):
    """Bands derived from a measured exemplar, in the same shape as BANDS."""
    out = []
    for key, _, _, _ in BANDS:
        op, rule_d, rule_r = DERIVE[key]
        v = ref.get(key)
        lims = []
        for rule in (rule_d, rule_r):
            if op == "range":
                lims.append((round(rule[0] * v, 1), round(rule[1] * v, 1)))
            elif op == "max":
                lims.append(round(max(rule[0] * v, rule[1]), 1))
            else:
                lims.append(round(rule[0] * v, 1))
        out.append((key, op, lims[0], lims[1]))
    return out


def body(s, include_appendix=False):
    s = re.sub(r"(?<!\\)%.*", "", s)
    m = re.search(r"\\begin\{document\}", s)
    if m:
        s = s[m.end():]
    ends = [r"\\end\{document\}", r"\\bibliography\{", r"\\begin\{thebibliography\}"]
    if not include_appendix:
        ends += [r"\\appendix\b", r"\\section\*?\{(?:Appendix|Supplementary)"]
    cut = [m.start() for e in ends for m in [re.search(e, s)] if m]
    if cut:
        s = s[:min(cut)]
    s = re.sub(r"\\iffalse\b.*?\\fi\b", "", s, flags=re.S)
    return s


def clean(s):
    s = re.sub(r"\\begin\{(%s)\*?\}.*?\\end\{\1\*?\}" % ENVS, "", s, flags=re.S)
    s = re.sub(r"\\\[.*?\\\]", "", s, flags=re.S)
    s = re.sub(r"\$\$.*?\$\$", "", s, flags=re.S)
    # structural markup: titles, labels, list markers, environment delimiters
    s = re.sub(r"\\(?:sub)*section\*?(?:\[[^\]]*\])?" + BR, "\n\n", s)
    s = re.sub(r"\\(?:sub)?paragraph\*?" + BR, "", s)
    s = re.sub(r"\\label" + BR, "", s)
    s = re.sub(r"\\(?:begin|end)\{[a-zA-Z*]+\}(?:\[[^\]]*\])*(?:" + BR + ")?", "", s)
    s = re.sub(r"\\item(?:\[[^\]]*\])?", "", s)
    return s


def collapse(p):
    """Return (text with math/macros as single tokens, numbers as '#')."""
    p = KEYS.sub("X", p)
    p = re.sub(r"\$[^$]*\$", lambda m: "X" + "#" * len(NUM.findall(m.group(0))), p)
    p = NUM.sub("#", p)
    for _ in range(3):
        p = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?\{([^{}]*)\}",
                   lambda m: "X" + "#" * m.group(2).count("#"), p)
    return p


def measure(text, label):
    paras = []
    for p in re.split(r"\n\s*\n", text):
        p = re.sub(r"^\s*(\\[a-zA-Z]+\*?(?![a-zA-Z{\[])\s*)+", "", p)   # \noindent, \small ...
        if len(p.split()) > 40 and not p.strip().startswith("\\newcommand"):
            paras.append(p)
    sents, nums, we, which, semi, words, per_para = [], 0, 0, 0, 0, 0, []
    for p in paras:
        q = collapse(p)
        ss = [x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", q) if x.strip()]
        sents += ss
        per_para.append(len(ss))
        words += len(q.split())
        nums += q.count("#")
        we += len(re.findall(r"\b[Ww]e\b", q))
        which += len(re.findall(r", which", q))
        semi += q.count(";")
    if not sents:
        return {"file": label, "paragraphs": 0}
    L = [len(x.split()) for x in sents]
    N = [x.count("#") for x in sents]
    k = words / 1000.0
    return {
        "file": label,
        "paragraphs": len(paras),
        "prose_words": words,
        "sentences_per_paragraph": round(sum(per_para) / len(per_para), 1),
        "mean_sentence_words": round(sum(L) / len(L), 1),
        "pct_sentences_over_45": round(100.0 * sum(l > 45 for l in L) / len(L), 1),
        "numbers_per_1k": round(nums / k, 1),
        "pct_sentences_over_3_numbers": round(100.0 * sum(n > 3 for n in N) / len(N), 1),
        "max_numbers_per_sentence": max(N),
        "we_per_1k": round(we / k, 1),
        "which_per_1k": round(which / k, 1),
        "semicolons_per_1k": round(semi / k, 1),
    }


def metrics(path, include_appendix=False):
    s = body(open(path, errors="ignore").read(), include_appendix)
    return measure(clean(s), os.path.basename(path))


def sections(path, include_appendix=False):
    s = body(open(path, errors="ignore").read(), include_appendix)
    parts = re.split(r"(\\section\*?(?:\[[^\]]*\])?" + BR + ")", s)
    out = [("(front matter)", parts[0])]
    for i in range(1, len(parts), 2):
        title = re.sub(r"^\\section\*?(?:\[[^\]]*\])?\{|\}$", "", parts[i])
        out.append((title[:40], parts[i + 1] if i + 1 < len(parts) else ""))
    return [measure(clean(t), name) for name, t in out]


def gate(m, genre, bands):
    rows = []
    for key, op, dflt, res in bands:
        lim = res if genre == "results" else dflt
        v = m.get(key)
        if v is None:
            ok, band = False, "n/a"
        elif op == "range":
            ok, band = lim[0] <= v <= lim[1], "%g-%g" % lim
        elif op == "max":
            ok, band = v <= lim, "<= %g" % lim
        else:
            ok, band = v >= lim, ">= %g" % lim
        rows.append({"metric": key, "value": v, "band": band, "pass": ok})
    return rows


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        sys.exit(1)
    ref_path = args[args.index("--ref") + 1] if "--ref" in args else None
    genre = args[args.index("--genre") + 1] if "--genre" in args else "default"
    inc = "--include-appendix" in args
    target = args[0]
    if ref_path:
        ref = metrics(ref_path)
        if not ref.get("paragraphs"):
            sys.exit("style_metrics: no prose paragraphs found in reference %s" % ref_path)
        bands, calibration = derive_bands(ref), "derived from --ref"
    else:
        ref, bands, calibration = DEFAULT_REFERENCE, BANDS, "default"
    out = {"reference": ref, "target": metrics(target, inc)}
    if "--gate" in args:
        out["genre"] = genre
        out["calibration"] = calibration
        out["gate"] = gate(out["target"], genre, bands)
        out["gate_pass"] = all(r["pass"] for r in out["gate"])
    if "--sections" in args:
        out["sections"] = sections(target, inc)
    if "--json" in args:
        print(json.dumps(out, indent=2))
    else:
        keys = [k for k in DEFAULT_REFERENCE if k != "file"]
        print("reference: %s" % ref.get("file"))
        print("%-30s %12s %12s" % ("metric", "reference", "target"))
        for k in keys:
            print("%-30s %12s %12s" % (k, ref.get(k), out["target"].get(k)))
        if "gate" in out:
            print("\nStyle gate (genre: %s, bands: %s)" % (genre, calibration))
            print("%-30s %10s %12s %6s" % ("metric", "target", "band", "result"))
            for r in out["gate"]:
                print("%-30s %10s %12s %6s" % (r["metric"], r["value"], r["band"],
                                               "PASS" if r["pass"] else "FAIL"))
            print("GATE: %s" % ("PASS" if out["gate_pass"] else "FAIL"))
        if "sections" in out:
            cols = ["prose_words", "mean_sentence_words", "pct_sentences_over_45",
                    "sentences_per_paragraph", "numbers_per_1k", "pct_sentences_over_3_numbers",
                    "we_per_1k", "semicolons_per_1k"]
            print("\nPer section: " + ", ".join(cols))
            for m in out["sections"]:
                if m.get("paragraphs"):
                    print("%-40s " % m["file"] + " ".join("%7s" % m.get(c) for c in cols))
    if "gate" in out and not out["gate_pass"]:
        sys.exit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Flag hardcoded numbers in report prose.

The rule this enforces: every result-bearing number in a report should come from a
generated macro / placeholder, not be typed into the prose (which silently goes stale when
the analysis changes). This script scans the hand-edited source (``Report.tex`` or a
Markdown ``*.tmpl``) and prints numeric literals that look like results, as candidates for
review. It is a heuristic aid, not an oracle — expect some false positives (years, route
numbers). Resolve each by turning it into a macro, or whitelist the line with an inline
``% noqa: hardcode`` (LaTeX) or ``<!-- noqa: hardcode -->`` (Markdown).

Usage:
    python check_no_hardcoded_numbers.py paper/Report.tex [more files ...] [--strict]

Exit code is non-zero while unresolved candidates remain, so it can gate a build.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Commands whose own line is structural, not prose — skip entirely.
SKIP_LINE = re.compile(
    r"^\s*\\(input|include|includegraphics|label|ref|autoref|eqref|pageref|cite\w*|"
    r"bibliography|usepackage|documentclass|newcommand|providecommand|renewcommand|def|"
    r"setlength|geometry|graphicspath|hypersetup|definecolor|RequirePackage)\b"
)
# Words that, immediately before a number, mark it as a reference, not a result.
SKIP_PREV = {
    "figure", "fig", "fig.", "table", "tab", "tab.", "section", "sec", "sec.", "§",
    "chapter", "ch", "ch.", "appendix", "app", "equation", "eq", "eq.", "eqn", "step",
    "page", "p", "p.", "pp", "pp.", "no", "no.", "number", "part", "item", "note",
    "footnote", "line", "version", "phase", "tier", "ward", "district", "precinct",
    "route", "rte", "hwy", "highway", "title", "fy", "q", "h",
}
ROUTE_ACRONYM = re.compile(r"[A-Z]{1,4}$")   # MD, US, SR, PA, I (e.g., "MD 355", "I-95")

# Number categories (priority order; first claim on a span wins).
PATTERNS = [
    ("money",   re.compile(r"\\?\$\s?\d[\d,]*(?:\.\d+)?")),
    ("percent", re.compile(r"\d[\d,]*(?:\.\d+)?\s?\\?%")),
    ("multipl", re.compile(r"\b\d+(?:\.\d+)?x\b")),
    ("grouped", re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b")),
    ("decimal", re.compile(r"\b\d+\.\d+\b")),
    ("integer", re.compile(r"\b\d+\b")),
]


def strip_comment(line: str, md: bool) -> str:
    if md:
        return re.sub(r"<!--.*?-->", "", line)
    return re.split(r"(?<!\\)%", line, maxsplit=1)[0]   # unescaped % starts a comment


def prev_word(text: str) -> str:
    m = re.search(r"(\S+)\s*$", text)
    return m.group(1) if m else ""


def scan_line(text: str, strict: bool):
    text = text.replace("~", " ")        # LaTeX ~ is an interword space
    claimed: list[tuple[int, int]] = []
    hits = []
    for kind, pat in PATTERNS:
        for m in pat.finditer(text):
            s, e = m.span()
            if any(s < ce and e > cs for cs, ce in claimed):
                continue
            tok = m.group()
            before = text[:s]
            pw = prev_word(before).lower().strip("([{")
            pw_raw = prev_word(before).rstrip("-").rstrip()
            # filters --------------------------------------------------------
            if kind == "integer":
                digits = re.sub(r"\D", "", tok)
                val = int(digits) if digits else 0
                if not strict and val < 10:        # 0-9 are usually structural/spelled
                    continue
                if 1900 <= val <= 2099:            # a year
                    continue
            if pw in SKIP_PREV:
                continue
            # "MD 355", "I-95": number right after an all-caps route acronym
            if ROUTE_ACRONYM.search(pw_raw) and kind in ("integer", "decimal"):
                continue
            # LaTeX layout dimension, not a result: a number bound to a length unit or a
            # \...width/\...height length (0.54\linewidth, 0.6em, [0.5em], 2pt). Slides carry
            # these constantly, so flagging them would bury the real result numbers. (Font
            # sizes belong in theme commands like \decktitle, not raw in the body.)
            after = text[e:]
            if (re.match(r"\s*(?:pt|bp|pc|in|cm|mm|ex|em|mu|sp)\b", after)
                    or re.match(r"\s*\\(?:line|text|column|paper)width\b", after)
                    or re.match(r"\s*\\(?:text|paper)height\b", after)
                    or re.match(r"\s*\\(?:baselineskip|height|width|depth|totalheight)\b", after)):
                continue
            claimed.append((s, e))
            hits.append((kind, tok))
    return hits


def check_file(path: Path, strict: bool) -> int:
    md = path.suffix.lower() in (".md", ".markdown", ".tmpl")
    in_body = not (path.suffix.lower() == ".tex")   # .md: whole file is body
    n = 0
    for i, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not path.suffix.lower() == ".tex":
            in_body = True
        elif "\\begin{document}" in raw:
            in_body = True
            continue
        if not in_body:
            continue
        if "noqa: hardcode" in raw:
            continue
        if not md and (SKIP_LINE.match(raw) or "\\includegraphics" in raw):
            continue
        text = strip_comment(raw, md).strip()
        if not text:
            continue
        for kind, tok in scan_line(text, strict):
            n += 1
            ctx = text if len(text) <= 90 else text[:87] + "..."
            print(f"  {path.name}:{i}: [{kind}] {tok!r}   |  {ctx}")
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--strict", action="store_true",
                    help="also flag bare single-digit integers")
    args = ap.parse_args()

    total = 0
    for f in args.files:
        p = Path(f)
        if not p.exists():
            print(f"  (skip) {f}: not found")
            continue
        print(f"Scanning {p} ...")
        total += check_file(p, args.strict)

    print()
    if total:
        print(f"Found {total} hardcoded-number candidate(s). For each: convert to a "
              f"generated macro/placeholder, or whitelist the line with "
              f"'% noqa: hardcode' (LaTeX) / '<!-- noqa: hardcode -->' (Markdown).")
        return 1
    print("Clean: no hardcoded-number candidates found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

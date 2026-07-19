"""Deck helpers for reproducible Beamer decks.

Re-exports report_helpers (``Headlines`` macro registry + formatters + table builders --
identical to the analysis-report skill, so a project that has both shares one mental model)
and adds Beamer chart-fragment builders. The deck generator imports from here and writes
``charts/*.tex`` (TikZ) + ``tables/*.tex`` + ``tables/headlines.tex`` -- the single source
of every number on a slide.

It also re-exports the geo helpers (``geo_choropleth``, ``save_figure``) from geo_helpers, so
the generator has one import surface for everything. Those build a map as a vector
``figures/*.pdf`` (``\\includegraphics``), not a TikZ fragment; their heavy deps (geopandas,
contextily, matplotlib) are imported lazily inside the functions, so importing this module
stays dependency-free until a deck actually draws a map.

Charts are hand-rolled TikZ (filled ``\\fill`` bars + ``\\node`` labels), NOT pgfplots, on
purpose: pgfplots with ``axis y line=none`` silently drops the category labels, and getting
labels + value annotations placed reliably across versions is fiddly. Plain rectangles give
full control and never lose their labels. See references/beamer-convention.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_helpers import (  # noqa: E402  (re-exported for the generator's convenience)
    Headlines, latex_escape, num, money, usd, usd_m, usd_b, pct, ratio, text,
    latex_table, save_table, md_table,
)
from geo_helpers import geo_choropleth, save_figure  # noqa: E402  (lazy heavy deps inside)

_HEADER = "% AUTO-GENERATED fragment. Do NOT edit by hand; re-run the deck generator.\n"


def _rows(items):
    out = []
    for it in items:
        if len(it) >= 3:
            out.append((str(it[0]), float(it[1]), str(it[2])))
        else:
            out.append((str(it[0]), float(it[1]), str(it[1])))
    return out


def hbar_chart(items, color="deckfg", bar_max_cm=3.2, row_h=0.62, font=r"\small"):
    """Horizontal labeled bar chart as a self-contained TikZ picture (returns a string).

    ``items``: list of ``(label, value)`` or ``(label, value, display)``. Order is preserved
    top-to-bottom, so pass largest-first for the usual ranked look. Each row renders the
    label (right-aligned, ending at x=0), the bar, and the value at the bar's end. Save with
    ``save_chart`` and ``\\input`` it inside a frame column.

    Keep labels short enough to fit the column; if a chart overflows, shrink ``bar_max_cm``
    or drop ``font`` to ``\\footnotesize`` rather than letting it spill past the margin.
    """
    rows = _rows(items)
    maxv = max((v for _, v, _ in rows), default=1) or 1
    out = [rf"\begin{{tikzpicture}}[font={font}]"]
    for i, (lab, val, disp) in enumerate(rows):
        y = -i * row_h
        w = bar_max_cm * val / maxv
        out.append(rf"\node[anchor=east,text=deckink] at (0,{y:.2f}) {{{latex_escape(lab)}}};")
        out.append(rf"\fill[{color}] (0.12,{y-0.16:.2f}) rectangle ({0.12+w:.2f},{y+0.16:.2f});")
        out.append(rf"\node[anchor=west,text=deckink] at ({0.12+w+0.10:.2f},{y:.2f}) {{{latex_escape(disp)}}};")
    out.append(r"\end{tikzpicture}")
    return "\n".join(out)


def kpi_board(cards, cols=3, dx=4.4, dy=-2.7, font_size=26):
    """Grid of KPI stat cards as one TikZ picture (returns a string).

    ``cards``: list of ``(number, label[, accent_color])``. **Pass ``number`` as a headline
    macro** (e.g. ``r"\\DeckActiveMembers"``) or pre-escaped LaTeX -- NOT a raw value, because
    a bare ``$`` would start math mode inside the node. ``label`` is escaped for you. Uses the
    ``deckcard`` TikZ style from beamer-theme.tex.
    """
    out = [r"\begin{tikzpicture}"]
    for i, card in enumerate(cards):
        number, label = card[0], card[1]
        accent = card[2] if len(card) > 2 else "deckfg"
        x = (i % cols) * dx
        y = (i // cols) * dy
        out.append(
            rf"\node[deckcard] at ({x},{y}) {{{{\fontsize{{{font_size}}}{{{font_size+2}}}"
            rf"\selectfont\bfseries\color{{{accent}}}{number}}}\\[3pt]"
            rf"{{\footnotesize\color{{deckmuted}}{latex_escape(label)}}}}};")
    out.append(r"\end{tikzpicture}")
    return "\n".join(out)


def save_chart(path, tikz: str):
    """Write a TikZ fragment (from hbar_chart / kpi_board) to ``path`` for ``\\input``."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_HEADER + tikz + "\n", encoding="utf-8")
    return p

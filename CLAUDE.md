# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A collection of standalone Python scripts that generate SVG drawings, intended to be plotted with
a Bantam Tools NextDraw 8511 pen plotter. The plotter's drawable area is wider than tall, about
11.8 x 8.5 inches — keep that aspect ratio in mind when sizing new drawings. Documentation for the
`nextdraw` library is at https://bantam.tools/nd_py.

## Commands

```bash
uv sync                         # install dependencies
uv run scripts/<name>.py        # run a generator script (writes to output/)
uv run ruff check .             # lint
uv run ruff format .            # format
```

There is no test suite. There is no CLI entry point — each file in `scripts/` is run directly and
is expected to produce an SVG under `output/`.

## Architecture

- `src/msnextdraw/svg_utils.py` — the only shared library code. Provides a minimal `Point` class
  (2D vector with `+`, `-`, `*`, `dot`, `length`, `normalize`), an SVG path parser
  (`parse_svg_path`, handling M/L/H/V/C/S/Q/T/Z commands, sampling curves into line segments),
  polygon helpers (`compute_centroid`, `get_bounding_box`), and SVG file I/O
  (`load_svg_polygon`, `points_to_polyline_svg`, `insert_element_into_svg`, `save_svg`).
  `insert_element_into_svg` specifically looks for an Inkscape-style `<g id="layer1">` group to
  insert new elements into, falling back to right before `</svg>`.
- `scripts/*.py` — one file per drawing/algorithm, each independent and runnable on its own
  (`if __name__ == "__main__":` at the bottom calling a `draw_*`/`generate_*`/`main` function with
  keyword-argument defaults for all visual parameters). Scripts fall into two patterns:
  - **Self-contained generators** (e.g. `tree.py`, `spotlight_rays.py`): build SVG content directly
    as f-strings, no shared utilities.
  - **Input-driven tracers** (e.g. `trace_with_shapes.py`, `fill_sine.py`, `fill_collision.py`):
    load an existing SVG from `input/` via `svg_utils.load_svg_polygon`, run some geometric
    transform over its points, and write a new SVG to `output/` (often the original shape plus the
    new traced/filled path, via `insert_element_into_svg`).
- `input/` — hand-drawn or Inkscape-authored source SVGs (e.g. `outline.svg`) that the tracer
  scripts read a single path from.
- `output/` — generated SVGs, one per script, checked into the repo as the current output of each
  script.
- `example/nextdraw/` — vendored example scripts from the `nextdraw` Python library itself
  (installation guide/reference, not part of this project's own code — don't extend it).
- `pyproject.toml` declares `nextdraw-api`, `py5`, `svgwrite`, `vpype`, `vsketch` as dependencies,
  but no script currently imports them — SVG generation so far is done by hand-building path/element
  strings. Prefer following that existing convention (raw SVG string building via `svg_utils`)
  unless a task specifically calls for one of these heavier libraries.

## Conventions

- Every script writes directly to a hardcoded default path under `output/` and prints where it
  saved to; scripts take no CLI args except `sol11.py`, which uses `argparse` for its multiple
  modes (`animation`, `single`, `svg`, `plotter`).
- SVG y-axis is inverted relative to standard math convention (down is positive); scripts computing
  angles/directions account for this explicitly (see `spotlight_rays.py`'s `dy = -math.sin(angle)`).
- Ruff is configured with line-length 100, double quotes, space indent, import sorting
  (isort-style, force-sort-within-sections) — run `uv run ruff format .` before considering a
  script finished.

# cs

Lightweight Python CLI to overlay player movement paths from multiple CS2 demos into a single 2D SVG rendering.

## Features

- Analyze multiple `.dem` files in one run
- Filter by player name and side (`CT` / `T`)
- Overlay all extracted round paths in a single 2D output
- Generate a standalone SVG file that can be viewed in any browser

## Usage

```bash
python -m cs_overlay \
  --demo /path/to/match1.dem \
  --demo /path/to/match2.dem \
  --player "player_name" \
  --output /path/to/overlay.svg
```

Optional arguments:

- `--side CT|T`: restrict to one side
- `--label`: custom label for each `--demo` (same count as demos)
- `--title`: title text rendered in the SVG
- `--min-points`: minimum number of points required for a path (default: `2`)

## Demo parsing library

The app uses `demoparser2` when available at runtime to read CS2 demos.
Install it in your environment before running:

```bash
pip install demoparser2
```
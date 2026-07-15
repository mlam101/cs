# cs

Lightweight Python app to overlay player movement paths from multiple CS2 demos into a single 2D SVG rendering.

## Features

- Analyze multiple `.dem` files in one run
- GUI mode that discovers demos from an in-app `cs_overlay/demos` folder
- Upload demos into the app directly from a file picker
- Filter by player name and side (`CT` / `T`)
- Overlay all extracted round paths in a single 2D output
- Render player icons, weapon labels, flash markers, and grenade markers
- Preview full-match playback inside the app with a forward/back scrub bar and play/pause control
- Generate a standalone SVG file that can be viewed in any browser

## Usage

Start the GUI (default when no arguments are passed):

```bash
python -m cs_overlay
```

Put `.dem` files in:

```bash
cs_overlay/demos/
```

The GUI lets you upload/select demos, set filters, scrub through playback in-app, and write an SVG.

CLI mode is still available:

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
- `--gui`: force GUI mode
- `--demos-dir`: custom demos folder for GUI mode

## Demo parsing library

The app uses `demoparser2` when available at runtime to read CS2 demos.
Install it in your environment before running:

```bash
pip install demoparser2
```
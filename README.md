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
## BC campsite availability watcher (starter)

This repository now includes a starter website/API to monitor BC backcountry campsite availability and notify users when a watch becomes available.

### Files

- `/home/runner/work/cs/cs/campsite_watch_app.py` - Flask website + API routes
- `/home/runner/work/cs/cs/campsite_watch_storage.py` - SQLite schema and data access
- `/home/runner/work/cs/cs/campsite_watch_checker.py` - periodic check + state-change alert logic
- `/home/runner/work/cs/cs/campsite_watch_clients.py` - BC fetch client + notification client

### API endpoints

- `POST /api/watches` create watch
- `GET /api/watches?user_id=<id>` list user watches
- `PATCH /api/watches/:id` pause/resume using `{ "active": true|false }`
- `GET /api/watches/:id/checks` check history
- `GET /api/watches/:id/alerts` alert history
- `POST /api/run-checks` trigger checker manually

### Run

Install dependency:

```bash
pip install flask
```

Start app:

```bash
python /home/runner/work/cs/cs/campsite_watch_app.py
```

Then open `http://localhost:8000`.

### Legal note

Before configuring a real BC data endpoint, review Terms of Use and robots.txt, prefer official APIs, and use rate limiting/backoff.

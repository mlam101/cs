from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .demoparser_extractor import Demoparser2Extractor
from .gui import launch_gui
from .overlay import build_overlay_paths
from .svg_renderer import render_overlay_svg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Overlay player paths from multiple CS2 demos into a 2D SVG."
    )
    parser.add_argument("--demo", action="append", help="Path to a .dem file")
    parser.add_argument(
        "--label",
        action="append",
        help="Custom label for a --demo entry (must match number of demos)",
    )
    parser.add_argument("--player", help="Player name filter")
    parser.add_argument("--side", choices=["CT", "T"], help="Optional side filter")
    parser.add_argument("--output", default="overlay.svg", help="Output SVG path")
    parser.add_argument("--title", help="Optional chart title")
    parser.add_argument("--min-points", type=int, default=2, help="Minimum points per path")
    parser.add_argument("--gui", action="store_true", help="Launch desktop GUI mode")
    parser.add_argument("--demos-dir", help="Demos directory used by GUI mode")
    return parser


def main() -> int:
    if len(sys.argv) == 1:
        launch_gui()
        return 0

    parser = build_parser()
    args = parser.parse_args()
    if args.gui:
        launch_gui(default_demos_dir=args.demos_dir)
        return 0
    if not args.demo:
        parser.error("--demo is required in CLI mode (or use --gui)")

    labels = args.label or [Path(path).stem for path in args.demo]
    overlay_paths = build_overlay_paths(
        demo_paths=args.demo,
        extractor=Demoparser2Extractor(),
        player_name=args.player,
        side=args.side,
        labels=labels,
        min_points=args.min_points,
    )
    svg = render_overlay_svg(paths=overlay_paths, title=args.title)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

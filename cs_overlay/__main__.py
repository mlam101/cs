from __future__ import annotations

import argparse
from pathlib import Path

from .demoparser_extractor import Demoparser2Extractor
from .overlay import build_overlay_paths
from .svg_renderer import render_overlay_svg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Overlay player paths from multiple CS2 demos into a 2D SVG."
    )
    parser.add_argument("--demo", action="append", required=True, help="Path to a .dem file")
    parser.add_argument(
        "--label",
        action="append",
        help="Custom label for a --demo entry (must match number of demos)",
    )
    parser.add_argument("--player", help="Player name filter")
    parser.add_argument("--side", choices=["CT", "T"], help="Optional side filter")
    parser.add_argument("--output", required=True, help="Output SVG path")
    parser.add_argument("--title", help="Optional chart title")
    parser.add_argument("--min-points", type=int, default=2, help="Minimum points per path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

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

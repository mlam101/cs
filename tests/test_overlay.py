import unittest

from cs_overlay.models import PathTrace, Point
from cs_overlay.overlay import build_overlay_paths
from cs_overlay.svg_renderer import render_overlay_svg


class FakeExtractor:
    def __init__(self, traces_by_demo):
        self.traces_by_demo = traces_by_demo

    def extract_paths(self, demo_path, match_label, player_name=None, side=None):
        traces = self.traces_by_demo[demo_path]
        if player_name:
            traces = [t for t in traces if t.player_name == player_name]
        if side:
            traces = [t for t in traces if t.side == side]
        return [
            PathTrace(
                match_label=match_label,
                round_number=t.round_number,
                player_name=t.player_name,
                side=t.side,
                points=t.points,
            )
            for t in traces
        ]


class OverlayTests(unittest.TestCase):
    def test_build_overlay_paths_merges_and_filters(self):
        demo1_trace = PathTrace(
            match_label="demo1",
            round_number=1,
            player_name="player",
            side="CT",
            points=(Point(0, 0), Point(10, 10)),
        )
        demo2_short = PathTrace(
            match_label="demo2",
            round_number=2,
            player_name="player",
            side="CT",
            points=(Point(1, 1),),
        )
        extractor = FakeExtractor({"a.dem": [demo1_trace], "b.dem": [demo2_short]})

        merged = build_overlay_paths(
            demo_paths=["a.dem", "b.dem"],
            extractor=extractor,
            player_name="player",
            side="CT",
            labels=["match-a", "match-b"],
            min_points=2,
        )

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].match_label, "match-a")

    def test_render_overlay_svg_outputs_polylines(self):
        paths = [
            PathTrace(
                match_label="match-a",
                round_number=1,
                player_name="p1",
                side="CT",
                points=(Point(0, 0), Point(50, 50), Point(100, 50)),
            ),
            PathTrace(
                match_label="match-b",
                round_number=2,
                player_name="p2",
                side="T",
                points=(Point(0, 10), Point(60, 40), Point(120, 80)),
            ),
        ]

        svg = render_overlay_svg(paths, title="overlay")

        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)
        self.assertEqual(svg.count("<polyline"), 2)
        self.assertIn("overlay", svg)


if __name__ == "__main__":
    unittest.main()

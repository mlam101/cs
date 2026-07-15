from __future__ import annotations

from collections.abc import Iterable

from .models import PathTrace


def build_overlay_paths(
    demo_paths: Iterable[str],
    extractor,
    player_name: str | None = None,
    side: str | None = None,
    labels: Iterable[str] | None = None,
    min_points: int = 2,
) -> list[PathTrace]:
    """Extract and combine movement paths from multiple demos."""
    demo_paths = list(demo_paths)
    labels_list = list(labels) if labels is not None else demo_paths
    if len(labels_list) != len(demo_paths):
        raise ValueError("labels must have the same number of entries as demo_paths")

    merged: list[PathTrace] = []
    for demo_path, label in zip(demo_paths, labels_list):
        traces = extractor.extract_paths(
            demo_path=demo_path,
            match_label=label,
            player_name=player_name,
            side=side,
        )
        merged.extend(trace for trace in traces if len(trace.points) >= min_points)
    return merged

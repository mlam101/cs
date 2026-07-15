from __future__ import annotations

from hashlib import sha256
from html import escape

from .models import PathTrace


def render_overlay_svg(
    paths: list[PathTrace],
    width: int = 1024,
    height: int = 1024,
    padding: int = 24,
    title: str | None = None,
) -> str:
    if width <= 2 * padding or height <= 2 * padding:
        raise ValueError("width and height must be larger than twice the padding")
    if not paths:
        raise ValueError("No paths provided for rendering")

    xs = [point.x for path in paths for point in path.points]
    ys = [point.y for path in paths for point in path.points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)
    scale_x = (width - 2 * padding) / span_x
    scale_y = (height - 2 * padding) / span_y

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="#0f172a"/>',
    ]

    if title:
        lines.append(
            f'<text x="{padding}" y="{padding}" fill="#e2e8f0" font-size="20" font-family="Arial">{escape(title)}</text>'
        )

    for path in paths:
        color = _color_for_label(path.match_label)
        points = " ".join(
            f"{padding + (point.x - min_x) * scale_x:.2f},{height - padding - (point.y - min_y) * scale_y:.2f}"
            for point in path.points
        )
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-opacity="0.55" stroke-width="2"/>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def _color_for_label(label: str) -> str:
    digest = sha256(label.encode("utf-8")).hexdigest()
    return f"#{digest[:6]}"

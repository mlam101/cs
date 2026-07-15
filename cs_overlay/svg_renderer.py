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

    def scale_point(x: float, y: float) -> tuple[float, float]:
        return (
            padding + (x - min_x) * scale_x,
            height - padding - (y - min_y) * scale_y,
        )

    for path in paths:
        color = _color_for_label(path.match_label)
        points = " ".join(
            f"{scale_point(point.x, point.y)[0]:.2f},{scale_point(point.x, point.y)[1]:.2f}"
            for point in path.points
        )
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-opacity="0.55" stroke-width="2"/>'
        )
        start_x, start_y = scale_point(path.points[0].x, path.points[0].y)
        lines.append(
            f'<text x="{start_x:.2f}" y="{start_y - 6:.2f}" fill="#f8fafc" font-size="15">{escape(path.player_icon)}</text>'
        )

        if path.last_weapon:
            end_x, end_y = scale_point(path.points[-1].x, path.points[-1].y)
            lines.append(
                f'<text x="{end_x + 6:.2f}" y="{end_y:.2f}" fill="#fde68a" font-size="11" font-family="Arial">{escape(path.last_weapon)}</text>'
            )

        for flash_point in path.flash_points:
            marker_x, marker_y = scale_point(flash_point.x, flash_point.y)
            lines.append(
                f'<circle cx="{marker_x:.2f}" cy="{marker_y:.2f}" r="3" fill="#22d3ee" fill-opacity="0.9"/>'
            )

        for grenade_point in path.grenade_points:
            marker_x, marker_y = scale_point(grenade_point.x, grenade_point.y)
            lines.append(
                f'<rect x="{marker_x - 2:.2f}" y="{marker_y - 2:.2f}" width="4" height="4" fill="#f97316" fill-opacity="0.9"/>'
            )

    lines.append("</svg>")
    return "\n".join(lines)


def _color_for_label(label: str) -> str:
    digest = sha256(label.encode("utf-8")).hexdigest()
    return f"#{digest[:6]}"

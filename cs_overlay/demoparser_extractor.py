from __future__ import annotations

from collections import defaultdict

from .models import PathTrace, Point


class Demoparser2Extractor:
    CORE_COLUMNS = (
        "X",
        "Y",
        "name",
        "team_name",
        "is_alive",
        "round_num",
        "active_weapon_name",
    )
    OPTIONAL_COLUMNS = (
        "is_flashed",
        "flash_duration",
    )

    def extract_paths(
        self,
        demo_path: str,
        match_label: str,
        player_name: str | None = None,
        side: str | None = None,
    ) -> list[PathTrace]:
        try:
            from demoparser2 import DemoParser
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "demoparser2 is required to parse CS2 demos. Install with: pip install demoparser2"
            ) from exc

        ticks = self._parse_ticks_with_fallback(DemoParser, demo_path)
        records = _to_records(ticks)
        grouped_points: dict[tuple[int, str, str], list[Point]] = defaultdict(list)
        grouped_flash_points: dict[tuple[int, str, str], list[Point]] = defaultdict(list)
        grouped_grenade_points: dict[tuple[int, str, str], list[Point]] = defaultdict(list)
        grouped_weapon: dict[tuple[int, str, str], str | None] = {}

        for row in records:
            if not row.get("is_alive"):
                continue

            current_player = str(row.get("name") or "")
            current_side = str(row.get("team_name") or "")
            if player_name and current_player != player_name:
                continue
            if side and current_side != side:
                continue

            x = row.get("X")
            y = row.get("Y")
            round_number = row.get("round_num")
            if x is None or y is None or round_number is None:
                continue

            key = (int(round_number), current_player, current_side)
            point = Point(float(x), float(y))
            grouped_points[key].append(point)

            weapon_name = str(row.get("active_weapon_name") or "").strip() or None
            if weapon_name:
                grouped_weapon[key] = weapon_name
                if "grenade" in weapon_name.lower():
                    grouped_grenade_points[key].append(point)

            is_flashed = bool(row.get("is_flashed"))
            if not is_flashed:
                try:
                    is_flashed = float(row.get("flash_duration") or 0) > 0
                except (TypeError, ValueError):
                    is_flashed = False
            if is_flashed:
                grouped_flash_points[key].append(point)

        return [
            PathTrace(
                match_label=match_label,
                round_number=round_number,
                player_name=player,
                side=team_side,
                points=tuple(points),
                last_weapon=grouped_weapon.get((round_number, player, team_side)),
                flash_points=tuple(grouped_flash_points.get((round_number, player, team_side), [])),
                grenade_points=tuple(grouped_grenade_points.get((round_number, player, team_side), [])),
            )
            for (round_number, player, team_side), points in grouped_points.items()
        ]

    def _parse_ticks_with_fallback(self, parser_cls, demo_path: str):
        preferred_columns = [*self.CORE_COLUMNS, *self.OPTIONAL_COLUMNS]
        parser = parser_cls(demo_path)
        try:
            return parser.parse_ticks(preferred_columns)
        except Exception as exc:
            if not _is_missing_entity_error(exc):
                raise
        return parser.parse_ticks(list(self.CORE_COLUMNS))


def _to_records(data) -> list[dict]:
    if hasattr(data, "to_dict"):
        try:
            return list(data.to_dict("records"))
        except TypeError:
            pass
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    raise TypeError("Unsupported parser output format; expected table-like rows")


def _is_missing_entity_error(error: Exception) -> bool:
    return "entity" in str(error).lower() and "not found" in str(error).lower()

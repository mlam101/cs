from __future__ import annotations

from collections import defaultdict

from .models import PathTrace, Point


class Demoparser2Extractor:
    REQUIRED_COLUMNS = ("X", "Y", "name", "team_name", "is_alive", "round_num")

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

        ticks = DemoParser(demo_path).parse_ticks(list(self.REQUIRED_COLUMNS))
        records = _to_records(ticks)
        grouped: dict[tuple[int, str, str], list[Point]] = defaultdict(list)

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

            grouped[(int(round_number), current_player, current_side)].append(
                Point(float(x), float(y))
            )

        return [
            PathTrace(
                match_label=match_label,
                round_number=round_number,
                player_name=player,
                side=team_side,
                points=tuple(points),
            )
            for (round_number, player, team_side), points in grouped.items()
        ]


def _to_records(data) -> list[dict]:
    if hasattr(data, "to_dict"):
        try:
            return list(data.to_dict("records"))
        except TypeError:
            pass
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    raise TypeError("Unsupported parser output format; expected table-like rows")

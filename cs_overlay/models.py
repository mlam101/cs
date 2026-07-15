from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class PathTrace:
    match_label: str
    round_number: int
    player_name: str
    side: str
    points: tuple[Point, ...]

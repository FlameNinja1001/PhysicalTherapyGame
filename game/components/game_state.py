from dataclasses import dataclass, field

@dataclass
class GameStateComponent:
    """Core game logic state - score, progression, and level info."""
    score: int = 0
    level: int = 1
    target_reps: int = 10
    phase: str = "PLAYING"
    streak: int = 0

    # Event queue for game events (cleared each frame)
    events: list[str] = field(default_factory=list)

    # Level progression info
    templates: list[str] = field(default_factory=list)
    active_idx: int = 0

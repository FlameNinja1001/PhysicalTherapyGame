from dataclasses import dataclass, field

@dataclass
class GameStateComponent:
    score: int = 0
    level: int = 1
    target_reps: int = 10
    phase: str = "PLAYING"
    last_rep_event: bool = False
    streak: int = 0
    dt: float = 0.016  # Delta time for frame-independent updates

    # UI Info
    templates: list[str] = field(default_factory=list)
    active_idx: int = 0
    fullscreen: bool = False

from dataclasses import dataclass, field

@dataclass
class GameStateComponent:
    score: int = 0
    level: int = 1
    target_reps: int = 10
    phase: str = "PLAYING"
    last_rep_event: bool = False
    streak: int = 0

    # UI Info
    templates: list[str] = field(default_factory=list)
    active_idx: int = 0
    fullscreen: bool = False

from dataclasses import dataclass
import numpy as np

@dataclass
class ExerciseComponent:
    name: str = ""
    template_path: str = ""
    start_state: np.ndarray | None = None
    peak_state: np.ndarray | None = None
    movement_vector: np.ndarray | None = None
    vector_sq_length: float = 1.0
    dev_thresh: float = 35.0
    prog_start_thresh: float = 0.25
    prog_peak_thresh: float = 0.40

@dataclass
class RepStateComponent:
    phase: int = 0          # 0=align, 1=going, 2=returning
    rep_count: int = 0
    progress: float = 0.0
    deviation: float = 0.0
    state_msg: str = "NO TEMPLATE"

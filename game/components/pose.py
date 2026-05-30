from dataclasses import dataclass, field

@dataclass
class PoseLandmarksComponent:
    landmarks: list | None = None     # mediapipe landmarks list

@dataclass
class JointAnglesComponent:
    angles: list[float] = field(default_factory=lambda: [0.0] * 8)

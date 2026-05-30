# PhysicalTherapyGame
HackJPS 2026 submission, theme is "Healthcare"

## Project Overview
An ECS-based physical therapy gamification system using Pygame, OpenCV, and MediaPipe.

## Structure
- `run_game.py`: Main entry point to launch the game.
- `game/`: Core ECS game logic (components, systems, core utilities).
- `tools/`: Utility scripts for development.
    - `make_template.py`: Create exercise templates from videos.
    - `pose_tracker.py`: Standalone CV-only joint tracker we used for testing.
- `tests/`: Obsolete but claude prototype we based code around
- `training_data/`: Stored exercise `.npz` templates.

## Running the Game
```bash
uv run python run_game.py
```

## Creating New Exercises
```bash
uv run python tools/make_template.py path/to/video.mp4 training_data/my_exercise_name
```
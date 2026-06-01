# How We Built This: PhysicalTherapyGame

Physical therapy is critical for recovery, but let's be honest—doing 3 sets of 15 lateral raises in a quiet room is boring. We built **PhysicalTherapyGame** for HackJPS 2026 to turn repetitive rehabilitation into an engaging, interactive experience.

Here is a deep dive into the technical architecture and engineering decisions that brought this project to life.

## 🏗️ Architecture: The ECS Pattern
We chose an **Entity Component System (ECS)** architecture using the `esper` library. In a typical game, objects (Entities) hold their own logic. In ECS, we separate data (Components) from logic (Systems).

- **Components**: Plain data classes like `PoseLandmarksComponent`, `ExerciseComponent`, and `RepStateComponent`.
- **Systems**: Modular logic processors like `RenderSystem`, `RepDetectionSystem`, and `AngleSystem`.

This allowed us to cleanly separate the "Healthcare" logic (detecting a squat) from the "Game" logic (jumping over a platform).

## 👁️ Computer Vision & Pose Estimation
The core of the game is seeing the player. We used:
- **MediaPipe Pose**: To extract 33 3D skeletal landmarks in real-time.
- **OpenCV**: For frame processing, mirroring, and drawing debug skeletons.

### The Multithreading Secret
Running MediaPipe pose estimation on every frame can be heavy and drop your game's FPS. To keep the gameplay buttery smooth, we moved all camera input and AI processing to a **dedicated background thread** (`MediapipeThread`). The game loop simply "asks" the thread for the latest landmarks, ensuring the UI remains responsive even if the AI takes a few milliseconds longer.

## 📐 The "Movement Vector" Algorithm
How do you tell if someone is doing a "good" rep? Instead of hardcoding angle thresholds for every exercise, we developed a template-based approach:

1. **Templates**: We built a tool (`tools/make_template.py`) that takes a video of a perfect rep and extracts the starting pose and the peak pose.
2. **Angle Vectors**: We represent the human body as a vector of 12 critical joint angles (knees, hips, shoulders, elbows).
3. **Linear Algebra Projection**:
    - We calculate a **Movement Vector** (Peak Pose - Start Pose).
    - We project the user's current live angles onto this vector using a **Dot Product**.
    - This gives us a single `progress` value (0.0 to 1.0) regardless of the exercise.
4. **Form Tracking**: We calculate the perpendicular distance (deviation) from the movement vector. If you're leaning too far or your arms are wonky, the game detects the "Poor Form" and alerts you.

## 🎮 Gamifying the Therapy
We didn't want one-size-fits-all gameplay. We mapped exercise categories to specific minigame mechanics:
- **Legs (Squats/Lunges)**: Mapped to a **Platformer**. Your vertical movement controls the character's jumps.
- **Arms (Lateral Raises/Claps)**: Mapped to a **Jungle Climb**. Reaching up helps a monkey climb trees to get mangos.
- **Torso (Side Bends/Toe Touches)**: Mapped to a **Swimming Game**. Lateral movement steers a dolphin through coral reefs.

## 🎨 UI & UX
Built entirely in **Pygame**, we focused on a "high-energy" aesthetic:
- **Dynamic Zooming**: The demo video player uses smooth interpolation to zoom from a corner "guide" to a full-screen instruction.
- **Particle Systems**: Completing a rep triggers bursts of "juice" to provide positive reinforcement.
- **Responsive HUD**: Real-time feedback messages like "GREAT!" or "ALIGN TO START" guide the user through the physical movement.

## 🛠️ The Stack
- **Language**: Python 3.12+
- **Game Engine**: Pygame CE
- **AI/CV**: MediaPipe, OpenCV, NumPy
- **ECS**: Esper
- **Package Manager**: UV (for lightning-fast dependency management)

By combining computer vision with classic game design patterns, we've created a tool that makes the road to recovery just a little bit more fun.

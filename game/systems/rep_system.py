import esper
import numpy as np
from game.components.pose import JointAnglesComponent
from game.components.exercise import ExerciseComponent, RepStateComponent
from game.components.game_state import GameStateComponent

class RepDetectionSystem(esper.Processor):
    def process(self):
        for ent, (angles, ex, rep, state) in esper.get_components(
                JointAnglesComponent, ExerciseComponent, RepStateComponent, GameStateComponent):

            # Reset pulse event
            state.last_rep_event = False

            if ex.start_state is None:
                rep.state_msg = "NO TEMPLATE"
                continue

            live = np.array(angles.angles)

            # 1. Calculate Progress
            w = live - ex.start_state
            rep.progress = np.dot(w, ex.movement_vector) / ex.vector_sq_length
            rep.progress = np.clip(rep.progress, 0.0, 1.2)

            # 2. Calculate Deviation
            expected_angles = ex.start_state + (rep.progress * ex.movement_vector)
            rep.deviation = float(np.mean(np.abs(live - expected_angles)))

            rep.state_msg = "POOR FORM"

            # 3. State Machine
            if rep.deviation < ex.dev_thresh:
                if rep.phase == 0:
                    rep.state_msg = "ALIGN TO START"
                    if rep.progress < ex.prog_start_thresh:
                        rep.phase = 1
                elif rep.phase == 1:
                    rep.state_msg = "GO DOWN"
                    if rep.progress > ex.prog_peak_thresh:
                        rep.phase = 2
                elif rep.phase == 2:
                    rep.state_msg = "COME UP"
                    if rep.progress < ex.prog_start_thresh:
                        # Only count rep if below target
                        if rep.rep_count < state.target_reps:
                            rep.rep_count += 1
                            state.last_rep_event = True  # Signal to game logic
                        rep.phase = 1

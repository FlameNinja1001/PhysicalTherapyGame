import esper
from game.components.game_state import GameStateComponent
from game.components.exercise import RepStateComponent

from game.core.exercise_loader import ExerciseLoader
import esper

class GameLogicSystem(esper.Processor):
    def process(self, dt=0.016):
        for ent, (state, rep) in esper.get_components(GameStateComponent, RepStateComponent):
            # Check for exercise completion regardless of rep event
            if rep.rep_count >= state.target_reps and state.phase == "PLAYING":
                # Move to next exercise in group
                state.active_idx += 1
                if state.active_idx < len(state.templates):
                    # Load next template
                    new_ex = ExerciseLoader.load_template(state.templates[state.active_idx])
                    esper.add_component(ent, new_ex)
                    # Reset rep state
                    rep.rep_count = 0
                    rep.phase = 0
                    rep.progress = 0
                    print(f"Next Exercise: {state.templates[state.active_idx]}")
                else:
                    # All exercises in group complete
                    state.phase = "LEVEL_COMPLETE"
                    print("LEVEL COMPLETE!")

            # Score calculation on rep events
            if "REP_COMPLETE" in state.events:
                if rep.deviation < 15.0:
                    points = 10
                    state.streak += 1
                elif rep.deviation < 25.0:
                    points = 5
                    state.streak = max(1, state.streak)
                else:
                    points = 2
                    state.streak = 0

                multiplier = 1 + (state.streak // 3)
                state.score += points * multiplier

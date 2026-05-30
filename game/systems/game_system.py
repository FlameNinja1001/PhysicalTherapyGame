import esper
from game.components.game_state import GameStateComponent
from game.components.exercise import RepStateComponent

class GameLogicSystem(esper.Processor):
    def process(self):
        for ent, (state, rep) in esper.get_components(GameStateComponent, RepStateComponent):
            if state.last_rep_event:
                # Score calculation based on deviation during the rep
                # A simple version: if deviation was very low, more points
                if rep.deviation < 15.0:
                    points = 10
                    state.streak += 1
                elif rep.deviation < 25.0:
                    points = 5
                    state.streak = max(1, state.streak)
                else:
                    points = 2
                    state.streak = 0

                # Apply streak multiplier
                multiplier = 1 + (state.streak // 3)
                state.score += points * multiplier

                # Level progression
                if rep.rep_count >= state.target_reps * state.level:
                    state.level += 1
                    # Could trigger level up effects here
                    print(f"LEVEL UP! Now level {state.level}")

import os
import json
import numpy as np
from game.components.exercise import ExerciseComponent

class ExerciseLoader:
    @staticmethod
    def load_template(path: str) -> ExerciseComponent:
        ex = ExerciseComponent()
        ex.template_path = path
        ex.name = os.path.basename(path).replace(".npz", "").replace("_", " ").title()

        data = np.load(path)
        ex.start_state = data['start']
        ex.peak_state = data['peak']

        # Calculate the mathematical vector from Start -> Peak
        ex.movement_vector = ex.peak_state - ex.start_state
        ex.vector_sq_length = np.dot(ex.movement_vector, ex.movement_vector)

        if ex.vector_sq_length < 1e-5:
            print("WARNING: Start and Peak states are identical. Re-record template.")
            ex.vector_sq_length = 1e-5

        # Load config if exists
        conf_path = path + '.json'
        if os.path.exists(conf_path):
            with open(conf_path, 'r', encoding="utf-8") as f:
                c = json.load(f)
                ex.dev_thresh = c.get('dev', 35.0)
                ex.prog_start_thresh = c.get('start', 0.25)
                ex.prog_peak_thresh = c.get('peak', 0.40)

        return ex

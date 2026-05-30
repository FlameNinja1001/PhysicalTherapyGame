import math

def lerp(a, b, t):
    return a + (b - a) * t

def ease_out_expo(t):
    return 1 if t == 1 else 1 - pow(2, -10 * t)

def ease_out_cubic(t):
    return 1 - pow(1 - t, 3)

def oscillate(t, amplitude, frequency, offset=0):
    return amplitude * math.sin(t * frequency * 2 * math.pi) + offset

class Tween:
    def __init__(self, start_val, end_val, duration, easing_func=ease_out_cubic):
        self.start = start_val
        self.end = end_val
        self.duration = duration
        self.elapsed = 0
        self.value = start_val
        self.easing = easing_func
        self.finished = False

    def update(self, dt):
        if self.finished: return self.value

        self.elapsed += dt
        t = min(1.0, self.elapsed / self.duration)
        self.value = lerp(self.start, self.end, self.easing(t))

        if t >= 1.0:
            self.finished = True
        return self.value

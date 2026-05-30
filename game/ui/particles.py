import pygame
import random
import math
from game.ui import theme

class Particle:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.randint(0, theme.WIDTH)
        self.y = random.randint(0, theme.HEIGHT)
        self.size = random.uniform(1, 4)
        self.speed = random.uniform(10, 40)
        self.opacity = random.randint(30, 180)
        self.angle = random.uniform(0, math.pi * 2)
        self.amplitude = random.uniform(0.5, 2.0)

        if random.random() < 0.7:  # 70% red
            self.color = theme.ACCENT
        else:  # 30% cyan
            self.color = theme.CYAN

    def update(self, dt):
        self.y -= self.speed * dt
        self.x += math.sin(pygame.time.get_ticks() * 0.001 + self.angle) * self.amplitude

        if self.y < -10:
            self.reset()
            self.y = theme.HEIGHT + 10

    def draw(self, surface):
        s = pygame.Surface((int(self.size*2)+1, int(self.size*2)+1), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, self.opacity), (int(self.size), int(self.size)), int(self.size))
        surface.blit(s, (int(self.x), int(self.y)))

class ParticleSystem:
    def __init__(self, count=60):
        self.particles = [Particle() for _ in range(count)]

    def update(self, dt):
        for p in self.particles:
            p.update(dt)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

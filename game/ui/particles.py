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
        self.speed = random.uniform(10, 30)
        self.opacity = random.randint(30, 150)
        self.angle = random.uniform(0, math.pi * 2)
        self.amplitude = random.uniform(0.5, 2.0)

    def update(self, dt):
        self.y -= self.speed * dt
        self.x += math.sin(pygame.time.get_ticks() * 0.001 + self.angle) * self.amplitude

        if self.y < -10:
            self.reset()
            self.y = theme.HEIGHT + 10

    def draw(self, surface):
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (theme.ACCENT[0], theme.ACCENT[1], theme.ACCENT[2], self.opacity), (self.size, self.size), self.size)
        surface.blit(s, (self.x, self.y))

class ParticleSystem:
    def __init__(self, count=50):
        self.particles = [Particle() for _ in range(count)]

    def update(self, dt):
        for p in self.particles:
            p.update(dt)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

import pygame
import math
import time
import random

# ---------- CONFIG ----------
SCREEN_W, SCREEN_H = 800, 600
RAY_W, RAY_H = 96, 72          # internal resolution
MAX_STEPS = 40
MAX_DIST = 18.0
EPSILON = 0.02
FPS = 30

# ---------- SDFs ----------
def sdf_sphere(p, r):
    return math.sqrt(p[0]**2 + p[1]**2 + p[2]**2) - r

def sdf_tunnel(p, t):
    x, y, z = p
    radius = 1.2 + 0.3 * math.sin(z * 2 + t)
    thickness = 0.08
    return abs(math.sqrt(x*x + y*y) - radius) - thickness

def scene_sdf(p, t):
    sphere_pos = (
        p[0],
        p[1] + math.sin(t * 1.5) * 0.4,
        p[2] - 3
    )
    return min(
        sdf_tunnel(p, t),
        sdf_sphere(sphere_pos, 0.6)
    )

# ---------- RAYMARCH ----------
def raymarch(ro, rd, t):
    dist = 0.0
    for _ in range(MAX_STEPS):
        p = (
            ro[0] + rd[0] * dist,
            ro[1] + rd[1] * dist,
            ro[2] + rd[2] * dist,
        )
        d = scene_sdf(p, t)
        if d < EPSILON:
            return dist
        dist += d * 0.9
        if dist > MAX_DIST:
            break
    return None

# ---------- MAIN ----------
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("VHS Raymarch Background")
clock = pygame.time.Clock()

surf = pygame.Surface((RAY_W, RAY_H))
prev_surf = pygame.Surface((RAY_W, RAY_H))

running = True
while running:
    t = time.time() * 0.8

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # VHS scanline jitter
    scanline_offsets = [
        random.randint(-2, 2) if random.random() < 0.12 else 0
        for _ in range(RAY_H)
    ]

    # Occasional vertical tear
    tear_line = random.randint(0, RAY_H) if random.random() < 0.05 else None

    for y in range(RAY_H):
        for x in range(RAY_W):
            nx = ((x + scanline_offsets[y]) / RAY_W - 0.5) * 2
            ny = (y / RAY_H - 0.5) * 2 * (RAY_H / RAY_W)

            ro = (0, 0, -5 + t)

            length = math.sqrt(nx*nx + ny*ny + 1.5*1.5)
            rd = (nx / length, ny / length, 1.5 / length)

            d = raymarch(ro, rd, t)

            if d is None:
                base = 10
            else:
                base = max(0, 255 - int(d * 45))

            # VHS color bleed
            bleed = random.randint(-8, 8)
            r = min(255, max(0, base + bleed))
            g = min(255, max(0, int(base * 0.6)))
            b = min(255, max(0, 255 - base - bleed))

            # Noise shimmer
            noise = random.randint(-12, 12)
            r = min(255, max(0, r + noise))
            g = min(255, max(0, g + noise))
            b = min(255, max(0, b + noise))

            # Vertical tear color swap
            if tear_line and y > tear_line:
                r, g, b = b, r, g

            surf.set_at((x, y), (r, g, b))

    # Temporal smear / phosphor persistence
    if random.random() < 0.15:
        surf.blit(prev_surf, (random.randint(-1, 1), 0))

    prev_surf.blit(surf, (0, 0))

    pygame.transform.scale(surf, (SCREEN_W, SCREEN_H), screen)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()

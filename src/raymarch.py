import pygame
import math

# ---------- CONFIG ----------
SCREEN_W, SCREEN_H = 800, 600

class ProceduralBG:
    def __init__(self, width, height, scale=4):
        self.scale = scale  # downscale factor
        self.width = width // scale
        self.height = height // scale
        self.surface = pygame.Surface((self.width, self.height))
        self.time = 0

    def update(self, dt):
        self.time += dt
        for y in range(self.height):
            for x in range(self.width):
                # normalized coordinates [-1,1]
                nx = x / self.width * 2 - 1
                ny = y / self.height * 2 - 1

                # simple 2D “raymarchish” pattern: moving waves + radial gradient
                r = math.sqrt(nx*nx + ny*ny)
                v = math.sin(10*r - self.time*3) + math.cos(5*nx + self.time*2)
                color = int((v + 2) / 4 * 255)  # map [-2,2] -> [0,255]

                # trippy RGB mix
                self.surface.set_at((x, y), (color, 255 - color, (color * 2) % 256))

    def render(self, target_surface):
        scaled = pygame.transform.scale(self.surface, (SCREEN_W, SCREEN_H))
        target_surface.blit(scaled, (0, 0))

# ---------- MAIN ----------
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()
bg = ProceduralBG(SCREEN_W, SCREEN_H, scale=4)

running = True
while running:
    dt = clock.tick(60) / 1000 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    bg.update(dt)
    bg.render(screen) 

    # Scale up for display
    pygame.display.flip()
    clock.tick(30)

pygame.quit()

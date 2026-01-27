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
                # normalized screen coords [-1,1]
                nx = x / self.width * 2 - 1
                ny = y / self.height * 2 - 1

                color_acc = 0.0
                weight_acc = 0.0

                # number of depth layers (more = deeper but slower)
                DEPTH_STEPS = 6

                for i in range(DEPTH_STEPS):
                    # depth from near → far
                    z = i / DEPTH_STEPS

                    # perspective warp (far layers shrink)
                    px = nx * (1 + z * 1.5)
                    py = ny * (1 + z * 1.5)

                    r = math.sqrt(px*px + py*py)

                    # wave field (slower movement in the distance)
                    v = (
                        math.sin(10*r - self.time*(3 - z*2)) +
                        math.cos(5*px + self.time*(2 - z))
                    )

                    # depth falloff (fog)
                    weight = math.exp(-z * 2.5)

                    color_acc += v * weight
                    weight_acc += weight

                # normalize accumulated value
                v = color_acc / weight_acc

                # map to color
                color = int((v + 2) / 4 * 255)
                color = max(0, min(255, color))

                # depth-based shading
                self.surface.set_at(
                    (x, y),
                    (
                        color,
                        int(color * 0.7),
                        int(255 - color * 0.5)
                    )
                )


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

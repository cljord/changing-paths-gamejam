import pygame
import math
import sys

DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

TILE_SIZE = 32
FPS = 60

level = [
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

def point_inside_block(x, y):
  if x < 0 or x > DISPLAY_WIDTH or y < 0 or y > DISPLAY_HEIGHT:
    return True
  level_x = int(x // TILE_SIZE)
  level_y = int(y // TILE_SIZE)
  return level[level_x][level_y] == 1

class Light:
  def __init__(self, x, y, num_rays):
    self.x = x
    self.y = y
    self.num_rays = num_rays
    self.intersections = []

  def init_rays(self):
    rays = []
    for i in range(0, self.num_rays):
      angle = ((2 * math.pi) / self.num_rays) * i
      rays.append(Ray(self.x, self.y, angle))
    return rays

  def update(self):
    rays = self.init_rays()
    self.intersections = []
    for ray in rays:
      intersection = ray.compute_level_intersection_point()
      self.intersections.append(intersection)

  def render(self):
    pygame.draw.circle(display, (255, 0, 0), (self.x, self.y), 3)
    for intersection in self.intersections:
      pygame.draw.line(display, (255, 0, 0), (self.x, self.y), (intersection[0], intersection[1]))

class Ray:
  def __init__(self, x, y, angle):
    self.x = x
    self.y = y
    self.angle = angle

  def compute_level_intersection_point(self):
    x = 0
    y = 0
    steps = [c * 0.1 for c in range(0, 1000)]
    for c in steps:
      x += self.x + c * math.cos(self.angle)
      y += self.y + c * math.sin(self.angle)
      if point_inside_block(x, y):
        break
    return x, y

class Player:
  def __init__(self, x, y):
    self.x = x
    self.y = y

pygame.init()
display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
is_game_running = True
clock = pygame.Clock()

def draw_level():
  for row_index, row in enumerate(level):
    for column_index, entry in enumerate(row):
      if not entry:
        continue
      x = column_index * TILE_SIZE
      y = row_index * TILE_SIZE
      rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
      pygame.draw.rect(display, (255, 255, 255), rect, 1)

light_x = 0
light_y = 0
while is_game_running:
  display.fill((0, 0, 0))
  dt = clock.tick(FPS)
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      is_game_running = False
      pygame.quit()
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        is_game_running = False
        pygame.quit()
      if event.key == pygame.K_LEFT:
        light_x -= 1
      if event.key == pygame.K_RIGHT:
        light_x += 1
      if event.key == pygame.K_UP:
        light_y -= 1
      if event.key == pygame.K_DOWN:
        light_y += 1

  draw_level()
  light = Light(200 + light_x, 200 + light_y, 1024)
  light.update()
  light.render()

  pygame.display.flip()

sys.exit(0)
import pygame
import math
import sys

DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

TILE_SIZE = 32
FPS = 60

def compute_middle_of_tile_in_pixels(tile_x, tile_y):
  return (tile_x * TILE_SIZE) + (TILE_SIZE / 2), (tile_y * TILE_SIZE) + (TILE_SIZE / 2)

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
  return level[level_y][level_x] == 1

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

  def patrol(self):
    pass

  def update(self):
    rays = self.init_rays()
    self.intersections = []
    for ray in rays:
      intersection = ray.compute_level_intersection_point()
      self.intersections.append(intersection)

  def render_visibility_polygon(self):
    for index, intersection in enumerate(self.intersections):
      next_intersection = self.intersections[(index + 1) % len(self.intersections)]
      triangle = [(self.x, self.y), (intersection[0], intersection[1]), (next_intersection[0], next_intersection[1])]
      pygame.draw.polygon(display, (255, 0, 0), triangle)

  def render(self):
    self.render_visibility_polygon()
    pygame.draw.circle(display, (255, 255, 0), (self.x, self.y), 10)

class Ray:
  def __init__(self, x, y, angle):
    self.x = x
    self.y = y
    self.angle = self.normalise_angle(angle)

  def normalise_angle(self, angle):
    angle = angle % (2 * math.pi)
    if angle < 0:
      angle = (2 * math.pi) + angle
    return angle

  def compute_level_intersection_point(self):
    x = 0
    y = 0
    steps = [c * 2 for c in range(0, 1500)]
    for c in steps:
      x = self.x + c * math.cos(self.angle)
      y = self.y + c * math.sin(self.angle)
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

light_x, light_y = compute_middle_of_tile_in_pixels(3, 3)
light_speed = 100

while is_game_running:
  display.fill((0, 0, 0))
  dt = clock.tick(FPS) / 1000

  light_dx = 0
  light_dy = 0

  keys = pygame.key.get_pressed()
  if keys[pygame.K_LEFT]:
    light_dx -= light_speed
  if keys[pygame.K_RIGHT]:
    light_dx += light_speed
  if keys[pygame.K_UP]:
    light_dy -= light_speed
  if keys[pygame.K_DOWN]:
    light_dy += light_speed
  if keys[pygame.K_ESCAPE]:
    is_game_running = False
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      is_game_running = False

  light_x += light_dx * dt
  light_y += light_dy * dt

  draw_level()
  light = Light(light_x, light_y, 256)
  light.update()
  light.render()

  pygame.display.flip()

pygame.quit()
sys.exit(0)
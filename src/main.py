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

def distance(x1, x2, y1, y2):
  return math.sqrt(((x2 - x1) ** 2) + ((y2 - y1) ** 2))

class Goal:
  def __init__(self, tile_x, tile_y):
    self.x, self.y = compute_middle_of_tile_in_pixels(tile_x, tile_y)
    self.w = 10
    self.h = 10

  def update(self, dt):
    pass

  def render(self):
    pygame.draw.rect(display, (0, 255, 0), (self.x - self.w//2, self.y - self.h//2, self.w, self.h))

class Light:
  def __init__(self, x, y, num_rays):
    self.x = x
    self.y = y
    self.num_rays = num_rays
    self.intersections = []
    self.patrol_route = [(3, 3), (16, 3), (16, 11), (3, 11)]
    self.current_patrol_route_index = 1
    self.speed = 50

  def init_rays(self):
    rays = []
    for i in range(0, self.num_rays):
      angle = ((2 * math.pi) / self.num_rays) * i
      rays.append(Ray(self.x, self.y, angle))
    return rays

  def patrol(self, dt):
    target_tile = self.patrol_route[self.current_patrol_route_index]
    target_point = compute_middle_of_tile_in_pixels(*target_tile)
    x_distance = target_point[0] - self.x
    y_distance = target_point[1] - self.y
    angle = math.atan2(y_distance, x_distance)
    dx = math.cos(angle) * self.speed
    dy = math.sin(angle) * self.speed
    self.x += dx * dt
    self.y += dy * dt
    if math.sqrt((x_distance ** 2) + (y_distance ** 2)) < 2:
      self.current_patrol_route_index += 1
      self.current_patrol_route_index %= len(self.patrol_route)

  def update(self, dt):
    rays = self.init_rays()
    self.intersections = []
    for ray in rays:
      intersection = ray.compute_level_intersection_point()
      self.intersections.append(intersection)
    self.patrol(dt)

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
    self.w = 10
    self.h = 20
    self.dx = 0
    self.dy = 0
    self.speed = 75
    self.gravity = 100
    self.jump_velocity = -200
    self.on_ground = False

  def update(self, dt):
    keys = pygame.key.get_pressed()
    # horizontal movement
    if keys[pygame.K_LEFT]:
      self.dx = -self.speed
    elif keys[pygame.K_RIGHT]:
      self.dx = self.speed
    else:
      self.dx = 0

    # jump
    if keys[pygame.K_UP] and self.on_ground:
      self.dy = self.jump_velocity
      self.on_ground = False
    self.dy += self.gravity * dt

    # axis separation, move x first, then y
    self.x += self.dx * dt

    left = self.x
    right = self.x + self.w - 1
    top = self.y
    bottom = self.y + self.h - 1
    if self.dx > 0:
      if point_inside_block(right, top + 1) or point_inside_block(right, bottom - 1):
        # snap player and remove x velocity component
        tile_x = int(right // TILE_SIZE)
        self.x = tile_x * TILE_SIZE - self.w
        self.dx = 0
    if self.dx < 0:
      if point_inside_block(left, top + 1) or point_inside_block(left, bottom - 1):
        tile_x = int(left // TILE_SIZE) + 1
        self.x = tile_x * TILE_SIZE
        self.dx = 0
    
    self.y += self.dy * dt

    # recompute edges again
    left = self.x
    right = self.x + self.w - 1
    top = self.y
    bottom = self.y + self.h - 1
    if self.dy > 0:
      if point_inside_block(right - 1, bottom) or point_inside_block(left + 1, bottom):
        tile_y = int(bottom // TILE_SIZE)
        self.y = tile_y * TILE_SIZE - self.h
        self.dy = 0
        self.on_ground = True
    if self.dy < 0:
      if point_inside_block(right - 1, top) or point_inside_block(left + 1, top):
        tile_y = int(top // TILE_SIZE) + 1
        self.y = tile_y * TILE_SIZE
        self.dy = 0

  def render(self):
    pygame.draw.rect(display, (0, 255, 255), (self.x, self.y, self.w, self.h))
  
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
light = Light(light_x, light_y, 256)
player = Player(*compute_middle_of_tile_in_pixels(12, 12))
goal = Goal(12, 4)

while is_game_running:
  display.fill((0, 0, 0))
  dt = clock.tick(FPS) / 1000

  keys = pygame.key.get_pressed()
  if keys[pygame.K_ESCAPE]:
    is_game_running = False
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      is_game_running = False

  draw_level()
  light.update(dt)
  light.render()
  player.update(dt)
  player.render()
  goal.render()

  pygame.display.flip()

pygame.quit()
sys.exit(0)
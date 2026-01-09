from dataclasses import dataclass
import json
import math
import os
import pygame
import sys
from enum import Enum

DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

TILE_SIZE = 32
FPS = 60

class Light:
  def __init__(self, tilemap, x, y, patrol_route, num_rays=256):
    self.tilemap = tilemap
    self.x = x
    self.y = y
    self.num_rays = num_rays
    self.intersections = []
    self.patrol_route = patrol_route
    self.current_patrol_route_index = 1
    self.speed = 100
    self.triangles = []

  def init_rays(self):
    rays = []
    for i in range(0, self.num_rays):
      angle = ((2 * math.pi) / self.num_rays) * i
      rays.append(Ray(self.tilemap, self.x, self.y, angle))
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
    self.triangles = []
    for index, intersection in enumerate(self.intersections):
      next_intersection = self.intersections[(index + 1) % len(self.intersections)]
      triangle = [(self.x, self.y), (intersection[0], intersection[1]), (next_intersection[0], next_intersection[1])]
      self.triangles.append(triangle)
      pygame.draw.polygon(display, (255, 0, 0), triangle)

  def render(self):
    self.render_visibility_polygon()
    pygame.draw.circle(display, (255, 255, 0), (self.x, self.y), 10)


def compute_middle_of_tile_in_pixels(tile_x, tile_y):
  return (tile_x * TILE_SIZE) + (TILE_SIZE / 2), (tile_y * TILE_SIZE) + (TILE_SIZE / 2)

def point_inside_block(level, x, y):
  if x < 0 or x > DISPLAY_WIDTH or y < 0 or y > DISPLAY_HEIGHT:
    return True
  level_x = int(x // TILE_SIZE)
  level_y = int(y // TILE_SIZE)
  return level[level_y][level_x] == 1

def distance(x1, x2, y1, y2):
  return math.sqrt(((x2 - x1) ** 2) + ((y2 - y1) ** 2))

# point in polygon functions from this video by Erudite
# https://www.youtube.com/watch?v=TA8XQgiao4M
def is_between(value, y1, y2):
  # check if y value of point is "sandwiched"
  # between the y values of two points
  # that we iterate over in point-in-polygon testing
  if ((y1 > y2 and y1 >= value > y2) or
      y2 >= value > y1):
    return True
  return False

def calc_intersection(point, side_a, side_b):
  """
           / (x1, y1)
          /
(xp, yp) / <- we have y, what is x?
        /
       / (x2, y2)
=> after calculating (xp, yp): if point is greater than
calculated intersection, we can ignore it because we shoot ray to the right
therefore: if greater => ray shot to right won't hit the line of the polygon
  """
  m = (side_b[1] - side_a[1]) / (side_b[0] - side_a[0])
  x = ((point[1] - side_a[1])/m) + side_a[0]
  y = point[1]
  return (x, y)

def is_inside(point, polygon):
  count = 0
  for i in range(0, len(polygon)):
    a = polygon[i-1]
    b = polygon[i]
    # a[1] != b[1] checks whether y coords of
    # the two points are on one line => if so, no need to check ray
    if (a[1] != b[1] and
        is_between(point[1], a[1], b[1])):
      intersection = calc_intersection(point, a, b)
      if intersection[0] >= point[0]:
        count += 1
  if count % 2 == 0:
    return False
  return True

class Goal:
  def __init__(self, tile_x, tile_y):
    self.w = 10
    self.h = 10
    self.x, self.y = compute_middle_of_tile_in_pixels(tile_x, tile_y)
    self.x -= self.w // 2
    self.y -= self.h // 2

  def update(self, dt):
    pass

  def render(self):
    pygame.draw.rect(display, (0, 255, 0), (self.x, self.y, self.w, self.h))

  def set_tile_position(self, tile_x, tile_y):
    self.x, self.y = compute_middle_of_tile_in_pixels(tile_x, tile_y)
    self.x -= self.w // 2
    self.y -= self.h // 2



class Ray:
  def __init__(self, tilemap, x, y, angle):
    self.tilemap = tilemap
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
      if point_inside_block(self.tilemap, x, y):
        break
    return x, y

class Player:
  def __init__(self, tilemap, x, y):
    self.tilemap = tilemap
    self.x = x
    self.y = y
    self.w = 10
    self.h = 20
    self.dx = 0
    self.dy = 0
    self.speed = 200
    self.gravity = 300
    self.gravity_cut = 10 # extra gravity when jump is released
    self.jump_velocity = -300
    self.on_ground = False
    self.jump_timer = 0
    self.max_jump_timer = 0.3

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
      self.dy += self.jump_velocity
      self.on_ground = False
    
    if not keys[pygame.K_UP] and self.dy < 0:
      self.dy += self.gravity * self.gravity_cut * dt

    self.dy += self.gravity * dt

    # axis separation, move x first, then y
    self.x += self.dx * dt

    left = self.x
    right = self.x + self.w - 1
    top = self.y
    bottom = self.y + self.h - 1
    if self.dx > 0:
      if point_inside_block(self.tilemap, right, top + 1) or point_inside_block(self.tilemap, right, bottom - 1):
        # snap player and remove x velocity component
        tile_x = int(right // TILE_SIZE)
        self.x = tile_x * TILE_SIZE - self.w
        self.dx = 0
    if self.dx < 0:
      if point_inside_block(self.tilemap, left, top + 1) or point_inside_block(self.tilemap, left, bottom - 1):
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
      if point_inside_block(self.tilemap, right - 1, bottom) or point_inside_block(self.tilemap, left + 1, bottom):
        tile_y = int(bottom // TILE_SIZE)
        self.y = tile_y * TILE_SIZE - self.h
        self.dy = 0
        self.on_ground = True
        self.jump_timer = 0
    if self.dy < 0:
      if point_inside_block(self.tilemap, right - 1, top) or point_inside_block(self.tilemap, left + 1, top):
        tile_y = int(top // TILE_SIZE) + 1
        self.y = tile_y * TILE_SIZE
        self.dy = 0

  def render(self):
    pygame.draw.rect(display, (0, 255, 255), (self.x, self.y, self.w, self.h))
  
pygame.init()
display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
is_game_running = True
clock = pygame.Clock()

def draw_tilemap(tilemap):
  for row_index, row in enumerate(tilemap):
    for column_index, entry in enumerate(row):
      if not entry:
        continue
      x = column_index * TILE_SIZE
      y = row_index * TILE_SIZE
      rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
      pygame.draw.rect(display, (255, 255, 255), rect, 1)

@dataclass
class Level:
  tilemap: list[list[int]]
  lights: list[Light]
  player: Player
  goal: Goal

current_level_index = 1

def load_level(level_file):
  level = None
  with open("./src/levels.json", "r") as levels:
    level_data = json.load(levels)["1"]
    tilemap = level_data["tilemap"]
    player_start_pos = level_data["player_start_pos"]
    player = Player(tilemap, *compute_middle_of_tile_in_pixels(*player_start_pos))
    goal_pos = level_data["goal_pos"]
    goal = Goal(*goal_pos)
    lights = []
    for light in level_data["lights"]:
      start_pos = light["start_pos"]
      patrol_route = [tuple(patrol_point) for patrol_point in light["patrol_route"]]
      lights.append(Light(tilemap, *compute_middle_of_tile_in_pixels(start_pos[0], start_pos[1]), patrol_route))
    level = Level(tilemap, lights, player, goal)
    #level_json_loading_time = os.path.getmtime("./src/levels.json")
  return level

current_level = load_level("./src/levels.json")
level_json_loading_time = 0

#light_x, light_y = compute_middle_of_tile_in_pixels(3, 3)
#light = Light(current_level, light_x, light_y)
#player = Player(current_level, *compute_middle_of_tile_in_pixels(12, 12))
#goal = Goal(12, 4)

class game_states(Enum):
  play_state = 1
  dead_state = 2
  finish_state = 3

current_game_state = game_states.play_state

def display_death_text():
  ...

while is_game_running:
  display.fill((0, 0, 0))
  dt = clock.tick(FPS) / 1000

  #if os.path.getmtime("./src/levels.json") != level_json_loading_time:
    #with open("./src/levels.json", "r") as levels:
      #current_level = json.load(levels)["1"]
      #level_json_loading_time = os.path.getmtime("./src/levels.json")
      #player = Player(current_level, player.x, player.x)
      #light = Light(current_level, light.x, light.y, 256)

  keys = pygame.key.get_pressed()
  if keys[pygame.K_ESCAPE]:
    is_game_running = False
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      is_game_running = False

  draw_tilemap(current_level.tilemap)
  if current_game_state == game_states.play_state:
    for light in current_level.lights:
      light.update(dt)
    current_level.player.update(dt)

    for light in current_level.lights:
      light.render()
    current_level.goal.render()
    current_level.player.render()

  if current_game_state == game_states.dead_state:
    for light in current_level.lights:
      light.update(dt)
    current_level.player.update(dt)

    for light in current_level.lights:
      light.render()
    current_level.goal.render()
    current_level.player.render()

  for light in current_level.lights:
    for triangle in light.triangles:
      if is_inside((current_level.player.x, current_level.player.y), triangle):
        current_game_state = game_states.dead_state
        print("hitting me brooo")

  pygame.display.flip()

pygame.quit()
sys.exit(0)
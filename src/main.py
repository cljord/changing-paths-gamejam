from dataclasses import dataclass
import json
import math
import random
import pygame
import sys
from enum import Enum

DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

TILE_SIZE = 32
FPS = 60

world = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
camera_shake = 0
camera_shake_decay = 0.9
slowdown = 1

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
    self.rays = self.init_rays()
    self.time = 0
    self.light_surface = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
    self.noise_surface = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
    self.bloom_surface = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)

  def init_rays(self):
    rays = []
    for i in range(0, self.num_rays):
      angle = ((2 * math.pi) / self.num_rays) * i
      rays.append(Ray(self.tilemap, self.x, self.y, angle))
    return rays

  def update_rays(self):
    for i, ray in enumerate(self.rays):
      angle = ((2 * math.pi) / self.num_rays) * i
      self.rays[i].x = self.x
      self.rays[i].y = self.y
      self.rays[i].angle = angle

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
    if math.sqrt((x_distance ** 2) + (y_distance ** 2)) < 5:
      self.current_patrol_route_index += 1
      self.current_patrol_route_index %= len(self.patrol_route)

  def update(self, dt):
    self.time += dt * 0.5
    self.update_rays()
    self.intersections = []
    for ray in self.rays:
      intersection = ray.compute_level_intersection_point()
      self.intersections.append(intersection)
    self.patrol(dt)

  def render_visibility_polygon(self):
    self.triangles = []
    self.light_surface.fill((0, 0, 0, 0))
    light_brightness = int(180 + math.sin(self.time * 3) * 40)
    for index, intersection in enumerate(self.intersections):
      next_intersection = self.intersections[(index + 1) % len(self.intersections)]
      triangle = [(self.x, self.y), (intersection[0], intersection[1]), (next_intersection[0], next_intersection[1])]
      self.triangles.append(triangle)
      pygame.draw.polygon(self.light_surface, (255, 0, 0, light_brightness), triangle)
    self.create_noise()
    self.light_surface.blit(self.noise_surface, (0, 0), special_flags = pygame.BLEND_ADD)
    self.render_bloom(light_brightness)
    world.blit(self.light_surface, (0, 0))

  # TODO implement bloom myself again so I know what's going on here
  def render_bloom(self, intensity):
    self.bloom_surface.fill((0, 0, 0, 0))

    # Extract only bright light (kill dark reds)
    self.bloom_surface.blit(self.light_surface, (0, 0))
    self.bloom_surface.fill(
        (intensity, 0, 0, 255),
        special_flags=pygame.BLEND_MULT
    )

    # Strong blur
    small = pygame.transform.smoothscale(
        self.bloom_surface,
        (DISPLAY_WIDTH // 15, DISPLAY_HEIGHT // 15)
    )
    blurred = pygame.transform.smoothscale(
        small,
        (DISPLAY_WIDTH, DISPLAY_HEIGHT)
    )

    # Additive blend ONLY
    world.blit(blurred, (0, 0), special_flags=pygame.BLEND_ADD)

  def create_noise(self):
    self.noise_surface.fill((0, 0, 0, 0))
    for _ in range(2500):
      x = random.randint(0, DISPLAY_WIDTH)
      y = random.randint(0, DISPLAY_HEIGHT)
      alpha = random.randint(20, 50)
      self.noise_surface.set_at((x, y), (255, 100, 0, alpha))

  def render(self):
    self.render_visibility_polygon()
    pygame.draw.circle(world, (255, 255, 0), (self.x, self.y), 10)

def compute_middle_of_tile_in_pixels(tile_x, tile_y):
  return (tile_x * TILE_SIZE) + (TILE_SIZE // 2), (tile_y * TILE_SIZE) + (TILE_SIZE // 2)

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
    pygame.draw.rect(world, (0, 255, 0), (self.x, self.y, self.w, self.h))

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
    steps = [c * 2 for c in range(0, 500)]
    for c in steps:
      x = self.x + c * math.cos(self.angle)
      y = self.y + c * math.sin(self.angle)
      if point_inside_block(self.tilemap, x, y):
        break
    return x, y

particles = []

class RunParticle:
  PARTICLE_WIDTH = 7
  PARTICLE_HEIGHT = 7
  DECAY_FACTOR = 3
  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.w = self.PARTICLE_WIDTH
    self.h = self.PARTICLE_HEIGHT
    self.alive = True
    self.decay_factor = self.DECAY_FACTOR
    self.lifetime = 0
    self.starting_rotation = random.random()*180

  def update(self, dt):
    self.lifetime += dt
    self.w -= self.decay_factor * dt
    self.h -= self.decay_factor * dt
    if self.w <= 0.1 or self.h <= 0.1:
      self.alive = False

  def render(self):
    rect_surf = pygame.Surface((math.floor(self.w), math.floor(self.h)), pygame.SRCALPHA)
    pygame.draw.rect(rect_surf, (78, 78, 78), rect_surf.get_rect())
    rotated_surface = pygame.transform.rotate(rect_surf, (self.starting_rotation + self.lifetime)*180)
    rotated_surface_rect = rotated_surface.get_rect(center=(self.x, self.y))
    world.blit(rotated_surface, rotated_surface_rect)

class Player:
  def __init__(self, tilemap, x, y):
    self.tilemap = tilemap
    self.w = 10
    self.h = 20
    self.x = x - self.w // 2
    self.y = y - self.h // 2
    self.dx = 0
    self.dy = 0
    self.speed = 200
    self.gravity = 300
    self.gravity_cut = 10 # extra gravity when jump is released
    self.jump_velocity = -300
    self.on_ground = False
    self.jump_timer = 0
    self.max_jump_timer = 0.3
    self.squish_factor = 0
    self.particle_timer = 0
    self.particle_spawn_time = 0.01
    # TODO add coyote time + check for leaping off a tile (would allow a jump in midair currently)
    # because on_ground is never changed)

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
      else:
        if self.on_ground:
          if self.particle_timer > 0:
            self.particle_timer -= dt
          else:
            self.particle_timer = self.particle_spawn_time
            particles.append(RunParticle(self.x, self.y + self.h))
    elif self.dx < 0:
      if point_inside_block(self.tilemap, left, top + 1) or point_inside_block(self.tilemap, left, bottom - 1):
        tile_x = int(left // TILE_SIZE) + 1
        self.x = tile_x * TILE_SIZE
        self.dx = 0
      else:
        if self.on_ground:
          if self.particle_timer > 0:
            self.particle_timer -= dt
          else:
            self.particle_timer = self.particle_spawn_time
            particles.append(RunParticle(self.x + self.w, self.y + self.h))
    else:
      self.particle_timer = 0
    
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
        if not self.on_ground:
          self.squish_factor = 8
        self.on_ground = True
        self.jump_timer = 0
    if self.dy < 0:
      if point_inside_block(self.tilemap, right - 1, top) or point_inside_block(self.tilemap, left + 1, top):
        tile_y = int(top // TILE_SIZE) + 1
        self.y = tile_y * TILE_SIZE
        self.dy = 0

    if abs(self.squish_factor) < 0.1:
      self.squish_factor = 0

    if self.squish_factor > 0:
        self.squish_factor -= 20 * dt
        if self.squish_factor < 0:
            self.squish_factor = 0
    
    self.on_ground = (
    point_inside_block(self.tilemap, left + 1, bottom + 1) or
    point_inside_block(self.tilemap, right - 1, bottom + 1)
    )

  def render(self):
    pygame.draw.rect(world, (0, 255, 255), (self.x - self.squish_factor // 2, self.y + self.squish_factor, self.w + self.squish_factor, self.h - self.squish_factor))
  
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
      pygame.draw.rect(world, (255, 255, 255), rect, 2)

@dataclass
class Level:
  tilemap: list[list[int]]
  lights: list[Light]
  player: Player
  goal: Goal

current_level_index = 1

def load_level(all_level_data, current_level_index):
  current_level_data = all_level_data[str(current_level_index)]
  tilemap = current_level_data["tilemap"]
  player_start_pos = current_level_data["player_start_pos"]
  player = Player(tilemap, *compute_middle_of_tile_in_pixels(*player_start_pos))
  goal_pos = current_level_data["goal_pos"]
  goal = Goal(*goal_pos)
  lights = []
  for light in current_level_data["lights"]:
    start_pos = light["start_pos"]
    patrol_route = [tuple(patrol_point) for patrol_point in light["patrol_route"]]
    lights.append(Light(tilemap, *compute_middle_of_tile_in_pixels(start_pos[0], start_pos[1]), patrol_route))
  level = Level(tilemap, lights, player, goal)
  #level_json_loading_time = os.path.getmtime("./src/levels.json")
  global particles 
  particles = []
  return level

def load_level_data_from_file(level_file):
  with open(level_file, "r") as levels:
    return json.load(levels)

all_level_data = load_level_data_from_file("./src/levels.json")
current_level = load_level(all_level_data, current_level_index)
level_json_loading_time = 0

class game_states(Enum):
  play_state = 1
  dead_state = 2
  goal_state = 3
  finish_state = 3

current_game_state = game_states.play_state

def display_death_text():
  ...

while is_game_running:
  world.fill((0, 0, 0))
  dt = clock.tick(FPS) * slowdown / 1000

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

    for light in current_level.lights:
      for triangle in light.triangles:
        if is_inside((current_level.player.x + current_level.player.w // 2, current_level.player.y + current_level.player.h // 2), triangle):
          pass
          current_game_state = game_states.dead_state
          camera_shake = 3
          slowdown = 0.2
    
    dead_particles = []
    for particle in particles:
      particle.update(dt)
      if particle.alive:
        particle.render()
      else:
        dead_particles.append(particle)

    for particle in dead_particles:
      particles.remove(particle)

    player_rect = pygame.Rect(current_level.player.x, current_level.player. y, current_level.player.w, current_level.player.h)
    goal_rect = pygame.Rect(current_level.goal.x, current_level.goal.y, current_level.goal.w, current_level.goal.h)
    if player_rect.colliderect(goal_rect):
      current_level_index += 1
      slowdown = 1
      current_level = load_level(all_level_data, current_level_index)
      #current_game_state = game_states.goal_state
      # TODO add check for whether we are done with all levels
      # TODO if so, display finish logo
      print("booya")

  if current_game_state == game_states.dead_state:
    for light in current_level.lights:
      light.update(dt)
    for light in current_level.lights:
      light.render()
    current_level.goal.render()
    current_level.player.render()

    dead_particles = []
    for particle in particles:
      particle.update(dt)
      if particle.alive:
        particle.render()
      else:
        dead_particles.append(particle)

    for particle in dead_particles:
      particles.remove(particle)

  if keys[pygame.K_r]:
    current_level = load_level(all_level_data, current_level_index)
    slowdown = 1
    particles = []
    current_game_state = game_states.play_state

  # all these postprocessing effects are from https://dev.to/chrisgreening/simulating-simple-crt-and-glitch-effects-in-pygame-1mf1
  # add scanlines
  scanline_surface = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
  for y in range(0, DISPLAY_HEIGHT, 4):
    pygame.draw.line(scanline_surface, (0, 0, 0, 60), (0, y), (DISPLAY_WIDTH, y))

  world.blit(scanline_surface, (0, 0))

  # apply flicker - commented out because this doesn't look so good
  #if random.randint(0, 20) == 0:
    #flicker_surface = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.SRCALPHA)
    #flicker_surface.fill((255, 255, 255, 5))
    #world.blit(flicker_surface, (0, 0))

  # add glow/bloom
  #glow_surf = pygame.transform.smoothscale(world, (DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2))
  #glow_surf = pygame.transform.smoothscale(glow_surf, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
  #glow_surf.set_alpha(100)
  #world.blit(glow_surf, (0, 0))

  glitch_surface = world.copy()
  if random.random() < 0.1:
    shift_amount = 30
    y_start = random.randint(0, DISPLAY_HEIGHT - 20)
    slice_height = random.randint(5, 20)
    offset = random.randint(-shift_amount, shift_amount)

    slice_area = pygame.Rect(0, y_start, DISPLAY_WIDTH, slice_height)
    slice_copy = glitch_surface.subsurface(slice_area).copy()
    glitch_surface.blit(slice_copy, (offset, y_start))

  world.blit(glitch_surface, (0, 0))
  

  # chromatic aberration/RGB shift effect
  # original code in article for postprocessing effect mentioned above
  # was not working so well, so used ChatGPT to improve it
  # basically: isolate R, G, B channels with BLEND_MULT
  # (multiplying e.g. original surface with red fill means
  # only red pixels survive at original strength)
  # then combine with a slight offset
  # RED channel
  if random.random() < 0.02:
    shift = random.randint(1, 3)
    rgb = world.copy()

    red = rgb.copy()
    red.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)
    world.blit(red, (-shift, 0), special_flags=pygame.BLEND_ADD)

    # GREEN channel
    green = rgb.copy()
    green.fill((0, 255, 0), special_flags=pygame.BLEND_MULT)
    world.blit(green, (0, 0), special_flags=pygame.BLEND_ADD)

    # BLUE channel
    blue = rgb.copy()
    blue.fill((0, 0, 255), special_flags=pygame.BLEND_MULT)
    world.blit(blue, (shift, 2), special_flags=pygame.BLEND_ADD)

  camera_x_offset, camera_y_offset = 0, 0
  if camera_shake > 0.1:
    int_shake = int(camera_shake)
    camera_x_offset = random.randint(-int_shake, int_shake)
    camera_y_offset = random.randint(-int_shake, int_shake)
    camera_shake *= camera_shake_decay
  if slowdown < 1:
    slowdown = min(slowdown + dt, 1)

  # pixelate - commented out for now because this has to be done last, so affects final
  # call to blitting of the world surface, but just keeping this in here to maybe apply later
  small_surf = pygame.transform.scale(world, (DISPLAY_WIDTH // 1.5, DISPLAY_HEIGHT // 1.5))
  display.blit(pygame.transform.scale(small_surf, (DISPLAY_WIDTH, DISPLAY_HEIGHT)), (camera_x_offset, camera_y_offset))

  #display.blit(world, (camera_x_offset, camera_y_offset))

  pygame.display.flip()

pygame.quit()
sys.exit(0)
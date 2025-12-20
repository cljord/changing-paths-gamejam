import pygame
import sys

DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

class Ray:
  def __init__(self, x, y, angle):
    self.x = x
    self.y = y
    self.angle = angle

  def find_intersection_point(self):
    pass

  def update(self):
    self.find_intersection_point()

  def draw(self):

pygame.init()
display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
is_game_running = True

while is_game_running:
  display.fill((0, 0, 0))
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      is_game_running = False
      pygame.quit()

  pygame.display.flip()

sys.exit(0)
import pygame
import math
import sys

# Constants
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 728
MAP_WIDTH = 8
MAP_HEIGHT = 8
TILE_SIZE = 64
FOV = math.pi / 3
NUM_RAYS = 240
MAX_DEPTH = 800
DELTA_ANGLE = FOV / NUM_RAYS
DISTANCE = NUM_RAYS / (2 * math.tan(FOV / 2))
PROJ_COEFF = 3 * DISTANCE * TILE_SIZE
SCALE = SCREEN_WIDTH // NUM_RAYS

# Map (1 = wall, 0 = empty)
game_map = [
    [1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,1],
    [1,0,1,0,1,0,0,1],
    [1,0,1,0,1,0,0,1],
    [1,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1]
]

# Player
player_pos = [TILE_SIZE + TILE_SIZE // 2, TILE_SIZE + TILE_SIZE // 2]
player_angle = 0
player_speed = 2

def can_move(x, y):
    """Check if the position (x, y) is inside an empty map tile."""
    i = int(x / TILE_SIZE)
    j = int(y / TILE_SIZE)
    if 0 <= i < len(game_map[0]) and 0 <= j < len(game_map):
        return game_map[j][i] == 0
    return False

def line_of_sight(px, py, ex, ey):
    """Return True if there is a clear line of sight between player and enemy."""
    dx = ex - px
    dy = ey - py
    distance = math.hypot(dx, dy)
    steps = int(distance / 4)  # step size 4 pixels
    for step in range(1, steps):
        x = px + dx * step / steps
        y = py + dy * step / steps
        if not can_move(x, y):
            return False
    return True

# Enemies
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alive = True

    def distance_to_player(self):
        return math.hypot(player_pos[0] - self.x, player_pos[1] - self.y)

    def move_toward_player(self):
        angle = math.atan2(player_pos[1] - self.y, player_pos[0] - self.x)
        dx = 0.5 * math.cos(angle)
        dy = 0.5 * math.sin(angle)
        new_x = self.x + dx
        new_y = self.y + dy
        i = int(new_x / TILE_SIZE)
        j = int(new_y / TILE_SIZE)
        if 0 <= i < len(game_map[0]) and 0 <= j < len(game_map) and game_map[j][i] == 0:
            self.x = new_x
            self.y = new_y

    def draw(self, screen):
        if not self.alive:
            return
        # Skip drawing if a wall blocks line of sight
        if not line_of_sight(player_pos[0], player_pos[1], self.x, self.y):
            return
        dx = self.x - player_pos[0]
        dy = self.y - player_pos[1]
        distance = math.hypot(dx, dy)
        angle = math.atan2(dy, dx) - player_angle
        if -FOV / 2 < angle < FOV / 2:
            proj_height = PROJ_COEFF / (distance + 0.0001)
            x = SCREEN_WIDTH // 2 + math.tan(angle) * DISTANCE - proj_height // 4
            y = SCREEN_HEIGHT // 2 - proj_height // 2
            pygame.draw.rect(screen, (255, 0, 0), (x, y, proj_height // 2, proj_height))

enemies = [
    Enemy(5 * TILE_SIZE, 5 * TILE_SIZE),
    Enemy(3 * TILE_SIZE, 6 * TILE_SIZE)
]

# Init
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# Raycasting
def ray_casting(screen, pos, angle):
    start_angle = angle - FOV / 2
    for ray in range(NUM_RAYS):
        cur_angle = start_angle + ray * DELTA_ANGLE
        sin_a = math.sin(cur_angle)
        cos_a = math.cos(cur_angle)

        for depth in range(0, MAX_DEPTH, 4):
            x = pos[0] + depth * cos_a
            y = pos[1] + depth * sin_a

            i = int(x / TILE_SIZE)
            j = int(y / TILE_SIZE)
            if game_map[j][i] == 1:
                depth *= math.cos(angle - cur_angle)  # fix fish-eye
                wall_height = PROJ_COEFF / (depth + 0.0001)
                color = 255 / (1 + depth * depth * 0.0001)
                pygame.draw.rect(screen, (color, color, color),
                                 (ray * SCALE, SCREEN_HEIGHT // 2 - wall_height // 2, SCALE, wall_height))
                break

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        player_angle -= 0.03
    if keys[pygame.K_d]:
        player_angle += 0.03
    if keys[pygame.K_w]:
        dx = player_speed * math.cos(player_angle)
        dy = player_speed * math.sin(player_angle)
        new_x = player_pos[0] + dx
        new_y = player_pos[1] + dy
        if can_move(new_x, new_y):
            player_pos[0] = new_x
            player_pos[1] = new_y
    if keys[pygame.K_s]:
        dx = player_speed * math.cos(player_angle)
        dy = player_speed * math.sin(player_angle)
        new_x = player_pos[0] - dx
        new_y = player_pos[1] - dy
        if can_move(new_x, new_y):
            player_pos[0] = new_x
            player_pos[1] = new_y

    # Shooting
    if keys[pygame.K_SPACE]:
        for enemy in enemies:
            if enemy.alive:
                dx = enemy.x - player_pos[0]
                dy = enemy.y - player_pos[1]
                angle = math.atan2(dy, dx)
                angle_diff = abs((angle - player_angle + math.pi) % (2 * math.pi) - math.pi)
                if angle_diff < 0.1 and enemy.distance_to_player() < 300:
                    enemy.alive = False

    screen.fill((0, 0, 0))
    ray_casting(screen, player_pos, player_angle)

    for enemy in enemies:
        if enemy.alive:
            enemy.move_toward_player()
        enemy.draw(screen)

    pygame.display.flip()
    clock.tick(60)

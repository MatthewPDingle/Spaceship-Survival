import pygame
import random
import math
import time

# Initialize Pygame
pygame.init()
hit_sound1 = pygame.mixer.Sound("assets/hit1.flac")
hit_sound2 = pygame.mixer.Sound("assets/hit2.flac")
hit_sound3 = pygame.mixer.Sound("assets/hit3.flac")
fire_sound1 = pygame.mixer.Sound("assets/fire1.flac")
fire_sound2 = pygame.mixer.Sound("assets/fire2.flac")
fire_sound3 = pygame.mixer.Sound("assets/fire3.flac")
hp_sound = pygame.mixer.Sound("assets/hp1.flac")

# Constants
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1200
ENEMY_SPAWN_DISTANCE = 500
LASER_RATE_LIMIT = 0.1
HEALTH_BAR_Y_OFFSET = -30
HEALTH_BAR_X_OFFSET = -16

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 255, 255)

# Create surfaces with per-pixel alpha for health bars
outline_surf = pygame.Surface((32, 6), pygame.SRCALPHA)
fill_surf = pygame.Surface((32, 6), pygame.SRCALPHA)
pygame.draw.rect(fill_surf, (0, 255, 0, 160), fill_surf.get_rect())
pygame.draw.rect(outline_surf, (255, 255, 255, 160), outline_surf.get_rect(), 1)

# Helper function for accumulated movement
def apply_movement(entity):
    entity.rect.x += int(entity.move_x)
    entity.move_x -= int(entity.move_x)
    entity.rect.y += int(entity.move_y)
    entity.move_y -= int(entity.move_y)

# Function to draw health bar
def draw_health_bar(surf, rect, health, max_health):
    if health < 0:
        health = 0
    bar_length = rect.width
    bar_height = 6
    fill_percent = health / max_health
    fill = fill_percent * bar_length

    # Update fill_surf based on current health
    fill_surf.fill((0, 0, 0, 0))  # Clear the surface
    pygame.draw.rect(fill_surf, (0, 255, 0, 48), (0, 0, fill, bar_height))

    # Draw outline
    outline_rect = rect
    pygame.draw.rect(outline_surf, (255, 255, 255, 48), outline_rect, 1)

    # Blit the surfaces onto the main surface
    surf.blit(fill_surf, rect.center)
    surf.blit(outline_surf, rect.center)

# Function to handle collisions between a sprite and a group
def check_collisions(sprite, group, dokill=True):
    if isinstance(sprite, pygame.sprite.Group):
        for s in sprite.sprites():
            hits = pygame.sprite.spritecollide(s, group, dokill)
            for hit in hits:
                if isinstance(hit, Enemy):
                    print("A: Player crashes into enemy")
                    s.health -= 100  # Assuming this is damage from enemy collision
                    if hit.health <= 0:
                        hit.enemy_death()  # Call enemy_death if the enemy is defeated
                elif isinstance(hit, HPPowerUp):  # Collision with HP power-up
                    print("A: Player hits HPPowerUp")
                    s.health += 20
                    if s.health > s.max_health:
                        s.health = s.max_health
                else:
                    print("A: Player weapon hits enemy")
                    s.health -= hit.damage  # Assuming damage attribute for other sprites
                    if s.health <= 0:
                        s.enemy_death()
                    # Play appropriate sound effects based on the projectile type
                    if isinstance(hit, GreenLaser):
                        hit_sound1.play()
                    elif isinstance(hit, BlueLaser):
                        hit_sound2.play()
                    elif isinstance(hit, DumbMissile):
                        hit_sound3.play()

                if s.health <= 0:
                    print("A: Entity killed")
                    s.kill()
                
    else:           
        hits = pygame.sprite.spritecollide(sprite, group, dokill)
        for hit in hits:
            print(f"B: Collision with {type(hit).__name__}")
            if isinstance(hit, Enemy):
                print("B: Player crashes into enemy")
                sprite.health -= 100
                if hit.health <= 0:
                    hit.enemy_death()  # Enemy handles its own death
            elif isinstance(hit, HPPowerUp):  # Handling HP power-up collision
                print("B: Player hits HPPowerUp")
                sprite.health += 20
                if sprite.health > sprite.max_health:
                    sprite.health = sprite.max_health
                hp_sound.play() 
            else:
                print("B: Enemy weapon hits player")
                sprite.health -= hit.damage
                if isinstance(hit, GreenLaser):
                    hit_sound1.play()
                elif isinstance(hit, BlueLaser):
                    hit_sound2.play()
                elif isinstance(hit, DumbMissile):
                    hit_sound3.play()

            if sprite.health <= 0:
                print ("B: Entity killed")
                sprite.kill()

# Function to check if a point is within a certain distance of the player
def is_near_player(x, y, distance):
    player_x, player_y = player.sprites()[0].rect.center  # Access the first sprite in the group
    return math.hypot(x - player_x, y - player_y) < distance

# Base class for weapons
class Weapon(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, image, speed, damage, range):
        super().__init__()
        self.original_image = image
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.angle = angle
        self.speed = speed
        self.move_x = 0
        self.move_y = 0
        self.damage = damage
        self.range = range  # Add range attribute
        self.traveled_distance = 0  # Track distance traveled

    def update(self):
        # Rotate weapon image based on current angle
        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 1) 
        self.rect = self.image.get_rect(center=self.rect.center) 
    
        # Calculate movement
        self.move_x -= self.speed * math.sin(math.radians(self.angle))
        self.move_y -= self.speed * math.cos(math.radians(self.angle))
        apply_movement(self)

         # Update traveled distance
        self.traveled_distance += self.speed

        # Remove weapon if it goes off-screen or exceeds range
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or \
           self.rect.left > SCREEN_WIDTH or self.rect.right < 0 or \
           self.traveled_distance > self.range:
            self.kill()

# Green laser weapon
class GreenLaser(Weapon):
    def __init__(self, x, y, angle):
        image = pygame.Surface((1, 30))
        image.fill(GREEN)
        super().__init__(x, y, angle, image, 1, 20, math.inf)
        
# Blue laser weapon
class BlueLaser(Weapon):
    def __init__(self, x, y, angle):
        image = pygame.Surface((1, 30))
        image.fill(BLUE)
        super().__init__(x, y, angle, image, .5, 40, math.inf)
        
class DumbMissile(Weapon):
    def __init__(self, x, y, angle):
        image = pygame.image.load("assets/missile1.png").convert_alpha()
        super().__init__(x, y, angle, image, 0.8, 50, 500)

class HPPowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("assets/hp1.png")
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

# Base class for player and enemies
class Entity(pygame.sprite.Sprite):
    def __init__(self, image_path, health):
        super().__init__()
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.speed = 0.4  # Default speed, can be overridden in subclasses
        self.move_x = 0
        self.move_y = 0
        self.angle = 0
        self.health = health
        self.max_health = health

    def update(self):
        apply_movement(self)  # Apply accumulated movement
        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

        # Wrap around screen edges
        if self.rect.left > SCREEN_WIDTH:
            self.rect.right = 0
        if self.rect.right < 0:
            self.rect.left = SCREEN_WIDTH
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.bottom = 0
        if self.rect.bottom < 0:
            self.rect.top = SCREEN_HEIGHT
            
    def shoot(self):
        if self.weapon:
            weapon_instance = self.weapon(self.rect.centerx, self.rect.centery, self.angle) 
            # Play firing sound for the player's weapon
            if isinstance(weapon_instance, GreenLaser):
                fire_sound1.play()
            elif isinstance(weapon_instance, BlueLaser):
                fire_sound2.play()
            elif isinstance(weapon_instance, DumbMissile):
                fire_sound3.play()
                
            all_sprites.add(weapon_instance)
            if isinstance(self, Player):
                lasers.add(weapon_instance)
            else:
                enemy_lasers.add(weapon_instance)

# Player class
class Player(Entity):
    def __init__(self):
        super().__init__("assets/player.png", 100)
        self.last_shot_time = 0
        self.weapon = GreenLaser
        
        # Set initial position to the center of the screen
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    def update(self):
        # Handle rotation and movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.angle += 0.2
        if keys[pygame.K_d]:
            self.angle -= 0.2
        if keys[pygame.K_w]:
            self.move_x -= self.speed * math.sin(math.radians(self.angle))
            self.move_y -= self.speed * math.cos(math.radians(self.angle))

        super().update()  # Call Entity's update method 

        # Shooting lasers
        current_time = time.time()
        if keys[pygame.K_SPACE] and current_time - self.last_shot_time > LASER_RATE_LIMIT:
            self.shoot()  # Call the shoot method to create the weapon instance
            self.last_shot_time = current_time

# Enemy class
class Enemy(Entity):
    def __init__(self, image_path, health, firing_rate=0, weapon=None):
        super().__init__(image_path, health)
        self.speed = 0.02  # Slower speed for enemies
        self.weapon = weapon 
        
        # Firing rate and delay handling
        self.firing_rate = firing_rate
        if self.firing_rate > 0:
            self.shoot_delay = firing_rate
            self.last_shot_time = 0
            self.initial_delay = random.uniform(5, 10)
            self.can_shoot = False
        else:
            self.shoot_delay = None  # No shooting capability

    def update(self):
        # Calculate distances considering screen wrap-around
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dx_wrapped = min(abs(dx), SCREEN_WIDTH - abs(dx))
        dy_wrapped = min(abs(dy), SCREEN_HEIGHT - abs(dy))
        dist_wrapped = math.hypot(dx_wrapped, dy_wrapped)

        # Choose movement direction based on shortest distance
        if dist_wrapped < math.hypot(dx, dy):
            if abs(dx_wrapped) < abs(dx):
                dx = dx - SCREEN_WIDTH
            if abs(dy_wrapped) < abs(dy):
                dy = dy - SCREEN_HEIGHT

        # Normalize vector to get direction
        dist = math.hypot(dx, dy)
        dx /= dist
        dy /= dist

        # Move towards player
        self.move_x += dx * self.speed
        self.move_y += dy * self.speed

        # Apply accumulated movement to rect
        self.rect.x += int(self.move_x)
        self.move_x -= int(self.move_x)
        self.rect.y += int(self.move_y)
        self.move_y -= int(self.move_y)

        # Calculate angle towards player and rotate image
        angle = (180 / math.pi) * math.atan2(-dx, -dy)
        self.image = pygame.transform.rotozoom(self.original_image, angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

        # Wrap around screen edges
        if self.rect.left > SCREEN_WIDTH:
            self.rect.right = 0
        if self.rect.right < 0:
            self.rect.left = SCREEN_WIDTH
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.bottom = 0
        if self.rect.bottom < 0:
            self.rect.top = SCREEN_HEIGHT

         # Enable shooting after initial delay
        if self.firing_rate > 0 and not self.can_shoot and time.time() - start_time > self.initial_delay:
            self.can_shoot = True

        # Shooting logic
        if self.shoot_delay and self.can_shoot:
            current_time = time.time()
            if current_time - self.last_shot_time > self.shoot_delay:
                # Recalculate dx and dy for accurate aiming
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery

                self.angle = (180 / math.pi) * math.atan2(-dx, -dy)

                self.shoot()  # Call the shoot method to create the weapon instance
                self.last_shot_time = current_time

    def enemy_death(self):
        # Logic to drop HP power-up with a 10% chance
        if random.randint(1, 10) <= 3:  # 10% chance
            x, y = self.rect.center  # Enemy's current position
            hp_power_up = HPPowerUp(x, y)
            all_sprites.add(hp_power_up)
            power_ups.add(hp_power_up)

# Create sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
lasers = pygame.sprite.Group()
enemy_lasers = pygame.sprite.Group()
power_ups = pygame.sprite.Group()

# Get start time
start_time = time.time()

# Set screen dimensions
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Set game title
pygame.display.set_caption("Survival Game")

# Create player
player = Player()
all_sprites.add(player)

# Create enemies
for _ in range(5):
    while True:
        enemy1 = Enemy("assets/enemy1.png", 100)
        # Generate random position within annulus
        radius = random.randint(ENEMY_SPAWN_DISTANCE, SCREEN_WIDTH // 2)
        angle = random.uniform(0, 2 * math.pi)
        x = player.rect.centerx + radius * math.cos(angle)
        y = player.rect.centery + radius * math.sin(angle)
        enemy1.rect.center = (x, y)
        if not pygame.sprite.spritecollideany(enemy1, all_sprites):
            break  # No collision, position is valid
    all_sprites.add(enemy1)
    enemies.add(enemy1)

    while True:
        enemy2 = Enemy("assets/enemy2.png", 160, 4, GreenLaser)
        # Generate random position within annulus
        radius = random.randint(ENEMY_SPAWN_DISTANCE, SCREEN_WIDTH // 2)
        angle = random.uniform(0, 2 * math.pi)
        x = player.rect.centerx + radius * math.cos(angle)
        y = player.rect.centery + radius * math.sin(angle)
        enemy2.rect.center = (x, y)
        if not pygame.sprite.spritecollideany(enemy2, all_sprites):
            break  # No collision, position is valid
    all_sprites.add(enemy2)
    enemies.add(enemy2)
    
    while True:
        enemy3 = Enemy("assets/enemy3.png", 240, 8, BlueLaser) 
        # Generate random position within annulus
        radius = random.randint(ENEMY_SPAWN_DISTANCE, SCREEN_WIDTH // 2)
        angle = random.uniform(0, 2 * math.pi)
        x = player.rect.centerx + radius * math.cos(angle)
        y = player.rect.centery + radius * math.sin(angle)
        enemy3.rect.center = (x, y)
        if not pygame.sprite.spritecollideany(enemy3, all_sprites):
            break
    all_sprites.add(enemy3)
    enemies.add(enemy3)
    
    while True:
        enemy4 = Enemy("assets/enemy4.png", 120, 6, DumbMissile)
        # Generate random position within annulus, similar to other enemies
        radius = random.randint(ENEMY_SPAWN_DISTANCE, SCREEN_WIDTH // 2)
        angle = random.uniform(0, 2 * math.pi)
        x = player.rect.centerx + radius * math.cos(angle)
        y = player.rect.centery + radius * math.sin(angle)
        enemy4.rect.center = (x, y)
        if not pygame.sprite.spritecollideany(enemy4, all_sprites):
            break  # No collision, position is valid
    all_sprites.add(enemy4)
    enemies.add(enemy4)

# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update sprites
    if player.alive():  # Only update enemies if the player is alive
        all_sprites.update()
    else:
        player.kill()  # Remove the player from all groups
        for enemy in enemies:
            enemy.speed = 0  # Set enemy speed to 0
            enemy.shoot_delay = None  # Disable shooting

    # Check collisions
    check_collisions(player, enemies)
    check_collisions(player, enemy_lasers)
    check_collisions(enemies, lasers) 
    check_collisions(player, power_ups)

    # Draw everything
    screen.fill(BLACK)
    all_sprites.draw(screen)

    # Draw health bars
    if player.alive():  # Check if the player is alive
        health_bar_rect = pygame.Rect(0, 0, player.rect.width, 6)
        health_bar_rect.center = player.rect.center
        health_bar_rect.y += HEALTH_BAR_Y_OFFSET
        health_bar_rect.x += HEALTH_BAR_X_OFFSET
        draw_health_bar(screen, health_bar_rect, player.health, 100)
        
    for enemy in enemies:
        health_bar_rect = pygame.Rect(0, 0, enemy.rect.width, 6)
        health_bar_rect.center = enemy.rect.center
        health_bar_rect.y += HEALTH_BAR_Y_OFFSET
        health_bar_rect.x += HEALTH_BAR_X_OFFSET
        draw_health_bar(screen, health_bar_rect, enemy.health, enemy.max_health) 

    pygame.display.flip()

pygame.quit()
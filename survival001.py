# Import necessary libraries
import pygame
import random
import math
import time

# Initialize Pygame
pygame.init()

# Set screen dimensions
screen_width = 1600
screen_height = 1200
screen = pygame.display.set_mode((screen_width, screen_height))

# Set game title
pygame.display.set_caption("Survival Game")

# Define colors
black = (0, 0, 0)
white = (255, 255, 255)

# Function to draw health bar
def draw_health_bar(surf, center_x, center_y, health, max_health):
    if health < 0:
        health = 0
    bar_length = 32  # Half the length
    bar_height = 6   # Half the height

    # Calculate fill amount based on health percentage
    fill_percent = health / max_health
    fill = fill_percent * bar_length
    
    # Create surfaces with per-pixel alpha
    outline_surf = pygame.Surface((bar_length, bar_height), pygame.SRCALPHA)
    fill_surf = pygame.Surface((fill, bar_height), pygame.SRCALPHA)

    # Draw on the surfaces with transparency
    pygame.draw.rect(fill_surf, (0, 255, 0, 48), fill_surf.get_rect())
    pygame.draw.rect(outline_surf, (255, 255, 255, 48), outline_surf.get_rect(), 1)

    # Blit the surfaces onto the main surface
    surf.blit(fill_surf, (center_x - bar_length // 2, center_y - 30))
    surf.blit(outline_surf, (center_x - bar_length // 2, center_y - 30))
    
# Function to check if a point is within a certain distance of the player
def is_near_player(x, y, distance):
    player_x, player_y = player.rect.center
    return math.hypot(x - player_x, y - player_y) < distance    

# Laser class
class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.original_image = pygame.Surface((1, 30))  # Thinner laser
        self.original_image.fill((0, 255, 0))
        self.image = pygame.transform.rotozoom(self.original_image, angle, 1)
        self.rect = self.image.get_rect(center=(x, y))
        self.angle = angle
        self.speed = 1
        self.move_x = 0  
        self.move_y = 0
        
    def update(self):
        # Calculate movement
        self.move_x -= self.speed * math.sin(math.radians(self.angle))
        self.move_y -= self.speed * math.cos(math.radians(self.angle))

        # Apply accumulated movement to rect
        self.rect.x += int(self.move_x)
        self.move_x -= int(self.move_x)
        self.rect.y += int(self.move_y)
        self.move_y -= int(self.move_y)

        # Remove laser if it goes off-screen
        if self.rect.bottom < 0 or self.rect.top > screen_height or \
           self.rect.left > screen_width or self.rect.right < 0:
            self.kill()

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.image.load("assets/player.png").convert_alpha()  # Store original
        self.image = self.original_image.copy()  # Start with a copy
        self.rect = self.image.get_rect()
        self.rect.center = (screen_width // 2, screen_height // 2)
        self.speed = 0.4
        self.move_x = 0
        self.move_y = 0
        self.angle = 0 
        self.last_shot_time = 0
        self.health = 100

    def update(self):
        # Handle rotation with 'A' and 'D' keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.angle += .2  # Adjust rotation speed as needed
        if keys[pygame.K_d]:
            self.angle -= .2

        # Move forward based on angle and 'W' key press
        if keys[pygame.K_w]:
            self.move_x -= self.speed * math.sin(math.radians(self.angle))
            self.move_y -= self.speed * math.cos(math.radians(self.angle))

        # Apply accumulated movement to rect
        self.rect.x += int(self.move_x)
        self.move_x -= int(self.move_x)
        self.rect.y += int(self.move_y)
        self.move_y -= int(self.move_y)

        # Rotate player image
        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 1)  
        self.rect = self.image.get_rect(center=self.rect.center)

        # Wrap around screen edges
        if self.rect.left > screen_width:
            self.rect.right = 0
        if self.rect.right < 0:
            self.rect.left = screen_width
        if self.rect.top > screen_height:
            self.rect.bottom = 0
        if self.rect.bottom < 0:
            self.rect.top = screen_height
            
        # Shooting lasers with rate limiting
        current_time = time.time()
        if keys[pygame.K_SPACE] and current_time - self.last_shot_time > 0.1:
            laser = Laser(self.rect.centerx, self.rect.centery, self.angle)
            all_sprites.add(laser)
            lasers.add(laser)
            self.last_shot_time = current_time  # Update last shot time
            
        # Check for collisions with enemies
        hits = pygame.sprite.spritecollide(self, enemies, True)
        for hit in hits:
            self.health -= 100
            if self.health <= 0:
                self.kill()  # Player dies
                
        # Draw health bar
        draw_health_bar(screen, 5, 5, self.health, 100)

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, image_path, health, shoot_delay=None):  # Added health parameter
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(screen_width - self.rect.width)
        self.rect.y = random.randrange(screen_height - self.rect.height)
        self.speed = 0.02
        self.move_x = 0
        self.move_y = 0
        self.angle = 0
        self.health = health 
        self.max_health = health
        self.shoot_delay = shoot_delay  # Time between shots (in seconds)
        self.last_shot_time = 0
        self.can_shoot = False  # Flag to control shooting

    def update(self):
        # Calculate distances considering screen wrap-around
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dx_wrapped = min(abs(dx), screen_width - abs(dx))
        dy_wrapped = min(abs(dy), screen_height - abs(dy))
        dist_wrapped = math.hypot(dx_wrapped, dy_wrapped)

        # Choose movement direction based on shortest distance
        if dist_wrapped < math.hypot(dx, dy):
            if abs(dx_wrapped) < abs(dx):
                dx = dx - screen_width
            if abs(dy_wrapped) < abs(dy):
                dy = dy - screen_height

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

        # Wrap around screen edges (already existing code)
        if self.rect.left > screen_width:
            self.rect.right = 0
        if self.rect.right < 0:
            self.rect.left = screen_width
        if self.rect.top > screen_height:
            self.rect.bottom = 0
        if self.rect.bottom < 0:
            self.rect.top = screen_height
            
        # Check for laser collisions
        hits = pygame.sprite.spritecollide(self, lasers, True)
        for hit in hits:
            self.health -= 20
            if self.health <= 0:
                self.kill()  # Enemy dies
             
        # Enable shooting after 5 seconds
        if not self.can_shoot and time.time() - start_time > 5:
            self.can_shoot = True     
        
        # Shooting logic
        if self.shoot_delay and self.can_shoot:  # Check if enemy has shooting capability
            current_time = time.time()
            if current_time - self.last_shot_time > self.shoot_delay:
                # Calculate angle towards player
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                angle = (180 / math.pi) * math.atan2(-dx, -dy)

                # Create and shoot laser
                laser = Laser(self.rect.centerx, self.rect.centery, angle)
                all_sprites.add(laser)
                enemy_lasers.add(laser)  # Add a new group for enemy lasers
                self.last_shot_time = current_time
             
        # Draw health bar
        draw_health_bar(screen, self.rect.x, self.rect.y - 20, self.health, self.max_health)

# Create sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
lasers = pygame.sprite.Group()
enemy_lasers = pygame.sprite.Group()

# Create player and enemies
start_time = time.time()
player = Player()
all_sprites.add(player)
for i in range(10):
    # Create enemies with distance check
    while True:
        enemy1 = Enemy("assets/enemy1.png", 100)
        if not is_near_player(enemy1.rect.centerx, enemy1.rect.centery, 500):
            break  # Enemy is far enough, add it to groups
    all_sprites.add(enemy1)
    enemies.add(enemy1)

    while True:
        enemy2 = Enemy("assets/enemy2.png", 160, 2)
        if not is_near_player(enemy2.rect.centerx, enemy2.rect.centery, 500):
            break
    all_sprites.add(enemy2)
    enemies.add(enemy2)

# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update sprites
    all_sprites.update()

    # Check for collisions between player and enemies
    hits = pygame.sprite.spritecollide(player, enemies, True)
    for hit in hits:
        player.health -= 100
        if player.health <= 0:
            player.kill()

    # Draw everything
    screen.fill(black)
    all_sprites.draw(screen)

    # Draw health bars
    draw_health_bar(screen, 5, 5, player.health, 100)
    for enemy in enemies:
        draw_health_bar(screen, enemy.rect.centerx, enemy.rect.centery, enemy.health, enemy.max_health)

    pygame.display.flip()

pygame.quit()
import pygame
import sys

pygame.init()

# Screen
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gravity Square")
clock = pygame.time.Clock()

# Colors
WHITE = (240, 240, 240)
BLUE = (0, 150, 255)
DARK = (30, 30, 30)

# Square (player)
size = 40
x = WIDTH // 2 - size // 2
y = HEIGHT - size - 50

y_velocity = 0
gravity = 0.6
jump_strength = -12
on_ground = False

# Ground
ground_y = HEIGHT - 50

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Jump
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and on_ground:
                y_velocity = jump_strength
                on_ground = False

    # Apply gravity
    y_velocity += gravity
    y += y_velocity

    # Collision with ground
    if y + size >= ground_y:
        y = ground_y - size
        y_velocity = 0
        on_ground = True

    # Draw
    screen.fill(DARK)

    # Ground
    pygame.draw.rect(screen, WHITE, (0, ground_y, WIDTH, HEIGHT - ground_y))

    # Square
    pygame.draw.rect(screen, BLUE, (x, y, size, size))

    pygame.display.flip()
    clock.tick(60)

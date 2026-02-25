import pygame
import sys

pygame.init()

# Screen
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Animated Square")
clock = pygame.time.Clock()

# Colors
BACKGROUND = (25, 25, 25)
SQUARE_COLOR = (0, 200, 255)

# Square
size = 50
x = -size
y = HEIGHT // 2 - size // 2
speed = 3

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Animate movement
    x += speed
    if x > WIDTH:
        x = -size

    # Draw
    screen.fill(BACKGROUND)
    pygame.draw.rect(screen, SQUARE_COLOR, (x, y, size, size))

    pygame.display.flip()
    clock.tick(60)

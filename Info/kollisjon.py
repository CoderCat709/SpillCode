import pygame
import sys

pygame.init()

# Screen
WIDTH, HEIGHT = 500, 300
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Collision Detector")
clock = pygame.time.Clock()

# Colors
BG = (30, 30, 30)
PLAYER_COLOR = (0, 200, 255)
BOX_COLOR = (255, 80, 80)
COLLIDE_COLOR = (0, 255, 0)

# Player square
player = pygame.Rect(50, 125, 40, 40)
speed = 4

# Target square
box = pygame.Rect(350, 125, 40, 40)

# Font
font = pygame.font.SysFont(None, 32)

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.x -= speed
    if keys[pygame.K_RIGHT]:
        player.x += speed
    if keys[pygame.K_UP]:
        player.y -= speed
    if keys[pygame.K_DOWN]:
        player.y += speed

    # Collision check
    colliding = player.colliderect(box)

    # Draw
    screen.fill(BG)

    pygame.draw.rect(
        screen,
        COLLIDE_COLOR if colliding else PLAYER_COLOR,
        player
    )

    pygame.draw.rect(screen, BOX_COLOR, box)

    # Text
    text = font.render(
        "Collision!" if colliding else "No Collision",
        True,
        (255, 255, 255)
    )
    screen.blit(text, (20, 20))

    pygame.display.flip()
    clock.tick(60)

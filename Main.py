import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spill")

clock = pygame.time.Clock()

# ============================================================
#  SCALE — change this number to make the character bigger/smaller
#  1.0 = original size (32x32),  3.0 = three times bigger (96x96)
# ============================================================
CHARACTER_SCALE = 3.0

# ============================================================
#  GROUND
# ============================================================
GROUND_COLOR = (80, 80, 80)
GROUND_Y = HEIGHT - 80

# ============================================================
#  BACKGROUND  (bakgrunn.png stretched to fill the window)
# ============================================================
bg_raw   = pygame.image.load("bakgrunn.png").convert()
bg_image = pygame.transform.scale(bg_raw, (WIDTH, HEIGHT))

# ============================================================
#  SPRITE SHEET LOADER
#  Automatically works out each frame's width from the full sheet.
# ============================================================
def load_sheet(path, scale=CHARACTER_SCALE):
    sheet = pygame.image.load(path).convert_alpha()
    sheet_w, sheet_h = sheet.get_size()
    # Frames are stacked VERTICALLY, each frame is 32 wide x 32 tall
    frame_w = 32
    frame_h = 32
    num_frames = sheet_h // frame_h   # auto-detect from sheet height
    print(f"[DEBUG] {path}  ->  sheet {sheet_w}x{sheet_h},  "
          f"{num_frames} frames auto-detected")
    scaled_w = int(frame_w * scale)
    scaled_h = int(frame_h * scale)
    frames = []
    for i in range(num_frames):
        frame = sheet.subsurface((0, i * frame_h, frame_w, frame_h))
        frame = pygame.transform.scale(frame, (scaled_w, scaled_h))
        frames.append(frame)
    return frames, scaled_w, scaled_h

# Load all three animation strips — frame count is auto-detected from image height
frames_right, CHAR_W, CHAR_H = load_sheet("v1_høyre.png")
frames_left,  _,      _      = load_sheet("v1_venstre.png")
frames_idle,  _,      _      = load_sheet("Looking around.png")

# ============================================================
#  ROOM ENTRANCE DOOR  (bottom-right corner, on the ground)
# ============================================================
ENTRANCE_W = 60
ENTRANCE_H = 80
entrance_rect = pygame.Rect(
    WIDTH - ENTRANCE_W - 10,
    GROUND_Y - ENTRANCE_H,
    ENTRANCE_W,
    ENTRANCE_H,
)

# ============================================================
#  PHYSICS
# ============================================================
GRAVITY       =  0.9
JUMP_FORCE    = -14
HOLD_FORCE    = -0.4
MAX_HOLD_TIME =  18
SPEED         =   5

vel_y            = 0
jump_hold_frames = 0
on_ground        = False

# ============================================================
#  PLAYER  (single character, no switching)
# ============================================================
px = float(WIDTH  // 2)
py = float(GROUND_Y - CHAR_H)

# ============================================================
#  ANIMATION STATE MACHINE
#
#  States:
#    "idle"        - standing still, shows frame 0 of last walk direction
#    "walk_right"  - moving right, plays v1_høyre.png (3 frames, loops)
#    "walk_left"   - moving left,  plays v1_venstre.png (3 frames, loops)
#    "look_around" - triggered after 5 s of idle, plays Looking around.png
#                    (9 frames, loops until player moves)
# ============================================================
anim_state       = "idle"
anim_frame       = 0
anim_timer       = 0
ANIM_SPEED       = 8        # ticks between frame advances (lower = faster)

idle_still_timer = 0
IDLE_DELAY       = 5 * 60   # 5 seconds x 60 fps

last_direction   = "right"  # remembers facing direction when idle

def frames_for_state(state, last_dir):
    if state == "walk_right":   return frames_right
    if state == "walk_left":    return frames_left
    if state == "look_around":  return frames_idle
    # "idle" — frozen on frame 0 of whichever way the player last walked
    return [frames_right[0]] if last_dir == "right" else [frames_left[0]]


# ============================================================
print("=== Kontroller ===")
print("PIL VENSTRE/HOYRE : Beveg karakter")
print("SPACE             : Hopp")
print("ESC               : Avslutt")
print("Gaa inn i doeren i hoyre hjorne for aa bytte rom!")

# ============================================================
#  GAME LOOP
# ============================================================
while True:
    clock.tick(60)

    # ── Events ─────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

            if event.key == pygame.K_SPACE and on_ground:
                vel_y            = JUMP_FORCE
                jump_hold_frames = MAX_HOLD_TIME
                on_ground        = False

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                jump_hold_frames = 0

    keys = pygame.key.get_pressed()

    # ── Horizontal movement ────────────────────────────────
    moving = False
    if keys[pygame.K_LEFT]:
        px -= SPEED
        last_direction = "left"
        moving = True
    if keys[pygame.K_RIGHT]:
        px += SPEED
        last_direction = "right"
        moving = True

    px = max(0.0, min(float(WIDTH - CHAR_W), px))

    # ── Variable-height jump (hold SPACE to go higher) ─────
    if keys[pygame.K_SPACE] and jump_hold_frames > 0:
        vel_y            += HOLD_FORCE
        jump_hold_frames -= 1

    # ── Gravity & vertical collision ──────────────────────
    vel_y += GRAVITY
    py    += vel_y

    if py + CHAR_H >= GROUND_Y:
        py        = float(GROUND_Y - CHAR_H)
        vel_y     = 0
        on_ground = True

    # ── Animation state machine ────────────────────────────
    if moving:
        # Switch to the correct walk animation
        new_state = "walk_right" if last_direction == "right" else "walk_left"
        if anim_state != new_state:
            anim_state = new_state
            anim_frame = 0
            anim_timer = 0
        idle_still_timer = 0   # reset look-around countdown

    else:
        # Player just stopped — snap back to idle
        if anim_state in ("walk_right", "walk_left"):
            anim_state = "idle"
            anim_frame = 0
            anim_timer = 0

        # Count seconds standing still
        if anim_state in ("idle", "look_around"):
            idle_still_timer += 1

        # After 5 s trigger the look-around animation
        if anim_state == "idle" and idle_still_timer >= IDLE_DELAY:
            anim_state       = "look_around"
            anim_frame       = 0
            anim_timer       = 0
            idle_still_timer = 0

        # "look_around" keeps looping until the player moves (handled above)

    # ── Advance animation frame ────────────────────────────
    current_frames = frames_for_state(anim_state, last_direction)

    if anim_state != "idle":      # idle is always frame 0, no timer needed
        anim_timer += 1
        if anim_timer >= ANIM_SPEED:
            anim_timer  = 0
            anim_frame += 1
            if anim_frame >= len(current_frames):
                anim_frame = 0    # loop

    # ── Room entrance collision ────────────────────────────
    player_rect = pygame.Rect(int(px), int(py), CHAR_W, CHAR_H)
    if player_rect.colliderect(entrance_rect):
        pass  # TODO: add room-switch logic here

    # ── Draw ───────────────────────────────────────────────
    screen.blit(bg_image, (0, 0))

    # Ground strip
    pygame.draw.rect(screen, GROUND_COLOR, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

    # Entrance door
    pygame.draw.rect(screen, (30, 30, 30),   entrance_rect)
    pygame.draw.rect(screen, (180, 140, 80), entrance_rect, 4)
    knob = pygame.Rect(entrance_rect.left + 8, entrance_rect.centery, 8, 8)
    pygame.draw.ellipse(screen, (180, 140, 80), knob)

    # Player sprite
    sprite = current_frames[anim_frame]
    screen.blit(sprite, (int(px), int(py)))

    # Small HUD (shows current anim state for debugging — remove when done)
    font = pygame.font.Font(None, 24)
    hud  = font.render(
        f"ESC: Avslutt  |  SPACE: Hopp  |  PIL: Beveg  |  [{anim_state}]",
        True, (220, 220, 220)
    )
    screen.blit(hud, (10, 10))

    pygame.display.flip()
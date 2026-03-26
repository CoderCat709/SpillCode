import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spill")
clock = pygame.time.Clock()

# ============================================================
#  CONSTANTS
# ============================================================
CHARACTER_SCALE = 3.0
GROUND_Y        = HEIGHT - 80
GRAVITY         =  0.9
JUMP_FORCE      = -14
HOLD_FORCE      = -0.4
MAX_HOLD_TIME   =  18
SPEED           =   5
ANIM_SPEED      =   8
IDLE_DELAY      = 5 * 60

# ============================================================
#  HELPERS
# ============================================================
def scale_bg(path):
    return pygame.transform.scale(pygame.image.load(path).convert(), (WIDTH, HEIGHT))

def load_sheet(path, scale=CHARACTER_SCALE):
    sheet      = pygame.image.load(path).convert_alpha()
    frame_w    = frame_h = 32
    num_frames = sheet.get_height() // frame_h
    sw, sh     = int(frame_w * scale), int(frame_h * scale)
    return [
        pygame.transform.scale(sheet.subsurface((0, i * frame_h, frame_w, frame_h)), (sw, sh))
        for i in range(num_frames)
    ], sw, sh

# ============================================================
#  ASSETS
# ============================================================
frames_right, CHAR_W, CHAR_H = load_sheet("v1_høyre.png")
frames_left,  _,      _      = load_sheet("v1_venstre.png")
frames_idle,  _,      _      = load_sheet("Looking around.png")

# ============================================================
#  PLATFORM HITBOXES
#
#  Coordinates are for the 800x600 scaled screen.
#  Set DEBUG_PLATFORMS = True below to see red outlines while tuning.
#
#  bakgrunn (room1):
#    The stone floor slab runs across the full bottom ~y=490
#
#  bakgrunnv3 (room2):
#    Two raised ledges left and right with a gap in the middle
# ============================================================
PLATFORMS_ROOM1 = [
    pygame.Rect(0,   490, 800, 110),   # full ground slab
]

PLATFORMS_ROOM2 = [
    pygame.Rect(0,   390, 270, 210),   # left ledge
    pygame.Rect(530, 390, 270, 210),   # right ledge
]

ROOMS = {
    "room1": {
        "bg":        scale_bg("bakgrunn.png"),
        "platforms": PLATFORMS_ROOM1,
        "left":  None,      # wall — can't leave left
        "right": "room2",   # room2 is to the RIGHT
    },
    "room2": {
        "bg":        scale_bg("bakgrunnv3.png"),
        "platforms": PLATFORMS_ROOM2,
        "left":  "room1",   # back to room1
        "right": None,
    },
}

# ============================================================
#  DEBUG — flip to True to see platform rects while tuning
# ============================================================
DEBUG_PLATFORMS = False

# ============================================================
#  COLORS & FONTS
# ============================================================
BG_COLOR     = (30, 30, 30)
BUTTON_COLOR = (70, 130, 180)
HOVER_COLOR  = (100, 170, 220)
TEXT_COLOR   = (255, 255, 255)

font_large = pygame.font.SysFont(None, 64)
font_med   = pygame.font.SysFont(None, 36)
font_small = pygame.font.SysFont(None, 24)

# ============================================================
#  BUTTON
# ============================================================
class Button:
    def __init__(self, text, x, y, w, h):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface):
        col = HOVER_COLOR if self.rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(surface, col, self.rect, border_radius=8)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=8)
        surf = font_med.render(self.text, True, TEXT_COLOR)
        surface.blit(surf, surf.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))

cx = WIDTH // 2 - 100
menu_buttons = [
    Button("Spill",         cx, 220, 200, 50),
    Button("Innstillinger", cx, 290, 200, 50),
    Button("Avslutt",       cx, 360, 200, 50),
]
back_button = Button("Tilbake", cx, 300, 200, 50)

# ============================================================
#  PLAYER STATE
# ============================================================
px = py = vel_y = 0.0
jump_hold_frames = 0
on_ground        = True
anim_state       = "idle"
anim_frame       = anim_timer = idle_still_timer = 0
last_direction   = "right"
current_room     = "room1"
game_state       = "menu"

def get_spawn_y(start_px, platforms):
    """Find the y position to spawn the player standing on a platform."""
    for plat in sorted(platforms, key=lambda p: p.top):
        if plat.left <= start_px + CHAR_W // 2 <= plat.right:
            return float(plat.top - CHAR_H)
    return float(HEIGHT - CHAR_H)   # fallback

def reset_player(side="center"):
    global px, py, vel_y, jump_hold_frames, on_ground
    global anim_state, anim_frame, anim_timer, idle_still_timer, last_direction
    if   side == "right": px = float(WIDTH - CHAR_W - 20)
    elif side == "left":  px = 20.0
    else:                 px = float(WIDTH // 2 - CHAR_W // 2)
    py             = get_spawn_y(px, ROOMS[current_room]["platforms"])
    vel_y          = 0.0; jump_hold_frames = 0; on_ground = True
    anim_state     = "idle"; anim_frame = anim_timer = idle_still_timer = 0
    last_direction = "right"

def frames_for_state(state):
    if state == "walk_right":  return frames_right
    if state == "walk_left":   return frames_left
    if state == "look_around": return frames_idle
    return [frames_right[0]] if last_direction == "right" else [frames_left[0]]

def resolve_platforms(px, py, vel_y, platforms):
    """Move player vertically and land on platforms."""
    new_py    = py + vel_y
    grounded  = False
    prev_feet = py + CHAR_H

    for plat in platforms:
        # Horizontal overlap check
        if px + CHAR_W <= plat.left or px >= plat.right:
            continue
        # Falling onto top surface
        if prev_feet <= plat.top and new_py + CHAR_H >= plat.top:
            new_py   = float(plat.top - CHAR_H)
            vel_y    = 0.0
            grounded = True
            break

    # Safety net — don't fall off screen
    if new_py + CHAR_H > HEIGHT:
        new_py   = float(HEIGHT - CHAR_H)
        vel_y    = 0.0
        grounded = True

    return new_py, vel_y, grounded

# ============================================================
#  MAIN LOOP
# ============================================================
while True:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if game_state == "menu":
            for btn in menu_buttons:
                if btn.clicked(event):
                    if   btn.text == "Spill":         game_state = "playing"; current_room = "room1"; reset_player("center")
                    elif btn.text == "Innstillinger": game_state = "options"
                    elif btn.text == "Avslutt":       pygame.quit(); sys.exit()

        elif game_state == "options":
            if back_button.clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                game_state = "menu"

        elif game_state == "playing":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:   game_state = "menu"
                if event.key == pygame.K_SPACE and on_ground:
                    vel_y = JUMP_FORCE; jump_hold_frames = MAX_HOLD_TIME; on_ground = False
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                jump_hold_frames = 0

    # ── MENU ──────────────────────────────────────────────
    if game_state == "menu":
        screen.fill(BG_COLOR)
        t = font_large.render("SPILL", True, (100, 180, 255))
        screen.blit(t, t.get_rect(center=(WIDTH // 2, 130)))
        for btn in menu_buttons: btn.draw(screen)
        pygame.display.flip(); continue

    # ── OPTIONS ───────────────────────────────────────────
    if game_state == "options":
        screen.fill(BG_COLOR)
        t = font_large.render("Innstillinger", True, TEXT_COLOR)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, 130)))
        i = font_med.render("(ingen innstillinger ennå)", True, (160, 160, 160))
        screen.blit(i, i.get_rect(center=(WIDTH // 2, 220)))
        back_button.draw(screen)
        pygame.display.flip(); continue

    # ── PLAYING ───────────────────────────────────────────
    keys   = pygame.key.get_pressed()
    moving = False
    room   = ROOMS[current_room]

    if keys[pygame.K_LEFT]:
        px -= SPEED; last_direction = "left";  moving = True
    if keys[pygame.K_RIGHT]:
        px += SPEED; last_direction = "right"; moving = True

    if keys[pygame.K_SPACE] and jump_hold_frames > 0:
        vel_y += HOLD_FORCE; jump_hold_frames -= 1

    vel_y += GRAVITY
    py, vel_y, on_ground = resolve_platforms(px, py, vel_y, room["platforms"])

    # Room transitions
    if px + CHAR_W <= 0 and room["left"]:
        current_room = room["left"];  reset_player("right")
    elif px >= WIDTH and room["right"]:
        current_room = room["right"]; reset_player("left")
    else:
        if px < 0             and not room["left"]:  px = 0.0
        if px + CHAR_W > WIDTH and not room["right"]: px = float(WIDTH - CHAR_W)

    # Animation
    if moving:
        new_s = "walk_right" if last_direction == "right" else "walk_left"
        if anim_state != new_s:
            anim_state = new_s; anim_frame = anim_timer = 0
        idle_still_timer = 0
    else:
        if anim_state in ("walk_right", "walk_left"):
            anim_state = "idle"; anim_frame = anim_timer = 0
        idle_still_timer += 1
        if anim_state == "idle" and idle_still_timer >= IDLE_DELAY:
            anim_state = "look_around"; anim_frame = anim_timer = idle_still_timer = 0

    current_frames = frames_for_state(anim_state)
    if anim_state != "idle":
        anim_timer += 1
        if anim_timer >= ANIM_SPEED:
            anim_timer = 0
            anim_frame = (anim_frame + 1) % len(current_frames)

    # Draw
    screen.blit(room["bg"], (0, 0))

    if DEBUG_PLATFORMS:
        for plat in room["platforms"]:
            pygame.draw.rect(screen, (255, 0, 0), plat, 2)

    screen.blit(current_frames[anim_frame], (int(px), int(py)))
    screen.blit(font_small.render(
        f"ESC: Meny  |  SPACE: Hopp  |  PIL: Beveg  |  Rom: {current_room}",
        True, (220, 220, 220)), (10, 10))

    pygame.display.flip()
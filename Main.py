import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spill")

clock = pygame.time.Clock()

# ============================================================
#  SCALE
# ============================================================
CHARACTER_SCALE = 3.0

# ============================================================
#  GROUND
# ============================================================
GROUND_COLOR = (80, 80, 80)
GROUND_Y = HEIGHT - 80

# ============================================================
#  BACKGROUND
# ============================================================
bg_raw   = pygame.image.load("bakgrunn.png").convert()
bg_image = pygame.transform.scale(bg_raw, (WIDTH, HEIGHT))

# ============================================================
#  SPRITE SHEET LOADER
# ============================================================
def load_sheet(path, scale=CHARACTER_SCALE):
    sheet = pygame.image.load(path).convert_alpha()
    sheet_w, sheet_h = sheet.get_size()
    frame_w = 32
    frame_h = 32
    num_frames = sheet_h // frame_h
    print(f"[DEBUG] {path}  ->  sheet {sheet_w}x{sheet_h},  {num_frames} frames auto-detected")
    scaled_w = int(frame_w * scale)
    scaled_h = int(frame_h * scale)
    frames = []
    for i in range(num_frames):
        frame = sheet.subsurface((0, i * frame_h, frame_w, frame_h))
        frame = pygame.transform.scale(frame, (scaled_w, scaled_h))
        frames.append(frame)
    return frames, scaled_w, scaled_h

frames_right, CHAR_W, CHAR_H = load_sheet("v1_høyre.png")
frames_left,  _,      _      = load_sheet("v1_venstre.png")
frames_idle,  _,      _      = load_sheet("Looking around.png")

# ============================================================
#  PHYSICS CONSTANTS
# ============================================================
GRAVITY       =  0.9
JUMP_FORCE    = -14
HOLD_FORCE    = -0.4
MAX_HOLD_TIME =  18
SPEED         =   5

# ============================================================
#  HOW TO ADD A NEW ROOM:
#
#  1. Add a new background image for the room, e.g. "rom2.png"
#
#  2. Add a new entry to the ROOMS dictionary below, like:
#       "room2": {
#           "bg": pygame.transform.scale(
#                     pygame.image.load("rom2.png").convert(), (WIDTH, HEIGHT)),
#           "ground_color": (60, 40, 20),   # optional: change floor colour
#           "doors": {
#               "left":  None,              # None = no door on this side
#               "right": "room3",           # name of room to go to
#           }
#       }
#
#  3. Make sure the room you come FROM has a door pointing to your new room.
#     E.g. if you enter room2 from room1 via the RIGHT door,
#     room1's "right" door should say "room2".
#
#  Doors are always placed:
#    left  door  — left edge of the screen
#    right door  — right edge of the screen
#
#  The player is repositioned to the opposite side when switching rooms:
#    enter from right door → player appears on left side of new room
#    enter from left door  → player appears on right side of new room
# ============================================================
ROOMS = {
    "room1": {
        "bg": bg_image,
        "ground_color": (80, 80, 80),
        "doors": {
            "left":  None,       # no door on the left in room1
            "right": "room2",    # right door leads to room2
        }
    },
    # ---------- ADD MORE ROOMS BELOW ----------
    # "room2": {
    #     "bg": pygame.transform.scale(
    #               pygame.image.load("rom2.png").convert(), (WIDTH, HEIGHT)),
    #     "ground_color": (60, 40, 20),
    #     "doors": {
    #         "left":  "room1",   # back to room1
    #         "right": None,
    #     }
    # },
}

# ============================================================
#  DOOR VISUALS  (drawn automatically based on ROOMS config)
# ============================================================
DOOR_W = 60
DOOR_H = 80

def make_door_rect(side):
    """Returns the pygame.Rect for a door on the given side ('left' or 'right')."""
    if side == "right":
        return pygame.Rect(WIDTH - DOOR_W - 10, GROUND_Y - DOOR_H, DOOR_W, DOOR_H)
    else:  # left
        return pygame.Rect(10, GROUND_Y - DOOR_H, DOOR_W, DOOR_H)

def draw_door(surface, side):
    rect = make_door_rect(side)
    pygame.draw.rect(surface, (30, 30, 30), rect)
    pygame.draw.rect(surface, (180, 140, 80), rect, 4)
    knob_x = rect.right - 14 if side == "left" else rect.left + 8
    knob = pygame.Rect(knob_x, rect.centery, 8, 8)
    pygame.draw.ellipse(surface, (180, 140, 80), knob)

# ============================================================
#  ANIMATION HELPERS
# ============================================================
def frames_for_state(state, last_dir):
    if state == "walk_right":  return frames_right
    if state == "walk_left":   return frames_left
    if state == "look_around": return frames_idle
    return [frames_right[0]] if last_dir == "right" else [frames_left[0]]

# ============================================================
#  COLORS & FONT
# ============================================================
BG_COLOR     = (30, 30, 30)
BUTTON_COLOR = (70, 130, 180)
HOVER_COLOR  = (100, 170, 220)
TEXT_COLOR   = (255, 255, 255)

font_large = pygame.font.SysFont(None, 64)
font_med   = pygame.font.SysFont(None, 36)
font_small = pygame.font.SysFont(None, 24)

# ============================================================
#  BUTTON CLASS
# ============================================================
class Button:
    def __init__(self, text, x, y, w, h):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface):
        color = HOVER_COLOR if self.rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2, border_radius=8)
        text_surf = font_med.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

# ============================================================
#  GAME STATE
# ============================================================
# Viser forsjellige status av spill som er game meny akkurat nå
game_state = "menu"

# Player position & physics (reset when entering game)
px = py = 0.0
vel_y = 0.0
jump_hold_frames = 0
on_ground = False

anim_state       = "idle"
anim_frame       = 0
anim_timer       = 0
ANIM_SPEED       = 8
idle_still_timer = 0
IDLE_DELAY       = 5 * 60
last_direction   = "right"

current_room = "room1"

def reset_player(side="center"):
    """Reset player position. side = 'center', 'left', or 'right'."""
    global px, py, vel_y, jump_hold_frames, on_ground
    global anim_state, anim_frame, anim_timer, idle_still_timer, last_direction
    if side == "right":
        px = float(WIDTH - CHAR_W - 80)  # appear near right side
    elif side == "left":
        px = 80.0                         # appear near left side
    else:
        px = float(WIDTH // 2)
    py = float(GROUND_Y - CHAR_H)
    vel_y = 0.0
    jump_hold_frames = 0
    on_ground = True
    anim_state = "idle"
    anim_frame = 0
    anim_timer = 0
    idle_still_timer = 0
    last_direction = "right"

# ============================================================
#  MENU BUTTONS
# ============================================================
btn_cx = WIDTH // 2 - 100   # center x for buttons
menu_buttons = [
    Button("Spill",       btn_cx, 220, 200, 50),
    Button("Innstillinger", btn_cx, 290, 200, 50),
    Button("Avslutt",     btn_cx, 360, 200, 50),
]
options_back_button = Button("Tilbake", btn_cx, 300, 200, 50)

# ============================================================
print("=== Kontroller ===")
print("PIL VENSTRE/HØYRE : Beveg karakter")
print("SPACE             : Hopp")
print("ESC               : Tilbake til meny")
print("Gå inn i en dør for å bytte rom!")

# ============================================================
#  MAIN GAME LOOP
# ============================================================
while True:
    clock.tick(60)

    # ── Events ─────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        # ── MENU ──────────────────────────────────────────
        if game_state == "menu":
            for btn in menu_buttons:
                if btn.clicked(event):
                    if btn.text == "Spill":
                        game_state = "playing"
                        reset_player("center")
                        current_room = "room1"
                    elif btn.text == "Innstillinger":
                        game_state = "options"
                    elif btn.text == "Avslutt":
                        pygame.quit(); sys.exit()

        # ── OPTIONS ───────────────────────────────────────
        elif game_state == "options":
            if options_back_button.clicked(event):
                game_state = "menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game_state = "menu"

        # ── PLAYING ───────────────────────────────────────
        elif game_state == "playing":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"

                if event.key == pygame.K_SPACE and on_ground:
                    vel_y            = JUMP_FORCE
                    jump_hold_frames = MAX_HOLD_TIME
                    on_ground        = False

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    jump_hold_frames = 0

    # ── DRAW MENU ──────────────────────────────────────────
    if game_state == "menu":
        screen.fill(BG_COLOR)
        title = font_large.render("SPILL", True, (100, 180, 255))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 130)))
        for btn in menu_buttons:
            btn.draw(screen)
        pygame.display.flip()
        continue   # skip the game-update code below

    # ── DRAW OPTIONS ───────────────────────────────────────
    if game_state == "options":
        screen.fill(BG_COLOR)
        txt = font_large.render("Innstillinger", True, TEXT_COLOR)
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 130)))
        info = font_med.render("(ingen innstillinger ennå)", True, (160, 160, 160))
        screen.blit(info, info.get_rect(center=(WIDTH // 2, 220)))
        options_back_button.draw(screen)
        pygame.display.flip()
        continue

    # ── PLAYING LOGIC ──────────────────────────────────────
    keys = pygame.key.get_pressed()

    # Horizontal movement
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

    # Variable-height jump
    if keys[pygame.K_SPACE] and jump_hold_frames > 0:
        vel_y            += HOLD_FORCE
        jump_hold_frames -= 1

    # Gravity & vertical collision
    vel_y += GRAVITY
    py    += vel_y

    if py + CHAR_H >= GROUND_Y:
        py        = float(GROUND_Y - CHAR_H)
        vel_y     = 0
        on_ground = True

    # Animation state machine
    if moving:
        new_state = "walk_right" if last_direction == "right" else "walk_left"
        if anim_state != new_state:
            anim_state = new_state
            anim_frame = 0
            anim_timer = 0
        idle_still_timer = 0
    else:
        if anim_state in ("walk_right", "walk_left"):
            anim_state = "idle"
            anim_frame = 0
            anim_timer = 0
        if anim_state in ("idle", "look_around"):
            idle_still_timer += 1
        if anim_state == "idle" and idle_still_timer >= IDLE_DELAY:
            anim_state       = "look_around"
            anim_frame       = 0
            anim_timer       = 0
            idle_still_timer = 0

    # Advance animation frame
    current_frames = frames_for_state(anim_state, last_direction)
    if anim_state != "idle":
        anim_timer += 1
        if anim_timer >= ANIM_SPEED:
            anim_timer  = 0
            anim_frame += 1
            if anim_frame >= len(current_frames):
                anim_frame = 0

    # ── ROOM DOOR COLLISION ────────────────────────────────
    #
    #  HOW THIS WORKS:
    #  We look up the current room in ROOMS, check if there is a door on
    #  "left" or "right", and if the player walks into it we switch rooms.
    #
    player_rect = pygame.Rect(int(px), int(py), CHAR_W, CHAR_H)
    room_data   = ROOMS[current_room]

    for side in ("left", "right"):
        target_room = room_data["doors"].get(side)
        if target_room is None:
            continue                            # no door on this side
        if target_room not in ROOMS:
            continue                            # room not defined yet
        door_rect = make_door_rect(side)
        if player_rect.colliderect(door_rect):
            # Switch to the target room
            current_room = target_room
            # Place player on the OPPOSITE side of the new room
            enter_from = "right" if side == "right" else "left"
            reset_player(enter_from)
            break

    # ── DRAW PLAYING ───────────────────────────────────────
    room_bg = ROOMS[current_room]["bg"]
    room_gc = ROOMS[current_room].get("ground_color", GROUND_COLOR)

    screen.blit(room_bg, (0, 0))
    pygame.draw.rect(screen, room_gc, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

    # Draw doors that exist in this room
    for side in ("left", "right"):
        if ROOMS[current_room]["doors"].get(side) is not None:
            draw_door(screen, side)

    # Player sprite
    sprite = current_frames[anim_frame]
    screen.blit(sprite, (int(px), int(py)))

    # HUD
    hud = font_small.render(
        f"ESC: Meny  |  SPACE: Hopp  |  PIL: Beveg  |  [{anim_state}]  |  Rom: {current_room}",
        True, (220, 220, 220)
    )
    screen.blit(hud, (10, 10))

    pygame.display.flip()
import pygame
import sys
 
pygame.init()
 
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spill")
clock = pygame.time.Clock()
 
# Konstanter og globale variabler
CHARACTER_SCALE = 3.0
GRAVITY         =  0.9
JUMP_FORCE      = -14
HOLD_FORCE      = -0.4
MAX_HOLD_TIME   =  18
SPEED           =   5
ANIM_SPEED      =   8
CHAR_W = CHAR_H = 0  # set after loading sheets
 
def scale_bg(path):
    return pygame.transform.scale(pygame.image.load(path).convert(), (WIDTH, HEIGHT))
 
def load_sheet(path, scale=CHARACTER_SCALE):
    sheet      = pygame.image.load(path).convert_alpha()
    frame_w = frame_h = 32
    num_frames = sheet.get_height() // frame_h
    sw, sh = int(frame_w * scale), int(frame_h * scale)
    return [
        pygame.transform.scale(sheet.subsurface((0, i * frame_h, frame_w, frame_h)), (sw, sh))
        for i in range(num_frames)
    ], sw, sh
 
def load_png(path, scale=2.0):
    """Load a PNG image, scale it, and return (image, rect)."""
    image = pygame.image.load(path).convert_alpha()
    w = int(image.get_width()  * scale)
    h = int(image.get_height() * scale)
    image = pygame.transform.scale(image, (w, h))
    return image, image.get_rect()
 
frames_walk_right, CHAR_W, CHAR_H = load_sheet("Character_Animasjon/Character_BaseAnimasjon/v1_høyre.png")
frames_walk_left,  _,      _      = load_sheet("Character_Animasjon/Character_BaseAnimasjon/v1_venstre.png")
frames_idle_right, _,      _      = load_sheet("Character_Animasjon/Character_BaseAnimasjon/Looking_around_Høyre.png")
frames_idle_left,  _,      _      = load_sheet("Character_Animasjon/Character_BaseAnimasjon/Looking_around_Venstre.png")
 
# ── Bone item ─────────────────────────────────────────────────────────────────
class Bone(pygame.sprite.Sprite):
    """A static collectible bone placed in a room.
 
    Args:
        x (int): Left edge of the bone sprite.
        y (int): Top edge of the bone sprite.
    """
    
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_png("Items/Bones_Item.png")
        self.rect.topleft = (x, y)
 
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
 
_bone_x = 60   
_bone_placeholder = Bone(_bone_x, 0)        
_bone_ground_y = 490 - _bone_placeholder.rect.height
bone = Bone(_bone_x, _bone_ground_y)           
del _bone_placeholder
 
bone_collected = False   
# ─────────────Hitbox for the rooms───────────────────────────────────────────────────────
 
# Hitbokser for alle rommene
PLATFORMS_ROOM1 = [
    pygame.Rect(0,   490, 800, 110),
    pygame.Rect(750, 140, 210, 200),
    pygame.Rect(320, 0,   170, 330),
    pygame.Rect(0,   380,  20, 110),
    pygame.Rect(10,  370,  20,  20),
    pygame.Rect(20,  360,  20,  20),
    pygame.Rect(30,  350,  20,  20),
    pygame.Rect(40,  340,  20,  20),
    pygame.Rect(50,  330,  20,  20),
    pygame.Rect(60,  200,  20, 130),
]
 
PLATFORMS_ROOM2 = [
    pygame.Rect(0,   490, 220, 110),
    pygame.Rect(190, 485,  20,  20),
    pygame.Rect(200, 480,  20,  20),
    pygame.Rect(210, 475,  20,  20),
    pygame.Rect(220, 470,  20,  20),
    pygame.Rect(230, 465,  20,  20),
    pygame.Rect(240, 460,  20,  20),
    pygame.Rect(250, 455,  20,  20),
    pygame.Rect(260, 450,  20,  20),
    pygame.Rect(270, 445,  20,  20),
    pygame.Rect(280, 440,  40, 210),
    pygame.Rect(475, 440,  40, 210),
    pygame.Rect(515, 448,  20,  20),
    pygame.Rect(535, 456,  20,  20),
    pygame.Rect(555, 464,  20,  20),
    pygame.Rect(575, 472,  20,  20),
    pygame.Rect(590, 480,  20,  20),
    pygame.Rect(600, 490, 210, 110),
]
 
PLATFORMS_ROOM3 = [
    pygame.Rect(0,   490, 300, 110),
    pygame.Rect(360, 360, 140,  30),
    pygame.Rect(270, 190, 100,  30),
    pygame.Rect(600, 240,  90,  30),
    pygame.Rect(0,   155, 170,  60),  
]
 
PLATFORMS_ROOM4 = [
    pygame.Rect(500, 490, 400, 110),
    pygame.Rect(0,   490, 300, 110),
    pygame.Rect(500, 320, 200,  30),
]
 
PLATFORMS_ROOM5 = [
    pygame.Rect(0,   490, 800, 110),
    pygame.Rect(70,    0,  40, 500),
    pygame.Rect(690,   0, 130, 350),
]
 # Transisons to each room, and their backgrounds
ROOMS = {
    "room1": {
        "bg":        scale_bg("Bakgrunn/bakgrunn.png"),
        "platforms": PLATFORMS_ROOM1,
        "left":  None,
        "right": "room2",
    },
    "room2": {
        "bg":        scale_bg("Bakgrunn/bakgrunnv3.png"),
        "platforms": PLATFORMS_ROOM2,
        "left":  "room1",
        "right": "room3",
    },
    "room3": {
        "bg":        scale_bg("Bakgrunn/bakgrunnv4.png"),
        "platforms": PLATFORMS_ROOM3,
        "left":  "room2",
        "right": None,
        "left_high":           "room4",
        "left_high_threshold": 250,
    },
    "room4": {
        "bg":        scale_bg("Bakgrunn/bakgrunnv5.png"),
        "platforms": PLATFORMS_ROOM4,
        "left":  "room5",
        "right": "room3",
    },
    "room5": {
        "bg":        scale_bg("Bakgrunn/bakgrunnv6.png"),
        "platforms": PLATFORMS_ROOM5,
        "left":  None,
        "right": "room4",
    },
}
 
DEBUG_PLATFORMS = True
 
BG_COLOR     = (30, 30, 30)
BUTTON_COLOR = (70, 130, 180)
HOVER_COLOR  = (100, 170, 220)
TEXT_COLOR   = (255, 255, 255)
 
font_large = pygame.font.SysFont(None, 64)
font_med   = pygame.font.SysFont(None, 36)
font_small = pygame.font.SysFont(None, 24)
 
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
    Button("Start",   cx, 250, 200, 50),
    Button("Escape",  cx, 320, 200, 50),
]
retry_button = Button("Try forever", cx, 300, 200, 50)
menu_button2 = Button("Menu",        cx, 370, 200, 50)
 
px = py = vel_y = 0.0
jump_hold_frames = 0
on_ground        = True
anim_frame = anim_timer = 0
last_direction   = "right"
current_room     = "room1"
game_state       = "menu"
death_alpha      = 0
 
def get_spawn_y(start_px, platforms):
    for plat in sorted(platforms, key=lambda p: p.top, reverse=True):
        if plat.left <= start_px + CHAR_W // 2 <= plat.right:
            return float(plat.top - CHAR_H)
    return float(HEIGHT - CHAR_H)
 
def reset_player(side="center"):
    global px, py, vel_y, jump_hold_frames, on_ground
    global anim_frame, anim_timer, last_direction
    if   side == "right": px = float(WIDTH - CHAR_W - 20)
    elif side == "left":  px = 20.0
    else:                 px = float(WIDTH // 2 - CHAR_W // 2)
    py             = get_spawn_y(px, ROOMS[current_room]["platforms"])
    vel_y          = 0.0; jump_hold_frames = 0; on_ground = True
    anim_frame = anim_timer = 0
    last_direction = "right"
 
def frames_for_state(moving):
    if moving:
        return frames_walk_right if last_direction == "right" else frames_walk_left
    else:
        return frames_idle_right if last_direction == "right" else frames_idle_left
 
def resolve_platforms(px, py, vel_y, platforms):
    new_py    = py + vel_y
    grounded  = False
    prev_feet = py + CHAR_H
    for plat in platforms:
        if px + CHAR_W <= plat.left or px >= plat.right:
            continue
        if prev_feet <= plat.top + 1 and new_py + CHAR_H >= plat.top:
            new_py   = float(plat.top - CHAR_H)
            vel_y    = 0.0
            grounded = True
            break
    if current_room == "room1" and new_py + CHAR_H > HEIGHT:
        new_py   = float(HEIGHT - CHAR_H)
        vel_y    = 0.0
        grounded = True
    return new_py, vel_y, grounded
 
def resolve_walls(px, py, platforms):
    player = pygame.Rect(int(px), int(py), CHAR_W, CHAR_H)
    for plat in platforms:
        if not player.colliderect(plat):
            continue
        if plat.height < 40:
            continue
        if plat.top >= (py + CHAR_H) - 22:
            continue
        if py + CHAR_H <= plat.top + 4:
            continue
        overlap_left  = player.right - plat.left
        overlap_right = plat.right  - player.left
        if overlap_left < overlap_right:
            px = float(plat.left - CHAR_W)
        else:
            px = float(plat.right)
    return px
 
# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    clock.tick(60)
 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
 
        if game_state == "menu":
            for btn in menu_buttons:
                if btn.clicked(event):
                    if   btn.text == "Start":   game_state = "playing"; current_room = "room1"; reset_player("center")
                    elif btn.text == "Escape": pygame.quit(); sys.exit()
 
        elif game_state == "dead":
            if retry_button.clicked(event):
                game_state = "playing"; current_room = "room1"; reset_player("left")
                death_alpha = 0
            if menu_button2.clicked(event):
                game_state = "menu"; death_alpha = 0
 
        elif game_state == "playing":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "menu"
                if event.key == pygame.K_SPACE and on_ground:
                    vel_y = JUMP_FORCE; jump_hold_frames = MAX_HOLD_TIME; on_ground = False
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                jump_hold_frames = 0
 
    # ── MENU ──────────────────────────────────────────────────────────────────
    if game_state == "menu":
        screen.fill(BG_COLOR)
        t = font_large.render("SPILL", True, (100, 180, 255))
        screen.blit(t, t.get_rect(center=(WIDTH // 2, 150)))
        for btn in menu_buttons: btn.draw(screen)
        pygame.display.flip(); continue
 
    # ── DEATH SCREEN ──────────────────────────────────────────────────────────
    if game_state == "dead":
        death_alpha = min(255, death_alpha + 6)
        screen.fill((0, 0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(death_alpha)
        overlay.fill((80, 0, 0))
        screen.blit(overlay, (0, 0))
        if death_alpha > 180:
            t = font_large.render("Death took your soul", True, (255, max(0, death_alpha - 180), 0))
            screen.blit(t, t.get_rect(center=(WIDTH // 2, 150)))
            s = font_med.render("You have been consumed by the void", True, (180, 180, 180))
            screen.blit(s, s.get_rect(center=(WIDTH // 2, 230)))
            retry_button.draw(screen)
            menu_button2.draw(screen)
        pygame.display.flip(); continue
 
    # ── PLAYING ───────────────────────────────────────────────────────────────
    keys   = pygame.key.get_pressed()
    moving = False
    room   = ROOMS[current_room]
 
    if keys[pygame.K_LEFT]:
        px -= SPEED; last_direction = "left";  moving = True
    if keys[pygame.K_RIGHT]:
        px += SPEED; last_direction = "right"; moving = True
 
    if keys[pygame.K_SPACE] and jump_hold_frames > 0:
        vel_y += HOLD_FORCE; jump_hold_frames -= 1
 
    px = resolve_walls(px, py, room["platforms"])
 
    if on_ground:
        for plat in room["platforms"]:
            if px + CHAR_W <= plat.left or px >= plat.right:
                continue
            feet = py + CHAR_H
            if plat.top < feet and plat.top > feet - 22:
                py = float(plat.top - CHAR_H)
                break
 
    vel_y += GRAVITY
    py, vel_y, on_ground = resolve_platforms(px, py, vel_y, room["platforms"])
 
    if py > HEIGHT:
        game_state = "dead"; death_alpha = 0; continue
 
    # ── Bone collection check (only in room1, only if not yet collected) ──────
    if current_room == "room1" and not bone_collected:
        player_rect = pygame.Rect(int(px), int(py), CHAR_W, CHAR_H)
        if player_rect.colliderect(bone.rect):
            bone_collected = True
 
    # ── Room transitions ──────────────────────────────────────────────────────
    if px + CHAR_W <= 0:
        high_dest   = room.get("left_high")
        high_thresh = room.get("left_high_threshold", 999)
        if high_dest and py < high_thresh:
            current_room = high_dest; reset_player("right")
        elif room["left"]:
            current_room = room["left"]; reset_player("right")
        else:
            px = 0.0
 
    elif px >= WIDTH:
        if room["right"]:
            current_room = room["right"]; reset_player("left")
        else:
            px = float(WIDTH - CHAR_W)
 
    # ── Animation ───────────────────────────────────────────────────────────────
    current_frames = frames_for_state(moving)
    if moving:
        anim_timer += 1
        if anim_timer >= ANIM_SPEED:
            anim_timer = 0
            anim_frame = (anim_frame + 1) % len(current_frames)
    else:
        anim_frame = 0
        anim_timer = 0
 
    # ── Draw ──────────────────────────────────────────────────────────────────
    screen.blit(room["bg"], (0, 0))
 
    if DEBUG_PLATFORMS:
        for plat in room["platforms"]:
            pygame.draw.rect(screen, (255, 0, 0), plat, 2)
 
    # Draw bone in room1 if not yet collected
    if current_room == "room1" and not bone_collected:
        bone.draw(screen)
 
    screen.blit(current_frames[anim_frame], (int(px), int(py)))
 
    # Show if taken or not, and current room in HUD
    hud_text = "ESC: Meny  |  SPACE: Hopp  |  PIL: Beveg  |  Rom: " + current_room
    if bone_collected:
        hud_text += "  |  bone: 1"
    screen.blit(font_small.render(hud_text, True, (220, 220, 220)), (10, 10))
 
    pygame.display.flip()
import math
import os
import random

import pygame
import vehicle_data

pygame.init()

# =========================================================
# SCREEN
# =========================================================

WIDTH = 900
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Highway Racer")

clock = pygame.time.Clock()

# =========================================================
# COLORS
# =========================================================

BACKGROUND = (8, 10, 16)
PANEL = (15, 18, 28)

BLUE = (80, 180, 255)
WHITE = (240, 240, 245)
GRAY = (150, 155, 165)

BUTTON_FILL = (15, 19, 30)
BUTTON_FILL_HOVER = (20, 52, 82)
BUTTON_BORDER = (48, 55, 72)
TEXT_IDLE = (185, 191, 204)
DEEP_BLUE = (30, 110, 200)

# =========================================================
# FONTS
# =========================================================

title_font = pygame.font.Font(None, 92)
button_font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 26)
label_font = pygame.font.Font(None, 22)
name_font = pygame.font.Font(None, 50)

# =========================================================
# LAYOUT
# =========================================================

# Left column: title + buttons
COLUMN_X = 50
BUTTON_WIDTH = 320
BUTTON_HEIGHT = 48
BUTTON_GAP = 12
BUTTON_START_Y = 240

# Right column: vehicle showcase stage
STAGE = pygame.Rect(430, 50, 440, 600)
ROAD_LEFT = STAGE.x + 50
ROAD_RIGHT = STAGE.right - 50
LANE_LINES = (STAGE.x + 115, STAGE.right - 115)
CAR_MAX_W = 190
CAR_MAX_H = 390
CAR_CENTER = (STAGE.centerx, 340)

# (label, value returned to the main game loop)
BUTTONS = [
    ("PLAY", "play"),
    ("GARAGE", "garage"),
    ("ENVIRONMENT", "environment"),
    ("STATISTICS", "statistics"),
    ("SETTINGS", "settings"),
    ("EXIT", "quit"),
]

BUTTON_RECTS = [
    pygame.Rect(
        COLUMN_X,
        BUTTON_START_Y + i * (BUTTON_HEIGHT + BUTTON_GAP),
        BUTTON_WIDTH,
        BUTTON_HEIGHT,
    )
    for i in range(len(BUTTONS))
]

# =========================================================
# SMALL HELPERS
# =========================================================


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = clamp(t)
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t)),
    )


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def render_spaced(text, font, color, spacing=0):
    """Render text with extra letter spacing (tracking)."""
    glyphs = [font.render(ch, True, color) for ch in text]
    width = sum(g.get_width() for g in glyphs) + spacing * (len(text) - 1)
    height = max(g.get_height() for g in glyphs)
    surface = pygame.Surface((max(1, width), height), pygame.SRCALPHA)
    x = 0
    for g in glyphs:
        surface.blit(g, (x, 0))
        x += g.get_width() + spacing
    return surface


def blur(surface, shrink=5):
    """Cheap blur: scale down, scale up. Only used at load time."""
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(
        surface, (max(1, w // shrink), max(1, h // shrink))
    )
    return pygame.transform.smoothscale(small, (w, h))


def radial_glow(radius, color, max_alpha):
    """Pre-rendered soft round glow (per-pixel alpha)."""
    surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -3):
        alpha = int(max_alpha * (1 - r / radius) ** 2)
        pygame.draw.circle(surface, (*color, alpha), (radius, radius), r)
    return surface


def make_glow_text(text, font, color, glow_color, spacing=0, pad=26):
    """Returns (text_surface, glow_surface, pad)."""
    text_surface = render_spaced(text, font, color, spacing)
    glow_source = render_spaced(text, font, glow_color, spacing)
    w, h = glow_source.get_size()
    base = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    base.fill((*glow_color, 0))
    base.blit(glow_source, (pad, pad))
    return text_surface, blur(base, 5), pad


# =========================================================
# VEHICLE IMAGES
# =========================================================

menu_vehicle_images = {}

for car in vehicle_data.vehicles:

    image_path = os.path.join(
        os.path.dirname(__file__),
        car["image"]
    )

    menu_vehicle_images[car["image"]] = pygame.image.load(
        image_path
    ).convert_alpha()

# Showcase versions are scaled ONCE here (the old menu rescaled every
# frame). Each entry: (scaled_car, soft_shadow)
showcase_images = {}

for _key, _image in menu_vehicle_images.items():

    _w, _h = _image.get_size()
    _scale = min(CAR_MAX_W / _w, CAR_MAX_H / _h)
    _car = pygame.transform.smoothscale(
        _image, (max(1, int(_w * _scale)), max(1, int(_h * _scale)))
    )

    _mask = pygame.mask.from_surface(_car)
    _shadow = _mask.to_surface(
        setcolor=(0, 0, 0, 170), unsetcolor=(0, 0, 0, 0)
    )
    _shadow = blur(_shadow, 4)

    showcase_images[_key] = (_car, _shadow)


def get_vehicle_name(vehicle):
    name = vehicle.get("name") if hasattr(vehicle, "get") else None
    if not name:
        base = os.path.splitext(os.path.basename(vehicle["image"]))[0]
        name = base.replace("_", " ")
    return str(name).upper()


# =========================================================
# PRE-RENDERED STATIC GRAPHICS
# =========================================================


def build_background():
    bg = pygame.Surface((WIDTH, HEIGHT))

    # Vertical gradient
    for y in range(HEIGHT):
        color = lerp_color((5, 7, 12), (12, 16, 28), y / HEIGHT)
        pygame.draw.line(bg, color, (0, y), (WIDTH, y))

    # Ambient light behind the showcase and a faint one top-left
    glow = radial_glow(360, DEEP_BLUE, 70)
    bg.blit(glow, glow.get_rect(center=(STAGE.centerx, 340)))

    glow = radial_glow(260, (30, 120, 170), 28)
    bg.blit(glow, glow.get_rect(center=(140, 110)))

    # Faint diagonal speed lines
    for i in range(14):
        x = -200 + i * 90
        pygame.draw.line(
            bg, (14, 20, 34), (x, HEIGHT), (x + 320, 0), 1
        )

    # Vignette
    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    steps = 70
    for i in range(steps):
        alpha = int(170 * (1 - i / steps) ** 2)
        pygame.draw.rect(
            vignette,
            (0, 0, 0, alpha),
            (i, i, WIDTH - i * 2, HEIGHT - i * 2),
            1,
        )
    bg.blit(vignette, (0, 0))

    return bg.convert()


def build_stage():
    w, h = STAGE.size
    stage = pygame.Surface((w, h), pygame.SRCALPHA)

    # Panel body
    pygame.draw.rect(
        stage, (9, 12, 20, 205), (0, 0, w, h), border_radius=18
    )

    # Road
    road_x = ROAD_LEFT - STAGE.x
    road_w = ROAD_RIGHT - ROAD_LEFT
    pygame.draw.rect(stage, (14, 17, 27, 255), (road_x, 2, road_w, h - 4))

    # Neon road edges with soft halo
    for x in (road_x, road_x + road_w):
        pygame.draw.line(stage, (40, 100, 160, 60), (x, 2), (x, h - 3), 9)
        pygame.draw.line(stage, (60, 140, 210, 120), (x, 2), (x, h - 3), 5)
        pygame.draw.line(stage, (*BLUE, 255), (x, 2), (x, h - 3), 2)

    # Border
    pygame.draw.rect(
        stage, (45, 62, 92, 255), (0, 0, w, h), 2, border_radius=18
    )

    # Corner brackets
    m, ln, th = 12, 24, 3
    for cx, sx in ((m, 1), (w - m, -1)):
        for cy, sy in ((m, 1), (h - m, -1)):
            pygame.draw.line(stage, BLUE, (cx, cy), (cx + ln * sx, cy), th)
            pygame.draw.line(stage, BLUE, (cx, cy), (cx, cy + ln * sy), th)

    return stage.convert_alpha()


background_surface = build_background()
stage_surface = build_stage()
car_glow = radial_glow(230, (40, 140, 255), 125)

# Title (two lines) with glow
highway_text, highway_glow, TITLE_PAD = make_glow_text(
    "HIGHWAY", title_font, WHITE, (120, 190, 255), spacing=3
)
racer_text, racer_glow, _ = make_glow_text(
    "RACER", title_font, BLUE, BLUE, spacing=10
)

subtitle_surface = render_spaced(
    "ADAPTIVE RACING EXPERIENCE", small_font, GRAY, 3
)
footer_surface = render_spaced(
    "CLICK TO SELECT   |   ESC  EXIT", label_font, GRAY, 2
)
stage_label_surface = render_spaced(
    "SELECTED VEHICLE", label_font, GRAY, 4
)

_name_cache = {}
_button_label_cache = {}


def get_name_surface(name):
    if name not in _name_cache:
        _name_cache[name] = render_spaced(name, name_font, WHITE, 4)
    return _name_cache[name]


def get_button_labels(text):
    """(idle_label, hover_label) pre-rendered, cross-faded on hover."""
    if text not in _button_label_cache:
        _button_label_cache[text] = (
            render_spaced(text, button_font, TEXT_IDLE, 3),
            render_spaced(text, button_font, WHITE, 3),
        )
    return _button_label_cache[text]


# =========================================================
# DRAW BUTTON
# =========================================================

def draw_button(text, rect, mouse_pos, hover=None, x_offset=0):
    """
    Draws one menu button.

    Old calls draw_button(text, rect, mouse_pos) still work. The menu
    loop passes a smoothed `hover` value (0..1) and an entrance
    `x_offset` for the animations.
    """

    if hover is None:
        hover = 1.0 if rect.collidepoint(mouse_pos) else 0.0

    h = clamp(hover)
    r = rect.move(int(x_offset + 10 * h), 0)

    # Soft neon glow (solid colours, no alpha surfaces needed)
    if h > 0.03:
        for grow, strength in ((10, 0.10), (6, 0.18), (3, 0.32)):
            pygame.draw.rect(
                screen,
                lerp_color((10, 13, 22), BLUE, strength * h),
                r.inflate(grow * 2, grow * 2),
                border_radius=12 + grow,
            )

    # Body + border
    pygame.draw.rect(
        screen,
        lerp_color(BUTTON_FILL, BUTTON_FILL_HOVER, h),
        r,
        border_radius=12,
    )
    pygame.draw.rect(
        screen,
        lerp_color(BUTTON_BORDER, BLUE, h),
        r,
        2,
        border_radius=12,
    )

    # Left accent bar
    bar_height = int(lerp(r.height * 0.35, r.height - 20, h))
    bar = pygame.Rect(0, 0, 4, bar_height)
    bar.midleft = (r.x + 14, r.centery)
    pygame.draw.rect(
        screen,
        lerp_color((55, 75, 100), BLUE, h),
        bar,
        border_radius=2,
    )

    # Label (cross-fade between idle and bright)
    idle, bright = get_button_labels(text)
    label_pos = idle.get_rect(midleft=(r.x + 34, r.centery))
    screen.blit(idle, label_pos)
    if h > 0.02:
        bright.set_alpha(int(255 * h))
        screen.blit(bright, label_pos)

    # Chevron
    if h > 0.05:
        cx = r.right - 32 + int((1 - h) * 10)
        cy = r.centery
        pygame.draw.lines(
            screen,
            lerp_color(BUTTON_FILL_HOVER, BLUE, h),
            False,
            [(cx, cy - 7), (cx + 7, cy), (cx, cy + 7)],
            3,
        )


# =========================================================
# MAIN MENU
# =========================================================

def run_menu():
    pygame.display.set_caption("Highway Racer")

    hover = [0.0] * len(BUTTONS)

    # Road streaks inside the showcase stage
    streaks = [
        [
            random.choice(
                (
                    random.randint(ROAD_LEFT + 8, LANE_LINES[0] - 8),
                    random.randint(LANE_LINES[1] + 8, ROAD_RIGHT - 8),
                )
            ),
            random.uniform(STAGE.top, STAGE.bottom),
            random.randint(18, 60),
            random.uniform(260, 620),
        ]
        for _ in range(14)
    ]

    time_alive = 0.0
    showcase_time = 0.0
    last_selected = None
    hand_cursor = False
    dt = 1 / 60

    running = True

    try:
        while running:

            mouse_pos = pygame.mouse.get_pos()

            # =============================================
            # EVENTS
            # =============================================

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_ESCAPE:
                        return "menu"

                if event.type == pygame.MOUSEBUTTONDOWN:

                    if event.button == 1:

                        # PLAY / GARAGE / ENVIRONMENT /
                        # STATISTICS / SETTINGS / EXIT
                        for (label, action), rect in zip(
                            BUTTONS, BUTTON_RECTS
                        ):
                            if rect.collidepoint(event.pos):
                                return action

            # =============================================
            # UPDATE ANIMATION STATE
            # =============================================

            time_alive += dt

            selected_index = vehicle_data.player_data["selected_vehicle"]
            if selected_index != last_selected:
                last_selected = selected_index
                showcase_time = 0.0
            else:
                showcase_time += dt

            any_hover = False
            for i, rect in enumerate(BUTTON_RECTS):
                target = 1.0 if rect.collidepoint(mouse_pos) else 0.0
                any_hover = any_hover or target == 1.0
                hover[i] += (target - hover[i]) * min(1.0, dt * 14)

            if any_hover != hand_cursor:
                hand_cursor = any_hover
                try:
                    pygame.mouse.set_cursor(
                        pygame.SYSTEM_CURSOR_HAND
                        if hand_cursor
                        else pygame.SYSTEM_CURSOR_ARROW
                    )
                except pygame.error:
                    pass

            for streak in streaks:
                streak[1] += streak[3] * dt
                if streak[1] - streak[2] > STAGE.bottom:
                    streak[1] = STAGE.top - random.randint(0, 120)

            # =============================================
            # BACKGROUND
            # =============================================

            screen.blit(background_surface, (0, 0))

            # =============================================
            # SHOWCASE STAGE
            # =============================================

            screen.blit(stage_surface, STAGE.topleft)

            # Moving lane dashes + speed streaks (clipped to stage)
            screen.set_clip(STAGE.inflate(-6, -6))

            dash_period = 80
            offset = (time_alive * 280) % dash_period
            y = STAGE.top - dash_period + offset
            while y < STAGE.bottom:
                for lane_x in LANE_LINES:
                    pygame.draw.rect(
                        screen, (55, 115, 165), (lane_x - 2, y, 4, 36)
                    )
                y += dash_period

            for sx, sy, length, _speed in streaks:
                pygame.draw.line(
                    screen,
                    (35, 85, 130),
                    (sx, sy - length),
                    (sx, sy),
                    2,
                )

            screen.set_clip(None)

            # Glow behind the car (gentle pulse)
            car_key = vehicle_data.vehicles[selected_index]["image"]
            selected_car = vehicle_data.vehicles[selected_index]
            car_surface, shadow_surface = showcase_images[car_key]

            intro = ease_out(showcase_time / 0.7)
            pulse = 0.5 + 0.5 * math.sin(time_alive * 2.0)

            car_glow.set_alpha(int((150 + 80 * pulse) * intro))
            screen.blit(
                car_glow, car_glow.get_rect(center=CAR_CENTER)
            )

            # Car: slides up into place, then hovers slightly
            bob = math.sin(time_alive * 1.6) * 4
            cx = CAR_CENTER[0]
            cy = CAR_CENTER[1] + bob + (1 - intro) * 70

            shadow_surface.set_alpha(int(255 * intro))
            car_surface.set_alpha(int(255 * intro))

            screen.blit(
                shadow_surface,
                shadow_surface.get_rect(center=(cx + 12, cy + 16)),
            )
            screen.blit(
                car_surface, car_surface.get_rect(center=(cx, cy))
            )

            # Stage labels
            screen.blit(
                stage_label_surface,
                stage_label_surface.get_rect(
                    center=(STAGE.centerx, STAGE.top + 32)
                ),
            )

            name_surface = get_name_surface(get_vehicle_name(selected_car))
            name_rect = name_surface.get_rect(
                center=(STAGE.centerx, STAGE.bottom - 52)
            )
            screen.blit(name_surface, name_rect)

            pygame.draw.line(
                screen,
                BLUE,
                (STAGE.centerx - 40, STAGE.bottom - 24),
                (STAGE.centerx + 40, STAGE.bottom - 24),
                3,
            )

            # =============================================
            # TITLE
            # =============================================

            glow_alpha = int(150 + 70 * pulse)
            racer_glow.set_alpha(glow_alpha)
            highway_glow.set_alpha(100)

            hw_pos = highway_text.get_rect(topleft=(COLUMN_X, 52))
            rc_pos = racer_text.get_rect(topleft=(COLUMN_X, 118))

            screen.blit(
                highway_glow, (hw_pos.x - TITLE_PAD, hw_pos.y - TITLE_PAD)
            )
            screen.blit(highway_text, hw_pos)

            screen.blit(
                racer_glow, (rc_pos.x - TITLE_PAD, rc_pos.y - TITLE_PAD)
            )
            screen.blit(racer_text, rc_pos)

            # =============================================
            # SUBTITLE
            # =============================================

            pygame.draw.rect(
                screen, BLUE, (COLUMN_X, 186, 56, 3), border_radius=2
            )
            screen.blit(subtitle_surface, (COLUMN_X, 198))

            # =============================================
            # BUTTONS
            # =============================================

            for i, ((label, _action), rect) in enumerate(
                zip(BUTTONS, BUTTON_RECTS)
            ):
                # Staggered slide-in when the menu opens
                progress = ease_out((time_alive - 0.07 * i) / 0.45)
                x_offset = -(1 - progress) * 80

                draw_button(
                    label,
                    rect,
                    mouse_pos,
                    hover[i],
                    x_offset,
                )

            # =============================================
            # FOOTER
            # =============================================

            screen.blit(
                footer_surface,
                footer_surface.get_rect(
                    midleft=(COLUMN_X, HEIGHT - 38)
                ),
            )

            # =============================================
            # UPDATE
            # =============================================

            pygame.display.update()

            dt = min(clock.tick(60) / 1000, 0.05)

    finally:
        # Never leave the hand cursor stuck when leaving the menu
        try:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        except pygame.error:
            pass

    return "quit"
import math
import os
import random

import pygame

from vehicle_data import vehicles
import vehicle_data

pygame.init()

# =========================================================
# SCREEN
# =========================================================

WIDTH = 900
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Highway Racer - Garage")

clock = pygame.time.Clock()


# =========================================================
# COLORS
# =========================================================

BACKGROUND = (8, 10, 16)
PANEL = (15, 18, 28)

BLUE = (80, 180, 255)
RED = (255, 55, 75)
GREEN = (50, 220, 140)
YELLOW = (255, 205, 60)

WHITE = (240, 240, 245)
GRAY = (150, 155, 165)

DARK = (10, 12, 17)
WINDOW = (25, 45, 60)
WHEEL = (5, 5, 8)
LIGHT = (235, 245, 255)

ROAD_EDGE_LINE = (220, 225, 230)
RUMBLE_COLOR = (235, 235, 240)

RUMBLE_WIDTH = 10
RUMBLE_HEIGHT = 25
RUMBLE_GAP = 25

# Shared with the redesigned main menu
BUTTON_FILL = (15, 19, 30)
BUTTON_FILL_HOVER = (20, 52, 82)
BUTTON_BORDER = (48, 55, 72)
TEXT_IDLE = (185, 191, 204)
DEEP_BLUE = (30, 110, 200)

# Garage specific
LOCK_RED = (230, 75, 95)
TEAL = (60, 230, 200)
PURPLE = (170, 110, 255)
PANEL_DARK = (9, 12, 20)
PANEL_BORDER = (45, 62, 92)


# =========================================================
# FONTS
# =========================================================

title_font = pygame.font.Font(None, 70)
large_font = pygame.font.Font(None, 45)
medium_font = pygame.font.Font(None, 30)
small_font = pygame.font.Font(None, 24)
label_font = pygame.font.Font(None, 22)
name_font = pygame.font.Font(None, 54)
button_font = pygame.font.Font(None, 34)
coin_font = pygame.font.Font(None, 36)


# =========================================================
# LAYOUT
# =========================================================

STAGE = pygame.Rect(150, 100, 600, 400)
RING_CENTER = (STAGE.centerx, 260)
RING_R = 128

CAR_MAX_W = 170
CAR_MAX_H = 240

STATS_PANEL = pygame.Rect(150, 512, 600, 88)

PREVIOUS_BUTTON = pygame.Rect(60, 225, 70, 70)
NEXT_BUTTON = pygame.Rect(770, 225, 70, 70)
BACK_BUTTON = pygame.Rect(50, 618, 170, 48)
SELECT_BUTTON = pygame.Rect(300, 618, 300, 48)

COIN_PILL = pygame.Rect(650, 34, 200, 54)

# Optional: when True, leaving the garage restores the vehicle that was
# actually equipped (instead of keeping whichever car you last browsed).
# False keeps the original behaviour exactly.
RESTORE_EQUIPPED_ON_EXIT = False


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


_text_cache = {}


def get_text(text, font, color, spacing=0):
    """Cached letter-spaced text surface."""
    key = (text, id(font), color, spacing)
    if key not in _text_cache:
        _text_cache[key] = render_spaced(text, font, color, spacing)
    return _text_cache[key]


def blur(surface, shrink=5):
    """Cheap blur: scale down, scale up. Load time only."""
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

vehicle_images = {}

for car in vehicles:

    image_path = os.path.join(
        os.path.dirname(__file__),
        car["image"]
    )

    vehicle_images[car["image"]] = pygame.image.load(
        image_path
    ).convert_alpha()


# Showroom versions are scaled ONCE here (the old garage rescaled every
# frame). Each entry: (normal, dark_locked_version, soft_shadow)
showroom_images = {}

for _key, _image in vehicle_images.items():

    _w, _h = _image.get_size()
    _scale = min(CAR_MAX_W / _w, CAR_MAX_H / _h)
    _car = pygame.transform.smoothscale(
        _image, (max(1, int(_w * _scale)), max(1, int(_h * _scale)))
    )

    _locked = _car.copy()
    _locked.fill((55, 65, 90, 255), special_flags=pygame.BLEND_RGBA_MULT)

    _shadow = blur(
        pygame.mask.from_surface(_car).to_surface(
            setcolor=(0, 0, 0, 170), unsetcolor=(0, 0, 0, 0)
        ),
        4,
    )

    showroom_images[_key] = (_car, _locked, _shadow)

# Soft light behind each car, tinted with that vehicle's colour
vehicle_glows = []

for _vehicle in vehicles:
    _tint = lerp_color(_vehicle.get("color", BLUE), BLUE, 0.45)
    vehicle_glows.append(radial_glow(210, _tint, 125))

# The highest stat value defines the full length of every stat bar
# (PHANTOM has speed 120, which would overflow a 0-100 bar).
STAT_MAX = max(
    100,
    max(
        max(v["speed"], v["handling"], v["acceleration"])
        for v in vehicles
    ),
)


# =========================================================
# PRE-RENDERED STATIC GRAPHICS
# =========================================================

def build_background():
    bg = pygame.Surface((WIDTH, HEIGHT))

    for y in range(HEIGHT):
        color = lerp_color((5, 7, 12), (12, 16, 28), y / HEIGHT)
        pygame.draw.line(bg, color, (0, y), (WIDTH, y))

    glow = radial_glow(380, DEEP_BLUE, 62)
    bg.blit(glow, glow.get_rect(center=RING_CENTER))

    glow = radial_glow(260, (30, 120, 170), 28)
    bg.blit(glow, glow.get_rect(center=(140, 60)))

    for i in range(14):
        x = -200 + i * 90
        pygame.draw.line(bg, (14, 20, 34), (x, HEIGHT), (x + 320, 0), 1)

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

    pygame.draw.rect(
        stage, (*PANEL_DARK, 205), (0, 0, w, h), border_radius=18
    )

    cx = RING_CENTER[0] - STAGE.x
    cy = RING_CENTER[1] - STAGE.y

    # Turntable platform
    pygame.draw.circle(stage, (13, 17, 28, 255), (cx, cy), RING_R + 6)
    pygame.draw.circle(stage, (30, 44, 66, 255), (cx, cy), RING_R + 6, 2)
    pygame.draw.circle(stage, (22, 32, 50, 255), (cx, cy), RING_R - 30, 1)
    pygame.draw.circle(stage, (22, 32, 50, 255), (cx, cy), RING_R - 80, 1)
    pygame.draw.line(
        stage, (22, 32, 50, 255), (cx - RING_R, cy), (cx + RING_R, cy), 1
    )
    pygame.draw.line(
        stage, (22, 32, 50, 255), (cx, cy - RING_R), (cx, cy + RING_R), 1
    )

    # Tick marks around the platform
    for deg in range(0, 360, 6):
        a = math.radians(deg)
        long_tick = deg % 30 == 0
        r1 = RING_R + 14
        r2 = RING_R + (26 if long_tick else 20)
        pygame.draw.line(
            stage,
            (60, 90, 130, 255) if long_tick else (38, 56, 82, 255),
            (cx + math.cos(a) * r1, cy + math.sin(a) * r1),
            (cx + math.cos(a) * r2, cy + math.sin(a) * r2),
            2 if long_tick else 1,
        )

    pygame.draw.rect(
        stage, (*PANEL_BORDER, 255), (0, 0, w, h), 2, border_radius=18
    )

    # Corner brackets
    m, ln, th = 12, 24, 3
    for bx, sx in ((m, 1), (w - m, -1)):
        for by, sy in ((m, 1), (h - m, -1)):
            pygame.draw.line(stage, BLUE, (bx, by), (bx + ln * sx, by), th)
            pygame.draw.line(stage, BLUE, (bx, by), (bx, by + ln * sy), th)

    return stage.convert_alpha()


def build_lock_icon():
    icon = pygame.Surface((64, 76), pygame.SRCALPHA)

    # Shackle
    pygame.draw.arc(icon, LOCK_RED, (16, 6, 32, 34), 0, math.pi, 5)
    pygame.draw.line(icon, LOCK_RED, (17, 23), (17, 34), 5)
    pygame.draw.line(icon, LOCK_RED, (47, 23), (47, 34), 5)

    # Body
    pygame.draw.rect(icon, (14, 18, 30), (8, 32, 48, 38), border_radius=8)
    pygame.draw.rect(icon, LOCK_RED, (8, 32, 48, 38), 3, border_radius=8)

    # Keyhole
    pygame.draw.circle(icon, LOCK_RED, (32, 48), 5)
    pygame.draw.line(icon, LOCK_RED, (32, 50), (32, 59), 4)

    return icon.convert_alpha()


background_surface = build_background()
stage_surface = build_stage()
lock_icon = build_lock_icon()

# Header
garage_text, garage_glow, TITLE_PAD = make_glow_text(
    "GARAGE", title_font, BLUE, BLUE, spacing=8
)


# =========================================================
# DRAW VEHICLE
# (legacy vector renderer - kept for compatibility, the redesigned
# garage displays the PNG vehicles instead)
# =========================================================

def draw_vehicle(x, y, vehicle_type, color):

    # =====================================================
    # SEDAN
    # =====================================================

    if vehicle_type == "sedan":

        width = 100
        height = 175

        # Main body
        pygame.draw.rect(
            screen,
            color,
            (x, y, width, height),
            border_radius=18
        )

        # Hood
        pygame.draw.rect(
            screen,
            color,
            (x + 8, y + 5, width - 16, 35),
            border_radius=10
        )

        # Roof
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + 18, y + 42),
                (x + 82, y + 42),
                (x + 72, y + 95),
                (x + 28, y + 95)
            ]
        )

        # Front windshield
        pygame.draw.polygon(
            screen,
            WINDOW,
            [
                (x + 25, y + 47),
                (x + 75, y + 47),
                (x + 68, y + 72),
                (x + 32, y + 72)
            ]
        )

        # Rear windshield
        pygame.draw.polygon(
            screen,
            WINDOW,
            [
                (x + 32, y + 78),
                (x + 68, y + 78),
                (x + 75, y + 92),
                (x + 25, y + 92)
            ]
        )

        # Headlights
        pygame.draw.rect(
            screen,
            LIGHT,
            (x + 12, y + 12, 20, 8),
            border_radius=4
        )

        pygame.draw.rect(
            screen,
            LIGHT,
            (x + 68, y + 12, 20, 8),
            border_radius=4
        )

        # Wheels
        for wheel_y in (35, 115):

            pygame.draw.rect(
                screen,
                WHEEL,
                (x - 8, y + wheel_y, 10, 40),
                border_radius=4
            )

            pygame.draw.rect(
                screen,
                WHEEL,
                (x + width - 2, y + wheel_y, 10, 40),
                border_radius=4
            )


    # =====================================================
    # SPORTS CAR
    # =====================================================

    elif vehicle_type == "sports":

        width = 110

        # Main body
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + 10, y + 20),
                (x + 100, y + 20),
                (x + 108, y + 150),
                (x + 90, y + 170),
                (x + 20, y + 170),
                (x + 2, y + 150)
            ]
        )

        # Roof
        pygame.draw.polygon(
            screen,
            color,
            [
                (x + 20, y + 55),
                (x + 90, y + 55),
                (x + 75, y + 105),
                (x + 35, y + 105)
            ]
        )

        # Windshield
        pygame.draw.polygon(
            screen,
            WINDOW,
            [
                (x + 28, y + 58),
                (x + 82, y + 58),
                (x + 72, y + 85),
                (x + 38, y + 85)
            ]
        )

        # Racing stripe
        pygame.draw.rect(
            screen,
            WHITE,
            (x + 49, y + 15, 12, 145)
        )

        # Headlights
        pygame.draw.rect(
            screen,
            LIGHT,
            (x + 12, y + 25, 25, 8),
            border_radius=4
        )

        pygame.draw.rect(
            screen,
            LIGHT,
            (x + 73, y + 25, 25, 8),
            border_radius=4
        )

        # Wheels
        for wheel_y in (40, 120):

            pygame.draw.rect(
                screen,
                WHEEL,
                (x - 8, y + wheel_y, 12, 38),
                border_radius=5
            )

            pygame.draw.rect(
                screen,
                WHEEL,
                (x + width - 4, y + wheel_y, 12, 38),
                border_radius=5
            )


    # =====================================================
    # SUV
    # =====================================================

    elif vehicle_type == "suv":

        width = 110

        # Main body
        pygame.draw.rect(
            screen,
            color,
            (x, y, width, 180),
            border_radius=12
        )

        # Roof
        pygame.draw.rect(
            screen,
            color,
            (x + 10, y + 25, 90, 85),
            border_radius=12
        )

        # Windows
        pygame.draw.rect(
            screen,
            WINDOW,
            (x + 18, y + 35, 74, 55),
            border_radius=8
        )

        # Window divider
        pygame.draw.rect(
            screen,
            DARK,
            (x + 52, y + 35, 6, 55)
        )

        # Front bumper
        pygame.draw.rect(
            screen,
            DARK,
            (x + 8, y + 5, 94, 15),
            border_radius=5
        )

        # Headlights
        pygame.draw.rect(
            screen,
            LIGHT,
            (x + 15, y + 8, 25, 6),
            border_radius=3
        )

        pygame.draw.rect(
            screen,
            LIGHT,
            (x + 70, y + 8, 25, 6),
            border_radius=3
        )

        # Wheels
        for wheel_y in (40, 125):

            pygame.draw.rect(
                screen,
                WHEEL,
                (x - 9, y + wheel_y, 12, 42),
                border_radius=5
            )

            pygame.draw.rect(
                screen,
                WHEEL,
                (x + width - 3, y + wheel_y, 12, 42),
                border_radius=5
            )


    # =====================================================
    # TRUCK
    # =====================================================

    elif vehicle_type == "truck":

        width = 125

        # Truck body
        pygame.draw.rect(
            screen,
            color,
            (x, y + 60, width, 110),
            border_radius=10
        )

        # Cabin
        pygame.draw.rect(
            screen,
            color,
            (x + 15, y + 10, 95, 90),
            border_radius=12
        )

        # Windshield
        pygame.draw.rect(
            screen,
            WINDOW,
            (x + 25, y + 25, 75, 35),
            border_radius=6
        )

        # Grill
        pygame.draw.rect(
            screen,
            DARK,
            (x + 25, y + 75, 75, 18),
            border_radius=5
        )

        # Headlights
        pygame.draw.rect(
            screen,
            LIGHT,
            (x + 10, y + 68, 18, 10),
            border_radius=3
        )

        pygame.draw.rect(
            screen,
            LIGHT,
            (x + 97, y + 68, 18, 10),
            border_radius=3
        )

        # Wheels
        for wheel_y in (55, 125):

            pygame.draw.rect(
                screen,
                WHEEL,
                (x - 10, y + wheel_y, 14, 42),
                border_radius=5
            )

            pygame.draw.rect(
                screen,
                WHEEL,
                (x + width - 4, y + wheel_y, 14, 42),
                border_radius=5
            )


    # =====================================================
    # MOTORCYCLE
    # =====================================================

    elif vehicle_type == "bike":

        center_x = x + 50

        # Wheels
        pygame.draw.circle(
            screen,
            WHEEL,
            (center_x, y + 35),
            18
        )

        pygame.draw.circle(
            screen,
            WHEEL,
            (center_x, y + 140),
            18
        )

        # Inner wheels
        pygame.draw.circle(
            screen,
            GRAY,
            (center_x, y + 35),
            10
        )

        pygame.draw.circle(
            screen,
            GRAY,
            (center_x, y + 140),
            10
        )

        # Main body
        pygame.draw.polygon(
            screen,
            color,
            [
                (center_x - 15, y + 50),
                (center_x + 15, y + 50),
                (center_x + 25, y + 115),
                (center_x - 25, y + 115)
            ]
        )

        # Fuel tank
        pygame.draw.ellipse(
            screen,
            color,
            (
                center_x - 30,
                y + 65,
                60,
                55
            )
        )

        # Seat
        pygame.draw.rect(
            screen,
            DARK,
            (
                center_x - 20,
                y + 110,
                40,
                12
            ),
            border_radius=5
        )

        # Handlebar
        pygame.draw.line(
            screen,
            GRAY,
            (center_x - 20, y + 48),
            (center_x + 20, y + 48),
            5
        )

        # Headlight
        pygame.draw.circle(
            screen,
            LIGHT,
            (center_x, y + 42),
            7
        )


# =========================================================
# GLOW HELPER
# =========================================================

def draw_glow(rect, color, amount, radius=12):
    """Soft neon halo drawn with solid colours (no alpha surfaces)."""
    if amount <= 0.03:
        return

    for grow, strength in ((10, 0.10), (6, 0.18), (3, 0.32)):
        pygame.draw.rect(
            screen,
            lerp_color((10, 13, 22), color, strength * clamp(amount)),
            rect.inflate(grow * 2, grow * 2),
            border_radius=radius + grow,
        )


def draw_coin(center, r=11):
    pygame.draw.circle(screen, (150, 105, 20), center, r)
    pygame.draw.circle(screen, YELLOW, center, r - 1)
    pygame.draw.circle(screen, (220, 160, 30), center, max(2, r - 4), 2)
    pygame.draw.circle(
        screen,
        (255, 240, 170),
        (center[0] - r // 3, center[1] - r // 3),
        max(1, r // 5),
    )


def draw_check(center, color, size=7):
    x, y = center
    pygame.draw.lines(
        screen,
        color,
        False,
        [(x - size, y), (x - size // 3, y + size * 2 // 3), (x + size, y - size // 2)],
        3,
    )


# =========================================================
# STAT BAR
# =========================================================

def draw_stat(name, value, x, y, width=220, color=BLUE, max_value=100):
    """
    Animated-looking stat bar. `value` may be a float (the garage passes
    a smoothly changing value so the bar grows/shrinks).
    Old calls draw_stat(name, value, x, y) still work.
    """

    # Label + value
    label = get_text(name, label_font, TEXT_IDLE, 2)
    screen.blit(label, (x, y))

    number = small_font.render(str(int(round(value))), True, WHITE)
    screen.blit(number, number.get_rect(topright=(x + width, y - 2)))

    bar_y = y + 28
    bar_h = 12

    # Track
    pygame.draw.rect(
        screen,
        (30, 36, 50),
        (x, bar_y, width, bar_h),
        border_radius=6,
    )

    fill_w = int(width * clamp(value / max_value))

    if fill_w > 0:

        # Glow under the fill
        pygame.draw.rect(
            screen,
            lerp_color(PANEL_DARK, color, 0.16),
            (x - 2, bar_y - 3, fill_w + 4, bar_h + 6),
            border_radius=8,
        )

        # Fill
        pygame.draw.rect(
            screen,
            color,
            (x, bar_y, fill_w, bar_h),
            border_radius=6,
        )

        # Highlight
        if fill_w > 8:
            pygame.draw.rect(
                screen,
                lerp_color(color, WHITE, 0.55),
                (x + 4, bar_y + 2, fill_w - 8, 2),
                border_radius=1,
            )

            # Bright end cap
            pygame.draw.circle(
                screen,
                lerp_color(color, WHITE, 0.75),
                (x + fill_w - 5, bar_y + bar_h // 2),
                3,
            )

    # Segment ticks
    for k in range(1, 10):
        tx = x + int(width * k / 10)
        pygame.draw.line(
            screen, (12, 15, 24), (tx, bar_y), (tx, bar_y + bar_h - 1), 1
        )


# =========================================================
# BUTTON
# =========================================================

def draw_button(
    text,
    rect,
    mouse_pos,
    hover=None,
    x_offset=0,
    accent=BLUE,
    primary=False,
    icon=None,
):
    """
    Draws one garage button.

    Old calls draw_button(text, rect, mouse_pos) still work. The garage
    loop passes a smoothed `hover` value (0..1).

    accent  - highlight colour
    primary - filled, accent-tinted style (BUY / SELECT)
    icon    - None, "back", "check" or "coin"
    """

    if hover is None:
        hover = 1.0 if rect.collidepoint(mouse_pos) else 0.0

    h = clamp(hover)
    r = rect.move(int(x_offset), -int(2 * h))

    draw_glow(r, accent, h + (0.3 if primary else 0.0))

    if primary:
        fill_idle = lerp_color(BUTTON_FILL, accent, 0.18)
        fill_hover = lerp_color(BUTTON_FILL, accent, 0.42)
        border_idle = lerp_color(BUTTON_BORDER, accent, 0.6)
    else:
        fill_idle = BUTTON_FILL
        fill_hover = BUTTON_FILL_HOVER
        border_idle = BUTTON_BORDER

    pygame.draw.rect(
        screen, lerp_color(fill_idle, fill_hover, h), r, border_radius=12
    )
    pygame.draw.rect(
        screen,
        lerp_color(border_idle, accent, h),
        r,
        2,
        border_radius=12,
    )

    # Label (cross-fade idle -> bright)
    idle_color = WHITE if primary else TEXT_IDLE
    idle = get_text(text, button_font, idle_color, 3)
    label_rect = idle.get_rect(center=r.center)

    if icon == "back":
        label_rect.centerx += 12
    elif icon in ("check", "coin"):
        label_rect.centerx += 14

    screen.blit(idle, label_rect)

    if not primary and h > 0.02:
        bright = get_text(text, button_font, WHITE, 3)
        bright.set_alpha(int(255 * h))
        screen.blit(bright, label_rect)

    # Icons
    icon_color = lerp_color(TEXT_IDLE, accent, h) if not primary else WHITE

    if icon == "back":
        cx = r.x + 28 - int(h * 4)
        cy = r.centery
        pygame.draw.lines(
            screen,
            icon_color,
            False,
            [(cx + 5, cy - 8), (cx - 3, cy), (cx + 5, cy + 8)],
            3,
        )

    elif icon == "check":
        draw_check((label_rect.x - 18, r.centery), WHITE)

    elif icon == "coin":
        draw_coin((label_rect.x - 18, r.centery), 10)


def draw_nav_arrow(rect, direction, hover):
    """Previous / next vehicle button. direction: -1 left, +1 right."""

    h = clamp(hover)
    r = rect.move(0, -int(2 * h))

    draw_glow(r, BLUE, h, radius=18)

    pygame.draw.rect(
        screen,
        lerp_color(BUTTON_FILL, BUTTON_FILL_HOVER, h),
        r,
        border_radius=18,
    )
    pygame.draw.rect(
        screen,
        lerp_color(BUTTON_BORDER, BLUE, h),
        r,
        2,
        border_radius=18,
    )

    cx = r.centerx + int(direction * 4 * h)
    cy = r.centery
    s = -direction  # chevron tip points in `direction`

    pygame.draw.lines(
        screen,
        lerp_color((120, 140, 170), BLUE, h),
        False,
        [
            (cx + 7 * s, cy - 15),
            (cx - 7 * s, cy),
            (cx + 7 * s, cy + 15),
        ],
        5,
    )


# =========================================================
# SMALL UI PIECES
# =========================================================

def get_chip(text, color):
    key = ("chip", text, color)

    if key not in _text_cache:
        label = render_spaced(text, label_font, color, 3)
        w, h = label.get_width() + 26, 26
        chip = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(
            chip,
            (*lerp_color(PANEL_DARK, color, 0.14), 235),
            (0, 0, w, h),
            border_radius=13,
        )
        pygame.draw.rect(
            chip, (*color, 255), (0, 0, w, h), 2, border_radius=13
        )
        chip.blit(label, label.get_rect(center=(w // 2, h // 2)))
        _text_cache[key] = chip

    return _text_cache[key]


def get_toast(text, color):
    key = ("toast", text, color)

    if key not in _text_cache:
        label = render_spaced(text, small_font, WHITE, 3)
        w, h = label.get_width() + 46, 36
        pill = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(
            pill,
            (*lerp_color((10, 13, 22), color, 0.28), 240),
            (0, 0, w, h),
            border_radius=18,
        )
        pygame.draw.rect(
            pill, (*color, 255), (0, 0, w, h), 2, border_radius=18
        )
        pill.blit(label, label.get_rect(center=(w // 2, h // 2)))
        _text_cache[key] = pill

    return _text_cache[key]


def draw_price_row(center_x, y, price, coins):
    """Price + coin icon (+ how many more coins are needed)."""

    need = max(0, price - coins)

    label = get_text("PRICE", label_font, GRAY, 3)
    number = get_text(str(price), medium_font, YELLOW, 1)
    extra = (
        get_text(f"NEED {need} MORE", label_font, LOCK_RED, 2)
        if need
        else None
    )

    total = label.get_width() + 12 + 22 + 8 + number.get_width()
    if extra:
        total += 22 + extra.get_width()

    x = center_x - total // 2

    screen.blit(label, label.get_rect(midleft=(x, y)))
    x += label.get_width() + 12

    draw_coin((x + 11, y), 10)
    x += 22 + 8

    screen.blit(number, number.get_rect(midleft=(x, y)))
    x += number.get_width()

    if extra:
        x += 22
        screen.blit(extra, extra.get_rect(midleft=(x, y)))


def draw_owned_row(center_x, y):
    label = get_text("OWNED", label_font, GREEN, 3)
    total = 22 + 10 + label.get_width()
    x = center_x - total // 2

    draw_check((x + 8, y), GREEN, 6)
    screen.blit(label, label.get_rect(midleft=(x + 32, y)))


# =========================================================
# VEHICLE SELECTION LOGIC (unchanged behaviour)
# =========================================================

def previous_vehicle():
    vehicle_data.player_data["selected_vehicle"] -= 1

    if vehicle_data.player_data["selected_vehicle"] < 0:
        vehicle_data.player_data["selected_vehicle"] = len(vehicles) - 1


def next_vehicle():
    vehicle_data.player_data["selected_vehicle"] += 1

    if vehicle_data.player_data["selected_vehicle"] >= len(vehicles):
        vehicle_data.player_data["selected_vehicle"] = 0


def buy_or_select():
    """
    BUY / SELECT button logic, exactly as before.
    Returns "unlocked", "no_coins" or "selected" so the screen can
    show visual feedback.
    """

    index = vehicle_data.player_data["selected_vehicle"]

    # Vehicle is locked
    if not vehicle_data.player_data["unlocked"][index]:

        price = vehicles[index]["price"]

        # Enough coins
        if vehicle_data.player_data["coins"] >= price:

            vehicle_data.unlock_vehicle(index)

            print(
                vehicles[index]["name"],
                "unlocked!"
            )

            return "unlocked"

        else:

            print(
                "Not enough coins!"
            )

            return "no_coins"

    # Vehicle already unlocked
    else:

        vehicle_data.select_vehicle(index)

        print(
            vehicles[index]["name"],
            "selected"
        )

        return "selected"


# =========================================================
# SHOWROOM CAR
# =========================================================

def draw_showroom_car(index, x_off, y_off, alpha):
    """Draws one vehicle (plus shadow, and a padlock if it is locked)."""

    a = int(255 * clamp(alpha))
    if a <= 0:
        return

    normal, locked_img, shadow = showroom_images[vehicles[index]["image"]]
    unlocked = vehicle_data.player_data["unlocked"][index]

    image = normal if unlocked else locked_img

    cx = RING_CENTER[0] + x_off
    cy = RING_CENTER[1] + y_off

    shadow.set_alpha(a)
    image.set_alpha(a)

    screen.blit(shadow, shadow.get_rect(center=(cx + 10, cy + 14)))
    screen.blit(image, image.get_rect(center=(cx, cy)))

    if not unlocked:
        lock_icon.set_alpha(a)
        screen.blit(lock_icon, lock_icon.get_rect(center=(cx, cy)))


# =========================================================
# GARAGE
# =========================================================

def run_garage():

    pygame.display.set_caption("Highway Racer - Garage")

    hover = {"back": 0.0, "prev": 0.0, "next": 0.0, "select": 0.0}

    # ---- state ------------------------------------------------
    start_index = vehicle_data.player_data["selected_vehicle"]

    shown_index = start_index
    outgoing_index = None
    trans_t = 1.0
    nav_dir = 1

    # Which vehicle is actually equipped (for the SELECTED badge)
    if vehicle_data.player_data["unlocked"][start_index]:
        equipped_index = start_index
    else:
        equipped_index = None

    coins_shown = float(vehicle_data.player_data["coins"])

    stats_shown = [
        0.0, 0.0, 0.0
    ]

    accent = BLUE

    toast = None        # [text, color, age]
    shake_t = 0.0
    burst_t = None

    time_alive = 0.0
    hand_cursor = False
    dt = 1 / 60

    sparks = [
        [
            random.uniform(STAGE.x + 30, STAGE.right - 30),
            random.uniform(STAGE.y + 20, STAGE.bottom - 20),
            random.uniform(14, 44),
            random.uniform(0, 6.28),
        ]
        for _ in range(18)
    ]

    def go_previous():
        nonlocal nav_dir
        nav_dir = -1
        previous_vehicle()

    def go_next():
        nonlocal nav_dir
        nav_dir = 1
        next_vehicle()

    def go_buy_or_select():
        nonlocal toast, shake_t, burst_t, equipped_index

        result = buy_or_select()

        if result == "unlocked":
            toast = ["VEHICLE UNLOCKED", GREEN, 0.0]
            burst_t = 0.0

        elif result == "no_coins":
            toast = ["NOT ENOUGH COINS", LOCK_RED, 0.0]
            shake_t = 0.4

        else:
            equipped_index = vehicle_data.player_data["selected_vehicle"]
            toast = ["VEHICLE SELECTED", BLUE, 0.0]

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

                    # Extra keyboard shortcuts
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        go_previous()

                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        go_next()

                    elif event.key in (
                        pygame.K_RETURN,
                        pygame.K_KP_ENTER,
                        pygame.K_SPACE,
                    ):
                        go_buy_or_select()

                if event.type == pygame.MOUSEBUTTONDOWN:

                    if event.button == 1:

                        # BACK
                        if BACK_BUTTON.collidepoint(event.pos):

                            return "menu"

                        # PREVIOUS
                        if PREVIOUS_BUTTON.collidepoint(event.pos):

                            go_previous()

                        # NEXT
                        if NEXT_BUTTON.collidepoint(event.pos):

                            go_next()

                        # BUY / SELECT
                        if SELECT_BUTTON.collidepoint(event.pos):

                            go_buy_or_select()

            # =============================================
            # CURRENT VEHICLE
            # =============================================

            index = vehicle_data.player_data["selected_vehicle"]

            car = vehicles[index]

            is_unlocked = vehicle_data.player_data[
                "unlocked"
            ][index]

            coins = vehicle_data.player_data["coins"]

            # =============================================
            # UPDATE ANIMATION STATE
            # =============================================

            time_alive += dt

            if index != shown_index:
                outgoing_index = shown_index
                shown_index = index
                trans_t = 0.0
            else:
                trans_t = min(1.0, trans_t + dt / 0.35)
                if trans_t >= 1.0:
                    outgoing_index = None

            e_trans = ease_out(trans_t)
            e_enter = ease_out(time_alive / 0.8)
            e_ui = ease_out((time_alive - 0.1) / 0.5)
            ui_y = int((1 - e_ui) * 50)

            pulse = 0.5 + 0.5 * math.sin(time_alive * 2.0)

            # Hover smoothing
            targets = {
                "back": BACK_BUTTON,
                "prev": PREVIOUS_BUTTON,
                "next": NEXT_BUTTON,
                "select": SELECT_BUTTON,
            }

            any_hover = False
            for key, rect in targets.items():
                target = 1.0 if rect.collidepoint(mouse_pos) else 0.0
                any_hover = any_hover or target == 1.0
                hover[key] += (target - hover[key]) * min(1.0, dt * 14)

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

            # Stats bars ease towards the current vehicle's values
            stat_targets = (
                car["speed"], car["handling"], car["acceleration"]
            )
            for i in range(3):
                stats_shown[i] += (
                    (stat_targets[i] - stats_shown[i])
                    * min(1.0, dt * 7)
                )

            # Coin counter eases towards the real value
            coins_shown += (coins - coins_shown) * min(1.0, dt * 7)
            if abs(coins - coins_shown) < 0.5:
                coins_shown = float(coins)

            # Ring colour: blue when owned, red when locked
            accent_target = BLUE if is_unlocked else LOCK_RED
            accent = lerp_color(accent, accent_target, min(1.0, dt * 8))

            if shake_t > 0:
                shake_t = max(0.0, shake_t - dt)

            if toast is not None:
                toast[2] += dt
                if toast[2] > 1.7:
                    toast = None

            if burst_t is not None:
                burst_t += dt
                if burst_t > 0.8:
                    burst_t = None

            for spark in sparks:
                spark[1] -= spark[2] * dt
                if spark[1] < STAGE.y + 12:
                    spark[1] = STAGE.bottom - 14
                    spark[0] = random.uniform(
                        STAGE.x + 30, STAGE.right - 30
                    )

            # =============================================
            # BACKGROUND
            # =============================================

            screen.blit(background_surface, (0, 0))

            # =============================================
            # TITLE
            # =============================================

            garage_glow.set_alpha(int(140 + 70 * pulse))
            title_pos = garage_text.get_rect(topleft=(50, 24))

            screen.blit(
                garage_glow,
                (title_pos.x - TITLE_PAD, title_pos.y - TITLE_PAD),
            )
            screen.blit(garage_text, title_pos)

            pygame.draw.rect(
                screen, BLUE, (50, 80, 46, 3), border_radius=2
            )
            screen.blit(
                get_text("VEHICLE SHOWROOM", label_font, GRAY, 4),
                (106, 74),
            )

            # =============================================
            # COINS
            # =============================================

            coin_flash = clamp(abs(coins - coins_shown) / 40.0)

            pygame.draw.rect(
                screen, PANEL_DARK, COIN_PILL, border_radius=16
            )
            pygame.draw.rect(
                screen,
                lerp_color((80, 70, 35), YELLOW, 0.35 + 0.65 * coin_flash),
                COIN_PILL,
                2,
                border_radius=16,
            )

            draw_coin((COIN_PILL.x + 30, COIN_PILL.centery), 14)

            screen.blit(
                get_text("COINS", label_font, GRAY, 3),
                (COIN_PILL.x + 58, COIN_PILL.y + 8),
            )

            coin_text = coin_font.render(
                f"{int(round(coins_shown))}",
                True,
                lerp_color(YELLOW, WHITE, coin_flash),
            )
            screen.blit(coin_text, (COIN_PILL.x + 58, COIN_PILL.y + 24))

            # =============================================
            # SHOWROOM STAGE
            # =============================================

            screen.blit(stage_surface, STAGE.topleft)

            # Floating sparks
            screen.set_clip(STAGE.inflate(-6, -6))

            for sx, sy, _speed, phase in sparks:
                glow_amt = 0.5 + 0.5 * math.sin(time_alive * 1.5 + phase)
                pygame.draw.rect(
                    screen,
                    lerp_color((28, 58, 92), (90, 170, 240), glow_amt),
                    (int(sx), int(sy), 2, 2),
                )

            screen.set_clip(None)

            # Glow behind the car
            glow_strength = (150 + 70 * pulse) * (1.0 if is_unlocked else 0.5)

            if outgoing_index is not None:
                out_glow = vehicle_glows[outgoing_index]
                out_glow.set_alpha(int(glow_strength * (1 - e_trans)))
                screen.blit(
                    out_glow, out_glow.get_rect(center=RING_CENTER)
                )

            in_glow = vehicle_glows[shown_index]
            in_glow.set_alpha(int(glow_strength * e_trans * e_enter))
            screen.blit(in_glow, in_glow.get_rect(center=RING_CENTER))

            # Rotating turntable arcs
            ring_rect = pygame.Rect(0, 0, (RING_R + 6) * 2, (RING_R + 6) * 2)
            ring_rect.center = RING_CENTER
            spin = time_alive * 0.7

            for k in range(4):
                start = spin + k * (math.pi / 2)
                pygame.draw.arc(
                    screen, accent, ring_rect, start, start + 0.9, 4
                )

            inner_rect = ring_rect.inflate(-70, -70)
            inner_color = lerp_color(accent, (14, 18, 28), 0.55)

            for k in range(3):
                start = -spin * 1.4 + k * (2 * math.pi / 3)
                pygame.draw.arc(
                    screen, inner_color, inner_rect, start, start + 0.55, 2
                )

            # Unlock burst
            if burst_t is not None:
                b = ease_out(burst_t / 0.8)
                pygame.draw.circle(
                    screen,
                    lerp_color(WHITE, (14, 22, 34), b),
                    RING_CENTER,
                    int(40 + 230 * b),
                    max(1, int(8 * (1 - b))),
                )

            # Cars (slide + fade between vehicles)
            bob = math.sin(time_alive * 1.5) * 4

            if outgoing_index is not None:
                draw_showroom_car(
                    outgoing_index,
                    -nav_dir * 140 * e_trans,
                    bob,
                    1 - e_trans,
                )

            draw_showroom_car(
                shown_index,
                nav_dir * 140 * (1 - e_trans),
                bob + (1 - e_enter) * 60,
                e_trans * e_enter,
            )

            # Status + type chips
            if not is_unlocked:
                status_chip = get_chip("LOCKED", LOCK_RED)
            elif shown_index == equipped_index:
                status_chip = get_chip("SELECTED", GREEN)
            else:
                status_chip = get_chip("UNLOCKED", BLUE)

            screen.blit(
                get_chip(str(car.get("type", "")).upper(), GRAY),
                (STAGE.x + 26, STAGE.y + 24),
            )
            screen.blit(
                status_chip,
                status_chip.get_rect(
                    topright=(STAGE.right - 26, STAGE.y + 24)
                ),
            )

            # Vehicle name
            car_name = get_text(car["name"], name_font, WHITE, 5)
            car_name.set_alpha(int(255 * e_trans))
            screen.blit(
                car_name,
                car_name.get_rect(center=(STAGE.centerx, STAGE.bottom - 66)),
            )

            # Price / owned row
            if not is_unlocked:
                draw_price_row(
                    STAGE.centerx, STAGE.bottom - 30, car["price"], coins
                )
            else:
                draw_owned_row(STAGE.centerx, STAGE.bottom - 30)

            # Toast message
            if toast is not None:
                age = toast[2]
                pill = get_toast(toast[0], toast[1])
                fade = clamp((1.7 - age) / 0.4)
                pill.set_alpha(int(255 * min(1.0, age / 0.12) * fade))
                rise = int((1 - ease_out(age / 0.2)) * 10)
                screen.blit(
                    pill,
                    pill.get_rect(
                        center=(STAGE.centerx, STAGE.y + 38 + rise)
                    ),
                )

            # =============================================
            # NAVIGATION
            # =============================================

            draw_nav_arrow(PREVIOUS_BUTTON, -1, hover["prev"])
            draw_nav_arrow(NEXT_BUTTON, 1, hover["next"])

            # =============================================
            # STATS PANEL
            # =============================================

            panel = STATS_PANEL.move(0, ui_y)

            pygame.draw.rect(screen, PANEL_DARK, panel, border_radius=14)
            pygame.draw.rect(
                screen, PANEL_BORDER, panel, 2, border_radius=14
            )

            stat_defs = (
                ("SPEED", BLUE),
                ("HANDLING", TEAL),
                ("ACCELERATION", PURPLE),
            )

            for i, (stat_name, stat_color) in enumerate(stat_defs):
                draw_stat(
                    stat_name,
                    stats_shown[i],
                    panel.x + 18 + i * 192,
                    panel.y + 16,
                    180,
                    stat_color,
                    STAT_MAX,
                )

            # =============================================
            # BUY / SELECT BUTTON
            # =============================================

            shake_x = 0
            if shake_t > 0:
                shake_x = int(
                    math.sin(shake_t * 60) * 9 * (shake_t / 0.4)
                )

            if is_unlocked:

                if shown_index == equipped_index:
                    select_label = "SELECTED"
                    select_accent = GREEN
                    select_icon = "check"
                else:
                    select_label = "SELECT VEHICLE"
                    select_accent = BLUE
                    select_icon = None

            else:

                select_label = f"BUY - {car['price']}"
                select_icon = "coin"
                select_accent = (
                    YELLOW if coins >= car["price"] else LOCK_RED
                )

            draw_button(
                select_label,
                SELECT_BUTTON.move(0, ui_y),
                mouse_pos,
                hover["select"],
                shake_x,
                select_accent,
                True,
                select_icon,
            )

            # =============================================
            # BACK
            # =============================================

            draw_button(
                "BACK",
                BACK_BUTTON.move(0, ui_y),
                mouse_pos,
                hover["back"],
                0,
                BLUE,
                False,
                "back",
            )

            # =============================================
            # VEHICLE COUNTER
            # =============================================

            count = len(vehicles)
            dots_y = 642 + ui_y
            dots_x0 = 735 - (count - 1) * 11

            for i in range(count):
                owned = vehicle_data.player_data["unlocked"][i]
                dx = dots_x0 + i * 22

                if i == index:
                    pygame.draw.rect(
                        screen,
                        accent,
                        (dx - 8, dots_y - 4, 16, 8),
                        border_radius=4,
                    )
                else:
                    pygame.draw.circle(
                        screen,
                        (70, 110, 150) if owned else (58, 60, 72),
                        (dx, dots_y),
                        4,
                    )

            counter = get_text(
                f"{index + 1} / {count}", small_font, GRAY, 2
            )
            screen.blit(
                counter,
                counter.get_rect(midright=(850, dots_y)),
            )

            # =============================================
            # HINT
            # =============================================

            hint = get_text(
                "LEFT / RIGHT  BROWSE      ENTER  BUY / SELECT      ESC  BACK",
                label_font,
                (105, 112, 128),
                2,
            )
            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 686)))

            # =============================================
            # UPDATE
            # =============================================

            pygame.display.update()

            dt = min(clock.tick(60) / 1000, 0.05)

    finally:

        # Never leave the hand cursor stuck when leaving the garage
        try:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        except pygame.error:
            pass

        if RESTORE_EQUIPPED_ON_EXIT and equipped_index is not None:
            vehicle_data.player_data["selected_vehicle"] = equipped_index

    return "menu"
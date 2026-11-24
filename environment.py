import math
import os
import random

import pygame
import vehicle_data

pygame.font.init()


# =========================================================
# SCREEN
# =========================================================

WIDTH = 900
HEIGHT = 700

screen = pygame.display.get_surface()

if screen is None:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

clock = pygame.time.Clock()


# =========================================================
# COLORS
# =========================================================

BACKGROUND = (8, 10, 16)
PANEL = (15, 18, 28)

BLUE = (80, 180, 255)
WHITE = (240, 240, 245)
GRAY = (150, 155, 165)
GREEN = (50, 220, 140)

# Shared with the redesigned main menu and garage
BUTTON_FILL = (15, 19, 30)
BUTTON_FILL_HOVER = (20, 52, 82)
BUTTON_BORDER = (48, 55, 72)
TEXT_IDLE = (185, 191, 204)
DEEP_BLUE = (30, 110, 200)
PANEL_DARK = (9, 12, 20)
PANEL_BORDER = (45, 62, 92)

CARD_BODY = (11, 14, 23)

FOREST_ACCENT = (60, 220, 130)
CITY_ACCENT = BLUE


# =========================================================
# FONTS
# =========================================================

title_font = pygame.font.Font(None, 70)
button_font = pygame.font.Font(None, 34)
small_font = pygame.font.Font(None, 26)
label_font = pygame.font.Font(None, 22)
name_font = pygame.font.Font(None, 48)


# =========================================================
# ENVIRONMENTS
# =========================================================
# "id" is exactly what run_environment() returns and what main.py
# stores in vehicle_data.selected_environment.

ENVIRONMENTS = [

    {
        "id": "forest",
        "name": "FOREST",
        "desc": "Lush greenery and sun-dappled roads",
        "tags": ("DAYLIGHT", "NATURE"),
        "accent": FOREST_ACCENT,
    },

    {
        "id": "city_night",
        "name": "CITY NIGHT",
        "desc": "Neon skylines and glowing streets",
        "tags": ("NIGHT", "NEON"),
        "accent": CITY_ACCENT,
    },
]

# Text on the START button. With the current main.py a chosen
# environment is stored and you return to the menu, see notes.
START_LABEL = "START RACE"


# =========================================================
# LAYOUT
# =========================================================

CARD_W = 380
CARD_H = 440
CARD_Y = 112
CARD_X = (50, 470)

# Preview window inside every card
PREVIEW_PAD = 14
PW = CARD_W - PREVIEW_PAD * 2       # 352
PH = 270
TH = 540                            # height of the scrolling scenery tile

BACK_BUTTON = pygame.Rect(50, 590, 280, 52)
START_BUTTON = pygame.Rect(550, 590, 300, 52)

ROAD_X0 = 116
ROAD_X1 = 236


# =========================================================
# SMALL HELPERS (same family as menu.py / garage.py)
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
# PROCEDURAL ENVIRONMENT ART
# =========================================================
# No image files are needed: both previews are painted once at load
# time into seamless vertical tiles that scroll like the road does in
# the race. (Optional real artwork is supported, see load_still().)

def blit_wrap(tile, surf, x, y):
    for dy in (-TH, 0, TH):
        tile.blit(surf, (x, y + dy))


def wrap_circle(tile, color, cx, cy, r, alpha=255):
    if alpha >= 255:
        for dy in (-TH, 0, TH):
            pygame.draw.circle(tile, color, (cx, cy + dy), r)
    else:
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, alpha), (r, r), r)
        blit_wrap(tile, s, cx - r, cy - r)


def vignette_surface(width, height, strength, steps=42):
    v = pygame.Surface((width, height), pygame.SRCALPHA)
    for i in range(steps):
        alpha = int(strength * (1 - i / steps) ** 2)
        pygame.draw.rect(
            v,
            (0, 0, 0, alpha),
            (i, i, width - i * 2, height - i * 2),
            1,
        )
    return v


def top_gradient(width, height, color, max_alpha):
    g = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        a = int(max_alpha * (1 - y / height) ** 2)
        pygame.draw.line(g, (*color, a), (0, y), (width, y))
    return g


# ---------------------------------------------------------
# FOREST
# ---------------------------------------------------------

def build_forest_tile():
    rng = random.Random(11)
    tile = pygame.Surface((PW, TH))
    tile.fill((17, 50, 29))

    # Grass variation
    for _ in range(90):
        wrap_circle(
            tile,
            rng.choice([(30, 84, 44), (12, 38, 22), (40, 100, 50)]),
            rng.randint(0, PW),
            rng.randint(0, TH),
            rng.randint(18, 55),
            26,
        )

    # Dirt shoulders + asphalt
    pygame.draw.rect(tile, (70, 56, 38), (ROAD_X0 - 9, 0, 9, TH))
    pygame.draw.rect(tile, (70, 56, 38), (ROAD_X1, 0, 9, TH))
    pygame.draw.rect(
        tile, (36, 38, 44), (ROAD_X0, 0, ROAD_X1 - ROAD_X0, TH)
    )

    for _ in range(260):
        shade = rng.randint(40, 52)
        pygame.draw.rect(
            tile,
            (shade, shade, shade + 4),
            (rng.randint(ROAD_X0 + 2, ROAD_X1 - 4), rng.randint(0, TH - 2), 2, 2),
        )

    # Edge lines + lane dashes
    pygame.draw.rect(tile, (205, 208, 212), (ROAD_X0 + 4, 0, 3, TH))
    pygame.draw.rect(tile, (205, 208, 212), (ROAD_X1 - 7, 0, 3, TH))

    for lane_x in (156, 196):
        for y in range(0, TH, 60):
            pygame.draw.rect(
                tile, (225, 225, 218), (lane_x - 2, y + 8, 4, 30)
            )

    # Bushes along the road
    for _ in range(26):
        x = rng.choice((rng.randint(94, 106), rng.randint(246, 258)))
        y = rng.randint(0, TH)
        r = rng.randint(5, 9)
        wrap_circle(tile, (16, 62, 30), x, y, r + 1)
        wrap_circle(tile, (36, 98, 46), x - 1, y - 1, r)

    # Trees
    greens = [(28, 92, 44), (34, 108, 50), (24, 78, 40), (40, 120, 56)]
    trees = []

    for _ in range(46):
        if rng.random() < 0.5:
            x = rng.randint(14, 88)
        else:
            x = rng.randint(PW - 88, PW - 14)
        trees.append((x, rng.randint(0, TH), rng.randint(15, 27)))

    for x, y, r in trees:
        wrap_circle(tile, (6, 20, 12), x + 7, y + 9, r, 100)

    for x, y, r in sorted(trees, key=lambda t: t[1]):
        base = rng.choice(greens)
        wrap_circle(tile, lerp_color(base, (0, 0, 0), 0.35), x, y, r)
        wrap_circle(tile, base, x - 1, y - 1, r - 3)

        for _ in range(5):
            wrap_circle(
                tile,
                lerp_color(base, (120, 200, 90), rng.uniform(0.1, 0.4)),
                x + rng.randint(-r // 2, r // 2),
                y + rng.randint(-r // 2, r // 2),
                rng.randint(3, 6),
            )

        wrap_circle(tile, (150, 220, 110), x - r // 3, y - r // 3, max(3, r // 2), 60)

    # Sun dapples
    for _ in range(30):
        wrap_circle(
            tile,
            (200, 230, 120),
            rng.randint(0, PW),
            rng.randint(0, TH),
            rng.randint(14, 34),
            22,
        )

    return tile.convert()


def build_forest_overlay():
    overlay = pygame.Surface((PW, PH), pygame.SRCALPHA)

    shafts = pygame.Surface((PW, PH), pygame.SRCALPHA)
    for x in (30, 110, 190, 270, 340):
        pygame.draw.polygon(
            shafts,
            (255, 238, 170, 34),
            [(x, 0), (x + 34, 0), (x - 70, PH), (x - 104, PH)],
        )
    overlay.blit(blur(shafts, 4), (0, 0))

    overlay.blit(top_gradient(PW, 120, (180, 220, 200), 85), (0, 0))
    overlay.blit(vignette_surface(PW, PH, 130), (0, 0))

    return overlay.convert_alpha()


# ---------------------------------------------------------
# CITY NIGHT
# ---------------------------------------------------------

NEON_COLORS = [
    (60, 220, 255),
    (255, 70, 200),
    (150, 100, 255),
    (255, 170, 60),
]


def build_city_tile():
    rng = random.Random(23)
    tile = pygame.Surface((PW, TH))
    tile.fill((8, 10, 18))

    # Sidewalks + asphalt
    pygame.draw.rect(tile, (30, 34, 50), (ROAD_X0 - 16, 0, 16, TH))
    pygame.draw.rect(tile, (30, 34, 50), (ROAD_X1, 0, 16, TH))
    pygame.draw.rect(
        tile, (20, 22, 33), (ROAD_X0, 0, ROAD_X1 - ROAD_X0, TH)
    )

    for _ in range(220):
        shade = rng.randint(24, 36)
        pygame.draw.rect(
            tile,
            (shade, shade, shade + 8),
            (rng.randint(ROAD_X0 + 2, ROAD_X1 - 4), rng.randint(0, TH - 2), 2, 2),
        )

    # Buildings (top-down rooftops) on both sides
    glows = {c: radial_glow(14, c, 110) for c in NEON_COLORS}

    for side in (0, 1):
        heights = []
        total = 0
        while total < TH - 70:
            h = rng.randint(62, 120)
            heights.append(h)
            total += h + 14

        # Scale so buildings + alleys fill the tile exactly (seamless)
        available = TH - 14 * len(heights)
        scale = available / sum(heights)
        heights = [int(h * scale) for h in heights]
        heights[-1] += available - sum(heights)

        y = 0
        for h in heights:
            w = rng.randint(54, 86)
            x = (98 - w) if side == 0 else (PW - 98)
            rect = pygame.Rect(x, y, w, h)

            roof = (
                rng.randint(22, 30),
                rng.randint(26, 34),
                rng.randint(42, 58),
            )

            # Shadow + roof + setback tier
            pygame.draw.rect(
                tile, (4, 5, 10), rect.move(5, 6), border_radius=3
            )
            pygame.draw.rect(tile, roof, rect, border_radius=3)
            pygame.draw.rect(
                tile,
                (roof[0] + 8, roof[1] + 8, roof[2] + 10),
                rect.inflate(-14, -14),
                border_radius=2,
            )

            # Rooftop units
            for _ in range(rng.randint(2, 4)):
                ux = rng.randint(rect.x + 10, max(rect.x + 11, rect.right - 22))
                uy = rng.randint(rect.y + 10, max(rect.y + 11, rect.bottom - 20))
                pygame.draw.rect(
                    tile,
                    (roof[0] + 22, roof[1] + 22, roof[2] + 26),
                    (ux, uy, rng.randint(6, 12), rng.randint(6, 10)),
                    border_radius=2,
                )

            # Neon strip on the edge facing the road
            neon = rng.choice(NEON_COLORS)
            edge_x = rect.right - 3 if side == 0 else rect.x
            halo = pygame.Surface((13, h - 8), pygame.SRCALPHA)
            halo.fill((*neon, 40))
            tile.blit(halo, (edge_x - 5, y + 4))
            pygame.draw.rect(tile, neon, (edge_x, y + 4, 3, h - 8))

            # Rooftop beacon
            beacon = rng.choice(NEON_COLORS + [(255, 60, 60)])
            bx = rng.randint(rect.x + 8, rect.right - 8)
            by = rng.randint(rect.y + 8, rect.bottom - 8)
            tile.blit(
                glows.get(beacon, glows[NEON_COLORS[1]]),
                (bx - 14, by - 14),
            )
            pygame.draw.circle(tile, beacon, (bx, by), 2)

            y += h + 14

    # Neon road edges with halo
    halo = pygame.Surface((PW, TH), pygame.SRCALPHA)
    for x, color in ((ROAD_X0 + 3, NEON_COLORS[0]), (ROAD_X1 - 4, NEON_COLORS[1])):
        pygame.draw.line(halo, (*color, 26), (x, 0), (x, TH), 15)
        pygame.draw.line(halo, (*color, 48), (x, 0), (x, TH), 8)
    tile.blit(halo, (0, 0))

    pygame.draw.rect(tile, NEON_COLORS[0], (ROAD_X0 + 2, 0, 3, TH))
    pygame.draw.rect(tile, NEON_COLORS[1], (ROAD_X1 - 5, 0, 3, TH))

    # Lane dashes
    for lane_x in (156, 196):
        for y in range(0, TH, 60):
            pygame.draw.rect(
                tile, (118, 126, 160), (lane_x - 2, y + 8, 4, 30)
            )

    # Street lamps casting warm light onto the road
    lamp_glow = radial_glow(52, (255, 196, 110), 100)
    for y in range(0, TH, 135):
        for lx, ly in ((ROAD_X0 - 8, y + 40), (ROAD_X1 + 8, y + 107)):
            blit_wrap(tile, lamp_glow, lx - 52, ly - 52)
            for dy in (-TH, 0, TH):
                pygame.draw.circle(tile, (255, 236, 180), (lx, ly + dy), 3)

    return tile.convert()


def build_city_overlay():
    overlay = pygame.Surface((PW, PH), pygame.SRCALPHA)
    overlay.blit(top_gradient(PW, 110, (110, 70, 200), 80), (0, 0))
    overlay.blit(vignette_surface(PW, PH, 170), (0, 0))
    return overlay.convert_alpha()


def build_headlight_cone():
    cone = pygame.Surface((150, 180), pygame.SRCALPHA)

    for i in range(7):
        layer = pygame.Surface((150, 180), pygame.SRCALPHA)
        half = 68 - i * 9
        pygame.draw.polygon(
            layer,
            (225, 235, 255, 14),
            [(75, 180), (75 - half, 0), (75 + half, 0)],
        )
        cone.blit(layer, (0, 0))

    return blur(cone, 3)


def load_still(env_id):
    """
    OPTIONAL: if assets/environments/<id>.png exists (e.g. forest.png,
    city_night.png) it replaces the painted scene with your artwork,
    cropped to fill the card. Returns None when the file is absent.
    """
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "assets",
        "environments",
        env_id + ".png",
    )

    if not os.path.exists(path):
        return None

    try:
        image = pygame.image.load(path).convert()
    except pygame.error:
        return None

    iw, ih = image.get_size()
    scale = max(PW / iw, PH / ih)
    scaled = pygame.transform.smoothscale(
        image, (int(iw * scale) + 1, int(ih * scale) + 1)
    )

    still = pygame.Surface((PW, PH))
    still.blit(
        scaled,
        scaled.get_rect(center=(PW // 2, PH // 2)),
    )
    return still.convert()


# ---------------------------------------------------------
# Build everything once
# ---------------------------------------------------------

def build_background():
    bg = pygame.Surface((WIDTH, HEIGHT))

    for y in range(HEIGHT):
        color = lerp_color((5, 7, 12), (12, 16, 28), y / HEIGHT)
        pygame.draw.line(bg, color, (0, y), (WIDTH, y))

    glow = radial_glow(380, DEEP_BLUE, 48)
    bg.blit(glow, glow.get_rect(center=(WIDTH // 2, 330)))

    glow = radial_glow(260, (30, 120, 170), 28)
    bg.blit(glow, glow.get_rect(center=(140, 60)))

    for i in range(14):
        x = -200 + i * 90
        pygame.draw.line(bg, (14, 20, 34), (x, HEIGHT), (x + 320, 0), 1)

    bg.blit(vignette_surface(WIDTH, HEIGHT, 170, 70), (0, 0))

    return bg.convert()


def build_corner_mask():
    mask = pygame.Surface((PW, PH), pygame.SRCALPHA)
    mask.fill((*CARD_BODY, 255))
    pygame.draw.rect(mask, (0, 0, 0, 0), (0, 0, PW, PH), border_radius=12)
    return mask.convert_alpha()


background_surface = build_background()
corner_mask = build_corner_mask()

dim_surface = pygame.Surface((PW, PH))
dim_surface.fill((0, 0, 0))

flash_surface = pygame.Surface((PW, PH))
flash_surface.fill((255, 255, 255))

headlight_cone = build_headlight_cone()
underglow = radial_glow(70, (60, 220, 255), 90)

# One preview per environment, same order as ENVIRONMENTS
previews = []

for _env in ENVIRONMENTS:

    if _env["id"] == "forest":
        _tile = build_forest_tile()
        _overlay = build_forest_overlay()
    else:
        _tile = build_city_tile()
        _overlay = build_city_overlay()

    previews.append({
        "tile": _tile,
        "overlay": _overlay,
        "still": load_still(_env["id"]),
        "glow": radial_glow(250, _env["accent"], 120),
    })

env_title, env_title_glow, TITLE_PAD = make_glow_text(
    "ENVIRONMENT", title_font, BLUE, BLUE, spacing=8
)


# =========================================================
# PLAYER CAR IN THE PREVIEW
# =========================================================

def load_preview_car():
    """Selected vehicle (same PNG as menu/garage) drawn on the road."""

    try:
        vehicle = vehicle_data.vehicles[
            vehicle_data.player_data["selected_vehicle"]
        ]
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            vehicle["image"],
        )
        image = pygame.image.load(path).convert_alpha()
    except Exception:
        return None

    iw, ih = image.get_size()
    scale = min(96 / ih, 64 / iw)
    car = pygame.transform.smoothscale(
        image, (max(1, int(iw * scale)), max(1, int(ih * scale)))
    )
    shadow = blur(
        pygame.mask.from_surface(car).to_surface(
            setcolor=(0, 0, 0, 170), unsetcolor=(0, 0, 0, 0)
        ),
        3,
    )
    return car, shadow


# =========================================================
# DRAW BUTTON
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
    Draws one button.

    Old calls draw_button(text, rect, mouse_pos) still work. The
    environment loop passes a smoothed `hover` value (0..1).

    accent  - highlight colour
    primary - filled, accent-tinted style (START RACE)
    icon    - None, "back" or "play"
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

    idle_color = WHITE if primary else TEXT_IDLE
    idle = get_text(text, button_font, idle_color, 3)
    label_rect = idle.get_rect(center=r.center)

    if icon in ("back", "play"):
        label_rect.centerx += 14

    screen.blit(idle, label_rect)

    if not primary and h > 0.02:
        bright = get_text(text, button_font, WHITE, 3)
        bright.set_alpha(int(255 * h))
        screen.blit(bright, label_rect)

    icon_color = WHITE if primary else lerp_color(TEXT_IDLE, accent, h)

    if icon == "back":
        cx = r.x + 30 - int(h * 4)
        cy = r.centery
        pygame.draw.lines(
            screen,
            icon_color,
            False,
            [(cx + 5, cy - 8), (cx - 3, cy), (cx + 5, cy + 8)],
            3,
        )

    elif icon == "play":
        cx = label_rect.x - 28 + int(h * 3)
        cy = r.centery
        pygame.draw.polygon(
            screen,
            icon_color,
            [(cx, cy - 9), (cx, cy + 9), (cx + 14, cy)],
        )


# =========================================================
# ENVIRONMENT CARD
# =========================================================

def draw_card(index, rect, scroll, hover, selected, flash, car, t):
    """
    One environment card: scrolling preview, name, description, tags
    and a selection badge. `hover` / `selected` are smoothed 0..1.
    """

    env = ENVIRONMENTS[index]
    preview = previews[index]
    accent = env["accent"]

    focus = clamp(selected + 0.5 * hover)

    # Glow + body
    draw_glow(rect, accent, selected * 0.9 + hover * 0.5, radius=18)

    pygame.draw.rect(screen, CARD_BODY, rect, border_radius=18)
    pygame.draw.rect(
        screen,
        lerp_color(PANEL_BORDER, accent, clamp(selected + hover * 0.6)),
        rect,
        2,
        border_radius=18,
    )

    # ---- preview window ----------------------------------
    win = pygame.Rect(
        rect.x + PREVIEW_PAD, rect.y + PREVIEW_PAD, PW, PH
    )

    screen.set_clip(win)

    if preview["still"] is not None:
        screen.blit(preview["still"], win.topleft)
    else:
        off = int(scroll) % TH
        screen.blit(preview["tile"], (win.x, win.y - TH + off))
        screen.blit(preview["tile"], (win.x, win.y + off))

    # Player car driving down the road
    if car is not None and preview["still"] is None:
        car_surface, shadow = car
        sway = math.sin(t * 1.3 + index) * 7
        cx = win.centerx + sway
        cy = win.y + int(PH * 0.64)

        if env["id"] == "city_night":
            screen.blit(
                headlight_cone,
                headlight_cone.get_rect(
                    midbottom=(cx, cy - car_surface.get_height() // 2 + 14)
                ),
            )
            screen.blit(underglow, underglow.get_rect(center=(cx, cy + 4)))

        screen.blit(shadow, shadow.get_rect(center=(cx + 5, cy + 6)))
        screen.blit(car_surface, car_surface.get_rect(center=(cx, cy)))

    screen.blit(preview["overlay"], win.topleft)

    # Dim unselected cards, flash on selection
    dim_surface.set_alpha(int(120 * (1 - focus)))
    screen.blit(dim_surface, win.topleft)

    if flash > 0.01:
        flash_surface.set_alpha(int(80 * flash))
        screen.blit(flash_surface, win.topleft)

    screen.set_clip(None)

    screen.blit(corner_mask, win.topleft)
    pygame.draw.rect(
        screen,
        lerp_color((40, 52, 76), accent, focus),
        win,
        2,
        border_radius=12,
    )

    # Status chip (top-left of the preview)
    if selected > 0.6:
        chip = get_chip("SELECTED", GREEN)
        screen.blit(chip, (win.x + 14, win.y + 14))
    elif hover > 0.5:
        chip = get_chip("CLICK TO SELECT", BLUE)
        screen.blit(chip, (win.x + 14, win.y + 14))

    # Radio badge (top-right of the preview)
    bx, by = win.right - 28, win.y + 28
    pygame.draw.circle(screen, (10, 13, 22), (bx, by), 15)
    pygame.draw.circle(
        screen, lerp_color((90, 100, 120), accent, selected), (bx, by), 15, 2
    )
    if selected > 0.02:
        pygame.draw.circle(screen, accent, (bx, by), int(11 * selected))
        if selected > 0.6:
            pygame.draw.lines(
                screen,
                (10, 14, 24),
                False,
                [(bx - 6, by), (bx - 2, by + 5), (bx + 6, by - 5)],
                3,
            )

    # ---- text ---------------------------------------------
    name = get_text(env["name"], name_font, WHITE, 4)
    screen.blit(name, name.get_rect(midleft=(rect.x + 26, rect.y + 318)))

    desc = get_text(env["desc"], label_font, GRAY, 1)
    screen.blit(desc, desc.get_rect(midleft=(rect.x + 26, rect.y + 352)))

    chip_x = rect.x + 26
    tag_color = accent if selected > 0.5 else (130, 140, 160)

    for tag in env["tags"]:
        chip = get_chip(tag, tag_color)
        screen.blit(chip, (chip_x, rect.y + 386))
        chip_x += chip.get_width() + 10


# =========================================================
# ENVIRONMENT MENU
# =========================================================

def run_environment():

    pygame.display.set_caption("Highway Racer - Environment")

    card_rects = [
        pygame.Rect(CARD_X[0], CARD_Y, CARD_W, CARD_H),
        pygame.Rect(CARD_X[1], CARD_Y, CARD_W, CARD_H),
    ]

    # Start with the environment that is currently active
    current_id = getattr(vehicle_data, "selected_environment", "forest")
    ids = [env["id"] for env in ENVIRONMENTS]
    selected_index = ids.index(current_id) if current_id in ids else 0

    sel = [1.0 if i == selected_index else 0.0 for i in range(2)]
    hover = {"back": 0.0, "start": 0.0, "card0": 0.0, "card1": 0.0}
    flash = [0.0, 0.0]
    scroll = [0.0, 0.0]

    car = load_preview_car()

    accent_start = ENVIRONMENTS[selected_index]["accent"]

    last_click = (None, 0)
    time_alive = 0.0
    hand_cursor = False
    dt = 1 / 60

    def choose(i):
        nonlocal selected_index
        if i != selected_index:
            selected_index = i
            flash[i] = 1.0

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
                        choose(0)

                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        choose(1)

                    elif event.key in (
                        pygame.K_RETURN,
                        pygame.K_KP_ENTER,
                        pygame.K_SPACE,
                    ):
                        return ENVIRONMENTS[selected_index]["id"]

                if event.type == pygame.MOUSEBUTTONDOWN:

                    if event.button == 1:

                        # START RACE -> "forest" / "city_night"
                        if START_BUTTON.collidepoint(event.pos):
                            return ENVIRONMENTS[selected_index]["id"]

                        # BACK TO MENU
                        elif BACK_BUTTON.collidepoint(event.pos):
                            return "menu"

                        # FOREST / CITY NIGHT cards
                        else:
                            for i, rect in enumerate(card_rects):
                                if rect.collidepoint(event.pos):

                                    now = pygame.time.get_ticks()

                                    # Double-click = quick confirm
                                    if (
                                        last_click[0] == i
                                        and now - last_click[1] < 400
                                    ):
                                        return ENVIRONMENTS[i]["id"]

                                    choose(i)
                                    last_click = (i, now)

            # =============================================
            # UPDATE ANIMATION STATE
            # =============================================

            time_alive += dt
            pulse = 0.5 + 0.5 * math.sin(time_alive * 2.0)

            targets = {
                "back": BACK_BUTTON,
                "start": START_BUTTON,
                "card0": card_rects[0],
                "card1": card_rects[1],
            }

            any_hover = False
            for key, rect in targets.items():
                target = 1.0 if rect.collidepoint(mouse_pos) else 0.0
                any_hover = any_hover or target == 1.0
                hover[key] += (target - hover[key]) * min(1.0, dt * 12)

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

            for i in range(2):
                goal = 1.0 if i == selected_index else 0.0
                sel[i] += (goal - sel[i]) * min(1.0, dt * 9)
                flash[i] = max(0.0, flash[i] - dt * 3.0)

                # Scenery speeds up on hover / selection
                speed = 38 + 110 * hover[f"card{i}"] + 70 * sel[i]
                scroll[i] += speed * dt

            accent_start = lerp_color(
                ENVIRONMENTS[0]["accent"],
                ENVIRONMENTS[1]["accent"],
                sel[1] / max(0.001, sel[0] + sel[1]),
            )

            # =============================================
            # BACKGROUND
            # =============================================

            screen.blit(background_surface, (0, 0))

            # Light behind the selected card
            for i in range(2):
                if sel[i] > 0.02:
                    g = previews[i]["glow"]
                    g.set_alpha(int((120 + 50 * pulse) * sel[i]))
                    screen.blit(
                        g,
                        g.get_rect(center=card_rects[i].center),
                    )

            # =============================================
            # TITLE
            # =============================================

            env_title_glow.set_alpha(int(140 + 70 * pulse))
            title_pos = env_title.get_rect(topleft=(50, 24))

            screen.blit(
                env_title_glow,
                (title_pos.x - TITLE_PAD, title_pos.y - TITLE_PAD),
            )
            screen.blit(env_title, title_pos)

            # =============================================
            # SUBTITLE
            # =============================================

            pygame.draw.rect(
                screen, BLUE, (50, 80, 46, 3), border_radius=2
            )
            screen.blit(
                get_text("CHOOSE YOUR RACING ENVIRONMENT", label_font, GRAY, 4),
                (106, 74),
            )

            # Currently active environment (what is saved right now)
            if current_id in ids:
                active_name = ENVIRONMENTS[ids.index(current_id)]["name"]
                chip = get_chip(f"ACTIVE: {active_name}", GRAY)
                screen.blit(chip, chip.get_rect(topright=(850, 46)))

            # =============================================
            # CARDS
            # =============================================

            for i, base in enumerate(card_rects):

                # Staggered slide-in + hover lift
                e = ease_out((time_alive - 0.12 * i) / 0.5)
                lift = int(6 * hover[f"card{i}"])
                rect = base.move(0, int((1 - e) * 60) - lift)

                draw_card(
                    i,
                    rect,
                    scroll[i],
                    hover[f"card{i}"],
                    sel[i],
                    flash[i],
                    car,
                    time_alive,
                )

            # =============================================
            # BUTTONS
            # =============================================

            e_ui = ease_out((time_alive - 0.25) / 0.5)
            ui_y = int((1 - e_ui) * 50)

            draw_button(
                "BACK TO MENU",
                BACK_BUTTON.move(0, ui_y),
                mouse_pos,
                hover["back"],
                0,
                BLUE,
                False,
                "back",
            )

            draw_button(
                START_LABEL,
                START_BUTTON.move(0, ui_y),
                mouse_pos,
                hover["start"],
                0,
                accent_start,
                True,
                "play",
            )

            # =============================================
            # HINT
            # =============================================

            hint = get_text(
                "LEFT / RIGHT  SWITCH      ENTER  START RACE      ESC  BACK",
                label_font,
                (105, 112, 128),
                2,
            )


            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 676)))

            # =============================================
            # UPDATE
            # =============================================

            pygame.display.update()

            dt = min(clock.tick(60) / 1000, 0.05)

    finally:

        # Never leave the hand cursor stuck when leaving this screen
        try:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        except pygame.error:
            pass

    return "menu"
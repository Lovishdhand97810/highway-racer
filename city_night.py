import pygame

# =========================================================
# CITY NIGHT ASSETS
# =========================================================

SIDEWALK_PATH = "assets/city_night/textures/sidewalk.png"

sidewalk_image = pygame.image.load(
    SIDEWALK_PATH
).convert_alpha()

sidewalk_image = pygame.transform.smoothscale(
    sidewalk_image,
    (200, 200)
)
# =========================================================
# CITY NIGHT BUILDING ASSETS
# =========================================================

BUILDING_1_PATH = "assets/city_night/buildings/building_1.png"
BUILDING_2_PATH = "assets/city_night/buildings/building_2.png"

building_1 = pygame.image.load(
    BUILDING_1_PATH
).convert_alpha()

building_2 = pygame.image.load(
    BUILDING_2_PATH
).convert_alpha()

# Scale once to fit the 200px roadside area
BUILDING_WIDTH = 165

def resize_building(image):

    ratio = BUILDING_WIDTH / image.get_width()

    new_height = int(
        image.get_height() * ratio
    )

    return pygame.transform.smoothscale(
        image,
        (BUILDING_WIDTH, new_height)
    )

building_1 = resize_building(building_1)
building_2 = resize_building(building_2)


# STREETLIGHT
STREETLIGHT_PATH = "assets/city_night/streetlights/streetlight.png"

streetlight_image = pygame.image.load(
    STREETLIGHT_PATH
).convert_alpha()

streetlight_image = pygame.transform.smoothscale(
    streetlight_image,
    (100, 70)
)
# STREETLIGHT GLOW - SOFT RADIAL GRADIENT
GLOW_SIZE = 220
GLOW_RADIUS = GLOW_SIZE // 2

streetlight_glow = pygame.Surface(
    (GLOW_SIZE, GLOW_SIZE),
    pygame.SRCALPHA
)

for y in range(GLOW_SIZE):
    for x in range(GLOW_SIZE):

        dx = x - GLOW_RADIUS
        dy = y - GLOW_RADIUS

        distance = (dx * dx + dy * dy) ** 0.5

        if distance < GLOW_RADIUS:

            strength = 1 - (distance / GLOW_RADIUS)

            alpha = int(65 * (strength ** 2))

            streetlight_glow.set_at(
                (x, y),
                (255, 185, 75, alpha)
            )
# ROAD LIGHT REFLECTION
ROAD_GLOW_WIDTH = 140
ROAD_GLOW_HEIGHT = 260

road_light_glow = pygame.Surface(
    (ROAD_GLOW_WIDTH, ROAD_GLOW_HEIGHT),
    pygame.SRCALPHA
)

center_x = ROAD_GLOW_WIDTH // 2
center_y = ROAD_GLOW_HEIGHT // 2

for y in range(ROAD_GLOW_HEIGHT):
    for x in range(ROAD_GLOW_WIDTH):

        dx = (x - center_x) / center_x
        dy = (y - center_y) / center_y

        distance = (dx * dx + dy * dy) ** 0.5

        if distance < 1:

            strength = 1 - distance
            alpha = int(28 * (strength ** 2))

            road_light_glow.set_at(
                (x, y),
                (255, 190, 90, alpha)
            )
# =========================================================
# CITY NIGHT COLORS
# =========================================================

NIGHT_GROUND = (12, 17, 32)
NIGHT_ROAD = (25, 28, 42)
NIGHT_ROAD_EDGE = (65, 75, 105)

BUILDING_COLOR = (25, 35, 60)
WINDOW_COLOR = (255, 215, 90)


def draw_city_night(screen, width, height,offset=0):

    # Night background
    screen.fill(NIGHT_GROUND)

    # =====================================================
    # SIDEWALK TEXTURES
    # =====================================================

    tile_width = sidewalk_image.get_width()
    tile_height = sidewalk_image.get_height()

    sidewalk_scroll = offset % tile_height
    start_y = sidewalk_scroll - tile_height

    while start_y < height:
        # LEFT SIDE
        screen.blit(
            sidewalk_image,
            (0, int(start_y))
        )

        # RIGHT SIDE
        screen.blit(
            sidewalk_image,
            (width - tile_width, int(start_y))
        )

        start_y += tile_height
    # =====================================================
    # CITY NIGHT BUILDINGS — CONTINUOUS SCROLLING
    # =====================================================

    BUILDING_GAP = 100

    # Buildings on each side
    building_columns = [
        (15, [building_1, building_2]),
        (720, [building_2, building_1])
    ]

    for x, images in building_columns:

        # Height of one complete repeating sequence
        cycle_height = sum(
            image.get_height() + BUILDING_GAP
            for image in images
        )

        # Scroll position
        scroll = offset % cycle_height

        # Draw enough copies to cover the screen
        y = scroll - cycle_height

        while y < height:

            for image in images:
                screen.blit(
                    image,
                    (x, int(y))
                )

                y += image.get_height() + BUILDING_GAP

    # STREETLIGHTS
    STREETLIGHT_GAP = 420

    light_scroll = offset % STREETLIGHT_GAP
    light_y = light_scroll - STREETLIGHT_GAP

    while light_y < height:
        # LEFT SIDE - ROAD EDGE
        screen.blit(
            streetlight_image,
            (150, int(light_y))
        )

        # RIGHT SIDE - ROAD EDGE
        screen.blit(
            streetlight_image,
            (650, int(light_y))
        )

        light_y += STREETLIGHT_GAP

def draw_city_streetlights(screen, width, height, offset=0):

    STREETLIGHT_GAP = 420

    light_scroll = offset % STREETLIGHT_GAP
    light_y = light_scroll - STREETLIGHT_GAP

    while light_y < height:
        # LEFT SIDE GLOW
        screen.blit(
            streetlight_glow,
            (70, int(light_y) - 95)
        )

        # RIGHT SIDE GLOW
        screen.blit(
            streetlight_glow,
            (570, int(light_y) - 95)
        )
        # ROAD REFLECTION - LEFT
        screen.blit(
            road_light_glow,
            (200, int(light_y) - 95)
        )

        # ROAD REFLECTION - RIGHT
        screen.blit(
            road_light_glow,
            (560, int(light_y) - 95)
        )
        # LEFT STREETLIGHT
        screen.blit(
            streetlight_image,
            (150, int(light_y))
        )

        # RIGHT STREETLIGHT
        screen.blit(
            streetlight_image,
            (650, int(light_y))
        )

        light_y += STREETLIGHT_GAP


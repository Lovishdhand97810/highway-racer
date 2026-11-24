import pygame
import random
import vehicle_data
from city_night import draw_city_night, draw_city_streetlights
from vehicle_data import vehicles

# =========================================================
# 1. INITIALIZATION
# =========================================================

pygame.init()

WIDTH = 900
HEIGHT = 700
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Highway Racer")

clock = pygame.time.Clock()


# =========================================================
# 2. COLORS
# =========================================================

BACKGROUND = (12, 14, 20)


# =========================================================
# FOREST ENVIRONMENT COLORS
# =========================================================

GRASS = (31, 174, 105)
ROAD = (38, 40, 48)
ROAD_EDGE = (85, 90, 105)

LANE_COLOR = (100, 180, 255)

RED = (255, 55, 75)
YELLOW = (255, 205, 60)
GOLD = (255, 200, 50)

BLACK = (8, 10, 14)
WHITE = (255, 255, 255)
GRAY = (150, 155, 165)


# =========================================================
# 3. FONTS
# =========================================================

font_small = pygame.font.Font(None, 26)
font_medium = pygame.font.Font(None, 32)
font_large = pygame.font.Font(None, 70)


# =========================================================
# 4. GAME CONFIGURATION
# =========================================================

ROAD_LEFT = 200
ROAD_WIDTH = 500
LANE_COUNT = 3
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT

ROAD_LINE_HEIGHT = 40
ROAD_LINE_GAP = 40

# Road appearance
ROAD_SHOULDER_WIDTH = 12
ROAD_BORDER_WIDTH = 5
ROAD_MARKING_WIDTH = 5
ROAD_MARKING_COLOR = (220, 225, 235)
ROAD_SHOULDER_COLOR = (45, 48, 58)
ROAD_EDGE_COLOR = (235, 235, 240)
ROAD_SIDE_MARKER_COLOR = (255, 205, 70)
ROAD_SIDE_MARKER_WIDTH = 8
ROAD_SIDE_MARKER_HEIGHT = 32
ROAD_SIDE_MARKER_GAP = 68

PLAYER_Y = HEIGHT - 140

# =========================================================
# ENVIRONMENT TEXTURES
# =========================================================

GRASS_PATH = "assets/environment/grass.png"
ROADSIDE_LEFT_PATH = "assets/environment/roadside_left.png"
ROADSIDE_RIGHT_PATH = "assets/environment/roadside_right.png"
TREE_1_PATH = "assets/environment/greentree.png"
TREE_2_PATH = "assets/environment/yellowtree.png"
COIN_SHEET_PATH = "assets/coins/coin_sheet.png"

coin_sheet = pygame.image.load(
    COIN_SHEET_PATH
).convert_alpha()
# Split coin spritesheet into 6 animation frames
COIN_FRAMES = []

frame_width = coin_sheet.get_width() // 6
frame_height = coin_sheet.get_height()

for i in range(6):

    frame = coin_sheet.subsurface(
        (
            i * frame_width,
            0,
            frame_width,
            frame_height
        )
    ).copy()

    COIN_FRAMES.append(frame)

grass_texture = pygame.image.load(
    GRASS_PATH
).convert()

roadside_left = pygame.image.load(
    ROADSIDE_LEFT_PATH
).convert()

roadside_right = pygame.image.load(
    ROADSIDE_RIGHT_PATH
).convert()

tree_1 = pygame.image.load(
    TREE_1_PATH
).convert_alpha()

tree_2 = pygame.image.load(
    TREE_2_PATH
).convert_alpha()
# Make trees smaller

# tree_1 = pygame.transform.smoothscale(
#     tree_1,
#     (
#         int(tree_1.get_width() * 0.075),
#         int(tree_1.get_height() * 0.075)
#     )
# )
#
# tree_2 = pygame.transform.smoothscale(
#     tree_2,
#     (
#         int(tree_2.get_width() * 0.075),
#         int(tree_2.get_height() * 0.075)
#     )
# )

# =========================================================
# SCALE ENVIRONMENT TREES
# =========================================================

TREE_HEIGHT = 150

tree_1_ratio = (
    TREE_HEIGHT / tree_1.get_height()
)

tree_1 = pygame.transform.smoothscale(
    tree_1,
    (
        int(tree_1.get_width() * tree_1_ratio),
        TREE_HEIGHT
    )
)


tree_2_ratio = (
    TREE_HEIGHT / tree_2.get_height()
)

tree_2 = pygame.transform.smoothscale(
    tree_2,
    (
        int(tree_2.get_width() * tree_2_ratio),
        TREE_HEIGHT
    )
)


# Flip roadside textures horizontally
roadside_left = pygame.transform.flip(
    roadside_left,
    True,
    False
)

roadside_right = pygame.transform.flip(
    roadside_right,
    True,
    False
)




VEHICLE_SIZES = {
    "sedan": (60, 100),
    "sports": (65, 100),
    "suv": (68, 105),
    "truck": (72, 105),
    "bike": (40, 90),
}


# =========================================================
# 5. ENEMY VEHICLE DATA
# =========================================================

enemy_vehicles = []

for vehicle in vehicles:
    vehicle_type = vehicle["type"]
    width, height = VEHICLE_SIZES[vehicle_type]

    enemy_vehicles.append({
        "name": vehicle["name"],
        "type": "sedan",
        "color": vehicle["color"],
        "image": "assets/cars/Police.png",
        "speed": 5.5 + vehicle["speed"] / 25,
        "width": width,
        "height": height,
    })

# =========================================================
# 6. ROAD FUNCTIONS
# =========================================================

def get_lane_x(lane, vehicle_width):
    """
    Return the centered X position of a vehicle in a lane.
    """

    return (
        ROAD_LEFT
        + lane * LANE_WIDTH
        + (LANE_WIDTH - vehicle_width) // 2
    )


def create_road_lines():
    """
    Create the two lane divider systems.
    """

    road_lines = []

    for lane in range(1, LANE_COUNT):

        x = ROAD_LEFT + lane * LANE_WIDTH

        lane_lines = []

        for y in range(
            0,
            HEIGHT + ROAD_LINE_HEIGHT + ROAD_LINE_GAP,
            ROAD_LINE_HEIGHT + ROAD_LINE_GAP
        ):

            lane_lines.append([x, y])

        road_lines.append(lane_lines)

    return road_lines


def create_road_side_markers():
    """
    Create moving markers on both sides of the road.
    """

    markers = []

    for y in range(
        0,
        HEIGHT + ROAD_SIDE_MARKER_HEIGHT + ROAD_SIDE_MARKER_GAP,
        ROAD_SIDE_MARKER_HEIGHT + ROAD_SIDE_MARKER_GAP
    ):

        markers.append(y)

    return markers


def update_road_lines(
    road_lines,
    road_side_markers,
    speed
):
    """
    Move all road markings downward.
    """

    # -----------------------------------------------------
    # LANE DIVIDERS
    # -----------------------------------------------------

    for lane_lines in road_lines:

        for line in lane_lines:

            line[1] += speed

            if line[1] > HEIGHT:

                line[1] = -ROAD_LINE_HEIGHT

    # -----------------------------------------------------
    # SIDE MARKERS
    # -----------------------------------------------------

    for i in range(
        len(road_side_markers)
    ):

        road_side_markers[i] += speed

        if road_side_markers[i] > HEIGHT:

            road_side_markers[i] = (
                -ROAD_SIDE_MARKER_HEIGHT
            )


def draw_road(
    road_lines,
    road_side_markers,
    environment_offset
):
    """
    Draw the complete highway.
    """

    # =====================================================
    # GRASS
    # =====================================================

    if vehicle_data.selected_environment == "city_night":

        draw_city_night(
            screen,
            WIDTH,
            HEIGHT,
            environment_offset
        )
    else:

        screen.fill(
            GRASS
        )

    road_right = (
            ROAD_LEFT + ROAD_WIDTH
    )

    # =====================================================
    # ROADSIDE TEXTURES
    # =====================================================
    # =====================================================
    # DIRT + GRASS ROAD EDGE
    # =====================================================

    if vehicle_data.selected_environment != "city_night":

        tile_width = roadside_left.get_width()
        tile_height = roadside_left.get_height()

        for y in range(
                -tile_height,
                HEIGHT + tile_height,
                tile_height
        ):
            draw_y = y + environment_offset

            # LEFT SIDE
            screen.blit(
                roadside_right,
                (
                    ROAD_LEFT - tile_width,
                    draw_y
                )
            )

            # RIGHT SIDE
            screen.blit(
                roadside_left,
                (
                    ROAD_LEFT + ROAD_WIDTH,
                    draw_y
                )
            )

    # =====================================================
    # ROAD SHOULDER
    # =====================================================

    pygame.draw.rect(
        screen,
        ROAD_SHOULDER_COLOR,
        (
            ROAD_LEFT - ROAD_SHOULDER_WIDTH,
            0,
            ROAD_WIDTH
            + ROAD_SHOULDER_WIDTH * 2,
            HEIGHT
        )
    )

    # =====================================================
    # MAIN ROAD
    # =====================================================

    pygame.draw.rect(
        screen,
        ROAD,
        (
            ROAD_LEFT,
            0,
            ROAD_WIDTH,
            HEIGHT
        )
    )

    # =====================================================
    # LEFT ROAD EDGE
    # =====================================================

    pygame.draw.rect(
        screen,
        ROAD_EDGE_COLOR,
        (
            ROAD_LEFT,
            0,
            ROAD_BORDER_WIDTH,
            HEIGHT
        )
    )

    # =====================================================
    # RIGHT ROAD EDGE
    # =====================================================

    pygame.draw.rect(
        screen,
        ROAD_EDGE_COLOR,
        (
            road_right - ROAD_BORDER_WIDTH,
            0,
            ROAD_BORDER_WIDTH,
            HEIGHT
        )
    )



    # =====================================================
    # LANE DIVIDERS
    # =====================================================

    for lane_lines in road_lines:

        for line in lane_lines:

            pygame.draw.rect(
                screen,
                ROAD_MARKING_COLOR,
                (
                    int(line[0])
                    - ROAD_MARKING_WIDTH // 2,
                    int(line[1]),
                    ROAD_MARKING_WIDTH,
                    ROAD_LINE_HEIGHT
                ),
                border_radius=2
            )

    # =====================================================
    # ROADSIDE MARKERS
    # =====================================================

    left_marker_x = (
        ROAD_LEFT
        - ROAD_SHOULDER_WIDTH
        + 3
    )

    right_marker_x = (
        road_right
        + ROAD_SHOULDER_WIDTH
        - ROAD_SIDE_MARKER_WIDTH
        - 3
    )

    for y in road_side_markers:

        # -------------------------------------------------
        # LEFT
        # -------------------------------------------------

        pygame.draw.rect(
            screen,
            ROAD_SIDE_MARKER_COLOR,
            (
                left_marker_x,
                int(y),
                ROAD_SIDE_MARKER_WIDTH,
                ROAD_SIDE_MARKER_HEIGHT
            ),
            border_radius=2
        )

        # -------------------------------------------------
        # RIGHT
        # -------------------------------------------------

        pygame.draw.rect(
            screen,
            ROAD_SIDE_MARKER_COLOR,
            (
                right_marker_x,
                int(y),
                ROAD_SIDE_MARKER_WIDTH,
                ROAD_SIDE_MARKER_HEIGHT
            ),
            border_radius=2
        )
        # CITY NIGHT STREETLIGHTS
        if vehicle_data.selected_environment == "city_night":
            draw_city_streetlights(
                screen,
                WIDTH,
                HEIGHT,
                environment_offset
            )


# =========================================================
# 7. VEHICLE DRAWING
# =========================================================

def draw_player_vehicle(
    x,
    y,
    vehicle_type,
    color,
    image_path=None
):
    """Draw a vehicle using simple pygame shapes."""

    dark = (10, 12, 17)
    window = (25, 45, 60)
    wheel = (5, 5, 8)
    light = (235, 245, 255)

    x = int(x)
    y = int(y)
    # Use vehicle image if available
    if image_path:

        # Load image only once
        if not hasattr(draw_player_vehicle, "image_cache"):
            draw_player_vehicle.image_cache = {}

        if image_path not in draw_player_vehicle.image_cache:

            vehicle_image = pygame.image.load(
                image_path
            ).convert_alpha()

            old_width, old_height = VEHICLE_SIZES[vehicle_type]

            if vehicle_type == "bike":
                target_width = int(old_width * 2.5)
            else:
                target_width = int(old_width * 2.5)

            original_width = vehicle_image.get_width()
            original_height = vehicle_image.get_height()

            target_height = int(
                original_height * target_width / original_width
            )

            vehicle_image = pygame.transform.smoothscale(
                vehicle_image,
                (target_width, target_height)
            )

            draw_player_vehicle.image_cache[image_path] = (
                vehicle_image,
                old_width,
                old_height
            )

        else:

            vehicle_image, old_width, old_height = (
                draw_player_vehicle.image_cache[image_path]
            )

        draw_x = x + (
                old_width - vehicle_image.get_width()
        ) // 2

        draw_y = y + (
                old_height - vehicle_image.get_height()
        ) // 2

        screen.blit(
            vehicle_image,
            (draw_x, draw_y)
        )

        return

        return
    # -----------------------------------------------------
    # VEHICLE SHADOW
    # -----------------------------------------------------

    shadow_width, shadow_height = VEHICLE_SIZES[vehicle_type]

    pygame.draw.ellipse(
        screen,
        (20, 20, 25),
        (
            x + 3,
            y + shadow_height - 4,
            shadow_width - 6,
            9
        )
    )

    # -----------------------------------------------------
    # SEDAN
    # -----------------------------------------------------

    if vehicle_type == "sedan":
        width = 60
        height = 100

        pygame.draw.rect(
            screen,
            color,
            (x, y, width, height),
            border_radius=10
        )

        pygame.draw.polygon(
            screen,
            color,
            [
                (x + 10, y + 25),
                (x + 50, y + 25),
                (x + 45, y + 60),
                (x + 15, y + 60)
            ]
        )

        pygame.draw.polygon(
            screen,
            window,
            [
                (x + 16, y + 28),
                (x + 44, y + 28),
                (x + 40, y + 43),
                (x + 20, y + 43)
            ]
        )

        pygame.draw.polygon(
            screen,
            window,
            [
                (x + 20, y + 47),
                (x + 40, y + 47),
                (x + 44, y + 58),
                (x + 16, y + 58)
            ]
        )

        for light_x in (x + 8, x + 37):
            pygame.draw.rect(
                screen,
                light,
                (light_x, y + 7, 15, 5),
                border_radius=2
            )

        for wheel_y in (20, 70):
            pygame.draw.rect(
                screen,
                wheel,
                (x - 5, y + wheel_y, 6, 22),
                border_radius=2
            )
            pygame.draw.rect(
                screen,
                wheel,
                (x + width - 1, y + wheel_y, 6, 22),
                border_radius=2
            )

    # -----------------------------------------------------
    # SPORTS CAR
    # -----------------------------------------------------

    elif vehicle_type == "sports":
        width = 65

        pygame.draw.polygon(
            screen,
            color,
            [
                (x + 8, y + 8),
                (x + 57, y + 8),
                (x + 64, y + 82),
                (x + 52, y + 98),
                (x + 13, y + 98),
                (x + 1, y + 82)
            ]
        )
        # Body highlight
        highlight = (
            min(255, color[0] + 35),
            min(255, color[1] + 35),
            min(255, color[2] + 35)
        )

        pygame.draw.line(
            screen,
            highlight,
            (x + 8, y + 20),
            (x + 12, y + 70),
            3
        )

        pygame.draw.polygon(
            screen,
            color,
            [
                (x + 13, y + 30),
                (x + 52, y + 30),
                (x + 44, y + 58),
                (x + 21, y + 58)
            ]
        )

        pygame.draw.polygon(
            screen,
            window,
            [
                (x + 18, y + 32),
                (x + 47, y + 32),
                (x + 42, y + 48),
                (x + 23, y + 48)
            ]
        )

        pygame.draw.rect(
            screen,
            WHITE,
            (x + 29, y + 6, 7, 87)
        )

        for light_x in (x + 7, x + 43):
            pygame.draw.rect(
                screen,
                light,
                (light_x, y + 12, 15, 5),
                border_radius=2
            )

        for wheel_y in (25, 70):
            pygame.draw.rect(
                screen,
                wheel,
                (x - 5, y + wheel_y, 6, 20),
                border_radius=2
            )
            pygame.draw.rect(
                screen,
                wheel,
                (x + width - 1, y + wheel_y, 6, 20),
                border_radius=2
            )

    # -----------------------------------------------------
    # SUV
    # -----------------------------------------------------

    elif vehicle_type == "suv":
        width = 68

        pygame.draw.rect(
            screen,
            color,
            (x, y, width, 105),
            border_radius=8
        )

        pygame.draw.rect(
            screen,
            window,
            (x + 10, y + 18, 48, 32),
            border_radius=5
        )

        pygame.draw.rect(
            screen,
            dark,
            (x + 32, y + 18, 5, 32)
        )

        pygame.draw.rect(
            screen,
            dark,
            (x + 5, y + 3, width - 10, 8),
            border_radius=3
        )

        for light_x in (x + 8, x + 46):
            pygame.draw.rect(
                screen,
                light,
                (light_x, y + 6, 14, 5),
                border_radius=2
            )

        for wheel_y in (22, 75):
            pygame.draw.rect(
                screen,
                wheel,
                (x - 5, y + wheel_y, 6, 22),
                border_radius=2
            )
            pygame.draw.rect(
                screen,
                wheel,
                (x + width - 1, y + wheel_y, 6, 22),
                border_radius=2
            )

    # -----------------------------------------------------
    # TRUCK
    # -----------------------------------------------------

    elif vehicle_type == "truck":
        width = 72

        pygame.draw.rect(
            screen,
            color,
            (x, y + 35, width, 65),
            border_radius=6
        )

        pygame.draw.rect(
            screen,
            color,
            (x + 8, y + 5, 56, 45),
            border_radius=7
        )

        pygame.draw.rect(
            screen,
            window,
            (x + 16, y + 12, 40, 20),
            border_radius=4
        )

        pygame.draw.rect(
            screen,
            dark,
            (x + 16, y + 35, 40, 9),
            border_radius=2
        )

        for light_x in (x + 6, x + 56):
            pygame.draw.rect(
                screen,
                light,
                (light_x, y + 34, 10, 6),
                border_radius=2
            )

        for wheel_y in (30, 78):
            pygame.draw.rect(
                screen,
                wheel,
                (x - 5, y + wheel_y, 7, 22),
                border_radius=2
            )
            pygame.draw.rect(
                screen,
                wheel,
                (x + width - 2, y + wheel_y, 7, 22),
                border_radius=2
            )

    # -----------------------------------------------------
    # BIKE
    # -----------------------------------------------------

    elif vehicle_type == "bike":
        # Bike width = 40, so center is x + 20.
        center_x = x + 20

        pygame.draw.circle(
            screen,
            wheel,
            (center_x, y + 15),
            11
        )

        pygame.draw.circle(
            screen,
            wheel,
            (center_x, y + 75),
            11
        )

        pygame.draw.circle(
            screen,
            GRAY,
            (center_x, y + 15),
            5
        )

        pygame.draw.circle(
            screen,
            GRAY,
            (center_x, y + 75),
            5
        )

        pygame.draw.polygon(
            screen,
            color,
            [
                (center_x - 8, y + 25),
                (center_x + 8, y + 25),
                (center_x + 13, y + 65),
                (center_x - 13, y + 65)
            ]
        )

        pygame.draw.ellipse(
            screen,
            color,
            (
                center_x - 17,
                y + 35,
                34,
                32
            )
        )

        pygame.draw.rect(
            screen,
            dark,
            (
                center_x - 11,
                y + 65,
                22,
                7
            ),
            border_radius=3
        )

        pygame.draw.line(
            screen,
            GRAY,
            (center_x - 12, y + 24),
            (center_x + 12, y + 24),
            3
        )

        pygame.draw.circle(
            screen,
            light,
            (center_x, y + 20),
            4
        )


# =========================================================
# 8. ENEMY FUNCTIONS
# =========================================================

def get_enemy_lane(enemy):
    """Return the lane closest to the enemy's center."""
    center_x = enemy["x"] + enemy["width"] / 2

    lane = int(
        (center_x - ROAD_LEFT) / LANE_WIDTH
    )

    return max(0, min(LANE_COUNT - 1, lane))


def create_enemy(enemy_vehicle, lane, y):
    """Create one enemy vehicle."""
    x = get_lane_x(
        lane,
        enemy_vehicle["width"]
    )

    return {
        "x": x,
        "y": y,
        "type": enemy_vehicle["type"],
        "color": enemy_vehicle["color"],
        "name": enemy_vehicle["name"],
        "speed": enemy_vehicle["speed"],
        "width": enemy_vehicle["width"],
        "height": enemy_vehicle["height"],
        "image": enemy_vehicle["image"],
        "target_x": x,
        "lane": lane,
        "ai_timer": 120,
        "changing_lane": False,
    }


def lane_is_safe(enemy, target_lane, enemy_cars):
    """Check whether a target lane is safe."""
    target_x = get_lane_x(
        target_lane,
        enemy["width"]
    )

    for other in enemy_cars:
        if other is enemy:
            continue

        if abs(other["y"] - enemy["y"]) > 100:
            continue

        if abs(other["x"] - target_x) < LANE_WIDTH * 0.55:
            return False

    return True


def choose_enemy_lane(
    enemy,
    enemy_cars,
    player_x,
    player_y,
    difficulty_level
):
    """Choose another lane for the enemy."""

    current_lane = enemy["lane"]

    possible_lanes = [
        lane
        for lane in range(LANE_COUNT)
        if lane != current_lane
    ]

    # Remove lanes that are occupied by nearby enemies
    safe_lanes = [
        lane
        for lane in possible_lanes
        if lane_is_safe(
            enemy,
            lane,
            enemy_cars
        )
    ]

    # If no lane is safe, stay in the current lane
    if not safe_lanes:
        return None

    if not possible_lanes:
        return None

    # At higher difficulty, sometimes move toward player
    player_lane = int(
        (
            player_x - ROAD_LEFT
        ) / LANE_WIDTH
    )

    player_lane = max(
        0,
        min(
            LANE_COUNT - 1,
            player_lane
        )
    )
    # Avoid moving into player's lane when nearby
    if abs(enemy["y"] - player_y) < 180:

        safe_lanes = [
            lane
            for lane in safe_lanes
            if lane != player_lane
        ]

        if not safe_lanes:
            return None


    if (
        difficulty_level >= 3
        and player_lane in possible_lanes
        and random.random() < 0.50
    ):
        return player_lane

    return random.choice(safe_lanes)


def reset_enemy(enemy):
    """Send an enemy back above the screen with new vehicle data."""
    enemy_vehicle = random.choice(enemy_vehicles)
    lane = random.randint(0, LANE_COUNT - 1)

    enemy["type"] = enemy_vehicle["type"]
    enemy["color"] = enemy_vehicle["color"]
    enemy["name"] = enemy_vehicle["name"]
    enemy["speed"] = enemy_vehicle["speed"]
    enemy["width"] = enemy_vehicle["width"]
    enemy["height"] = enemy_vehicle["height"]

    enemy["x"] = get_lane_x(
        lane,
        enemy["width"]
    )

    enemy["target_x"] = enemy["x"]
    enemy["lane"] = lane
    enemy["changing_lane"] = False
    enemy["ai_timer"] = 120

    enemy["y"] = (
        -enemy["height"]
        - random.randint(250, 450)
    )


# =========================================================
# 9. COIN FUNCTIONS
# =========================================================

COIN_RADIUS = 14


def get_lane_center(lane):
    return (
        ROAD_LEFT
        + lane * LANE_WIDTH
        + LANE_WIDTH // 2
    )


def spawn_coin_pattern(coins_on_road):
    """Spawn a single, row or zigzag coin pattern."""
    pattern = random.choice([
        "single",
        "row",
        "zigzag"
    ])

    lane = random.randint(0, LANE_COUNT - 1)

    base_y = -random.randint(150, 400)

    if pattern == "single":
        coins_on_road.append({
            "x": get_lane_center(lane),
            "y": base_y
        })

    elif pattern == "row":
        for i in range(3):
            coins_on_road.append({
                "x": get_lane_center(lane),
                "y": base_y - i * 70
            })

    elif pattern == "zigzag":
        for i in range(4):
            current_lane = (
                lane + i
            ) % LANE_COUNT

            coins_on_road.append({
                "x": get_lane_center(current_lane),
                "y": base_y - i * 70
            })


def reset_coin(coin):
    """Move a collected/off-screen coin back above the road."""
    lane = random.randint(0, LANE_COUNT - 1)

    coin["x"] = get_lane_center(lane)
    coin["y"] = -random.randint(150, 500)

def draw_coin(coin):
    """Draw animated PNG coin."""

    x = int(coin["x"])
    y = int(coin["y"])

    # Choose animation frame
    coin_frame = (
        pygame.time.get_ticks() // 100
    ) % len(COIN_FRAMES)

    coin_image = COIN_FRAMES[coin_frame]

    # Resize coin
    coin_image = pygame.transform.smoothscale(
        coin_image,
        (53, 53)
    )

    # Center coin on its position
    coin_rect = coin_image.get_rect(
        center=(x, y)
    )

    screen.blit(
        coin_image,
        coin_rect
    )


# =========================================================
# 10. HUD
# =========================================================

def draw_hud(
    score,
    distance,
    difficulty_level,
    player_vehicle,
    line_speed,
    coins,
    lives
):
    """Draw the game's top HUD."""
    hud = pygame.Surface(
        (WIDTH, 75),
        pygame.SRCALPHA
    )

    hud.fill(
        (5, 7, 12, 220)
    )

    screen.blit(
        hud,
        (0, 0)
    )

    pygame.draw.line(
        screen,
        LANE_COLOR,
        (0, 74),
        (WIDTH, 74),
        2
    )

    screen.blit(
        font_medium.render(
            f"SCORE  {score}",
            True,
            WHITE
        ),
        (30, 18)
    )

    screen.blit(
        font_small.render(
            f"DISTANCE  {distance:.1f} km",
            True,
            WHITE
        ),
        (30, 48)
    )

    screen.blit(
        font_small.render(
            f"LEVEL  {difficulty_level}",
            True,
            YELLOW
        ),
        (250, 48)
    )

    vehicle_name = font_small.render(
        player_vehicle["name"],
        True,
        player_vehicle["color"]
    )

    vehicle_name_rect = vehicle_name.get_rect(
        center=(450, 15)
    )

    screen.blit(
        vehicle_name,
        vehicle_name_rect
    )

    speed_text = font_medium.render(
        f"SPEED  {int(line_speed * 15)} km/h",
        True,
        LANE_COLOR
    )

    speed_rect = speed_text.get_rect(
        center=(450, 48)
    )

    screen.blit(
        speed_text,
        speed_rect
    )

    screen.blit(
        font_medium.render(
            f"COINS: {coins}",
            True,
            GOLD
        ),
        (600, 25)
    )

    screen.blit(
        font_medium.render(
            f"LIVES:  {lives}",
            True,
            RED
        ),
        (750, 25)
    )


def draw_pause_screen():
    """Draw the pause overlay."""
    overlay = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    overlay.fill(
        (5, 7, 12, 190)
    )

    screen.blit(
        overlay,
        (0, 0)
    )

    title = font_large.render(
        "PAUSED",
        True,
        WHITE
    )

    title_rect = title.get_rect(
        center=(WIDTH // 2, HEIGHT // 2 - 40)
    )

    screen.blit(
        title,
        title_rect
    )

    info = font_medium.render(
        "Press P to continue",
        True,
        GRAY
    )

    info_rect = info.get_rect(
        center=(WIDTH // 2, HEIGHT // 2 + 35)
    )

    screen.blit(
        info,
        info_rect
    )


def draw_crash_flash():
    """Draw the red flash after a collision."""
    flash = pygame.Surface(
        (WIDTH, HEIGHT),
        pygame.SRCALPHA
    )

    flash.fill(
        (255, 40, 60, 80)
    )

    screen.blit(
        flash,
        (0, 0)
    )


# =========================================================
# 11. GAME FUNCTION
# =========================================================

def run_game():
    pygame.display.set_caption("Highway Racer")

    # -----------------------------------------------------
    # PLAYER VEHICLE
    # -----------------------------------------------------

    selected_index = vehicle_data.player_data[
        "selected_vehicle"
    ]

    player_vehicle = vehicles[selected_index]

    vehicle_type = player_vehicle["type"]
    vehicle_color = player_vehicle["color"]

    vehicle_speed = player_vehicle["speed"]
    vehicle_handling = player_vehicle["handling"]
    vehicle_acceleration = player_vehicle["acceleration"]

    car_width, car_height = VEHICLE_SIZES[
        vehicle_type
    ]

    car_x = (
        WIDTH // 2
        - car_width // 2
    )

    car_y = PLAYER_Y

    # -----------------------------------------------------
    # PLAYER SPEED
    # -----------------------------------------------------

    current_speed = 0

    max_speed = 6 + (
        vehicle_speed / 15
    )

    acceleration_rate = (
        0.05
        + vehicle_acceleration / 2000
    )

    deceleration_rate = 0.08

    handling_speed = (
        3
        + vehicle_handling / 25
    )

    # -----------------------------------------------------
    # GAME STATE
    # -----------------------------------------------------

    lives = 3
    score = 0
    distance = 0
    coins = 0

    score_timer = 0
    collision_cooldown = 0
    flash_timer = 0

    paused = False

    # -----------------------------------------------------
    # ROAD
    # -----------------------------------------------------

    road_lines = create_road_lines()
    road_side_markers = create_road_side_markers()

    environment_offset = 0
    city_environment_offset = 0
    # =====================================================
    # TREES
    # =====================================================

    environment_trees = [

        # LEFT SIDE
        {
            "image": tree_1,
            "x": 5,
            "y": 20
        },

        {
            "image": tree_2,
            "x": 5,
            "y": 220
        },

        {
            "image": tree_1,
            "x": 5,
            "y": 420
        },

        {
            "image": tree_2,
            "x": 5,
            "y": 620
        },

        # RIGHT SIDE
        {
            "image": tree_2,
            "x": 770,
            "y": 120
        },

        {
            "image": tree_1,
            "x": 770,
            "y": 320
        },

        {
            "image": tree_2,
            "x": 770,
            "y": 520
        },

        {
            "image": tree_1,
            "x": 770,
            "y": 720
        }
    ]
    # -----------------------------------------------------
    # ENEMIES
    # -----------------------------------------------------

    enemy_cars = []

    for i in range(3):

        enemy_vehicle = random.choice(
            enemy_vehicles
        )

        # Spread enemies across different lanes
        lane = i % LANE_COUNT

        enemy = create_enemy(
            enemy_vehicle,
            lane,
            -enemy_vehicle["height"] - i * 250
        )

        enemy_cars.append(enemy)

    # -----------------------------------------------------
    # COINS
    # -----------------------------------------------------

    coins_on_road = []
    coin_effects = []

    for _ in range(2):
        spawn_coin_pattern(
            coins_on_road
        )

    # =====================================================
    # MAIN GAME LOOP
    # =====================================================

    running = True

    while running:

        # -------------------------------------------------
        # EVENTS
        # -------------------------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    return "menu"

                if event.key == pygame.K_p:
                    paused = not paused

        # -------------------------------------------------
        # PAUSE
        # -------------------------------------------------

        if paused:
            draw_pause_screen()
            pygame.display.update()
            clock.tick(FPS)
            continue

        # -------------------------------------------------
        # DIFFICULTY
        # -------------------------------------------------

        base_difficulty = min(
            10,
            1 + int(distance / 20)
        )

        if vehicle_data.difficulty == "Easy":

            difficulty_level = max(1, base_difficulty - 2)

        elif vehicle_data.difficulty == "Hard":

            difficulty_level = min(10, base_difficulty + 2)

        else:

            difficulty_level = base_difficulty

        # -------------------------------------------------
        # PLAYER INPUT
        # -------------------------------------------------

        keys = pygame.key.get_pressed()
        # Accelerate with W
        if keys[pygame.K_w]:
            current_speed += acceleration_rate
            current_speed = min(
                current_speed,
                max_speed
                 )
        else:
            current_speed -= deceleration_rate
            current_speed = max(
                current_speed,
                0
            )

        # Move left with A
        if keys[pygame.K_a]:
            car_x -= handling_speed

# Move right with D
        if keys[pygame.K_d]:
            car_x += handling_speed
        

        # Keep player inside road
        car_x = max(
            ROAD_LEFT,
            min(
                car_x,
                ROAD_LEFT + ROAD_WIDTH - car_width
            )
        )

        # -------------------------------------------------
        # TIMERS
        # -------------------------------------------------

        if collision_cooldown > 0:
            collision_cooldown -= 1

        if flash_timer > 0:
            flash_timer -= 1

        # -------------------------------------------------
        # SCORE
        # -------------------------------------------------

        score_timer += 1

        if score_timer >= 6:
            score += 1
            score_timer = 0

        # -------------------------------------------------
        # DISTANCE
        # -------------------------------------------------

        line_speed = 3 + current_speed
        environment_offset += line_speed

        if environment_offset >= 128:
            environment_offset -= 128
        if vehicle_data.selected_environment == "city_night":
            city_environment_offset += line_speed
        distance += line_speed / 60

        # =================================================
        # DRAW ROAD
        # =================================================

        # =================================================
        # DRAW ROAD
        # =================================================

        update_road_lines(
            road_lines,
            road_side_markers,
            line_speed
        )

        if vehicle_data.selected_environment == "city_night":

            draw_road(
                road_lines,
                road_side_markers,
                city_environment_offset
            )

        else:

            draw_road(
                road_lines,
                road_side_markers,
                environment_offset
            )
        # =====================================================
        # DRAW ENVIRONMENT TREES
        # =====================================================

        # =====================================================
        # UPDATE AND DRAW ENVIRONMENT TREES
        # =====================================================

        TREE_GAP = 160

        if vehicle_data.selected_environment == "forest":

            for tree in environment_trees:

                # Move tree downward
                tree["y"] += line_speed

                if tree["y"] > HEIGHT:

                    # Find trees on the same side
                    same_side_trees = [
                        other
                        for other in environment_trees
                        if (
                                other["x"] == tree["x"]
                                and other is not tree
                        )
                    ]

                    if same_side_trees:
                        highest_tree = min(
                            same_side_trees,
                            key=lambda other: other["y"]
                        )

                        tree["y"] = (
                                highest_tree["y"]
                                - tree["image"].get_height()
                                - TREE_GAP
                        )

                screen.blit(
                    tree["image"],
                    (
                        tree["x"],
                        tree["y"]
                    )
                )
        # =================================================
        # PLAYER HITBOX
        # =================================================

        player_rect = pygame.Rect(
            int(car_x),
            int(car_y),
            car_width,
            car_height
        )

        # =================================================
        # ENEMY AI
        # =================================================

        for enemy in enemy_cars:


            enemy["ai_timer"] -= 1

            if enemy["ai_timer"] <= 0:

                # Try to change lane every few seconds
                base_interval = 120

                difficulty_bonus = (
                        difficulty_level * 8
                )

                enemy["ai_timer"] = max(
                    60,
                    base_interval - difficulty_bonus
                )

                if random.random() < 0.35:

                    new_lane = choose_enemy_lane(
                        enemy,
                        enemy_cars,
                        car_x + car_width / 2,
                        car_y,
                        difficulty_level
                    )

                    if new_lane is not None:
                        enemy["target_x"] = get_lane_x(
                            new_lane,
                            enemy["width"]
                        )

                        enemy["changing_lane"] = True
                        enemy["lane"] = new_lane
        # =================================================
        # ENEMY MOVEMENT + COLLISION
        # =================================================

        for enemy in enemy_cars:

            enemy["y"] += (
                enemy["speed"]
                + current_speed * 0.15
                + difficulty_level * 0.1
            )

            # Smooth lane change
            difference = (
                enemy["target_x"]
                - enemy["x"]
            )

            lane_change_speed = 4

            if abs(difference) <= lane_change_speed:

                enemy["x"] = enemy["target_x"]
                enemy["changing_lane"] = False

            elif difference > 0:
                enemy["x"] += lane_change_speed

            else:
                enemy["x"] -= lane_change_speed

            enemy_rect = pygame.Rect(
                int(enemy["x"]),
                int(enemy["y"]),
                enemy["width"],
                enemy["height"]
            )

            draw_player_vehicle(
                enemy["x"],
                enemy["y"],
                enemy["type"],
                enemy["color"],
                enemy["image"],

            )

            player_hitbox = player_rect.inflate(
                -10,
                -10
            )

            enemy_hitbox = enemy_rect.inflate(
                -8,
                -8
            )

            if player_hitbox.colliderect(
                enemy_hitbox
            ):
                if collision_cooldown == 0:

                    lives -= 1
                    collision_cooldown = 60
                    flash_timer = 15

                    score = max(
                        0,
                        score - 100
                    )

                    reset_enemy(
                        enemy
                    )

        # -------------------------------------------------
        # RESET OFF-SCREEN ENEMIES
        # -------------------------------------------------

        for enemy in enemy_cars:
            if enemy["y"] > HEIGHT:
                reset_enemy(enemy)

        # =================================================
        # COINS
        # =================================================

        for coin in coins_on_road:

            coin["y"] += line_speed

            coin_rect = pygame.Rect(
                int(coin["x"] - COIN_RADIUS),
                int(coin["y"] - COIN_RADIUS),
                COIN_RADIUS * 2,
                COIN_RADIUS * 2
            )

            draw_coin(coin)

            if player_rect.colliderect(
                coin_rect
            ):
                coins += 1
                score += 25

                coin_effects.append({
                    "x": coin["x"],
                    "y": coin["y"],
                    "timer": 20
                })

                reset_coin(coin)

            elif coin["y"] > HEIGHT:
                reset_coin(coin)

        # -------------------------------------------------
        # COIN EFFECTS
        # -------------------------------------------------

        for effect in coin_effects[:]:

            effect["timer"] -= 1

            radius = (
                14
                + (20 - effect["timer"]) * 2
            )

            pygame.draw.circle(
                screen,
                GOLD,
                (
                    int(effect["x"]),
                    int(effect["y"])
                ),
                radius,
                3
            )

            if effect["timer"] <= 0:
                coin_effects.remove(effect)

        # -------------------------------------------------
        # SPAWN MORE COINS
        # -------------------------------------------------

        if len(coins_on_road) < 6:
            spawn_coin_pattern(
                coins_on_road
            )

        # =================================================
        # PLAYER VEHICLE
        # =================================================

        if (
            collision_cooldown == 0
            or collision_cooldown % 10 < 5
        ):
            draw_player_vehicle(
                car_x,
                car_y,
                vehicle_type,
                vehicle_color,
                player_vehicle["image"]
            )

        # =================================================
        # HUD
        # =================================================

        draw_hud(
            score,
            distance,
            difficulty_level,
            player_vehicle,
            line_speed,
            coins,
            lives
        )

        # -------------------------------------------------
        # CRASH FLASH
        # -------------------------------------------------

        if flash_timer > 0:
            draw_crash_flash()

        # =================================================
        # GAME OVER
        # =================================================

        if lives <= 0:

            vehicle_data.player_data["coins"] += coins
            vehicle_data.save_data()

            return (
                "game_over",
                score,
                coins,
                distance
            )

        # FPS COUNTER

        if vehicle_data.show_fps:
            fps_value = int(clock.get_fps())

            fps_text = font_small.render(
                f"FPS: {fps_value}",
                True,
                WHITE
            )

            screen.blit(fps_text, (WIDTH - 100, HEIGHT - 35))

        # DISPLAY

        pygame.display.update()
        clock.tick(FPS)

    return "quit"

import pygame
import player_data
pygame.init()

WIDTH = 900
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Highway Racer")


clock = pygame.time.Clock()


# ---------------- COLORS ----------------

BACKGROUND = (8, 10, 16)
PANEL = (15, 18, 28)

BLUE = (80, 180, 255)
RED = (255, 55, 75)
WHITE = (240, 240, 245)
GRAY = (150, 155, 165)
GOLD = (255, 200, 50)


# ---------------- FONTS ----------------

title_font = pygame.font.Font(None, 90)
large_font = pygame.font.Font(None, 45)
medium_font = pygame.font.Font(None, 32)


# ---------------- BUTTON ----------------

def draw_button(text, x, y, width, height, mouse_pos):

    rect = pygame.Rect(
        x,
        y,
        width,
        height
    )

    if rect.collidepoint(mouse_pos):

        pygame.draw.rect(
            screen,
            (30, 70, 100),
            rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            BLUE,
            rect,
            2,
            border_radius=12
        )

    else:

        pygame.draw.rect(
            screen,
            PANEL,
            rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            (60, 65, 80),
            rect,
            2,
            border_radius=12
        )

    text_surface = medium_font.render(
        text,
        True,
        WHITE
    )

    text_rect = text_surface.get_rect(
        center=rect.center
    )

    screen.blit(
        text_surface,
        text_rect
    )

    return rect


# ---------------- GAME OVER ----------------

def run_game_over(score, coins, distance,total_coins):
    player_data.stats["games_played"] += 1

    player_data.stats["highest_score"] = max(
        player_data.stats["highest_score"],
        score
    )

    player_data.stats["total_coins"] = total_coins

    player_data.stats["longest_distance"] = max(
        player_data.stats["longest_distance"],
        distance
    )

    player_data.save_stats()
    
    running = True

    while running:

        mouse_pos = pygame.mouse.get_pos()

        # ---------------- EVENTS ----------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN:

                if retry_button.collidepoint(event.pos):

                    return "retry"

                if menu_button.collidepoint(event.pos):

                    return "menu"

                if exit_button.collidepoint(event.pos):

                    return "quit"


        # ---------------- BACKGROUND ----------------

        screen.fill(BACKGROUND)


        # Dark road in background

        pygame.draw.rect(
            screen,
            (18, 21, 30),
            (250, 0, 400, HEIGHT)
        )


        # Road markings

        for y in range(0, HEIGHT, 100):

            pygame.draw.rect(
                screen,
                (40, 70, 90),
                (445, y, 10, 55)
            )


        # ---------------- TITLE ----------------

        title = title_font.render(
            "GAME OVER",
            True,
            RED
        )

        title_rect = title.get_rect(
            center=(WIDTH // 2, 100)
        )

        screen.blit(
            title,
            title_rect
        )


        # ---------------- SCORE PANEL ----------------

        panel = pygame.Rect(
            250,
            180,
            400,
            240
        )

        pygame.draw.rect(
            screen,
            PANEL,
            panel,
            border_radius=15
        )

        pygame.draw.rect(
            screen,
            (60, 65, 80),
            panel,
            2,
            border_radius=15
        )


        # Score

        score_text = large_font.render(
            f"SCORE     {score}",
            True,
            WHITE
        )

        score_rect = score_text.get_rect(
            center=(WIDTH // 2, 225)
        )

        screen.blit(
            score_text,
            score_rect
        )


        # Coins

        coin_text = large_font.render(
            f"COINS     {coins}",
            True,
            GOLD
        )

        coin_rect = coin_text.get_rect(
            center=(WIDTH // 2, 280)
        )

        screen.blit(
            coin_text,
            coin_rect
        )


        # Distance

        distance_text = medium_font.render(
            f"DISTANCE     {distance:.1f} km",
            True,
            GRAY
        )

        distance_rect = distance_text.get_rect(
            center=(WIDTH // 2, 335)
        )

        screen.blit(
            distance_text,
            distance_rect
        )

        # Total Coins

        total_coins_text = medium_font.render(
            f"TOTAL COINS     {total_coins}",
            True,
            GOLD
        )

        total_coins_rect = total_coins_text.get_rect(
            center=(WIDTH // 2, 375)
        )

        screen.blit(
            total_coins_text,
            total_coins_rect
        )

        # ---------------- BUTTONS ----------------

        retry_button = draw_button(
            "RETRY",
            250,
            455,
            180,
            60,
            mouse_pos
        )

        menu_button = draw_button(
            "MAIN MENU",
            460,
            455,
            190,
            60,
            mouse_pos
        )

        exit_button = draw_button(
            "EXIT",
            350,
            535,
            200,
            55,
            mouse_pos
        )


        # ---------------- FOOTER ----------------

        footer = medium_font.render(
            "BETTER LUCK NEXT TIME!",
            True,
            GRAY
        )

        footer_rect = footer.get_rect(
            center=(WIDTH // 2, 625)
        )

        screen.blit(
            footer,
            footer_rect
        )


        pygame.display.update()

        clock.tick(60)


    return "quit"
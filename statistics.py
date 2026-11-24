import pygame
import player_data

WIDTH = 900
HEIGHT = 700

screen = pygame.display.get_surface()

WHITE = (240, 240, 245)
GOLD = (255, 200, 50)
BLUE = (80, 180, 255)
GRAY = (150, 155, 165)
GREEN = (40, 160, 80)

title_font = pygame.font.Font(None, 75)
medium_font = pygame.font.Font(None, 38)
small_font = pygame.font.Font(None, 28)


def run_statistics():

    running = True

    while running:

        screen.fill((15, 18, 28))

        title = title_font.render("GAME STATISTICS", True, BLUE)
        screen.blit(title, title.get_rect(center=(450, 90)))

        stats = player_data.stats

        items = [
            ("GAMES PLAYED", stats["games_played"], WHITE),
            ("HIGHEST SCORE", stats["highest_score"], GOLD),
            ("TOTAL COINS", stats["total_coins"], GOLD),
            ("LONGEST DISTANCE", f'{stats["longest_distance"]:.1f} km', BLUE)
        ]

        y = 190

        for label, value, color in items:

            pygame.draw.rect(
                screen,
                (25, 30, 45),
                (200, y, 500, 65),
                border_radius=10
            )

            label_text = medium_font.render(label, True, GRAY)
            value_text = medium_font.render(str(value), True, color)

            screen.blit(label_text, (225, y + 17))
            screen.blit(value_text, (650 - value_text.get_width(), y + 17))

            y += 90

        back_rect = pygame.Rect(300, 570, 300, 60)

        pygame.draw.rect(
            screen,
            GREEN,
            back_rect,
            border_radius=10
        )

        back_text = medium_font.render("BACK TO MENU", True, WHITE)
        screen.blit(back_text, back_text.get_rect(center=back_rect.center))

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

            if event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    if back_rect.collidepoint(event.pos):
                        return "menu"

        pygame.display.update()

    return "menu"

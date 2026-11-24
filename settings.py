import pygame
import vehicle_data
pygame.init()

WIDTH = 900
HEIGHT = 700

screen = pygame.display.get_surface()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (40, 160, 80)
GRAY = (100, 100, 100)

font = pygame.font.Font(None, 40)
small_font = pygame.font.Font(None, 28)


def run_settings():

    running = True
    show_controls = False
    while running:

        screen.fill((20, 30, 25))

        title = font.render("SETTINGS", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        difficulty_rect = pygame.Rect(280, 220, 340, 55)
        fps_rect = pygame.Rect(280, 300, 340, 55)
        controls_rect = pygame.Rect(280, 380, 340, 55)
        back_rect = pygame.Rect(280, 590, 340, 55)

        difficulty_text = small_font.render(
            f"Difficulty: {vehicle_data.difficulty}", True, WHITE
        )
        fps_status = "ON" if vehicle_data.show_fps else "OFF"

        fps_text = small_font.render(
            f"Show FPS: {fps_status}", True, WHITE
        )

        controls_text = small_font.render(
            "Controls: Arrow Keys to Drive", True, WHITE
        )
        back_text = small_font.render("BACK TO MENU", True, WHITE)

        for rect in [difficulty_rect, fps_rect, controls_rect, back_rect]:
            pygame.draw.rect(screen, GREEN, rect, border_radius=8)

        screen.blit(difficulty_text, difficulty_text.get_rect(center=difficulty_rect.center))
        screen.blit(fps_text, fps_text.get_rect(center=fps_rect.center))
        screen.blit(controls_text, controls_text.get_rect(center=controls_rect.center))
        if show_controls:

            control_lines = [
                "W - Accelerate",
                "A - Move Left",
                "D - Move Right",
                "P - Pause",
                "ESC - Return to Menu"
            ]

            for i, line in enumerate(control_lines):
                text = small_font.render(line, True, WHITE)
                screen.blit(text, (350, 445 + i * 27))
        screen.blit(back_text, back_text.get_rect(center=back_rect.center))

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if difficulty_rect.collidepoint(event.pos):

                    levels = ["Easy", "Normal", "Hard"]
                    current = levels.index(vehicle_data.difficulty)
                    vehicle_data.difficulty = levels[(current + 1) % 3]


                elif fps_rect.collidepoint(event.pos):

                    vehicle_data.show_fps = not vehicle_data.show_fps



                elif controls_rect.collidepoint(event.pos):

                    show_controls = not show_controls


                elif back_rect.collidepoint(event.pos):

                    return "menu"

        pygame.display.update()

    return "menu"
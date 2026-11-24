import pygame
import vehicle_data

from menu import run_menu
from game import run_game
from game_over import run_game_over
from garage import run_garage
from environment import run_environment
from settings import run_settings
from statistics import run_statistics



# =========================================================
# MAIN LOOP
# =========================================================

running = True

while running:
 

    # =====================================================
    # MAIN MENU
    # =====================================================

    menu_result = run_menu()


    # =====================================================
    # EXIT
    # =====================================================

    if menu_result == "quit":
        break


    # =====================================================
    # GARAGE
    # =====================================================

    if menu_result == "garage":

        garage_result = run_garage()

        if garage_result == "quit":
            break

        if garage_result == "menu":
            continue

    # =====================================================
    # ENVIRONMENT
    # =====================================================

    if menu_result == "environment":

        environment_result = run_environment()

        if environment_result == "quit":
            break

        if environment_result == "menu":
            continue

        if environment_result in ("forest", "city_night"):
            vehicle_data.selected_environment = (
                environment_result
            )

            continue

    # =====================================================
    # SETTINGS
    # =====================================================

    if menu_result == "settings":

        settings_result = run_settings()

        if settings_result == "quit":
            break

        if settings_result == "menu":
            continue

    # =====================================================
    # PLAY
    # =====================================================

    elif menu_result == "play":

        game_result = run_game()


        # Player closed game
        if game_result == "quit":
            break


        # Player pressed ESC
        if game_result == "menu":
            continue


        # =================================================
        # GAME OVER
        # =================================================

        if isinstance(game_result, tuple):

            result, score, coins, distance = game_result


            if result == "game_over":

                # -----------------------------------------
                # SAVE COINS FROM THIS RACE
                # -----------------------------------------

                vehicle_data.player_data["coins"] += coins

                # -----------------------------------------
                # GAME OVER SCREEN
                # -----------------------------------------

                over_result = run_game_over(
                    score,
                    coins,
                    distance,
                    vehicle_data.player_data["coins"]
                )


                if over_result == "quit":
                    break


                if over_result == "retry":
                    continue


                if over_result == "menu":
                    continue

    # =====================================================
    # STATISTICS
    # =====================================================

    if menu_result == "statistics":

        statistics_result = run_statistics()

        if statistics_result == "quit":
            break

        if statistics_result == "menu":
            continue
# =========================================================
# CLOSE PYGAME
# =========================================================

pygame.quit()
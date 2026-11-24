import json
import os

DATA_FILE = os.path.join(
    os.path.dirname(__file__),
    "player_stats.json"
)

stats = {
    "games_played": 0,
    "highest_score": 0,
    "total_coins": 0,
    "longest_distance": 0.0
}


def load_stats():

    global stats

    try:
        with open(DATA_FILE, "r") as file:
            saved_data = json.load(file)

        stats.update(saved_data)

    except (FileNotFoundError, json.JSONDecodeError):
        pass


def save_stats():

    with open(DATA_FILE, "w") as file:
        json.dump(stats, file, indent=4)


load_stats()
import json
import os


SAVE_FILE = "player_data.json"


# =========================================================
# VEHICLES
# =========================================================

vehicles = [

    {
        "name": "STREET",
        "type": "sedan",
        "color": (220, 45, 60),
        "image": "assets/cars/Audi.png",
        "speed": 70,
        "handling": 70,
        "acceleration": 70,
        "price": 0
    },

    {
        "name": "RAPTOR",
        "type": "sports",
        "color": (40, 140, 255),
        "image": "assets/cars/Black_viper.png",
        "speed": 85,
        "handling": 60,
        "acceleration": 80,
        "price": 500
    },

    {
        "name": "PHANTOM",
        "type": "suv",
        "color": (50, 210, 130),
        "image": "assets/cars/race_car.png",
        "speed": 120,
        "handling": 75,
        "acceleration": 75,
        "price": 5000
    },

    {
        "name": "TITAN",
        "type": "truck",
        "color": (255, 170, 40),
        "image": "assets/cars/Mini_truck.png",
        "speed": 65,
        "handling": 55,
        "acceleration": 60,
        "price": 1500
    },

    {
        "name": "BLAZE",
        "type": "bike",
        "color": (180, 80, 255),
        "image": "assets/cars/motorcycle_yellow.png",
        "speed": 95,
        "handling": 90,
        "acceleration": 95,
        "price": 2000
    }
]


# =========================================================
# PLAYER DATA
# =========================================================

player_data = {

    "coins": 0,

    "unlocked": [True, False, False, False, False],

    "selected_vehicle": 0
}


# =========================================================
# LOAD SAVE
# =========================================================

def load_data():

    global player_data

    if os.path.exists(SAVE_FILE):

        try:

            with open(
                SAVE_FILE,
                "r"
            ) as file:

                player_data = json.load(file)

        except:

            print("Save file corrupted. Starting new game.")


# =========================================================
# SAVE DATA
# =========================================================

def save_data():

    with open(
        SAVE_FILE,
        "w"
    ) as file:

        json.dump(
            player_data,
            file,
            indent=4
        )


# =========================================================
# UNLOCK VEHICLE
# =========================================================

def unlock_vehicle(index):

    if player_data["unlocked"][index]:

        return True

    price = vehicles[index]["price"]

    if player_data["coins"] >= price:

        player_data["coins"] -= price

        player_data["unlocked"][index] = True

        save_data()

        return True

    return False


# =========================================================
# SELECT VEHICLE
# =========================================================

def select_vehicle(index):

    if player_data["unlocked"][index]:

        player_data["selected_vehicle"] = index

        save_data()

        return True

    return False


# =========================================================
# SELECTED ENVIRONMENT
# =========================================================

selected_environment = "forest"

difficulty = "Normal"
show_fps = False
# =========================================================
# STARTUP
# =========================================================

load_data()


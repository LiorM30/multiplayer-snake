from unittest.mock import DEFAULT
from enums import Color


class Snake_Config:
    SCREEN_WIDTH = 600
    SCREEN_HEIGHT = 600
    GAME_WIDTH = 15
    GAME_HEIGHT = 15
    TILE_WIDTH = int(SCREEN_WIDTH / GAME_WIDTH)
    TILE_HEIGHT = int(SCREEN_HEIGHT / GAME_HEIGHT)
    FPS = 30
    BGCOLOR = Color.BLACK.value
    GAME_NAME = "Snake"
    GAME_SPEED = 150  # milliseconds,time it takes for the snake to move a tile
    TIME_BETWEEN_SNAKE_UPDATES = int(GAME_SPEED / 10)
    SNAKE_PARTS_DIRECTORY = 'assets\\images\\snake parts\\'
    APPLE_IMAGE_PATH = 'assets\\images\\apple.png'
    DEFAULT_SNAKE_COLOR = (48, 216, 238)
    SNAKE_COLORS = (Color.CYAN, Color.GREEN, Color.YELLOW, Color.FUCHSIA)

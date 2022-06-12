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
    EXPLOSION_DIRECTORY = 'assets\\images\\explosion\\'
    SNAKE_PARTS_DIRECTORY = 'assets\\images\\snake parts\\'
    APPLE_IMAGE_PATH = 'assets\\images\\apple.png'
    EXPLOTION_COLOR_KEY = (0, 252, 0)
    SCORES_FILE_PATH = 'assets\\scores.json'

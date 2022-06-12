from enum import Enum


class Player_Command(str, Enum):  # inhereting from str to make serializeble
    MOVE_UP = 'move up'
    MOVE_DOWN = 'move down'
    MOVE_LEFT = 'move left'
    MOVE_RIGHT = 'move right'

    QUIT = 'quit'


class Direction(Enum):
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'


class Game_Object(str, Enum):
    Player = 'player'
    APPLE = 'apple'
    SNAKE_HEAD = 'snake head'
    SNAKE_BODY = 'snake body'
    SNAKE_TAIL = 'snake tail'


class Color(Enum):
    # (R, G, B)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    BLACK = (0, 0, 0)
    FUCHSIA = (255, 0, 255)
    GRAY = (128, 128, 128)
    LIME = (0, 128, 0)
    MAROON = (128, 0, 0)
    NAVYBLUE = (0, 0, 128)
    OLIVE = (128, 128, 0)
    PURPLE = (128, 0, 128)
    RED = (255, 0, 0)
    SILVER = (192, 192, 192)
    TEAL = (0, 128, 128)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 128, 0)
    CYAN = (0, 255, 255)


class Snake_Part(Enum):
    TAIL = 'tail'
    BODY = 'body'
    HEAD = 'head'

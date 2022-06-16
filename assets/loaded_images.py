import pygame
import os

from snake_config import Snake_Config as Config
from enums import Game_Object


class Loaded_Images:
    """
    Class used for already loaded images as to not load them in run time
    """

    def __init__(self) -> None:
        # snake parts
        self.snake_head = pygame.image.load(os.path.join(
            Config.SNAKE_PARTS_DIRECTORY, 'head.png'
        ))
        self.snake_head = pygame.transform.scale(
            self.snake_head, (Config.TILE_WIDTH, Config.TILE_HEIGHT)
        )

        self.snake_body = pygame.image.load(os.path.join(
            Config.SNAKE_PARTS_DIRECTORY, 'body.png'
        ))
        self.snake_body = pygame.transform.scale(
            self.snake_body, (Config.TILE_WIDTH, Config.TILE_HEIGHT)
        )

        self.snake_tail = pygame.image.load(os.path.join(
            Config.SNAKE_PARTS_DIRECTORY, 'tail.png'
        ))
        self.snake_tail = pygame.transform.scale(
            self.snake_tail, (Config.TILE_WIDTH, Config.TILE_HEIGHT)
        )

        # apple
        self.apple = pygame.image.load(Config.APPLE_IMAGE_PATH)
        self.apple = pygame.transform.scale(
            self.apple, (Config.TILE_WIDTH, Config.TILE_HEIGHT)
        )

        self.all = {
            Game_Object.SNAKE_HEAD: self.snake_head,
            Game_Object.SNAKE_BODY: self.snake_body,
            Game_Object.SNAKE_TAIL: self.snake_tail,
            Game_Object.APPLE: self.apple,
        }

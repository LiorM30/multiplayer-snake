from traceback import print_tb
import pygame
import os

from snake_config import Snake_Config as Config
from enums import Game_Object, Color, Direction


class Loaded_Images:
    """
    Class used for already loaded images as to not load them in run time
    """

    def __init__(self) -> None:
        # snake parts
        temp = pygame.image.load(os.path.join(
            Config.SNAKE_PARTS_DIRECTORY, 'head.png'
        ))
        self._snake_head = temp.copy()
        self._snake_head = pygame.transform.scale(
            self._snake_head, (Config.TILE_WIDTH, Config.TILE_HEIGHT)
        )

        temp = pygame.image.load(os.path.join(
            Config.SNAKE_PARTS_DIRECTORY, 'body.png'
        ))
        self._snake_body = temp.copy()
        self._snake_body = pygame.transform.scale(
            self._snake_body, (Config.TILE_WIDTH, Config.TILE_HEIGHT)
        )

        temp = pygame.image.load(os.path.join(
            Config.SNAKE_PARTS_DIRECTORY, 'tail.png'
        ))
        self._snake_tail = temp.copy()
        self._snake_tail = pygame.transform.scale(
            self._snake_tail, (Config.TILE_WIDTH, Config.TILE_HEIGHT)
        )

        # apple
        self._apple = pygame.image.load(Config.APPLE_IMAGE_PATH).copy()
        self._apple = pygame.transform.scale(
            self._apple, (Config.TILE_WIDTH, Config.TILE_HEIGHT)
        )

        self._all = {
            Game_Object.SNAKE_HEAD: self._snake_head,
            Game_Object.SNAKE_BODY: self._snake_body,
            Game_Object.SNAKE_TAIL: self._snake_tail,
            Game_Object.APPLE: self._apple
        }

    def get_image(
        self,
        object: Game_Object,
        color: Color,
        direction: Direction
    ) -> pygame.Surface:
        image = self._all[object].copy()
        if color:
            var = pygame.PixelArray(image)
            var.replace(Config.DEFAULT_SNAKE_COLOR, color)
            del var
        match direction:
            case Direction.UP:
                return pygame.transform.rotate(
                    image, 0
                )
            case Direction.DOWN:
                return pygame.transform.rotate(
                    image, 180
                )
            case Direction.RIGHT:
                return pygame.transform.rotate(
                    image, 270
                )
            case Direction.LEFT:
                return pygame.transform.rotate(
                    image, 90
                )
            case _:
                return image

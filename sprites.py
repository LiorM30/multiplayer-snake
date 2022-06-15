import pygame

from enums import Direction, Game_Object, Snake_Part, Color
from snake_config import Snake_Config as Config


class Player(pygame.sprite.Sprite):
    def __init__(self, ID: int, coords: tuple[int, int]) -> None:
        super().__init__()

        self._ID = ID
        self._coords = coords

        self._image = pygame.Surface((50, 50))
        self._image.fill((255, 255, 255))
        self.rect = self._image.get_rect()
        self.rect.center = coords

        self._x_speed = 0  # the sprite's movement speeds
        self._y_speed = 0

    def update(self):
        self._move()

    def _move(self):
        self.rect.y += self._y_speed
        self.rect.x += self._x_speed

    def change_y_speed(self, speed):
        self._y_speed += speed

    def change_x_speed(self, speed):
        self._x_speed += speed

    def get_coords(self) -> tuple[int, int]:
        return (self.rect.x, self.rect.y)


class Snake_Body(pygame.sprite.Sprite):
    def __init__(
        self,
        x: int, y: int,
        part: Snake_Part, direction: Direction,
        all_images: dict
    ) -> None:

        super().__init__()

        self.all_images = all_images
        self._part = part
        match part:
            case Snake_Part.HEAD:
                self.image = self.all_images[Game_Object.SNAKE_HEAD]
            case Snake_Part.BODY:
                self.image = self.all_images[Game_Object.SNAKE_BODY]
            case Snake_Part.TAIL:
                self.image = self.all_images[Game_Object.SNAKE_TAIL]
        self.change_costume(part)

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.direction = direction

        self.explosion_sprites = self.all_images[Game_Object.EXPLOSION]
        self.explode_frame = 0
        self.is_exploding = False
        self.current_rotation = 0  # pointing up
        self.set_direction(direction)

        self._layer = self.rect.bottom

    def update(self):
        if self.is_exploding:
            self.explode()
        else:
            self.move()

    def move(self) -> None:
        """
        Moves the sprite according to its direction
        """

        match self.direction:
            case Direction.UP:
                self.rect.y -= Config.TILE_HEIGHT / 10
            case Direction.DOWN:
                self.rect.y += Config.TILE_HEIGHT / 10
            case Direction.LEFT:
                self.rect.x -= Config.TILE_WIDTH / 10
            case Direction.RIGHT:
                self.rect.x += Config.TILE_WIDTH / 10
            case _:
                pass

    def set_direction(self, new_direction: Direction) -> None:
        """
        Sets the sprites direction and rotates the sprite according to the direction

        ...
        :param new_direction: the direction to point to
        """

        self.direction = new_direction
        match new_direction:
            case Direction.UP:
                self.image = pygame.transform.rotate(
                    self.image, 0 - self.current_rotation
                )
                self.current_rotation += 0 - self.current_rotation
            case Direction.DOWN:
                self.image = pygame.transform.rotate(
                    self.image, 180 - self.current_rotation
                )
                self.current_rotation += 180 - self.current_rotation
            case Direction.RIGHT:
                self.image = pygame.transform.rotate(
                    self.image, 270 - self.current_rotation
                )
                self.current_rotation += 270 - self.current_rotation
            case Direction.LEFT:
                self.image = pygame.transform.rotate(
                    self.image, 90 - self.current_rotation
                )
                self.current_rotation += 90 - self.current_rotation

    def goto(self, x: int, y: int):
        """
        Moves the sprite to the desired location

        ...
        :param x: the x value on screen
        :param y: the y value on screen
        """

        self.rect.x = x
        self.rect.right = y

    def pos(self) -> tuple[int, int]:
        """
        :return: the position of the sprite on screen
        """

        return (self.rect.x, self.rect.y)

    def snap(self) -> None:
        """
        Snaps the sprite to the nearest tile
        """

        self.rect.x = self.round_to_multiple(self.rect.x, Config.TILE_WIDTH)
        self.rect.y = self.round_to_multiple(self.rect.y, Config.TILE_HEIGHT)

    def round_to_multiple(self, number, multiple) -> int:
        """
        :param number: the number to do the operation on
        :param multiple: the multiple to round to
        :return: the number rounded to the nearest multiple
        """

        return multiple * round(number / multiple)

    def get_x(self) -> int:
        """
        :return: the x value of the sprite
        """

        return self.rect.x

    def get_y(self) -> int:
        """
        :return: the y value of the sprite
        """

        return self.rect.y

    def collide_point(self, coords: tuple[int, int]) -> bool:
        """
        :param coords: a point on screen
        :return: whether the point is in the sprite
        """

        return self.rect.collidepoint(coords)

    def explode(self) -> None:
        """
        Makes the sprite go BOOM, should be called untill the sprite is killed
        """

        if not self.is_exploding:
            self.rect.y -= Config.TILE_HEIGHT
            self.rect.x -= Config.TILE_WIDTH / 2
            self.is_exploding = True
        if self.explode_frame > len(self.explosion_sprites) - 1:
            self.kill()
        else:
            self.image = self.explosion_sprites[self.explode_frame]
            self.image = pygame.transform.scale(
                self.image, (Config.TILE_WIDTH * 2, Config.TILE_HEIGHT * 2)
            )
            self.explode_frame += 1

    def change_costume(self, new_costume: Snake_Part) -> None:
        """
        Changes the sprite's costume

        ...
        :param new_costume: the costume to change to
        """

        self._part = new_costume
        match new_costume:
            case Snake_Part.HEAD:
                self.image = self.all_images[Game_Object.SNAKE_HEAD]
            case Snake_Part.BODY:
                self.image = self.all_images[Game_Object.SNAKE_BODY]
            case Snake_Part.TAIL:
                self.image = self.all_images[Game_Object.SNAKE_TAIL]

    def to_dict(self):
        a_dict = {}
        match self._part:
            case Snake_Part.HEAD:
                a_dict['object'] = Game_Object.SNAKE_HEAD
            case Snake_Part.BODY:
                a_dict['object'] = Game_Object.SNAKE_BODY
            case Snake_Part.TAIL:
                a_dict['object'] = Game_Object.SNAKE_TAIL

        a_dict['coords'] = list(self.pos())
        a_dict['direction'] = self.direction

        return a_dict


class Apple(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, all_images: dict) -> None:
        super().__init__()
        self.all_images = all_images
        self.image = all_images[Game_Object.APPLE]

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        pygame.draw.rect(
            self.image,
            Color.RED.value,
            pygame.Rect(x, y, Config.TILE_WIDTH, Config.TILE_HEIGHT)
        )

    def get_x(self) -> int:
        """
        :return: the x value of the sprite
        """

        return self.rect.x

    def get_y(self) -> int:
        """
        :return: the x value of the sprite
        """

        return self.rect.y

    def pos(self):
        return (self.rect.x, self.rect.y)

    def get_rect(self) -> pygame.rect:
        """
        :return: the sprite's rect
        """

        return self.rect

    def to_dict(self):
        return {
            'object': Game_Object.APPLE,
            'coords': self.pos(),
            'direction': None
        }

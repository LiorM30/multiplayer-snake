import json
from os import kill
import socket
import threading
import pygame
from dataclasses import dataclass
from time import sleep
import logging
import argparse
import random

from enums import Direction, Player_Command, Game_Object, Snake_Part
from sprites import Player as Player_Sprite
from sprites import Snake_Body, Apple
from game_packet_API import Game_Packet, Game_Packet_Type
from snake_config import Snake_Config as Config
from assets.loaded_images import Loaded_Images


@dataclass
class Player:
    username: str
    ID: int
    sock: socket.socket


@dataclass
class Request:
    type: Player_Command
    player_ID: int


class Snake_Server:
    def __init__(self, port) -> None:
        self._parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        self._parser.add_argument(
            '--log_level', action='store', type=int, default=20,
            help='Log level (50=Critical, 40=Error, 30=Warning ,20=Info ,10=Debug, 0=None)'
        )
        self._args = self._parser.parse_args()

        logging.basicConfig(
            level=self._args.log_level,
            format='[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(module)s] [%(funcName)s]: %(message)s',  # noqa
            datefmt='%d-%m-%Y %H:%M:%S',
            filename='game_logs.log'
        )

        logging.getLogger().addHandler(logging.StreamHandler())

        self._logger = logging.getLogger()

        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind(
            (socket.gethostbyname(socket.gethostname()), port))
        self._logger.debug('Server is up and running')

        self._players = {}
        self._threads = []
        self._requests = []

        self._get_clients()
        self._logger.debug('Got all clients')

        # self._player_sprites = {}

        pygame.init()
        self._clock = pygame.time.Clock()

        self._snakes = {}
        self._snake_sprite_group = pygame.sprite.Group()
        self._init_snakes()
        self._apples = self._generate_apples()
        self._apple_sprite_group = pygame.sprite.Group()
        self._apple_sprite_group.add(self._apples)

        self.image_loader = Loaded_Images()
        self.all_images = self.image_loader.all

        self._sprites_to_send = []

        for ID, player in self._players.items():
            self._send_data(
                player.sock,
                Game_Packet(
                    type=Game_Packet_Type.START_GAME
                )
            )

    def _get_clients(self) -> None:
        """
        Listens to connections and adds them to the players dict
        Creates a thread to handle them and adds it to the threads list
        """
        currentID = 0
        while True:
            self.server_sock.listen()
            client, client_address = self.server_sock.accept()
            username = self._recieve_packet(client)['data']['username']
            self._logger.debug(f'Client {username} connected')

            new_player = Player(
                username=username,
                ID=currentID,
                sock=client,
            )

            self._players[currentID] = new_player

            self._threads.append(
                threading.Thread(
                    target=self._handle_player,
                    args=(new_player,)
                )
            )

            self._player_sprites[currentID] = Player_Sprite(
                currentID,
                (0, 0)
            )

            currentID += 1
            if len(self._players) == 2:
                break

    def _handle_player(self, player: Player):
        """
        Handles the player and recieves all data sent by them
        Puts the data in the requests list
        ...
        :param player: the player to handle
        """
        try:
            while True:
                packet = self._recieve_packet(player.sock)
                if packet['type'] == Game_Packet_Type.PLAYER_INPUTS:
                    if packet['data']['status'] == Player_Command.QUIT:
                        player.sock.close()
                        self._logger.debug(
                            f'Client disconnected, name: {player.username}'
                        )
                        break

                    for key, val in packet['data'].items():
                        if val is not None:
                            self._requests.append(
                                Request(val, player.ID)
                            )
                            print(val)

                elif packet['type'] == Game_Packet_Type.RECIEVE_SPRITES:
                    self._send_data(
                        player.sock,
                        Game_Packet(
                            type=Game_Packet_Type.SPRITES_TO_RENDER,
                            data=self._sprites_to_send
                        )
                    )

        except ConnectionResetError:
            self._logger.debug(f'Player {player.username} has disconnected')
            self._players.pop(player.ID)

    def _init_snakes(self) -> None:
        """
        Initializes the snakes according to the number of players
        """

        row_space = Config.SCREEN_HEIGHT / len(self._players)
        for i in range(len(self._players)):
            self._snakes[i].append(
                Snake_Body(
                    7.5 * Config.TILE_WIDTH,
                    row_space * (i + 1) * Config.TILE_HEIGHT,
                    Snake_Part.HEAD,
                    Direction.RIGHT,
                    self.all_images
                )
            )
            self._snakes[i].append(
                Snake_Body(
                    6.5 * Config.TILE_WIDTH,
                    row_space * (i + 1) * Config.TILE_HEIGHT,
                    Snake_Part.HEAD,
                    Direction.RIGHT,
                    self.all_images
                )
            )
            self._snakes[i].append(
                Snake_Body(
                    5.5 * Config.TILE_WIDTH,
                    row_space * (i + 1) * Config.TILE_HEIGHT,
                    Snake_Part.HEAD,
                    Direction.RIGHT,
                    self.all_images
                )
            )
            self._snake_sprite_group.add(self._snakes[i])

    def _generate_apples(self, num_of_apples: int) -> Apple:
        """
        Generates a list of apples

        ...
        :return: a list of apples that dont intersect with the snakes and aren't off screen
        """
        apples = []
        apple_coords_list = []

        for _ in range(num_of_apples):
            apple_coords = (
                random.randrange(0, Config.GAME_WIDTH) * Config.TILE_WIDTH
                + Config.TILE_WIDTH / 2,
                random.randrange(0, Config.GAME_HEIGHT) * Config.TILE_HEIGHT
                + Config.TILE_WIDTH / 2,
            )

            again = True
            while again:
                again = False
                for snake in self._snakes:
                    for part in snake:
                        if part.collide_point(apple_coords):
                            apple_coords = (
                                random.randrange(0, Config.GAME_WIDTH + 1) * Config.TILE_WIDTH
                                + Config.TILE_WIDTH / 2,  # offset
                                random.randrange(0, Config.GAME_HEIGHT + 1) * Config.TILE_HEIGHT
                                + Config.TILE_WIDTH / 2,
                            )
                            again = True
                            break
                # checks if the apple is in the same coords as another one
                if apple_coords in apple_coords_list:
                    again = True

            apple_coords_list.append(apple_coords)
            apples.append(Apple(
                apple_coords[0], apple_coords[1], self.all_images
            ))

        return apples

    def _snake_hit_apple(self, snake: list[Snake_Body]) -> Apple:
        """
        Checks if the snake given hit an apple and returns the apple it hit
        if th snake didng hit an apple returns None
        ...
        :param snake: the snake to check
        :return: the apple it hit
        """
        for apple in self._apples:
            if apple.rect.collidelist(snake) != -1:
                return apple
        return None

    def _grow_snake(self, snake: list[Snake_Body]) -> None:
        """
        Makes the snake grow, adds body to the snake list and sprite group
        """

        snake[-1].change_costume(Snake_Part.BODY)
        new_part = Snake_Body(
            snake[-1].get_x() + Config.TILE_WIDTH / 2,
            snake[-1].get_y() + Config.TILE_HEIGHT / 2,
            Snake_Part.TAIL,
            None,
            self.all_images
        )

        snake.append(new_part)
        self._snake_sprite_group.add(new_part)

    def _snake_hit_self(self, snake: list[Snake_Body]) -> bool:
        """
        :return: if the snake hits itself
        """

        if len(snake) < 5:  # can only hit body from the fifth onward
            return False
        return snake[0].rect.collidelist(snake[4:]) != -1

    def _snake_hit_screen_edge(self, snake: list[Snake_Body]) -> bool:
        """
        :return: if the snake hit the edge of the screen
        """

        return not 0 <= snake[0].get_y() < Config.SCREEN_HEIGHT \
            and not 0 <= snake[0].get_x() < Config.SCREEN_WIDTH

    def _send_data(self, client: socket.socket, data: Game_Packet) -> None:
        """
        Sends data to the client
        The data is a dictionary of all sprites and their location
        ...
        :param client: the client to send to
        :param data: the data to send
        """
        ser_data = json.dumps(vars(data))
        client.send(ser_data.encode())

    def _recieve_packet(self, client: socket.socket) -> Game_Packet:
        return json.loads(
            client.recv(1024).decode()
        )

    def mainloop(self) -> None:
        """
        The mainloop of the program, call to run it
        """

        self._logger.debug('In mainloop')

        # creating custom events names
        CHANGE_DIRECTION = pygame.USEREVENT + 1
        UPDATE_SNAKE = pygame.USEREVENT + 2
        # setting event times
        pygame.time.set_timer(CHANGE_DIRECTION, Config.GAME_SPEED)
        pygame.time.set_timer(UPDATE_SNAKE, Config.TIME_BETWEEN_SNAKE_UPDATES)

        new_directions = {}
        for i in len(self._players):
            new_directions[i] = Direction.RIGHT

        for t in self._threads:
            t.start()
        while True:
            if self._requests:
                for request in self._requests:
                    player_ID = request.player_ID
                    snake_head = self._snakes[player_ID][0]
                    match request.type:
                        case Player_Command.MOVE_UP:
                            if snake_head.direction != Direction.DOWN:
                                new_directions[player_ID] = Direction.UP
                        case Player_Command.MOVE_DOWN:
                            if snake_head.direction != Direction.UP:
                                new_directions[player_ID] = Direction.DOWN
                        case Player_Command.MOVE_LEFT:
                            if snake_head.direction != Direction.RIGHT:
                                new_directions[player_ID] = Direction.LEFT
                        case Player_Command.MOVE_RIGHT:
                            if snake_head.direction != Direction.LEFT:
                                new_directions[player_ID] = Direction.RIGHT

                self._requests.clear()  # clear events list after iterating through them

            for event in pygame.event.get():
                if event.type == UPDATE_SNAKE:
                    self._snake_sprite_group.update()

                if event.type == CHANGE_DIRECTION:
                    for snake_ID, snake in self._snakes.items():
                        snake[0].set_direction(new_directions[snake_ID])

                        for part in snake:
                            part.snap()  # snap to the nearest tile
                            # since pygame is not accurate enough
                            # we need to snap every part to place

                        for i in range(len(snake) - 1, 0, -1):
                            current_part = snake[i]
                            next_part = snake[i - 1]
                            if current_part.get_x() > next_part.get_x():
                                current_part.set_direction(Direction.LEFT)
                            elif current_part.get_x() < next_part.get_x():
                                current_part.set_direction(Direction.RIGHT)
                            elif current_part.get_y() > next_part.get_y():
                                current_part.set_direction(Direction.UP)
                            elif current_part.get_y() < next_part.get_y():
                                current_part.set_direction(Direction.DOWN)

            for snake_id, snake in self._snakes.items():
                apple_hit = self._snake_hit_apple(snake)
                if apple_hit:
                    self._grow_snake(snake)
                    apple_hit.kill()
                    new_apple = self._generate_apples(1)
                    self._apples.append(new_apple)
                    self._apple_sprite_group.add(new_apple)

                if self._snake_hit_self(snake) or self._snake_hit_screen_edge(snake):
                    # self._explode_snake()
                    pass

            # for ID, sprite in self._player_sprites.items():
                # sprite.update()
            self._snake_sprite_group.update()

            new_sprites_to_send = []
            for snake_id, snake in self._snakes.items():
                for part in snake:
                    match part.type
                    new_sprites_to_send.append(
                        [Game_Object.Player, list(sprite.get_coords())]
                    )

            self._sprites_to_send = new_sprites_to_send.copy()

            # for ID, player in self._players.items():
            #     self._send_data(player.sock, self._sprites_to_send)
            # sleep(1/30)
            self._clock.tick(20)


def main():
    server = Snake_Server(3333)
    server.mainloop()


if __name__ == "__main__":
    main()

import json
import socket
import threading
import pygame
from dataclasses import dataclass
from time import sleep
import logging
import argparse
import random

from enums import Direction, Player_Command, Snake_Part, \
    Player_State, Game_State
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
            help='Log level (50=Critical, 40=Error, 30=Warning ,20=Info ,10=Debug, 0=None)'  # noqa
        )

        self._parser.add_argument(
            '--player_count', action='store', type=int,
            default=2, choices=range(0, 5),
            help='number of players that will play, up to 4'
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

        self._num_of_players = self._args.player_count

        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind(
            (socket.gethostbyname(socket.gethostname()), port)
        )
        self._logger.debug('Server is up and running')

        self._players = {}
        self._players_lost = []
        self._player_won = 0
        self._threads = []
        self._requests = []
        self.stop_handling_clients = False

        self._get_clients()
        self._logger.debug('Got all clients')

        pygame.init()

        # need a screen for things like sprites
        self._server_screen = pygame.display.set_mode(
            (40, 40)
        )

        self._clock = pygame.time.Clock()

        # setting the snakes dictionary
        self._snakes = {}
        for ID in self._players:
            self._snakes[ID] = []
        self._snake_sprite_group = pygame.sprite.Group()

        self._sprites_to_send = []

        # initializing sprites
        self._init_snakes()
        self._apples = self._generate_apples(len(self._players))
        self._apple_sprite_group = pygame.sprite.Group()
        self._apple_sprite_group.add(self._apples)

        # need to load the images not during gametime
        # to not take up time

        self.image_loader = Loaded_Images()
        self.all_images = self.image_loader._all

        self._logger.debug('Done initializing')

    def _get_clients(self) -> None:
        """
        Listens to connections and adds them to the players dict
        Creates a thread to handle them and adds it to the threads list
        """
        currentID = 0
        while True:
            self._logger.debug('Listening for clients')
            self.server_sock.listen()
            client, client_address = self.server_sock.accept()
            username = self._recieve_packet(client).data['username']
            self._logger.debug(f'Client {username} connected')

            new_player = Player(
                username=username,
                ID=currentID,
                sock=client
            )

            self._players[currentID] = new_player

            self._threads.append(
                threading.Thread(
                    target=self._handle_player,
                    args=(new_player,)
                )
            )

            self._send_data(
                client=client,
                data=Game_Packet(
                    type=Game_Packet_Type.PLAYER_INFO,
                    data={
                        'player ID': currentID,
                        'player color': Config.SNAKE_COLORS[currentID]
                    }
                )
            )

            currentID += 1
            if len(self._players) == self._num_of_players:
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
                if packet.type == Game_Packet_Type.PLAYER_READY:
                    self._logger.debug(f'Player {player.ID} is ready')
                    self._players_ready += 1
                elif packet.type == Game_Packet_Type.PLAYER_INPUTS:
                    if packet.data['status'] == Player_Command.QUIT:
                        player.sock.close()
                        self._remove_snake(player.ID)
                        self._snakes.pop(player.ID)
                        self._players.pop(player.ID)

                        self._logger.debug(
                            f'Player {player.username} has disconnected'
                        )
                        break

                    for key, val in packet.data.items():
                        if val is not None:
                            self._requests.append(
                                Request(val, player.ID)
                            )
                            print(val)

                elif packet.type == Game_Packet_Type.GAME_STATUS_REQUEST:
                    data = {
                        'sprites': [],
                        'game state': None,
                        'player state': None
                    }
                    for sprite in self._sprites_to_send:
                        data['sprites'].append(sprite.to_dict())
                    if len(self._players) == len(self._players_lost) + 1:
                        data['game state'] = Game_State.DONE
                    else:
                        data['game state'] = Game_State.ONGOING

                    if self._player_won == player.ID:
                        data['player state'] = Player_State.WON
                    elif player.ID in self._players_lost:
                        data['player state'] = Player_State.LOST

                    self._send_data(
                        player.sock,
                        Game_Packet(
                            type=Game_Packet_Type.GAME_STATUS,
                            data=data
                        )
                    )
                    if self.stop_handling_clients:
                        player.sock.close()
                        self._players.pop(player.ID)
                        self._logger.debug(
                            f'Closed connection with {player.username}'
                        )
                        break

        except ConnectionResetError or json.decoder.JSONDecodeError:
            self._logger.debug(
                f'Player {player.username} has disconnected unexpectedly'
            )
            self._snakes.pop(player.ID)
            self._remove_snake(player.ID)
            self._players.pop(player.ID)

    def _init_snakes(self) -> None:
        """
        Initializes the snakes according to the number of players
        """

        count = 1
        row_space = Config.SCREEN_HEIGHT / (len(self._players) + 1)
        for ID, player in self._players.items():
            part_x = 7.5
            self._snakes[ID].append(
                Snake_Body(
                    part_x * Config.TILE_WIDTH,
                    row_space * count,
                    Snake_Part.HEAD,
                    Direction.RIGHT,
                    Config.SNAKE_COLORS[ID],
                    self.all_images
                )
            )
            # alternating between facing left and facing right
            if count % 2 == 0:
                part_x += 1
            else:
                part_x -= 1
            self._snakes[ID].append(
                Snake_Body(
                    part_x * Config.TILE_WIDTH,
                    row_space * count,
                    Snake_Part.BODY,
                    Direction.RIGHT,
                    Config.SNAKE_COLORS[ID],
                    self.all_images
                )
            )
            if count % 2 == 0:
                part_x += 1
            else:
                part_x -= 1
            self._snakes[ID].append(
                Snake_Body(
                    part_x * Config.TILE_WIDTH,
                    row_space * count,
                    Snake_Part.TAIL,
                    Direction.RIGHT,
                    Config.SNAKE_COLORS[ID],
                    self.all_images
                )
            )
            self._sprites_to_send.extend(self._snakes[ID])
            self._snake_sprite_group.add(self._snakes[ID])
            count += 1

    def _generate_apples(self, num_of_apples: int) -> Apple:
        """
        Generates a list of apples

        ...
        :return: a list of apples that dont intersect\
         with the snakes and aren't off screen
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
                for snake in self._snakes.values():
                    for part in snake:
                        if part.collide_point(apple_coords):
                            apple_coords = (
                                random.randrange(
                                    0, Config.GAME_WIDTH + 1
                                ) * Config.TILE_WIDTH
                                + Config.TILE_WIDTH / 2,  # offset
                                random.randrange(
                                    0, Config.GAME_HEIGHT + 1
                                ) * Config.TILE_HEIGHT
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
        self._sprites_to_send.extend(apples)
        return apples

    def _snake_hit_apple(self, snake_ID: int) -> Apple:
        """
        Checks if the snake given hit an apple and returns the apple it hit
        if th snake didng hit an apple returns None
        ...
        :param snake: the snake to check
        :return: the apple it hit
        """

        for apple in self._apples:
            if apple.rect.collidelist(self._snakes[snake_ID]) != -1:
                return apple
        return None

    def _grow_snake(self, snake_ID) -> None:
        """
        Makes the snake grow, adds body to the snake list and sprite group
        ...
        :param snake_ID: the ID of the snake to grow
        """

        self._snakes[snake_ID][-1].change_costume(Snake_Part.BODY)
        new_part = Snake_Body(
            self._snakes[snake_ID][-1].get_x() + Config.TILE_WIDTH / 2,
            self._snakes[snake_ID][-1].get_y() + Config.TILE_HEIGHT / 2,
            Snake_Part.TAIL,
            None,
            Config.SNAKE_COLORS[snake_ID],
            self.all_images
        )

        self._sprites_to_send.append(new_part)
        self._snakes[snake_ID].append(new_part)
        self._snake_sprite_group.add(new_part)

    def _snake_hit_self(self, snake_ID: int) -> bool:
        """
        :param snake_ID: the id of the snake to check
        :return: if the snake hits itself
        """

        if len(self._snakes[snake_ID]) > 4:
            if self._snakes[snake_ID][0].rect.collidelist(self._snakes[snake_ID][4:]) != -1:  # noqa
                self._logger.debug(
                    f'snake {snake_ID} has collided with itself'
                )
                return True
        for ID, snake in self._snakes.items():
            if ID != snake_ID:
                if self._snakes[snake_ID][0].rect.collidelist(snake) >= 0:
                    self._logger.debug(
                        f'snake {snake_ID} has collided with snake {ID}'
                    )
                    return True
        return False

    def _snake_hit_screen_edge(self, snake_ID: int) -> bool:
        """
        :return: if the snake hit the edge of the screen
        """

        return not 0 <= self._snakes[snake_ID][0].get_y() < Config.SCREEN_HEIGHT or \
            not 0 <= self._snakes[snake_ID][0].get_x() < Config.SCREEN_WIDTH

    def _remove_snake(self, snake_ID: int) -> None:
        """
        Removes a snake from the game
        ...
        :param snake_ID: the ID of the snake to kill
        """

        for part in self._snakes[snake_ID]:
            part.kill()
            self._sprites_to_send.remove(part)

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
        """
        Recieves the packet the client sent
        ...
        :param client: the client to recieve from
        :return: the game packet
        """

        return Game_Packet(
            **json.loads(
                client.recv(1024).decode()
            )
        )

    def run_game(self) -> None:
        """
        The mainloop of the program, call to run it
        """

        self._logger.debug('Running game')
        self._players_ready = 0

        for t in self._threads:  # starting all threads
            t.start()

        # waiting for all players to be ready:
        while self._players_ready != len(self._players):
            pass
        self._logger.debug('Everyone is ready')

        #  telling the players that the game started
        for ID, player in self._players.items():
            self._send_data(
                player.sock,
                Game_Packet(
                    type=Game_Packet_Type.START_GAME
                )
            )
        self._logger.debug('Sent start game packets')

        # creating custom events names
        CHANGE_DIRECTION = pygame.USEREVENT + 1
        UPDATE_SNAKE = pygame.USEREVENT + 2
        # setting event times
        pygame.time.set_timer(CHANGE_DIRECTION, Config.GAME_SPEED)
        pygame.time.set_timer(UPDATE_SNAKE, Config.TIME_BETWEEN_SNAKE_UPDATES)

        new_directions = {}
        for ID in self._players:
            new_directions[ID] = Direction.RIGHT

        while True:
            if len(self._players) == 0:  # all players quit\game is done
                break
            self._clock.tick(20)

            if self._requests:  # has player requests
                for request in self._requests:
                    player_ID = request.player_ID
                    try:
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
                    except KeyError:
                        # someone quit unexpectidly while iterating
                        pass

                # clear events list after iterating through them
                self._requests.clear()

            for event in pygame.event.get():
                if event.type == CHANGE_DIRECTION:
                    for snake_ID, snake in self._snakes.items():
                        snake[0].set_direction(new_directions[snake_ID])

                        for part in snake:
                            part.snap()  # snap to the nearest tile
                            # since pygame is not accurate enough
                            # we need to snap every part to place
                        
                        # setting part directions
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

                # updating snakes
                if event.type == UPDATE_SNAKE:
                    for ID, snake in self._snakes.items():
                        if ID == 1:
                            for part in snake:
                                part.update()
                    # self._snake_sprite_group.update()

            IDs_to_remove = []
            for snake_ID in self._snakes:
                apple_hit = self._snake_hit_apple(snake_ID)
                if apple_hit:
                    self._grow_snake(snake_ID)
                    self._apples.remove(apple_hit)
                    self._sprites_to_send.remove(apple_hit)
                    apple_hit.kill()
                    new_apple = self._generate_apples(1)
                    self._apples.extend(new_apple)
                    self._apple_sprite_group.add(new_apple)

                if self._snake_hit_self(snake_ID) or \
                   self._snake_hit_screen_edge(snake_ID):

                    # only one player left
                    if len(self._players) - len(self._players_lost) == 1:
                        self._player_won = set(self._players) - set(self._players_lost)

                        # make sure every player got a game
                        # update before stopping the game
                        sleep(0.5)
                        self.stop_handling_clients = True

                    self._players_lost.append(snake_ID)
                    self._remove_snake(snake_ID)
                    IDs_to_remove.append(snake_ID)
            for ID in IDs_to_remove:
                self._snakes.pop(ID)

        self._logger.debug('Game done')


def main():
    server = Snake_Server(3333)
    server.run_game()


if __name__ == "__main__":
    main()

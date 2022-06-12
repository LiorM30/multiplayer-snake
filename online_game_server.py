import json
import socket
import threading
import pygame
from dataclasses import dataclass
from time import sleep
import logging
import argparse

from enums import Directions, Player_Commands, Game_Objects
from sprites import Player as Player_Sprite
from game_packet_API import Game_Packet, Game_Packet_Type


@dataclass
class Player:
    username: str
    ID: int
    sock: socket.socket


@dataclass
class Request:
    type: Player_Commands
    player_ID: int


class Online_Game_Server:
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
        self.server_sock.bind((socket.gethostbyname(socket.gethostname()), port))
        self._logger.debug('Server is up and running')

        self._players = {}
        self._threads = []
        self._requests = []

        self._player_sprites = {}

        self._sprites_to_send = []

        self._get_clients()
        self._logger.debug('Got all clients')

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
                    if packet['data']['status'] == Player_Commands.QUIT:
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

        for t in self._threads:
            t.start()
        while True:
            if self._requests:
                for request in self._requests:
                    player_ID = request.player_ID
                    match request.type:
                        case Player_Commands.MOVE_UP:
                            self._player_sprites[player_ID].change_y_speed(-10)
                        case Player_Commands.MOVE_DOWN:
                            self._player_sprites[player_ID].change_y_speed(10)
                        case Player_Commands.MOVE_LEFT:
                            self._player_sprites[player_ID].change_x_speed(-10)
                        case Player_Commands.MOVE_RIGHT:
                            self._player_sprites[player_ID].change_x_speed(10)

                        case Player_Commands.STOP_MOVE_UP:
                            self._player_sprites[player_ID].change_y_speed(10)
                        case Player_Commands.STOP_MOVE_DOWN:
                            self._player_sprites[player_ID].change_y_speed(-10)
                        case Player_Commands.STOP_MOVE_LEFT:
                            self._player_sprites[player_ID].change_x_speed(10)
                        case Player_Commands.STOP_MOVE_RIGHT:
                            self._player_sprites[player_ID].change_x_speed(-10)

                self._requests.clear()  # clear events list after iterating through them

            for ID, sprite in self._player_sprites.items():
                sprite.update()

            new_sprites_to_send = []
            for player_ID, sprite in self._player_sprites.items():
                new_sprites_to_send.append(
                    [Game_Objects.Player, list(sprite.get_coords())]
                )

            self._sprites_to_send = new_sprites_to_send.copy()

            # for ID, player in self._players.items():
            #     self._send_data(player.sock, self._sprites_to_send)
            sleep(1/30)


def main():
    server = Online_Game_Server(3333)
    server.mainloop()


if __name__ == "__main__":
    main()

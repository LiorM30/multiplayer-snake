import imp
import socket
import json
from time import sleep
import pygame
import logging
import argparse

from enums import Game_Object, Player_Command
from game_packet_API import Game_Packet, Game_Packet_Type
from snake_config import Snake_Config as Config
from assets.loaded_images import Loaded_Images


class Snake_Client:
    def __init__(self, server_ip, server_port) -> None:
        self._parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        self._parser.add_argument(
            '--log_level', action='store', type=int, default=20,
            help='Log level (50=Critical, 40=Error, 30=Warning ,20=Info ,10=Debug, 0=None)'
        )
        self._parser.add_argument(
            '--server_ip', action='store', type=str,
            default=socket.gethostbyname(socket.gethostname()),
            help='server IP, enter the desired server\'s IP address'
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

        #  -------------------

        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sock.connect((server_ip, server_port))
        self._logger.debug('Connected to server')

        self._username = input('enter your username:  ')
        self._send_data(
            Game_Packet(
                type=Game_Packet_Type.STANDARD_DATA,
                data={'username': self._username}
            )
        )

        while self._recieve_packet()['type'] != Game_Packet_Type.START_GAME:
            pass

        #  -------------------

        pygame.init()
        self._screen = pygame.display.set_mode(
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(Config.GAME_NAME)

        pygame.key.set_repeat()  # key events will not repeat while the key is pressed

        self._clock = pygame.time.Clock()

        self.image_loader = Loaded_Images()
        self.all_images = self.image_loader.all

        self._running = True

        player_sprite = pygame.image.load('assets\\player.png')
        player_sprite = pygame.transform.scale(
            player_sprite, (50, 50)
        )

        self._all_sprites = {
            Game_Object.Player: player_sprite
        }
        self.sprites_to_load = {}

    def mainloop(self):
        """
        The mainloop of the program, call to start it
        """
        while self._running:
            inputs = {  # all command types
                'move x': None,
                'move y': None,
                'status': None
            }
            # self._clock.tick(30)  # setting game FPS
            sleep(1/30)

            for event in pygame.event.get():
                # this one checks for the window being closed
                if event.type == pygame.QUIT:
                    inputs['status'] = Player_Command.QUIT
                    pygame.quit()

                if event.type == pygame.KEYDOWN:  # key-press events
                    match event.key:
                        case pygame.K_a:
                            inputs['move x'] = Player_Command.MOVE_LEFT
                        case pygame.K_d:
                            inputs['move x'] = Player_Command.MOVE_RIGHT
                        case pygame.K_w:
                            inputs['move y'] = Player_Command.MOVE_UP
                        case pygame.K_s:
                            inputs['move y'] = Player_Command.MOVE_DOWN
                        case pygame.K_ESCAPE:
                            inputs['status'] = Player_Command.QUIT
                if event.type == pygame.KEYUP:
                    match event.key:
                        case pygame.K_a:
                            inputs['move x'] = Player_Command.STOP_MOVE_LEFT
                        case pygame.K_d:
                            inputs['move x'] = Player_Command.STOP_MOVE_RIGHT
                        case pygame.K_w:
                            inputs['move y'] = Player_Command.STOP_MOVE_UP
                        case pygame.K_s:
                            inputs['move y'] = Player_Command.STOP_MOVE_DOWN

            if inputs['status'] == Player_Command.QUIT:  # if player quits, stop game
                self._running = False
            if not all(value is None for value in inputs.values()):
                self._send_data(
                    Game_Packet(
                        type=Game_Packet_Type.PLAYER_INPUTS,
                        data=inputs
                    )
                )

            self._request_sprites()
            self._screen.fill((0, 0, 0))
            self._render_sprites(self.sprites_to_load)
            pygame.display.flip()

    def _send_data(self, data: Game_Packet) -> None:
        """
        Sends data to the server
        The data is a dictionary of all inputs the player did
        ...
        :param data: the data to send
        """
        ser_data = json.dumps(vars(data))
        self.client_sock.send(ser_data.encode())

    def _render_sprites(self, sprites: list[tuple[Game_Object, tuple[int, int]]]) -> None:
        """
        Renders all sprites in the given list
        The list is a list of tuples with the object to render and its coords
        ...
        :param sprites: a list of all the sprites to draw on the screen and their coords
        """

        for sprite, coords in sprites:
            self._draw_object(sprite, coords)

    def _draw_object(self, object: Game_Object, coords: tuple[int, int]) -> None:
        """
        Draws the object at the given coords
        ...
        :param object: the object to load
        :param coords: the coords to draw it at
        """

        self._screen.blit(self._all_sprites[object], coords)

    def _request_sprites(self) -> None:
        """
        Sends the server a request for it to send the sprites to render
        puts those sprites in the sprites_to_load variable
        """

        self._send_data(
            Game_Packet(
                type=Game_Packet_Type.RECIEVE_SPRITES
            )
        )

        self.sprites_to_load = self._recieve_packet()['data']

    def _recieve_packet(self) -> Game_Packet:
        return json.loads(
            self.client_sock.recv(1024).decode()
        )


def main():
    client = Snake_Client('172.16.17.115', 3333)
    client.mainloop()


if __name__ == "__main__":
    main()

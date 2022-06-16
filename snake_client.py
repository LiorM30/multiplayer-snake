import socket
import json
from turtle import Screen
import pygame
import logging
import argparse

from enums import Direction, Game_Object, Player_Command, Color, \
    Player_State, Game_State
from game_packet_API import Game_Packet, Game_Packet_Type
from snake_config import Snake_Config as Config
from assets.loaded_images import Loaded_Images
from on_screen_text import On_Screen_Input


class Snake_Client:
    def __init__(self, server_port) -> None:
        self._parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        self._parser.add_argument(
            '--log_level', action='store', type=int, default=20,
            help='Log level (50=Critical, 40=Error, 30=Warning ,20=Info ,10=Debug, 0=None)'  # noqa
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
        self.client_sock.connect((self._args.server_ip, server_port))
        self._logger.debug('Connected to server')
        #  -------------------

        pygame.init()
        self._screen = pygame.display.set_mode(
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(Config.GAME_NAME)

        self._clock = pygame.time.Clock()

        self.game_keyboard = On_Screen_Input(self._screen)

        self._running = True
        self._game_is_done = False
        self._game_started = False
        self._player_won = False

        self._username = self.game_keyboard.get_input(
            length=10,
            color=Color.WHITE,
            x=int(Config.SCREEN_WIDTH / 2),
            y=int(Config.SCREEN_HEIGHT / 2),
            title_text='enter username:',
            BG_color=Color.BLACK
        )
        print(self._username)

        self._send_data(
            Game_Packet(
                type=Game_Packet_Type.STANDARD_DATA,
                data={'username': self._username}
            )
        )

        player_info = self._recieve_packet()
        self._client_ID = player_info.data['player ID']
        self._snake_color = player_info.data['player color']
        self._logger.debug(f'My ID is {self._client_ID}')
        self._logger.debug(f'My color is {self._snake_color}')

        self.image_loader = Loaded_Images()
        self._all_sprites = self.image_loader._all
        self._logger.debug('Ready')
        self._send_data(
            Game_Packet(
                type=Game_Packet_Type.PLAYER_READY
            )
        )

    def _drawGrid(self) -> None:
        """
        Draws the background grid
        """

        blockSize = Config.TILE_HEIGHT  # Set the size of the grid block
        for x in range(0, Config.SCREEN_WIDTH, blockSize):
            for y in range(0, Config.SCREEN_HEIGHT, blockSize):
                rect = pygame.Rect(x, y, blockSize, blockSize)
                pygame.draw.rect(self._screen, Color.WHITE.value, rect, 1)

    def mainloop(self):
        """
        The mainloop of the program, call to start it
        """

        # creating custom events names
        RENDER_GAME = pygame.USEREVENT + 1
        # setting event times
        pygame.time.set_timer(RENDER_GAME, Config.TIME_BETWEEN_SNAKE_UPDATES)
        while self._running:
            inputs = {  # all command types
                'change dir': None,
                'status': None
            }
            self._clock.tick(20)  # setting game FPS

            for event in pygame.event.get():
                # checks for the window being closed
                if event.type == pygame.QUIT:
                    inputs['status'] = Player_Command.QUIT
                    pygame.quit()
                    self._running = False

                elif event.type == RENDER_GAME:
                    if not self._game_started:
                        # before the game starts
                        # fill the screen with the player's color
                        self._screen.fill(self._snake_color)

                    elif self._game_is_done:
                        # if the game is done show if the player won
                        if self._player_won:
                            self.game_keyboard.render_text(
                                'you won!', Color.WHITE,
                                Config.SCREEN_HEIGHT / 2,
                                Config.SCREEN_WIDTH / 2
                            )
                        else:
                            self.game_keyboard.render_text(
                                'you lost!', Color.WHITE,
                                Config.SCREEN_HEIGHT / 2,
                                Config.SCREEN_WIDTH / 2
                            )

                    else:
                        game_state_pack = self._get_game_state()
                        # unpack the game state
                        sprites_to_load = game_state_pack.data['sprites']
                        player_state = game_state_pack.data['player state']
                        game_state = game_state_pack.data['game state']

                        self._screen.fill(Config.BGCOLOR)
                        if game_state == Game_State.DONE:
                            # since we render the game done text after the
                            # connection closed, we need to get that
                            # information in a game packet
                            self._game_is_done = True
                            if player_state == Player_State.WON:
                                self._player_won = True
                                self.game_keyboard.render_text(
                                    'you won!', Color.WHITE,
                                    Config.SCREEN_HEIGHT / 2,
                                    Config.SCREEN_WIDTH / 2
                                )
                                self._logger.debug('Player lost')
                            elif player_state == Player_State.LOST:
                                self.game_keyboard.render_text(
                                    'you lost!', Color.WHITE,
                                    Config.SCREEN_HEIGHT / 2,
                                    Config.SCREEN_WIDTH / 2
                                )
                                self._logger.debug('Player won')
                        else:
                            self._drawGrid()
                            self._render_sprites(sprites_to_load)

                    pygame.display.flip()

                elif event.type == pygame.KEYDOWN:  # key-press events
                    match event.key:
                        case pygame.K_a | pygame.K_LEFT:
                            inputs['change dir'] = Player_Command.MOVE_LEFT
                        case pygame.K_d | pygame.K_RIGHT:
                            inputs['change dir'] = Player_Command.MOVE_RIGHT
                        case pygame.K_w | pygame.K_UP:
                            inputs['change dir'] = Player_Command.MOVE_UP
                        case pygame.K_s | pygame.K_DOWN:
                            inputs['change dir'] = Player_Command.MOVE_DOWN
                        case pygame.K_ESCAPE:
                            inputs['status'] = Player_Command.QUIT

            if self._game_started and not self._game_is_done:
                # if player quits, stop game
                if inputs['status'] == Player_Command.QUIT:
                    self._running = False
                if not all(value is None for value in inputs.values()):
                    self._send_data(
                        Game_Packet(
                            type=Game_Packet_Type.PLAYER_INPUTS,
                            data=inputs
                        )
                    )
            if not self._game_started:
                if self._recieve_packet().type == Game_Packet_Type.START_GAME:
                    self._game_started = True

    def _send_data(self, data: Game_Packet) -> None:
        """
        Sends data to the server
        The data is a dictionary of all inputs the player did
        ...
        :param data: the data to send
        """

        ser_data = json.dumps(vars(data))
        self.client_sock.send(ser_data.encode())

    def _render_sprites(self, sprites: list[dict]) -> None:
        """
        Renders all sprites in the given list
        The list is a list of sprite wrappers
        ...
        :param sprites: a list of all the sprites to draw on the screen\
         and their coords
        """

        for sprite in sprites:
            if sprite['color']:
                sprite['color'] = tuple(sprite['color'])
            self._draw_object(
                sprite['object'],
                sprite['color'],
                sprite['coords'],
                sprite['direction']
            )

    def _draw_object(
        self,
        object: Game_Object,
        color: tuple[int, int, int],
        coords: tuple[int, int],
        direction: Direction
    ) -> None:
        """
        Draws the object at the given coords
        ...
        :param object: the object to load
        :param color: the color of the object, None for the default color
        :param coords: the coords to draw it at
        :param direction: the direction of the object
        """

        self._screen.blit(
            self.image_loader.get_image(object, color, direction),
            coords
        )

    def _get_game_state(self) -> Game_Packet:
        """
        Sends the server a request for it to send the sprites to render
        and returns the game state packet
        ...
        :returns: the current game state packet
        """

        self._send_data(
            Game_Packet(
                type=Game_Packet_Type.GAME_STATUS_REQUEST
            )
        )

        return self._recieve_packet()

    def _recieve_packet(self) -> Game_Packet:
        """
        Recieves a packet and returns it
        ...
        :return: the packet recieved
        """

        full_data = self.client_sock.recv(1024).decode()
        self.client_sock.settimeout(0.01)
        try:
            while True:
                full_data += self.client_sock.recv(1024).decode()
        except socket.timeout:  # no more data to recieve
            pass
        self.client_sock.settimeout(None)
        return Game_Packet(
            **json.loads(
                full_data
            )
        )


def main():
    client = Snake_Client(3333)
    client.mainloop()


if __name__ == "__main__":
    main()

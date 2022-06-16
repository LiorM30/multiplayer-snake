from enum import Enum
from dataclasses import dataclass


class Game_Packet_Type(str, Enum):
    GAME_STATUS_REQUEST = 'recieve sprites request'
    PLAYER_INPUTS = 'player inputs'
    GAME_STATUS = 'sprites to render'
    DONE_SENDING = 'done sending'
    START_GAME = 'start game'
    PLAYER_READY = 'player ready'
    PLAYER_INFO = 'player info'

    STANDARD_DATA = 'standard data'


@dataclass
class Game_Packet():
    type: Game_Packet_Type
    data: dict = None

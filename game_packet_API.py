from enum import Enum
from dataclasses import dataclass


class Game_Packet_Type(str, Enum):
    RECIEVE_SPRITES_REQUEST = 'recieve sprites request'
    PLAYER_INPUTS = 'player inputs'

    SPRITES_TO_RENDER = 'sprites to render'
    DONE_SENDING = 'done sending'
    START_GAME = 'start game'

    STANDARD_DATA = 'standard data'


@dataclass
class Game_Packet():
    type: Game_Packet_Type
    data: dict = None

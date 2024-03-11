"""A simple game engine for making command line games."""

from . import parser
from .command import Command, create_command
from .game import Game, GameConfig, create_game

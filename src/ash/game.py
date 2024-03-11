"""Game object for the game engine."""

from .parser import CommandParseError, CommandParser
from .command import Command

import asyncio
import typing
from collections import abc

import pydantic
import aioconsole


task_t = typing.Literal["pre_command", "post_command", "background"]


class GameConfig(typing.NamedTuple):
    """Configuration for the game engine.
    
    Attributes:
        background_delay (float): The delay between background tasks in seconds.
        show_help (bool): Whether to register a special command for showing the help message.
    """
    background_delay: float = 1.0
    show_help: bool = True


class Game[D: pydantic.BaseModel]:
    """Represents a game.

    Attributes:
        dataclass (type[D]): The dataclass type used for game data.
        config (GameConfig): The configuration for the game.
        commands (dict[str, Command[D, typing.Any]]): A dictionary of commands available in the game.
        tasks (dict[task_t, abc.Callable[[D], abc.Coroutine[None, None, None]]]): A dictionary of tasks in the game.
    """
    def __init__(self, dataclass: type[D], config: GameConfig) -> None:
        """Initializes a new instance of the Game class.

        Args:
            dataclass (type[D]): The dataclass type used for game data.
            config (GameConfig): The configuration for the game.

        Returns:
            None
        """
        self.dataclass = dataclass
        self.config = config

        self.commands: dict[str, Command[D, typing.Any]] = {}
        self.tasks: dict[task_t, abc.Callable[[D], abc.Coroutine[None, None, None]]] = {}
    
    def register_command[S: pydantic.BaseModel](self, name: str) -> abc.Callable[[Command[D, S]], Command[D, S]]:
        """Register a command with the given name.

        Args:
            name (str): The name of the command.

        Raises:
            ValueError: If show_help is True and name is "help", or if a command with the same name is already registered.

        Returns:
            abc.Callable[[Command[D, S]], Command[D, S]]: A decorator function that can be used to register the command.
        
        Example:
            ```python
            @game.register_command("test")
            @create_command(regex=r"(?P<param>\\w+)")
            class TestCommand(pydantic.BaseModel):
                param: str
            ```
        """
        if self.config.show_help and name == "help":
            raise ValueError("Cannot register a command named \"help\" when show_help is True.")
        elif name in self.commands:
            raise ValueError(f"Command with name \"{name}\" already registered.")
        def decorator(command: Command[D, S]) -> Command[D, S]:
            self.commands[name] = command
            return command
        return decorator
    
    def register_task(self, task_type: task_t) -> abc.Callable[[abc.Callable[[D], abc.Coroutine[None, None, None]]], abc.Callable[[D], abc.Coroutine[None, None, None]]]:
        """Registers a task of the given type.

        Args:
            task_type (task_t): The type of task to register.

        Returns:
            abc.Callable[[abc.Callable[[D], abc.Coroutine[None, None, None]]], abc.Callable[[D], abc.Coroutine[None, None, None]]]: A decorator function for registering the task.
        
        Example:
            ```python
            @game.register_task("background")
            async def background_task(data: D) -> None:
                # Task code here
                pass
            ```
        """
        def decorator(task: abc.Callable[[D], abc.Coroutine[None, None, None]]) -> abc.Callable[[D], abc.Coroutine[None, None, None]]:
            self.tasks[task_type] = task
            return task
        return decorator
    
    def help_message(self) -> str:
        """Returns the help message for the game.

        Returns:
            str: The help message for the game.
        """
        command_docs = {
            name: command.schema.__doc__ if not isinstance(command.schema.__doc__, type(None)) else "No description available."
            for name, command in self.commands.items()
        }
        t = " " * 4
        return f"Commands:{"".join([f"\n{t}{name}: {doc}" for name, doc in command_docs.items()])}"
    
    async def user_loop(self, data: D) -> None:
        """Asynchronous method that handles the user input loop.

        Args:
            data (D): The data object passed to the game.

        Returns:
            None
        """
        while True:
            uinput: list[str] = (await aioconsole.ainput("> ")).split(maxsplit=1)
            if len(uinput) > 0:
                if uinput[0] == "help" and self.config.show_help:
                    if len(uinput) > 1:
                        if uinput[1] in self.commands:
                            print(self.commands[uinput[1]].help_message())
                        else:
                            print(f"Command \"{uinput[1]}\" not found.")
                    else:
                        print(self.help_message())
                elif uinput[0] in self.commands:
                    command = self.commands[uinput[0]]
                    try:
                        params = command.parse(uinput[1] if len(uinput) > 1 else "")
                    except CommandParseError as e:
                        print(e)
                    else:
                        if "pre_command" in self.tasks:
                            await self.tasks["pre_command"](data)
                        await command.execute(data, params)
                        if "post_command" in self.tasks:
                            await self.tasks["post_command"](data)
                else:
                    print(f"Command \"{uinput[0]}\" not found.")
    
    async def background_loop(self, data: D) -> None:
        """Executes the background task in a loop.

        Args:
            data (D): The data to be passed to the background task.

        Returns:
            None
        """
        if "background" in self.tasks:
            while True:
                await self.tasks["background"](data)
                await asyncio.sleep(self.config.background_delay)
    
    async def run(self, data: D) -> None:
        """Runs the game with the given data.

        Args:
            data (D): The data to pass to the game.

        Returns:
            None
        """
        await asyncio.gather(self.user_loop(data), self.background_loop(data))


def create_game[D: pydantic.BaseModel](**kwargs) -> abc.Callable[[type[D]], Game[D]]:
    """Creates a game object with the given configuration from a dataclass.

    Args:
        **kwargs: The configuration for the game.

    Returns:
        abc.Callable[[type[D]], Game[D]]: A function that converts a dataclass into a game object.
    
    Example:
        ```python
        @create_game()
        class TestGame(pydantic.BaseModel):
            value: int = 0
        ```
    """
    def decorator(dataclass: type[D]) -> Game[D]:
        return Game(dataclass, GameConfig(**kwargs))
    return decorator

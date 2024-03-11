"""In-game commands for the game engine."""

from .parser import CommandParser, RegexCommandParser

import typing
from collections import abc

import pydantic


class Command[D: pydantic.BaseModel, S: pydantic.BaseModel]:
    """Represents an in-game command.

    Attributes:
        schema (type[S]): The schema class for validating the command parameters.
        parser (CommandParser): The parser used to parse the command parameters.
        action (Optional[Callable[[D, S], Coroutine[None, None, None]]]): The action to be executed when the command is executed.
    """
    def __init__(self, schema: type[S], parser: CommandParser) -> None:
        """Initializes a Command object.

        Args:
            schema (type[S]): The schema type for the command.
            parser (CommandParser): The parser for the command.

        Returns:
            None
        """
        self.schema = schema
        self.parser = parser

        self.action: typing.Optional[abc.Callable[[D, S], abc.Coroutine[None, None, None]]] = None
    
    def register_action(self) -> abc.Callable[[abc.Callable[[D, S], abc.Coroutine[None, None, None]]], abc.Callable[[D, S], abc.Coroutine[None, None, None]]]:
        """Registers the action for the command.

        Returns:
            Callable[[Callable[[D, S], Coroutine[None, None, None]]], Callable[[D, S], Coroutine[None, None, None]]]: A decorator for registering the action.

        Example:
            ```python
            @command.register_action()
            async def action(data: D, data: S) -> None:
                # Action code here
                pass
            ```
        """
        def decorator(action: abc.Callable[[D, S], abc.Coroutine[None, None, None]]) -> abc.Callable[[D, S], abc.Coroutine[None, None, None]]:
            self.action = action
            return action
        return decorator
    
    def parse(self, command: str) -> S:
        """Parses the command into a schema object.

        Args:
            command (str): The command to parse.

        Returns:
            S: The parsed schema object.
        """
        return self.parser.parse(self.schema, command)
    
    def help_message(self) -> str:
        """Returns the help message for the command.

        Returns:
            str: The help message for the command.
        """
        command_doc = self.action.__doc__ if not isinstance(self.action, type(None)) else "No description available."
        param_docs = {
            name: field.description if not isinstance(field.description, type(None)) else "No description available."
            for name, field in self.schema.model_fields.items()
        }
        t = " " * 4
        return f"{command_doc}\n\nUsage:\n{t}{self.parser.help_message()}\n\nParameters:{"".join([f"\n{t}{name}: {doc}" for name, doc in param_docs.items()])}"
    
    async def execute(self, data: D, params: S) -> None:
        """Executes the command action.

        Args:
            data (D): The data to pass to the action.
            schema (S): The schema object to pass to the action.

        Returns:
            None
        """
        if not isinstance(self.action, type(None)):
            await self.action(data, params)


def create_command[S: pydantic.BaseModel](parser: typing.Optional[CommandParser] = None, *, regex: typing.Optional[str] = None) -> abc.Callable[[type[S]], Command[typing.Any, S]]:
    """Creates command objects from schema classes.

    Args:
        parser (CommandParser, optional): The parser to use for parsing command arguments. If not provided, a RegexCommandParser will be used if `regex` is provided.
        regex (str, optional): The regular expression pattern to use for parsing command arguments. Only used if `parser` is not provided.

    Returns:
        Callable[[type[S]], Command[typing.Any, S]]: A decorator function that can be used to create commands objects.

    Raises:
        ValueError: If neither `parser` nor `regex` is provided.

    Example usage:
        ```python
        @create_command(regex=r"(?P<param>\\w+)")
        class TestCommand(pydantic.BaseModel):
            param: str
        ```
    """
    if isinstance(parser, type(None)):
        if isinstance(regex, type(None)):
            raise ValueError("Either parser or regex must be provided.")
        parser = RegexCommandParser(regex)
    def decorator(schema: type[S]) -> Command[typing.Any, S]:
        return Command(schema, parser)
    return decorator

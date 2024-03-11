"""Command parsers for the game engine."""

import types
import typing

import pydantic
import regex


class CommandParseError(Exception):
    """Raised when a command fails to parse."""


class CommandParser:
    """A class for parsing commands using a specified schema."""
    def parse[S: pydantic.BaseModel](self, schema: type[S], command: str) -> S:
        """Parses the given command using the specified schema.

        Args:
            schema (type[S]): The schema to use for parsing.
            command (str): The command to parse.

        Returns:
            S: The parsed object of type S.

        Raises:
            CommandParseError: Raised when the command fails to parse.
        """
        raise NotImplementedError()
    
    def help_message(self) -> str:
        """Returns a help message for the parser.

        Returns:
            str: The help message.
        """
        return "No help message available."


class RegexCommandParser(CommandParser):
    """A parser that uses regular expressions to parse commands.
    
    Attributes:
        pattern (str): The regular expression pattern to be used by the parser.
        cpattern (regex.Pattern): The compiled regular expression pattern to be used by the parser.
    """
    def __init__(self, pattern: str) -> None:
        """Initializes a Parser object with the given pattern.

        Args:
            pattern (str): The regular expression pattern to be used by the parser.

        Returns:
            None
        """
        self.pattern = pattern
        self.cpattern = regex.compile(pattern)
    
    def type_is_list(self, t: typing.Any) -> bool:
        """Returns True if the given type is a list type, False otherwise.

        Args:
            t (typing.Any): The type to check.

        Returns:
            bool: True if the given type is a list type, False otherwise.
        """
        return t is list or (isinstance(t, types.GenericAlias) and t.__origin__ is list)
    
    def parse[S: pydantic.BaseModel](self, schema: type[S], command: str) -> S:
        match = self.cpattern.fullmatch(command)
        if isinstance(match, type(None)):
            raise CommandParseError(f"Command does not match pattern: {self.pattern}")
        params = {
            name: match.captures(name) if self.type_is_list(field.annotation) else match.group(name)
            for name, field in schema.model_fields.items() if name in match.groupdict()
        }
        try:
            return schema.model_validate(params)
        except pydantic.ValidationError as e:
            raise CommandParseError(f"Parameters failed to validate.") from e
    
    def help_message(self) -> str:
        return f"Pattern: {self.pattern}"

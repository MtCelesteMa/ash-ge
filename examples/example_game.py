"""Example game created using ASH."""

import asyncio

import ash
import pydantic


# Create the game object
@ash.create_game()
class ExampleGame(pydantic.BaseModel):
    timer: int = 0
    n_actions: int = 0
    counter: int = 0


# Register tasks
@ExampleGame.register_task("background")
async def background_task(data: ExampleGame.dataclass) -> None:
    data.timer += 1


@ExampleGame.register_task("pre_command")
async def pre_command_task(data: ExampleGame.dataclass) -> None:
    data.n_actions += 1


# Register commands
@ExampleGame.register_command("add")
@ash.create_command(regex=r"(?P<value>[\d-]+)")
class AddCommand(pydantic.BaseModel):
    """A command to add a value to the counter."""
    value: int = pydantic.Field(description="The value to add to the counter.")


@AddCommand.register_action()
async def add_action(data: ExampleGame.dataclass, params: AddCommand.schema) -> None:
    """Adds the value to the counter."""
    data.counter += params.value


@ExampleGame.register_command("add-multiple")
@ash.create_command(regex=r"(?:(?P<values>[\d-]+)\s{0,1})+")
class AddMultipleCommand(pydantic.BaseModel):
    """A command to add multiple values to the counter."""
    values: list[int] = pydantic.Field(description="The values to add to the counter.")


@AddMultipleCommand.register_action()
async def addmul_action(data: ExampleGame.dataclass, params: AddMultipleCommand.schema) -> None:
    """Adds the values to the counter."""
    data.counter += sum(params.values)


@ExampleGame.register_command("view")
@ash.create_command(regex=r"(?P<value>counter|timer|n_actions)")
class ViewCommand(pydantic.BaseModel):
    """A command to view a value."""
    value: str = pydantic.Field(description="The value to view. Can be \"counter\", \"timer\", or \"n_actions\".")


@ViewCommand.register_action()
async def view_action(data: ExampleGame.dataclass, params: ViewCommand.schema) -> None:
    """Views the value."""
    print(getattr(data, params.value))


if __name__ == "__main__":
    # Run the game
    data = ExampleGame.dataclass()
    
    asyncio.run(ExampleGame.run(data))

from argparse import ArgumentParser, Namespace

from pydantic import BaseModel


class SubcommandRecordArguments(BaseModel):
    pass


async def subcommand_record(args: SubcommandRecordArguments) -> None:
    pass


async def execute_subcommand_record(
    args: Namespace,
) -> None:
    await subcommand_record(
        args=SubcommandRecordArguments(),
    )


async def add_arguments_subcommand_record(
    parser: ArgumentParser,
) -> None:
    parser.set_defaults(handler=execute_subcommand_record)

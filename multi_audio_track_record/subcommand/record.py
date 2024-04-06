from argparse import ArgumentParser, Namespace

from pydantic import BaseModel


class SubcommandRecordArguments(BaseModel):
    pass


def subcommand_record(args: SubcommandRecordArguments) -> None:
    pass


def execute_subcommand_record(
    args: Namespace,
) -> None:
    subcommand_record(
        args=SubcommandRecordArguments(),
    )


def add_arguments_subcommand_record(
    parser: ArgumentParser,
) -> None:
    parser.set_defaults(handler=execute_subcommand_record)

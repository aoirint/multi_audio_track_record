import asyncio
import logging
from argparse import ArgumentParser
from logging import getLogger

from . import __version__ as APP_VERSION
from .subcommand.record import add_arguments_subcommand_record

logger = getLogger(__name__)


async def main() -> None:
    parser = ArgumentParser(
        prog="MultiAudioTrackRecorder",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {APP_VERSION}",
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s : %(message)s",
    )

    subparsers = parser.add_subparsers()

    subparser_record = subparsers.add_parser("record")
    await add_arguments_subcommand_record(parser=subparser_record)

    args = parser.parse_args()
    if hasattr(args, "handler"):
        handler = args.handler
        if asyncio.iscoroutine(handler):
            await handler(args)
        else:
            handler(args)
    else:
        parser.print_help()

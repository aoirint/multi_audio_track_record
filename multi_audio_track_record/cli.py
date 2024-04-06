import logging
from argparse import ArgumentParser
from logging import getLogger

from . import __version__ as APP_VERSION

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

    args = parser.parse_args()
    if hasattr(args, "handler"):
        args.handler(args)
    else:
        parser.print_help()

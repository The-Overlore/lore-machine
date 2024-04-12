import argparse
import logging
import os
from logging import Handler
from typing import Optional, cast

from dotenv import load_dotenv

from overlore.types import EnvVariables


def setup_logging(log_to_file: Optional[str] = None) -> None:
    logger = logging.getLogger("overlore")
    logger.setLevel(logging.DEBUG)  # Set the logging level

    # Create a formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Check if handlers already exist for this logger
    if logger.hasHandlers():
        logger.handlers.clear()  # Clear existing handlers

    handler: Handler
    if log_to_file is not None:
        # Create a file handler and set the level to debug
        handler = logging.FileHandler(log_to_file)
    else:
        # Create a console handler and set the level to debug
        handler = logging.StreamHandler()

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    logger.propagate = False


class BootConfig:
    # CLI Argument
    world_db: str
    prod: bool

    # .env variables
    env: EnvVariables

    def __init__(self) -> None:
        self._get_args()
        self._load_env_variables()

    def _get_args(self) -> None:
        parser = argparse.ArgumentParser(
            description="The weaving loomer of all possible actual experiential occasions."
        )
        parser.add_argument(
            "--prod",
            action="store_true",
            help="Run lore-machine in production mode.",
        )
        parser.add_argument("-w", "--world_db", help="location of the world db", type=str, default="/litefs/world.db")
        parser.add_argument("-l", "--logging_file", help="location of the logging file", type=str)
        args = parser.parse_args()
        setup_logging(args.logging_file)

        self.world_db = args.world_db
        self.prod = args.prod

    def _load_env_variables(self) -> None:
        dotenv_path = ".env.production" if self.prod is True else ".env.development"
        load_dotenv(dotenv_path=dotenv_path)
        keys = EnvVariables.__annotations__.keys()
        try:
            self.env = cast(EnvVariables, {var: os.environ[var] for var in keys})
        except KeyError as e:
            raise RuntimeError("Failed to gather env variables from .env: ", e) from e

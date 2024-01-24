import argparse
import logging
import os
from logging import Handler
from typing import Optional

from dotenv import load_dotenv


def setup_logging(log_to_file: Optional[str] = None) -> None:
    logger = logging.getLogger("overlore")
    logger.setLevel(logging.DEBUG)  # Set the logging level

    # Create a formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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


class Config:
    # CLI Argument
    address: str
    port: int
    world_db: str
    prod: bool
    mock: bool
    prompt_loop: bool

    # .env variables
    OPENAI_API_KEY: str
    TORII_WS: str
    TORII_GRAPHQL: str
    KATANA_URL: str

    def __init__(self) -> None:
        self._get_args()
        self._load_env_variables()

    def _get_args(self) -> None:
        parser = argparse.ArgumentParser(
            description="The weaving loomer of all possible actual experiential occasions."
        )
        parser.add_argument(
            "--mock",
            action="store_true",
            help="Use mock data for GPT response instead of querying the API. (saves API calls)",
        )
        parser.add_argument(
            "--prompt-loop",
            action="store_true",
            help="Run lore-machine in a prompt testing loop.",
        )
        parser.add_argument(
            "--prod",
            action="store_true",
            help="Run lore-machine in production mode.",
        )
        parser.add_argument("-a", "--address", help="Host address for ws connection", type=str, default="localhost")
        parser.add_argument("-p", "--port", help="Host port for ws connection", type=int, default=8766)
        parser.add_argument("-w", "--world_db", help="location of the world db", type=str, default="/litefs/world.db")
        parser.add_argument("-l", "--logging_file", help="location of the logging file", type=str)
        args = parser.parse_args()
        setup_logging(args.logging_file)

        self.address = args.address
        self.port = args.port
        self.world_db = args.world_db
        self.prod = args.prod
        self.mock = args.mock
        self.prompt_loop = args.prompt_loop

    def _load_env_variables(self) -> None:
        self._get_args()

        dotenv_path = ".env.production" if self.prod is True else ".env.development"
        load_dotenv(dotenv_path=dotenv_path)

        tmp_torii_ws = os.environ.get("TORII_WS")
        tmp_torii_graphql = os.environ.get("TORII_GRAPHQL")
        tmp_katana_url = os.environ.get("KATANA_URL")
        self.OPENAI_API_KEY = (
            "OpenAI API Key" if os.environ.get("OPENAI_API_KEY") is None else str(os.environ.get("OPENAI_API_KEY"))
        )

        if tmp_torii_ws is None or tmp_torii_graphql is None or tmp_katana_url is None:
            raise RuntimeError("Required URLs not provided in .env file.")

        self.TORII_WS = str(tmp_torii_ws)
        self.TORII_GRAPHQL = str(tmp_torii_graphql)
        self.KATANA_URL = str(tmp_katana_url)

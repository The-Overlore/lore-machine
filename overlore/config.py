import argparse
import os

from dotenv import load_dotenv


class Config:
    # CLI Argument
    address: str
    port: int
    world_db: str
    prod: bool
    mock: bool

    # .env variables
    OPENAI_API_KEY: str
    TORII_WS: str
    TORII_GRAPHQL: str
    KATANA_URL: str

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
            "--prod",
            action="store_true",
            help="Run lore-machine in production mode.",
        )
        parser.add_argument("-a", "--address", help="Host address for ws connection", type=str, default="localhost")
        parser.add_argument("-p", "--port", help="Host port for ws connection", type=int, default=8766)
        parser.add_argument("-w", "--world_db", help="location of the world db", type=str, default="/litefs/world.db")

        args = parser.parse_args()

        self.address = args.address
        self.port = args.port
        self.world_db = args.world_db
        self.prod = args.prod
        self.mock = args.mock

    def load(self) -> None:
        self._get_args()

        dotenv_path = ".env.production" if self.prod is True else ".env.development"
        load_dotenv(dotenv_path=dotenv_path)

        tmp_torii_ws = os.environ.get("TORII_WS")
        tmp_torii_graphql = os.environ.get("TORII_GRAPHQL")
        tmp_katana_url = os.environ.get("KATANA_URL")
        self.OPENAI_API_KEY = (
            "OpenAI API Key" if os.environ.get("OPENAI_API_KEY") is None else str(os.environ.get("OPENAI_API_KEY"))
        )

        if tmp_torii_ws is None:
            raise RuntimeError("Failure to provide WS url")
        if tmp_torii_graphql is None:
            raise RuntimeError("Failure to provide graphql url")
        if tmp_katana_url is None:
            raise RuntimeError("Failure to provide katana url")

        self.TORII_WS = tmp_torii_ws
        self.TORII_GRAPHQL = tmp_torii_graphql
        self.KATANA_URL = tmp_katana_url

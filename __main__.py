import os
import sys
import json
from cli import BrushCli
from canvasbrush import Brush
from dotenv import load_dotenv

load_dotenv()

program_name = "brush"


def err(message: str):
    return f"{program_name}: {message}"


if __name__ == "__main__":
    args = BrushCli.parser_init(program_name)

    API_URL = os.environ.get("CANVAS_API_URL")
    API_KEY = os.environ.get("CANVAS_API_KEY")

    path_to_config = f"{os.path.dirname(__file__)}/brush.config.json"
    if not os.path.exists(path_to_config):
        config = {}
    else:
        with open(path_to_config, "r") as f:
            config = json.load(f)

    if not API_URL:
        sys.exit(err('you must set the "CANVAS_API_URL" environment variable'))

    if not API_KEY:
        sys.exit(err('you must set the "CANVAS_API_KEY" environment variable'))

    args.func(args, Brush(API_URL, API_KEY, config))

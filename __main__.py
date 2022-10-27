import os
import sys
import json
from cli import BrushCli
from canvasbrush import Brush
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

console = Console(highlight=False, stderr=True)

program_name = "brush"


def err(message: str):
    return f"{program_name}: {message}"


if __name__ == "__main__":
    args = BrushCli.parser_init(program_name)

    userpath = os.environ.get("BRUSH_CONFIG_PATH")
    CONFIG_PATH = (
        userpath if userpath else os.path.join(os.path.expanduser("~"), ".brushrc")
    )
    API_URL = os.environ.get("CANVAS_API_URL")
    API_KEY = os.environ.get("CANVAS_API_KEY")

    if not os.path.exists(CONFIG_PATH):
        fallback = os.path.join(os.path.expanduser("~"), ".brushrc")

        if CONFIG_PATH != os.path.join(
            os.path.expanduser("~"), ".brushrc"
        ) and os.path.exists(fallback):
            console.print(
                f"[bold yellow]WARNING:[/bold yellow] A configuration file does not exist at [bold blue]{CONFIG_PATH}[/bold blue], falling back to [bold blue]~/.brushrc[/bold blue]."
            )

            with open(fallback, "r") as f:
                config = json.load(f)
        else:
            console.print(
                "[bold yellow]WARNING:[/bold yellow] Brush is running with no configuration. Create a configuration file at [bold blue]~/.brushrc[/bold blue], or set the [bold blue]BRUSH_CONFIG_PATH[/bold blue] environment variable to a path to a configuration file."
            )
            config = {}
    else:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

    if not API_URL:
        sys.exit(err('you must set the "CANVAS_API_URL" environment variable'))

    if not API_KEY:
        sys.exit(err('you must set the "CANVAS_API_KEY" environment variable'))

    args.func(args, Brush(API_URL, API_KEY, config))

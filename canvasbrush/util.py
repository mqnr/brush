import re
from canvasapi.assignment import Assignment


class AssignmentPlusFile:
    def __init__(self, assignment: Assignment, file_path: str):
        self.assignment = assignment
        self.file_path = file_path


class ProgressBar:
    """A utility progress bar class."""

    def __init__(
        self,
        total: int,
        percentage=True,
        left_text: str = "Progress:",
        right_text: str = None,
        bar_length: int = 20,
    ):
        """Constructor for the progress bar class."""
        self.total = total
        self.percentage = percentage
        self.left_text = left_text
        self.right_text = right_text
        self.bar_length = bar_length

    def update(self, current: int):
        """Updates and prints the progress bar."""
        fraction = current / self.total

        arrow = int(fraction * self.bar_length - 1) * "=" + ">"
        padding = int(self.bar_length - len(arrow)) * " "

        ending = "\n" if current == self.total else "\r"

        if not self.right_text:
            progress_text = (
                f"{int(fraction*100)}%"
                if self.percentage
                else f"{current}/{self.total}"
            )
        else:
            progress_text = (
                self.right_text.replace("(PERCENTAGE)", f"{int(fraction*100)}")
                if self.percentage
                else self.right_text.replace("(CURRENT)", f"{current}").replace(
                    "(TOTAL)", f"{self.total}"
                )
            )

        print(f"{self.left_text} [{arrow}{padding}] {progress_text}", end=ending)


def lower_remove_prefixes(filename: str, variations: list[str]):
    s = filename.lower()
    for variation in variations:
        s = s.removeprefix(variation)

    return s


def is_integer(n: int | float):
    if isinstance(n, int):
        return True
    if isinstance(n, float):
        return n.is_integer()
    return False


def to_num(s: str):
    if not s:
        return s

    if s.isdigit():
        return int(s)
    else:
        return float(s)


def number_from_end(s: str):
    try:
        return int(next(re.finditer(r"\d+$", s)).group(0))
    except Exception:
        raise ValueError("no numbers from end of string")

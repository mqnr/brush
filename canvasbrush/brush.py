import re
from canvasapi import Canvas
from canvasapi.course import Course
from canvasbrush.util import (
    AssignmentPlusFile,
    lower_remove_prefixes,
    number_from_end,
)
from canvasbrush.uploader import Uploader


class Brush(Canvas):
    def __init__(self, api_url: str, api_key: str, config={}):
        super().__init__(api_url, api_key)
        self.student_name: str = config["student_name"]
        self.course_map: list = config["course_map"]

    def student_name_variations(self):
        name = self.student_name.lower()
        return [
            name,
            name.replace(" ", ""),
            name.replace(" ", "_"),
            name.replace(" ", "-"),
        ]

    def resolve_course(self, course_string: str):
        """Resolves a course ID from a user-provided string."""
        for course in self.course_map:
            if course_string.lower() in course["aliases"]:
                return self.get_course(course["id"])

        raise ValueError("invalid course provided")

    def resolve_course_from_filename(self, filename: str):
        split = re.split(
            "-|_|\.",
            lower_remove_prefixes(
                filename, self.student_name_variations() + ["-", "_"]
            ),
        )

        course = self.resolve_course(split[0])

        return course

    def resolve_assignment(self, course: Course, tokens: list[str]):
        is_al_previous = False
        is_previous = False
        first_round = []
        second_round = []
        operative = ""

        if len(tokens) == 0:
            raise ValueError("empty string passed for assignment ID resolution")

        last_token = tokens[len(tokens) - 1]

        if tokens[0].startswith("act"):
            for assignment in course.get_assignments(include=["submission"]):
                split = assignment.name.lower().split()
                if split[0] == "activity" or split[0] == "actividad":
                    operative = tokens[0]
                    first_round.append(assignment)
        elif tokens[0].startswith("exc"):
            for assignment in course.get_assignments(include=["submission"]):
                split = assignment.name.lower().split()
                if split[0] == "exercise" or split[0] == "exc":
                    operative = tokens[0]
                    first_round.append(assignment)
        elif tokens[0].startswith("rto"):
            for assignment in course.get_assignments(include=["submission"]):
                split = assignment.name.lower().split()
                if split[0] == "challenge" or split[0] == "ch":
                    operative = tokens[0]
                    first_round.append(assignment)
        elif tokens[0].startswith("evi"):
            for assignment in course.get_assignments(include=["submission"]):
                split = assignment.name.lower().split()
                if split[0] == "evidence" or split[0] == "evi" or split[0] == "evc":
                    operative = tokens[0]
                    first_round.append(assignment)

        if not operative or last_token == "noassump":
            look_for = (
                " ".join(tokens).lower()
                if last_token != "noassump"
                else " ".join(tokens[:-1]).lower()
            )

            for assignment in course.get_assignments(include=["submission"]):
                if look_for in assignment.name.lower():
                    return assignment

            raise ValueError("no valid assignment was found for string")

        for candidate in first_round:
            split = candidate.name.lower().split()[:-1]

            splitwork = " ".join(split)
            if "prev" in tokens:
                if "previous" in splitwork or "previus" in splitwork:
                    if (
                        "previous to topic" in splitwork
                        or "previus to topic" in splitwork
                    ):
                        second_round.append(candidate)
                        is_al_previous = True
                    else:
                        second_round.append(candidate)
                        is_previous = True
            else:
                if "previous" in splitwork or "previus" in splitwork:
                    pass
                else:
                    second_round.append(candidate)
                    is_previous = False

        for candidate in second_round:
            split = candidate.name.lower().split()[1:]

            if is_previous:
                sub_split = split[1:]
            elif is_al_previous:
                sub_split = split[3:]
            else:
                sub_split = split[:]

            if len(sub_split) > 0:
                try:
                    if number_from_end(operative) == int(
                        re.sub("[^0-9]", "", sub_split[0])
                    ):
                        return candidate
                except ValueError:
                    pass

        raise ValueError("no valid assignment was found winner for string")

    def resolve_assignment_from_filename(self, filename: str, course: Course = None):
        split = re.split(
            "-|_|\.",
            lower_remove_prefixes(
                filename, self.student_name_variations() + ["-", "_"]
            ),
        )[1:][:-1]

        if not course:
            course = self.resolve_course_from_filename(filename)

        return self.resolve_assignment(course, split)

    def bulk_submit(self, assignments: list[AssignmentPlusFile], comment: str):
        """Submit files to Canvas in bulk."""
        blacklisted: list[AssignmentPlusFile] = []
        pairings: list[list[AssignmentPlusFile]] = []

        for i, upper in enumerate(assignments):
            if len(blacklisted) == len(assignments):
                break

            if not upper in blacklisted:
                pair = [upper]
                for j, lower in enumerate(assignments):
                    if not lower in blacklisted:
                        if (
                            upper.assignment.course_id == lower.assignment.course_id
                            and upper.assignment.id == lower.assignment.id
                            and i != j
                        ):
                            pair.append(lower)
                            blacklisted.append(lower)
                pairings.append(pair)
                blacklisted.append(upper)

        for pair in pairings:
            ids = []
            for apf in pair:
                id = Uploader(
                    apf.assignment._requester,
                    f"courses/{apf.assignment.course_id}/assignments/{apf.assignment.id}/submissions/self/files",
                    apf.file_path,
                    submit_assignment=False,
                ).start()

                ids.append(id[1]["id"])

                yield id

            yield (
                pair[0].assignment.submit(
                    {
                        "submission_type": "online_upload",
                        "file_ids": ids,
                    },
                    None,
                    **{"comment[text_comment]": comment},
                )
                if comment
                else pair[0].assignment.submit(
                    {
                        "submission_type": "online_upload",
                        "file_ids": ids,
                    }
                )
            )

        yield True

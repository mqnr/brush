import argparse
import re
import validators
import os
import sys
from datetime import datetime
from canvasbrush import Brush
from canvasbrush.util import AssignmentPlusFile, ProgressBar, is_integer, to_num
import argparse
from canvasapi.assignment import Assignment
from canvasapi.course import Course
from pathlib import Path
from rich.console import Console

from cli.due_info import DueInfo

console = Console(highlight=False)


class BrushCli:
    @staticmethod
    def parser_init(program_name: str):
        """Initializes the parser and returns the arguments."""
        parser = argparse.ArgumentParser(prog=program_name)
        subparsers = parser.add_subparsers(
            title="subcommands", help="valid subcommands", required=True
        )

        # create parser for assignments command
        parser_assignments = subparsers.add_parser(
            "assignments", help="view and manage assignments"
        )
        parser_assignments.add_argument(
            "course", type=str, nargs="+", help="the course to view assignments for"
        )
        parser_assignments.add_argument(
            "--order-by",
            type=str,
            help="how to order the assignments. accepted values: position, name, due_at",
        )
        parser_assignments.set_defaults(func=BrushCli.list_assignments)

        # create parser for assignment command
        parser_assignment = subparsers.add_parser(
            "assignment", help="view and manage a single assignment"
        )
        parser_assignment.add_argument(
            "assignment", type=str, nargs="+", help="the assignment to view"
        )
        parser_assignment.add_argument(
            "--course", "-c", type=str, help="the course to view an assignment for"
        )
        parser_assignment.set_defaults(func=BrushCli.view_assignment)

        # create parser for submit command
        parser_submit = subparsers.add_parser("submit", help="submit to an assignment")
        parser_submit.add_argument(
            "files_or_urls", type=str, nargs="+", help="the files to submit"
        )
        parser_submit.add_argument(
            "--course", "-c", type=str, help="the course to upload to"
        )
        parser_submit.add_argument(
            "--assignment", "-a", type=str, help="assignment to upload to"
        )
        parser_submit.add_argument(
            "--comment",
            "-C",
            type=str,
            help="the comment to go with the submission, if any",
        )
        parser_submit.add_argument(
            "--type", "-t", type=str, help="the submission type to make"
        )
        parser_submit.add_argument(
            "--skip-bad-arguments",
            action=argparse.BooleanOptionalAction,
            help="silently ignore bad arguments. default: FALSE",
        )
        parser_submit.add_argument(
            "--allow-resubmit",
            action=argparse.BooleanOptionalAction,
            help="allow resubmitting to assignments. default: TRUE",
        )
        parser_submit.add_argument(
            "--allow-submit-directories",
            action=argparse.BooleanOptionalAction,
            help="allow the submission of directories. default: FALSE",
        )
        parser_submit.add_argument(
            "--zip-directories",
            action=argparse.BooleanOptionalAction,
            help="zip directories instead of submitting the files within them. default: FALSE",
        )
        parser_submit.add_argument(
            "--recursive",
            "-R",
            action=argparse.BooleanOptionalAction,
            help="recursively search directories. default: FALSE",
        )
        parser_submit.set_defaults(func=BrushCli.upload)

        return parser.parse_args()

    @staticmethod
    def derive_grade_string(
        brush: Brush, assignment: Assignment, course: Course = None
    ):
        submission = assignment.submission
        grade = submission["grade"] if submission["grade"] else None
        grade = (
            to_num(grade[:-1])
            if assignment.grading_type == "percent"
            else to_num(grade)
        )

        if "online_quiz" in assignment.submission_types:
            if grade or grade == 0:
                course = course if course else brush.get_course(assignment.course_id)
                quiz = course.get_quiz(assignment.quiz_id)
                total = quiz.points_possible

                grade_cmp = grade / total * 100

                total = int(total) if is_integer(total) else total
                grade = int(grade) if is_integer(grade) else grade

                internal_grade_string = (
                    f"{grade}/{total}"
                    if assignment.grading_type != "percent"
                    else f"{grade}%"
                )

                if grade_cmp < 70:
                    grade_string = (
                        f" [bold red](Grade: {internal_grade_string})[/bold red]"
                    )
                else:
                    grade_string = (
                        f" [bold green](Grade: {internal_grade_string})[/bold green]"
                        if grade_cmp >= 90
                        else f" [bold yellow](Grade: {grade}/{total})[/bold yellow]"
                    )
            else:
                grade_string = ""
        else:
            if grade or grade == 0:
                grade = int(grade) if is_integer(grade) else grade

                internal_grade_string = (
                    f"{grade}" if assignment.grading_type != "percent" else f"{grade}%"
                )

                if grade < 70:
                    grade_string = (
                        f" [bold red](Grade: {internal_grade_string})[/bold red]"
                    )
                else:
                    grade_string = (
                        f" [bold green](Grade: {internal_grade_string})[/bold green]"
                        if grade >= 90
                        else f" [bold yellow](Grade: {internal_grade_string})[/bold yellow]"
                    )
            else:
                grade_string = ""

        return grade_string

    @staticmethod
    def view_assignment(args: argparse.Namespace, brush: Brush):
        try:
            course = (
                brush.resolve_course(args.course)
                if args.course
                else brush.resolve_course(args.assignment[0])
            )
        except Exception as e:
            if "invalid course provided" in str(e):
                sys.exit(
                    f'No course was found for your search: "{"".join(args.course if args.course else args.assignment[0])}".'
                )
            else:
                sys.exit(f"Brush encountered an error while getting the course: {e}")

        assignment_string = (
            args.assignment + ["noassump"]
            if args.course
            else args.assignment[1:] + ["noassump"]
        )
        try:
            assignment = brush.resolve_assignment(course, assignment_string)
        except Exception as e:
            if "no valid assignment was found for string" in str(e):
                sys.exit(
                    f'No assignment was found for your search: "{" ".join(args.assignment[1:] if not args.course else args.assignment)}".'
                )
            else:
                sys.exit(
                    f"Brush encountered an error while getting the assignment: {e}"
                )

        grade_string = BrushCli.derive_grade_string(brush, assignment, course)
        dinfo = DueInfo(assignment.due_at, "America/Hermosillo")

        locked_info = (
            f"🔒 {assignment.lock_explanation}"
            if assignment.locked_for_user
            else "🔓 Open"
        )
        due_string = (
            f"📅🚫 No due date" if not assignment.due_at else f"📅 Due for {dinfo}"
        )

        overdue = (
            f"[red]OVERDUE[/red] "
            if dinfo.exists
            and datetime.now().astimezone() > dinfo.object
            and assignment.submission["workflow_state"] == "unsubmitted"
            and not assignment.locked_for_user
            else ""
        )

        match assignment.submission["workflow_state"]:
            case "submitted":
                submission_state = f"✅ Submitted {assignment.submission['submitted_at']}\n    Your submission is waiting to be graded"
            case "unsubmitted":
                submission_state = "❌ Not submitted"
            case "graded":
                submission_state = (
                    f"✅ Submitted {assignment.submission['submitted_at']}"
                )
            case "pending_review":
                submission_state = "Your submission is pending review"
            case _:
                submission_state = "⚠ Submission data invalid"

        console.print(
            f"""{overdue}[bold]{assignment.name}[/bold]{grade_string}
{locked_info}
{due_string}
    {submission_state}"""
        )

    @staticmethod
    def list_assignments(args: argparse.Namespace, brush: Brush):
        course = brush.resolve_course(" ".join(args.course))

        normalized = ""
        include_order_by = False
        if isinstance(args.order_by, str):
            if (
                (normalized := re.sub(r"\s+", "_", args.order_by).lower()) == "position"
                or normalized == "name"
                or "due" in normalized
            ):
                if "due" in normalized:
                    normalized = "due_at"
                include_order_by = True
            else:
                raise ValueError(
                    f'invalid value for order_by: {args.order_by}. valid values: "position", "name", "due_at"'
                )

        kw = (
            {"include": ["submission"], "order_by": normalized}
            if include_order_by
            else {"include": "submission"}
        )

        assignments = course.get_assignments(**kw)

        for i, assignment in enumerate(assignments):
            if i != 0:
                console.print("")

            grade_string = BrushCli.derive_grade_string(brush, assignment, course)
            dinfo = DueInfo(assignment.due_at, "America/Hermosillo")

            locked_info = (
                f"🔒 {assignment.lock_explanation}"
                if assignment.locked_for_user
                else "🔓 Open"
            )
            due_string = f"📅🚫 No due date" if not dinfo.exists else f"📅 Due for {dinfo}"

            overdue = (
                f"[red]OVERDUE[/red] "
                if dinfo.exists
                and datetime.now().astimezone() > dinfo.object
                and assignment.submission["workflow_state"] == "unsubmitted"
                and not assignment.locked_for_user
                else ""
            )
            console.print(
                f"""{overdue}[bold]{assignment.name}[/bold]{grade_string}
{locked_info}
{due_string}"""
            )

    @staticmethod
    def upload(args: argparse.Namespace, brush: Brush):
        assignments: list[AssignmentPlusFile] = []

        skip_bad_arguments = (
            args.skip_bad_arguments if args.skip_bad_arguments != None else False
        )

        allow_resubmit = args.allow_resubmit if args.allow_resubmit != None else True

        allow_submit_directories = (
            args.allow_submit_directories
            if args.allow_submit_directories != None
            else False
        )

        zip_directories = (
            args.zip_directories if args.zip_directories != None else False
        )

        recursive = args.recursive if args.recursive != None else False

        resource_args = []
        for resource in args.files_or_urls:
            if (
                os.path.exists(resource)
                and os.path.isdir(resource)
                and allow_submit_directories
            ):
                if zip_directories:
                    raise Exception("zipping directories is not yet supported")
                elif recursive:
                    [
                        resource_args.append(str(f))
                        for f in Path(resource).rglob("*")
                        if os.path.isfile(f)
                    ]
                else:
                    [
                        resource_args.append(f)
                        for f in os.listdir(resource)
                        if os.path.isfile(os.path.join(resource, f))
                    ]
            else:
                resource_args.append(resource)

        if not args.course:
            for i, resource in enumerate(resource_args):
                if i % 2 == 0:
                    if os.path.exists(resource):
                        assignment = brush.resolve_assignment_from_filename(
                            os.path.basename(resource)
                        )
                        resource_path = resource

                    elif "::" in resource:
                        split = resource.split("::")
                        if len(split) > 1 and validators.url(split[1]):
                            assignment = brush.resolve_assignment_from_filename(
                                split[0] + ".pdf"
                            )
                            resource_path = split[1]
                        else:
                            if skip_bad_arguments:
                                continue
                            else:
                                raise ValueError(
                                    "invalid URL argument (without course)"
                                )
                    else:
                        if skip_bad_arguments:
                            continue
                        else:
                            raise ValueError("invalid file argument")

                    skip = False
                    if not allow_resubmit:
                        for () in assignment.get_submissions():
                            if skip_bad_arguments:
                                skip = True
                                break
                            else:
                                raise ValueError("resubmitting not allowed")

                    if skip:
                        continue

                    assignments.append(AssignmentPlusFile(assignment, resource_path))

                    if i != len(args.files_or_urls) - 1:
                        path_next = args.files_or_urls[i + 1]

                        if "::" in path_next:
                            split = path_next.split("::")
                            if len(split) > 1 and validators.url(split[1]):
                                assignment = brush.resolve_assignment_from_filename(
                                    split[0] + ".pdf"
                                )
                                resource_path = split[1]
                            else:
                                raise ValueError(
                                    "invalid URL argument (without course)"
                                )
                        else:
                            assignment = brush.resolve_assignment_from_filename(
                                os.path.basename(path_next)
                            )
                            resource_path = path_next

                        assignments.append(
                            AssignmentPlusFile(assignment, resource_path)
                        )

            bar = ProgressBar(
                len(assignments),
                False,
                f"[bold green]Submitting:[/bold green]",
                f"[bold](CURRENT)/(TOTAL)[bold]",
            )

            processed = 0
            bar.update(processed)

            for e in brush.bulk_submit(assignments, args.comment):
                if isinstance(e, tuple):
                    processed += 1
                    bar.update(processed)
                if isinstance(e, bool):
                    console.print("✅ Submitted successfully.")
        else:
            for resource in args.files_or_urls:
                if validators.url(resource):
                    console.print(
                        f"[bold red]ERROR:[/bold red] Submitting URLs is not yet supported."
                    )
                else:
                    console.print(
                        brush.bulk_submit(
                            brush,
                            brush.resolve_course(args.course),
                            args.assignment,
                            resource,
                            args.comment,
                        )
                    )

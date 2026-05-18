"""neoclaw teach — Start a learning session."""
from __future__ import annotations

import click


@click.command()
@click.option("--simulator", is_flag=True, help="Use simulator")
@click.option("--lesson", type=int, default=None, help="Start at specific lesson")
@click.option("--offline", is_flag=True, help="Offline mode (no AI)")
def teach(simulator, lesson, offline):
    """Start an interactive Python learning session."""
    from neoclaw.education.curriculum import get_lesson, get_lessons
    from neoclaw.education.exercises import validate_exercise
    from neoclaw.education.hints import HintManager
    from neoclaw.education.progress_tracker import ProgressTracker

    tracker = ProgressTracker()
    hints = HintManager()

    # Pick lesson
    if lesson:
        current_lesson = get_lesson(lesson)
        if not current_lesson:
            click.echo(f"Lesson {lesson} not found.")
            return
    else:
        lessons = get_lessons()
        click.echo("Available lessons:")
        for lesson_item in lessons:
            click.echo(f"  {lesson_item.id}. {lesson_item.title} — {lesson_item.description}")
        lesson_id = click.prompt("Choose lesson", type=int, default=1)
        current_lesson = get_lesson(lesson_id)
        if not current_lesson:
            click.echo("Invalid lesson.")
            return

    click.echo(f"\n=== Lesson {current_lesson.id}: {current_lesson.title} ===")
    click.echo(current_lesson.description)
    click.echo(f"Concepts: {', '.join(current_lesson.concepts)}\n")

    for exercise in current_lesson.exercises:
        click.echo(f"\n--- Exercise: {exercise.title} ---")
        click.echo(exercise.description)
        click.echo(f"Difficulty: {'*' * exercise.difficulty}")
        click.echo("\nStarter code:")
        click.echo(exercise.starter_code)

        while True:
            click.echo("\nOptions: [s]ubmit code, [h]int, [skip], [q]uit")
            choice = click.prompt("Choice", default="s").lower()

            if choice == "q":
                click.echo("Session ended.")
                return
            elif choice == "skip":
                break
            elif choice == "h":
                hint = hints.get_hint(exercise.id)
                if hint:
                    click.echo(f"Hint ({hint.level.name}): {hint.message}")
                else:
                    click.echo("No hints available for this exercise.")
            elif choice == "s":
                click.echo("Enter your code (end with an empty line):")
                lines = []
                while True:
                    try:
                        line = input()
                        if line == "":
                            break
                        lines.append(line)
                    except EOFError:
                        break

                code = "\n".join(lines)
                if not code.strip():
                    click.echo("No code entered.")
                    continue

                click.echo("Running...")
                result = validate_exercise(exercise.id, code)

                click.echo(f"\nResult: {'PASS' if result.passed else 'FAIL'}")
                click.echo(f"Score: {result.score}/100")
                click.echo(f"Feedback: {result.feedback}")

                if result.execution.stdout:
                    click.echo(f"Output: {result.execution.stdout}")
                if result.execution.stderr:
                    click.echo(f"Error: {result.execution.stderr}")

                tracker.record_attempt(exercise.id, result.passed, result.score)

                if result.passed:
                    click.echo("Moving to next exercise!")
                    break

    click.echo("\n=== Lesson Complete! ===")
    click.echo(f"Completion rate: {tracker.get_completion_rate():.0f}%")
    next_ex = tracker.get_next_exercise()
    if next_ex:
        click.echo(f"Next suggested exercise: {next_ex}")

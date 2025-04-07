from pathlib import Path

from rich.console import Console
from rich.status import Status

from core.classroom import get_assignments, get_courses
from core.google import get_service
from core.grader import SubmissionsGrader
from models import Course, CourseWork

from .questions import (
    GradingPreference,
    get_grading_preference,
    select_assignment,
    select_course,
    select_or_generate_criteria,
    send_email_copy_confirmation,
    should_send_email,
)

console = Console()


def get_selection() -> tuple[Course | None, CourseWork | None]:
    """Obtém as seleções do usuário."""
    classroom_service = get_service("classroom", "v1")

    with Status("Carregando cursos...", spinner="dots"):
        courses = get_courses(classroom_service)

    if not courses:
        console.print("[red]Nenhum curso encontrado.[/red]")
        return None, None

    course = select_course(classroom_service, courses)
    if not course:
        return None, None

    with Status("Carregando atividades...", spinner="dots"):
        assignments = get_assignments(classroom_service, course.id)

    if not assignments:
        console.print("[red]Nenhuma atividade encontrada.[/red]")
        return None, None

    coursework = select_assignment(classroom_service, course.id, assignments)
    if not coursework:
        return None, None

    return course, coursework


def main():
    """Função principal do CLI."""
    console.print("[bold blue]🎓 Classroom Autograder 🎓[/bold blue]\n")

    try:
        # Obtém seleções do usuário
        course, coursework = get_selection()
        if not course or not coursework:
            return

        output_dir = Path("output") / course.id / coursework.id
        output_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"[green]Feedbacks serão salvos em: {output_dir}[/green]")

        classroom_service = get_service("classroom", "v1")
        drive_service = get_service("drive", "v3")

        criteria_path = select_or_generate_criteria(
            coursework,
            drive_service,
            output_dir,
        )

        send_email = should_send_email()
        if send_email:
            send_email_copy = send_email_copy_confirmation()
        else:
            send_email_copy = False

        grading_preference = get_grading_preference()

        return_grades = grading_preference == GradingPreference.RETURN
        submissions_grader = SubmissionsGrader(
            classroom_service,
            drive_service,
            course,
            coursework,
            criteria_path,
            output_dir,
            send_email=send_email,
            send_email_copy=send_email_copy,
            return_grades=return_grades,
        )

        submissions_grader.grade()

        console.print("\n[green]✨ Processo concluído![/green]")

    except Exception as e:
        console.print(f"[red]Erro: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    main()

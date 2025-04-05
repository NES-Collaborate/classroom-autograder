from typing import Tuple

from rich.console import Console
from rich.status import Status

from auth.google import get_service
from classroom import get_assignments, get_courses
from core.grader import grade_submissions

from .questions import (
    get_assignment_id,
    get_course_id,
    select_assignment,
    select_course,
    select_or_generate_criteria,
)

console = Console()


def get_selection() -> Tuple[str | None, str | None]:
    """Obtém as seleções do usuário."""
    classroom_service = get_service("classroom", "v1")

    with Status("Carregando cursos...", spinner="dots"):
        courses = get_courses(classroom_service)

    if not courses:
        console.print("[red]Nenhum curso encontrado.[/red]")
        return None, None

    selected_course = select_course(courses)
    if not selected_course:
        return None, None

    course_id = get_course_id(selected_course)

    with Status("Carregando atividades...", spinner="dots"):
        assignments = get_assignments(classroom_service, course_id)

    if not assignments:
        console.print("[red]Nenhuma atividade encontrada.[/red]")
        return None, None

    selected_assignment = select_assignment(assignments)
    if not selected_assignment:
        return None, None

    assignment_id = get_assignment_id(selected_assignment)

    return course_id, assignment_id


def main():
    """Função principal do CLI."""
    console.print("[bold blue]🎓 Classroom Autograder[/bold blue]\n")

    try:
        # Obtém seleções do usuário
        course_id, assignment_id = get_selection()
        if not course_id or not assignment_id:
            return

        classroom_service = get_service("classroom", "v1")
        drive_service = get_service("drive", "v3")

        criteria_path = select_or_generate_criteria()
        if not criteria_path:
            return

        grade_submissions(
            classroom_service, drive_service, course_id, assignment_id, criteria_path
        )

        console.print("\n[green]✨ Processo concluído![/green]")

    except Exception as e:
        console.print(f"[red]Erro: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    main()

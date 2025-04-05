from typing import Tuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from auth.google import get_service
from classroom import get_assignments, get_courses
from core.grader import grade_submissions

from .questions import create_selection_form, get_assignment_id, get_course_id

console = Console()


def get_selection() -> Tuple[str | None, str | None]:
    """Obtém as seleções do usuário."""

    classroom_service = get_service("classroom", "v1")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Carrega cursos
        progress.add_task(description="Carregando cursos...", total=None)
        courses = get_courses(classroom_service)

        if not courses:
            console.print("[red]Nenhum curso encontrado.[/red]")
            return None, None

        # Carrega atividades do primeiro curso (será atualizado após seleção)
        # TODO: somente carregar atividades após seleção do curso.
        progress.add_task(description="Carregando atividades...", total=None)
        first_course_id = courses[0]["id"]
        assignments = get_assignments(classroom_service, first_course_id)

        if not assignments:
            console.print("[red]Nenhuma atividade encontrada.[/red]")
            return None, None

    # Apresenta formulário de seleção
    answers = create_selection_form(courses, assignments).ask()

    if not answers:
        return None, None

    course_id = get_course_id(answers["course"])
    assignment_id = get_assignment_id(answers["assignment"])

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

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Corrigindo submissões...", total=None)
            grade_submissions(
                classroom_service, drive_service, course_id, assignment_id
            )

        console.print("\n[green]✨ Processo concluído![/green]")

    except Exception as e:
        console.print(f"[red]Erro: {str(e)}[/red]")
        raise


if __name__ == "__main__":
    main()

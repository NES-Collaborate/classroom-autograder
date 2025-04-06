"""Google Classroom integration module."""

from typing import Any, Dict, List

from rich.console import Console

console = Console()


def get_courses(service) -> List[Dict[str, Any]]:
    """Recupera lista de cursos do Google Classroom."""
    try:
        results = (
            service.courses().list(pageSize=100, courseStates=["ACTIVE"]).execute()
        )
        courses = results.get("courses", [])
        return courses
    except Exception as e:
        console.print(f"[red]Erro ao buscar cursos: {str(e)}[/red]")
        return []


def get_assignments(service, course_id: str) -> List[Dict[str, Any]]:
    """Recupera lista de atividades de um curso."""
    try:
        results = (
            service.courses()
            .courseWork()
            .list(courseId=course_id, pageSize=100, orderBy="dueDate desc")
            .execute()
        )
        assignments = results.get("courseWork", [])
        return assignments
    except Exception as e:
        console.print(f"[red]Erro ao buscar atividades: {str(e)}[/red]")
        return []

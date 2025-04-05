from typing import Any, Dict, List

import questionary
from rich.console import Console

console = Console()


def create_course_choices(courses: List[Dict[str, Any]]) -> List[str]:
    """Cria as opções de cursos para seleção."""
    return [f"{course['name']} ({course['id']})" for course in courses]


def create_assignment_choices(assignments: List[Dict[str, Any]]) -> List[str]:
    """Cria as opções de atividades para seleção."""
    return [f"{assignment['title']} ({assignment['id']})" for assignment in assignments]


def get_course_id(selected_course: str) -> str:
    """Extrai o ID do curso da string de seleção."""
    return selected_course.split("(")[-1].strip(")")


def get_assignment_id(selected_assignment: str) -> str:
    """Extrai o ID da atividade da string de seleção."""
    return selected_assignment.split("(")[-1].strip(")")


def create_selection_form(
    courses: List[Dict[str, Any]], assignments: List[Dict[str, Any]]
):
    """Cria o formulário de seleção."""
    return questionary.form(
        course=questionary.select(
            "Selecione o curso:", choices=create_course_choices(courses)
        ),
        assignment=questionary.select(
            "Selecione a atividade:", choices=create_assignment_choices(assignments)
        ),
    )

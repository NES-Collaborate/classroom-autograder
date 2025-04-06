from pathlib import Path
from typing import Any, Dict, List

import questionary
from rich.console import Console

from core.criteria_generator import CriteriaGenerator

console = Console()


def select_criteria_mode() -> str:
    """Solicita ao usuário que escolha entre usar um critério existente ou gerar um novo."""
    return questionary.select(
        "Como você quer definir os critérios de avaliação?",
        choices=[
            "Usar um arquivo existente",
            "Gerar um novo baseado no enunciado",
        ],
    ).ask()


def select_or_generate_criteria(
    course_id: str,
    assignment_id: str,
    classroom_service: ...,
    drive_service: ...,
    output_dir: Path,
) -> Path:
    """Gerencia a seleção ou geração de critérios de avaliação."""
    mode = select_criteria_mode()

    if mode == "Gerar um novo baseado no enunciado":
        criteria_generator = CriteriaGenerator(
            course_id, assignment_id, classroom_service, drive_service, output_dir
        )
        return criteria_generator.generate()

    return select_criteria_file()


def select_criteria_file() -> Path:
    """Solicita ao usuário que informe o caminho do arquivo de critérios."""
    return Path(
        questionary.path(
            "Informe o caminho do arquivo de critérios:",
            default="criteria.md",
            only_directories=False,
            file_filter=lambda path: path.endswith(".md"),
        ).ask()
    ).resolve()


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


def select_course(courses: List[Dict[str, Any]]) -> str:
    """Solicita ao usuário que selecione um curso."""
    return questionary.select(
        "Selecione o curso:", choices=create_course_choices(courses)
    ).ask()


def select_assignment(assignments: List[Dict[str, Any]]) -> str:
    """Solicita ao usuário que selecione uma atividade."""
    return questionary.select(
        "Selecione a atividade:", choices=create_assignment_choices(assignments)
    ).ask()

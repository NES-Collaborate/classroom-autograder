from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import questionary
from rich.console import Console

from core.criteria_generator import CriteriaGenerator
from models import Course, CourseWork, TeacherProfile

console = Console()


class GradingPreference(str, Enum):
    DRAFT = "Salvar notas como rascunho"
    RETURN = "Retornar notas automaticamente para os alunos"


def get_grading_preference() -> GradingPreference:
    """Pergunta ao usuário como deseja lidar com as notas."""
    return questionary.select(
        "Como você deseja lidar com as notas?",
        choices=[pref.value for pref in GradingPreference],
    ).ask()


def setup_teacher_profile() -> TeacherProfile:
    """Solicita informações do perfil do professor."""
    name = questionary.text("Nome do Professor:").ask()
    whatsapp = questionary.text(
        "Número do WhatsApp (formato: 5511999999999):",
        validate=lambda text: len(text) >= 12 and text.isdigit(),
    ).ask()
    email = questionary.text(
        "Email para envio dos feedbacks:",
        validate=lambda text: "@" in text and "." in text.split("@")[1],
    ).ask()
    smtp_server = questionary.text("Servidor SMTP (ex: mail.example.com):").ask()
    smtp_port = questionary.text(
        "Porta SMTP:",
        default="465",
        validate=lambda text: text.isdigit() and 0 < int(text) <= 65535,
    ).ask()
    smtp_password = questionary.password("Senha SMTP:").ask()

    return TeacherProfile(
        name=name,
        whatsapp=whatsapp,
        email=email,
        smtp_server=smtp_server,
        smtp_port=int(smtp_port),
        smtp_password=smtp_password,
    )


def should_send_email() -> bool:
    """Solicita ao usuário se deseja enviar feedback por email."""
    return questionary.confirm(
        "Deseja enviar os feedbacks por email?", default=False
    ).ask()


def send_email_copy_confirmation() -> bool:
    """Solicita ao usuário se deseja enviar uma copia dos feedbacks por email."""
    return questionary.confirm(
        "Deseja receber uma cópia dos feedbacks enviador por email?", default=False
    ).ask()


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
    coursework: CourseWork,
    drive_service: Any,
    output_dir: Path,
) -> Path:
    """Gerencia a seleção ou geração de critérios de avaliação."""
    mode = select_criteria_mode()

    if mode == "Gerar um novo baseado no enunciado":
        criteria_generator = CriteriaGenerator(
            coursework,
            drive_service,
            output_dir,
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


def get_course(classroom_service: Any, selected_course: str) -> Course:
    """Retorna o objeto Course a partir da seleção do usuário."""
    course_id = get_course_id(selected_course)
    result = classroom_service.courses().get(id=course_id).execute()
    return Course.model_validate(result)


def get_coursework(
    classroom_service: Any, course_id: str, selected_assignment: str
) -> CourseWork:
    """Retorna o objeto CourseWork a partir da seleção do usuário."""
    assignment_id = get_assignment_id(selected_assignment)
    result = (
        classroom_service.courses()
        .courseWork()
        .get(courseId=course_id, id=assignment_id)
        .execute()
    )
    return CourseWork.model_validate(result)


def select_course(classroom_service: Any, courses: List[Dict[str, Any]]) -> Course:
    """Solicita ao usuário que selecione um curso e retorna o objeto Course."""
    selected = questionary.select(
        "Selecione o curso:", choices=create_course_choices(courses)
    ).ask()
    return get_course(classroom_service, selected)


def select_assignment(
    classroom_service: Any, course_id: str, assignments: List[Dict[str, Any]]
) -> CourseWork:
    """Solicita ao usuário que selecione uma atividade e retorna o objeto CourseWork."""
    selected = questionary.select(
        "Selecione a atividade:", choices=create_assignment_choices(assignments)
    ).ask()
    return get_coursework(classroom_service, course_id, selected)

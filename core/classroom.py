"""Google Classroom integration module."""

from typing import Any

from rich.console import Console

from models import CourseWork

console = Console()


def get_courses(service) -> list[dict[str, Any]]:
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


def get_assignments(service, course_id: str) -> list[dict[str, Any]]:
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


def get_course_work(service, course_id: str, assignment_id: str) -> CourseWork | None:
    """Recupera o contexto de uma atividade."""
    try:
        return CourseWork.model_validate(
            service.courses()
            .courseWork()
            .get(courseId=course_id, id=assignment_id)
            .execute()
        )
    except Exception as e:
        console.print(f"[red]Erro ao buscar contexto: {str(e)}[/red]")
        return None


def grade_submission(
    service,
    course_id: str,
    course_work_id: str,
    submission_id: str,
    draft_grade: float,
    assigned_grade: float | None = None,
) -> bool:
    """
    Grade a student submission.

    Args:
        service: The classroom service object
        course_id: ID of the course
        course_work_id: ID of the coursework/assignment
        submission_id: ID of the student submission
        draft_grade: The draft grade to assign (not visible to students)
        assigned_grade: The final grade to return to student (optional)

    Returns:
        True if grading was successful, False otherwise
    """
    try:
        # Prepare the grade data
        grade_data = {"draftGrade": draft_grade}
        update_mask = "draftGrade"

        # If assigned grade is provided, include it
        if assigned_grade is not None:
            grade_data["assignedGrade"] = assigned_grade
            update_mask += ",assignedGrade"

        # Update the student submission with the grade
        service.courses().courseWork().studentSubmissions().patch(
            courseId=course_id,
            courseWorkId=course_work_id,
            id=submission_id,
            updateMask=update_mask,
            body=grade_data,
        ).execute()

        return True
    except Exception as e:
        console.print(f"[red]Erro ao atribuir nota: {str(e)}[/red]")
        return False


def return_submission(
    service,
    course_id: str,
    course_work_id: str,
    submission_id: str,
) -> bool:
    """
    Return a student submission to the student.

    Args:
        service: The classroom service object
        course_id: ID of the course
        coursework_id: ID of the coursework/assignment
        submission_id: ID of the student submission

    Returns:
        True if returning was successful, False otherwise
    """
    try:
        service.courses().courseWork().studentSubmissions().return_(
            courseId=course_id, courseWorkId=course_work_id, id=submission_id, body={}
        ).execute()

        return True
    except Exception as e:
        console.print(f"[red]Erro ao retornar submissão: {str(e)}[/red]")
        return False

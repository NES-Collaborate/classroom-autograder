"""Module for LLM integration."""

from pathlib import Path

import magentic

from core import logger
from models import FeedbackResult, UserProfile


@magentic.prompt(
    """Você é um professor avaliando o trabalho submetido por um aluno.
Seu trabalho é avaliar de forma imparcial e fornecer feedback construtivo.
O feedback deve ser claro, direto e útil para o aluno.

Você deve retornar um objeto estruturado com:
1. feedback: O feedback completo em formato markdown que inclui:
   - Pontos positivos: O que o aluno fez bem
   - Pontos negativos: O que o aluno pode melhorar
   - Sugestões: Como o aluno pode melhorar
2. grade: A nota do aluno

O feedback deve ser escrito em português e deve ser claro e direto.

Considere o seguinte trabalho submetido pelo aluno {student_name}:

{context}

Critérios de avaliação:
{criteria}
""",
    model=magentic.OpenaiChatModel("gpt-4o-mini"),
)
def evaluate_student_submissions(
    context: str, criteria: str, student_name: str
) -> FeedbackResult:
    """Avalia células de um notebook usando LLM."""
    ...


def create_feedback(
    student: UserProfile,
    context: str,
    criteria_file: Path,
) -> FeedbackResult | str:
    """Cria feedback para uma submissão."""
    try:
        criteria = criteria_file.read_text(encoding="utf-8")

        # TODO: use "with open" to use models.
        with logger.status("Gerando feedback..."):
            # Gera o feedback usando LLM
            result = evaluate_student_submissions(context, criteria, student.full_name)

        logger.info(
            f"[dim]Feedback gerado para {student.full_name}, Nota: {result.grade}[/dim]"
        )
        return result

    except Exception as e:
        logger.error(f"Erro ao gerar feedback: {str(e)}")
        return f"# Erro na Avaliação\n\nNão foi possível gerar o feedback automaticamente.\nErro: {str(e)}"


@magentic.prompt(
    """Você é um professor avaliando o trabalho submetido por um aluno.

Seu trabalho é definir critérios de avaliação para uma determinada atividade / trabalho.

Considerando o enunciado da atividade a seguir, escreva critérios de avaliação precisos e claros a fim de delegar o trabalho de correção para outro professor.

Enunciado da atividade:
{context}""",
    model=magentic.OpenaiChatModel("gpt-4o-mini"),
)
def generate_criteria(context: str) -> str:
    """Gera critérios de avaliação usando LLM."""
    ...

"""Module for LLM integration."""

from pathlib import Path

import magentic
from rich.console import Console

from models import UserProfile

console = Console()


@magentic.prompt(
    """Você é um professor avaliando o trabalho submetido por um aluno.
Seu trabalho é avaliar de forma imparcial e fornecer feedback construtivo.
O feedback deve ser claro, direto e útil para o aluno.

O feedback deve incluir:
1. Pontos positivos: O que o aluno fez bem?
2. Pontos negativos: O que o aluno pode melhorar?
3. Sugestões: Como o aluno pode melhorar?
4. Pontuação: Qual é a pontuação final do aluno? [Entre 0 e 100]

O feedback deve ser escrito em português e deve ser claro e direto.

Considere o seguinte trabalho submetido pelo aluno {student_name}:

{context}

Critérios de avaliação:
{criteria}
""",
    model=magentic.OpenaiChatModel("gpt-4o-mini"),
)
def evaluate_student_submissions(context: str, criteria: str, student_name: str) -> str:
    """Avalia células de um notebook usando LLM."""
    ...


def create_feedback(
    student: UserProfile,
    context: str,
    criteria_file: Path,
) -> str:
    """Cria feedback para uma submissão."""
    try:
        criteria = criteria_file.read_text(encoding="utf-8")

        # TODO: use "with open" to use models.
        feedback = evaluate_student_submissions(context, criteria, student.full_name)

        return feedback

    except Exception as e:
        console.print(f"[red]Erro ao gerar feedback: {str(e)}[/red]")
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

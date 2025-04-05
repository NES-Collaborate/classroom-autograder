"""Module for LLM integration."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import magentic
from rich.console import Console

console = Console()


@magentic.prompt("""
Você está avaliando uma submissão de um notebook Jupyter. Analise cada célula e forneça feedback específico.

Para cada célula, considere:
1. Qualidade do código
2. Legibilidade
3. Eficiência
4. Correção do resultado

Template do feedback:

# Avaliação

## Nota Final
[nota]

## Feedback Detalhado

[feedback por célula]

## Comentários Gerais
[comentários gerais]
""")
def evaluate_notebook(
    cells: List[Dict[str, Any]], criteria: Optional[str] = None
) -> str:
    """Avalia células de um notebook usando LLM."""
    ...


def create_feedback(
    student_id: str,
    cells: List[Dict[str, Any]],
    criteria_file: Optional[Path] = None,
) -> str:
    """Cria feedback para uma submissão."""
    try:
        # Carrega critérios de avaliação se fornecidos
        criteria = None
        if criteria_file and criteria_file.exists():
            criteria = criteria_file.read_text(encoding="utf-8")

        # Gera avaliação
        feedback = evaluate_notebook(cells, criteria)
        return feedback

    except Exception as e:
        console.print(f"[red]Erro ao gerar feedback: {str(e)}[/red]")
        return f"# Erro na Avaliação\n\nNão foi possível gerar o feedback automaticamente.\nErro: {str(e)}"

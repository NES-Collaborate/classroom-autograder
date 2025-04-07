"""Module for LLM integration."""

from pathlib import Path

import magentic

from core import logger
from models import FeedbackResult, UserProfile


@magentic.prompt(
    """Você é um professor experiente avaliando o trabalho do aluno {student_name}.
Seu objetivo é fornecer um feedback personalizado, construtivo e motivador.

## Diretrizes para o feedback:
- Mantenha um tom amigável mas profissional
- Use emojis ocasionalmente para tornar o feedback mais engajador
- Referencie partes específicas do trabalho do aluno
- Forneça exemplos concretos de como melhorar, especialmente para código
- Priorize comentários práticos e acionáveis
- Evite repetir o título da atividade ou informações que já estarão no template HTML
- Seja específico sobre o que está bom e o que precisa melhorar

## Formato do feedback:
### Pontos Positivos ✅
- Liste aqui os aspectos bem executados, com exemplos específicos
- Destaque as áreas onde o aluno demonstrou compreensão

### Oportunidades de Melhoria 🔍
- Identifique áreas específicas para desenvolvimento
- Explique claramente o que poderia ser melhorado e por quê

### Sugestões Práticas 💡
- Ofereça exemplos concretos de como melhorar
- Para código, forneça snippets corrigidos
- Sugira recursos ou técnicas específicas que possam ajudar

## Atribuição de Nota:
Avalie o trabalho de acordo com os critérios fornecidos, atribuindo uma nota justa que reflita tanto as conquistas quanto as áreas de melhoria.

## Trabalho do aluno:
{context}

## Critérios de avaliação:
{criteria}
""",
    model=magentic.OpenaiChatModel("gpt-4o-mini"),
)
def evaluate_student_submissions(
    context: str, criteria: str, student_name: str
) -> FeedbackResult:
    """Avalia submissões de alunos usando LLM com feedback personalizado."""
    ...


def create_feedback(
    student: UserProfile,
    context: str,
    criteria_file: Path,
) -> FeedbackResult | str:
    """Cria feedback para uma submissão."""
    try:
        criteria = criteria_file.read_text(encoding="utf-8")

        with logger.status("Gerando feedback personalizado..."):
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
    """Você é um professor especialista em design de avaliações educacionais.

Sua tarefa é criar critérios de avaliação detalhados, objetivos e justos para a atividade descrita abaixo.

Os critérios devem:
- Ser organizados em categorias claras (ex: funcionalidade, estrutura, estilo)
- Incluir uma distribuição equilibrada de pontos
- Fornecer métricas específicas para cada nível de desempenho
- Ser facilmente aplicáveis por outros professores

Para atividades de programação, inclua critérios sobre:
- Funcionalidade do código
- Estrutura e organização
- Eficiência e otimização
- Documentação e legibilidade
- Tratamento de erros (quando aplicável)

Enunciado da atividade:
{context}""",
    model=magentic.OpenaiChatModel("gpt-4o-mini"),
)
def generate_criteria(context: str) -> str:
    """Gera critérios de avaliação detalhados usando LLM."""
    ...

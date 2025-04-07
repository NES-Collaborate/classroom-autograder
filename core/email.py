from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from smtplib import SMTP_SSL

import markdown2
from jinja2 import Environment, FileSystemLoader

from core import logger
from models import Course, CourseWork, FeedbackResult, TeacherProfile


class EmailSender:
    ROOT = Path(__file__).parent.parent
    TEMPLATE_DIR = ROOT / "templates"

    @classmethod
    def get_instance(cls) -> "EmailSender":
        """Retorna uma instância do EmailSender com as configurações do perfil."""
        profile = TeacherProfile.load(cls.ROOT)
        if not profile:
            from cli.questions import setup_teacher_profile

            profile = setup_teacher_profile()
            profile.save(cls.ROOT)

        return cls(profile)

    def __init__(self, profile: TeacherProfile):
        """Inicializa o EmailSender com as configurações do perfil."""
        self.profile = profile
        self.smtp = SMTP_SSL(self.profile.smtp_server, self.profile.smtp_port)
        self.smtp.login(self.profile.email, self.profile.smtp_password)
        self.smtp.set_debuglevel(0)

        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.TEMPLATE_DIR), autoescape=True
        )
        self.template = self.jinja_env.get_template("feedback_email_template.html")

    def _create_html_message(
        self,
        to_address: str,
        subject: str,
        body: str,
        *,
        course: Course,
        coursework: CourseWork,
    ) -> MIMEMultipart:
        """Cria uma mensagem HTML com o feedback."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.profile.name} <{self.profile.email}>"
        msg["To"] = to_address

        # Render template with context
        context = {
            "feedback_content": body,
            "whatsapp_link": f"{self.profile.whatsapp_link}?text=Olá *{self.profile.name}*, gostaria de discutir o feedback recebido sobre a atividade *{coursework.title}* do curso *{course.name}* com você!!",
            "teacher_name": self.profile.name,
        }

        # Adiciona informações do curso e atividade se disponíveis
        if course:
            context["course_name"] = course.name
            context["course_description"] = course.description or "N/A"

        if coursework:
            context["assignment_title"] = coursework.title
            context["assignment_description"] = coursework.description or "N/A"
            if coursework.maxPoints:
                context["assignment_points"] = str(coursework.maxPoints)

        html = self.template.render(**context)

        text_part = MIMEText(body, "plain")
        html_part = MIMEText(html, "html")

        msg.attach(text_part)
        msg.attach(html_part)

        return msg

    def _convert_markdown_to_html(self, markdown_content: str) -> str:
        """Converte conteúdo markdown para HTML."""
        extras = {
            "code-friendly": None,  # Melhor formatação de código
            "fenced-code-blocks": None,  # Suporte a blocos de código com ```
            "tables": None,  # Suporte a tabelas
            "break-on-newline": True,  # Quebras de linha como no markdown
            "header-ids": None,  # Adiciona IDs nos cabeçalhos
        }
        return markdown2.markdown(markdown_content, extras=extras)

    def send(
        self,
        to_address: str,
        feedback: FeedbackResult,
        *,
        course: Course,
        coursework: CourseWork,
    ) -> None:
        """Envia um email com o feedback formatado em HTML."""
        email_title = f"[NES] Feedback: {course.name} - {coursework.title}"
        if feedback.grade:
            email_title += f" (Nota: {feedback.grade:.1f}"
            if coursework.maxPoints:
                email_title += f"/{coursework.maxPoints:.1f}"
            email_title += ")"

        html_feedback = self._convert_markdown_to_html(feedback.feedback)

        with logger.status(f"Enviando email para [blue]{to_address}[/blue]..."):
            msg = self._create_html_message(
                to_address,
                email_title,
                html_feedback,
                course=course,
                coursework=coursework,
            )
            self.smtp.send_message(msg)
        logger.info(f"[dim]✉️  Email enviado para {to_address}[/dim]")

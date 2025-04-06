from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from smtplib import SMTP_SSL

from jinja2 import Environment, FileSystemLoader

from models import TeacherProfile


class EmailSender:
    CONFIG_DIR = Path.home() / ".config" / "classroom-autograder"
    TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

    @classmethod
    def get_instance(cls) -> "EmailSender":
        """Retorna uma instância do EmailSender com as configurações do perfil."""
        profile = TeacherProfile.load(cls.CONFIG_DIR)
        if not profile:
            from cli.questions import setup_teacher_profile

            profile = setup_teacher_profile()
            profile.save(cls.CONFIG_DIR)

        return cls(profile)

    def __init__(self, profile: TeacherProfile):
        """Inicializa o EmailSender com as configurações do perfil."""
        self.profile = profile
        self.smtp = SMTP_SSL(self.profile.smtp_server, self.profile.smtp_port)
        self.smtp.login(self.profile.email, self.profile.smtp_password)
        self.smtp.set_debuglevel(1)

        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.TEMPLATE_DIR), autoescape=True
        )
        self.template = self.jinja_env.get_template("feedback_email_template.html")

    def _create_html_message(
        self, to_address: str, subject: str, body: str
    ) -> MIMEMultipart:
        """Cria uma mensagem HTML com o feedback."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.profile.name} <{self.profile.email}>"
        msg["To"] = to_address

        # Render template with context
        html = self.template.render(
            feedback_content=body,
            whatsapp_link=self.profile.whatsapp_link,
            teacher_name=self.profile.name,
        )

        text_part = MIMEText(body, "plain")
        html_part = MIMEText(html, "html")

        msg.attach(text_part)
        msg.attach(html_part)

        return msg

    def send_email(self, to_address: str, subject: str, body: str) -> None:
        """Envia um email com o feedback formatado em HTML."""
        msg = self._create_html_message(to_address, subject, body)
        self.smtp.send_message(msg)

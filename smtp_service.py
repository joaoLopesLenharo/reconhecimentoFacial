import os
import smtplib
import json
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

# Caminho para o arquivo de configuração
CONFIG_FILE = Path('email_config.json')

# Carrega as configurações do arquivo JSON
def load_config() -> dict:
    """Carrega as configurações do arquivo JSON"""
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar configurações de e-mail: {e}")
        return {}

class SMTPService:
    def __init__(self):
        # Carrega as configurações do arquivo JSON
        self.config = load_config()
        
        # Configurações do servidor SMTP
        self.smtp_server = self.config.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(self.config.get('SMTP_PORT', 587))
        self.smtp_username = self.config.get('SMTP_USERNAME', '')
        self.smtp_password = self.config.get('SMTP_PASSWORD', '')
        self.sender_email = self.config.get('SMTP_SENDER_EMAIL', self.smtp_username)
        self.sender_name = self.config.get('SMTP_SENDER_NAME', 'Sistema de Monitoramento')
        
        print("Configurações de e-mail carregadas:")
        print(f"- Servidor: {self.smtp_server}:{self.smtp_port}")
        print(f"- Usuário: {self.smtp_username}")

    def send_email(self, to_email: str, subject: str, body_text: str, html_content: str = None) -> Dict[str, Any]:
        """
        Envia um e-mail usando SMTP
        
        Args:
            to_email: E-mail do destinatário
            subject: Assunto do e-mail
            body_text: Corpo do e-mail em texto puro
            html_content: (Opcional) Conteúdo HTML do e-mail
            
        Returns:
            Dict com status e mensagem
        """
        if not all([self.smtp_username, self.smtp_password]):
            return {
                'success': False,
                'error': 'Configuração de e-mail não encontrada. Configure SMTP_USERNAME e SMTP_PASSWORD.'
            }

        try:
            # Cria a mensagem
            msg = MIMEMultipart('alternative' if html_content else 'mixed')
            msg['From'] = f'"{self.sender_name}" <{self.sender_email}>'
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Adiciona o corpo da mensagem em texto puro
            part1 = MIMEText(body_text, 'plain', 'utf-8')
            
            if html_content:
                # Se houver conteúdo HTML, adiciona ambas as versões (texto e HTML)
                part2 = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(part1)
                msg.attach(part2)
            else:
                # Se não houver HTML, usa apenas o texto simples
                msg.attach(part1)
            
            # Conecta e envia o e-mail
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return {'success': True, 'message': 'E-mail enviado com sucesso'}
            
        except smtplib.SMTPException as e:
            return {
                'success': False,
                'error': f'Erro ao enviar e-mail: {str(e)}',
                'smtp_error': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro inesperado: {str(e)}'
            }

# Instância global do serviço SMTP
smtp_service = SMTPService()

def send_email(to_email: str, subject: str, body_text: str, html_content: str = None) -> Dict[str, Any]:
    """Função de conveniência para enviar e-mail"""
    return smtp_service.send_email(to_email, subject, body_text, html_content)

def is_configured() -> bool:
    """Verifica se o serviço SMTP está configurado"""
    config = load_config()
    return bool(config.get('SMTP_USERNAME') and config.get('SMTP_PASSWORD'))

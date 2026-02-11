import secrets
import logging
from typing import Optional
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

from ...domain.entities.auth_security import EmailVerification
from ...domain.ports.repository_ports import UserRepositoryPort

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending verification and transactional emails."""
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_use_tls: bool = True,
        from_email: Optional[str] = None,
        from_name: str = "clipsmith"
        user_repo: UserRepositoryPort = None
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.smtp_use_tls = smtp_use_tls or os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@clipsmith.com")
        self.from_name = from_name
        self.user_repo = user_repo
        
        # Initialize SMTP server
        self._smtp_server = None
        self._init_smtp_server()
    
    def _init_smtp_server(self):
        """Initialize SMTP server connection."""
        if not self.smtp_host or not self.smtp_user:
            logger.info("SMTP not configured - emails will be logged to console")
            return
        
        try:
            self._smtp_server = smtplib.SMTP(
                host=self.smtp_host,
                port=self.smtp_port,
                timeout=30
            )
            
            if self.smtp_use_tls:
                self._smtp_server.starttls()
            
            self._smtp_server.login(self.smtp_user, self.smtp_password)
            logger.info(f"SMTP server connected to {self.smtp_host}")
            
        except Exception as e:
            logger.error(f"Failed to initialize SMTP server: {e}")
            self._smtp_server = None
    
    def send_verification_email(self, user_email: str, verification_token: str, user_name: str) -> bool:
        """Send email verification email."""
        subject = "Verify your clipsmith account"
        
        # Create verification link
        verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={verification_token}"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Welcome to clipsmith, {user_name}!</h2>
                    <p style="font-size: 16px; margin-bottom: 20px;">Thank you for joining our community. To complete your registration, please verify your email address.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #2c3e50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                            Verify Email Address
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #666; margin-top: 20px;">
                        This link will expire in <strong>24 hours</strong>. If you didn't create an account, please ignore this email.
                    </p>
                    
                    <p style="font-size: 12px; color: #999; margin-top: 30px;">
                        If you have any questions, please contact our support team at support@clipsmith.com
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
        Welcome to clipsmith, {user_name}!
        
        Please verify your email address by clicking this link:
        {verification_url}
        
        This link will expire in 24 hours. If you didn't create an account, please ignore this email.
        
        clipsmith Team
        """
        
        return self._send_email(
            to_email=user_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
    
    def send_2fa_code_email(self, user_email: str, code: str, method: str, user_name: str) -> bool:
        """Send 2FA code email."""
        subject = f"Your clipsmith verification code ({method.upper()})"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">clipsmith Security Code</h2>
                    <p style="font-size: 16px; margin-bottom: 20px;">Hello {user_name},</p>
                    <p style="font-size: 16px; margin-bottom: 20px;">Your verification code is:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 8px; text-align: center; margin: 20px 0; font-family: monospace;">
                        <span style="font-size: 32px; font-weight: bold; letter-spacing: 3px; color: #2c3e50;">
                            {code}
                        </span>
                    </div>
                    
                    <p style="font-size: 14px; color: #666; margin-top: 20px;">
                        This code will expire in <strong>5 minutes</strong>.
                    </p>
                    
                    <p style="font-size: 12px; color: #999; margin-top: 20px;">
                        If you didn't request this code, please secure your account immediately and contact support.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
        clipsmith Security Code ({method.upper()})
        
        Hello {user_name},
        
        Your verification code is: {code}
        
        This code will expire in 5 minutes.
        
        If you didn't request this code, please secure your account immediately.
        
        clipsmith Team
        """
        
        return self._send_email(
            to_email=user_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
    
    def send_password_reset_email(self, user_email: str, reset_token: str, user_name: str) -> bool:
        """Send password reset email."""
        subject = "Reset your clipsmith password"
        
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50;">Password Reset Request</h2>
                    <p style="font-size: 16px; margin-bottom: 20px;">Hello {user_name},</p>
                    <p style="font-size: 16px; margin-bottom: 20px;">We received a request to reset your password. Click the button below to reset it:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <a href="{reset_url}" 
                           style="background-color: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #666; margin-top: 20px;">
                        This link will expire in <strong>1 hour</strong>.
                    </p>
                    
                    <p style="font-size: 12px; color: #999; margin-top: 30px;">
                        If you didn't request this reset, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request
        
        Hello {user_name},
        
        We received a request to reset your password. Use this link to reset it:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this reset, please ignore this email.
        
        clipsmith Team
        """
        
        return self._send_email(
            to_email=user_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email after successful registration."""
        subject = "Welcome to clipsmith!"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #2c3e50; text-align: center;">🎉 Welcome to clipsmith!</h1>
                    
                    <p style="font-size: 18px; margin: 30px 0;">Hello {user_name},</p>
                    <p style="font-size: 16px; margin-bottom: 20px;">
                        Thank you for joining clipsmith! We're excited to have you as part of our creative community.
                    </p>
                    
                    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 8px; text-align: center; margin: 30px 0;">
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/login" 
                           style="background-color: #2c3e50; color: white; padding: 15px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block; font-size: 16px;">
                            Get Started
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #666; margin-top: 30px;">
                        Best regards,<br>
                        The clipsmith Team
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
        Welcome to clipsmith!
        
        Hello {user_name},
        
        Thank you for joining clipsmith! We're excited to have you as part of our creative community.
        
        Get started here: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}/login
        
        Best regards,
        The clipsmith Team
        """
        
        return self._send_email(
            to_email=user_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
    
    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send email using configured SMTP server."""
        if not self._smtp_server:
            # Log email to console if SMTP not configured
            logger.info(f"Email would be sent to {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"HTML Body: {html_body[:200]}...")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            msg['Subject'] = subject
            msg['From'] = formataddr((self.from_name, self.from_email))
            msg['To'] = to_email
            
            # Send email
            text = msg.as_string()
            self._smtp_server.sendmail(self.from_email, [to_email], text)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
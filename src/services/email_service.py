"""
Email service for sending reflection summaries and analysis reports
"""
import logging
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
from typing import Dict, Any, Optional
from datetime import datetime
import os

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails with reflection summaries and analysis reports"""
    
    def __init__(self):
        self.settings = get_settings()
        self.smtp_server = getattr(self.settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(self.settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(self.settings, 'SMTP_USERNAME', None)
        self.smtp_password = getattr(self.settings, 'SMTP_PASSWORD', None)
        self.from_email = getattr(self.settings, 'FROM_EMAIL', self.smtp_username)
        self.smtp_timeout = getattr(self.settings, 'SMTP_TIMEOUT', 15)
        self.enabled = bool(self.smtp_username and self.smtp_password)
        
        if not self.enabled:
            logger.warning("Email service not configured - SMTP credentials missing")
    
    async def _send_email(
        self,
        recipient_email: str,
        subject: str,
        text_content: str,
        html_content: Optional[str] = None,
        attachments: Optional[list] = None
    ) -> bool:
        """
        Internal method to send email via SMTP
        
        Args:
            recipient_email: Email address to send to
            subject: Email subject line
            text_content: Plain text email body
            html_content: Optional HTML email body
            attachments: Optional list of attachment dicts with 'filename' and 'content'
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not enabled - cannot send email")
            return False
        
        try:
            # Build the message synchronously
            def build_message():
                msg_local = MIMEMultipart('alternative')
                msg_local['From'] = self.from_email
                msg_local['To'] = recipient_email
                msg_local['Subject'] = subject
                # Text content
                text_part_local = MIMEText(text_content, 'plain')
                msg_local.attach(text_part_local)
                # HTML content
                if html_content:
                    html_part_local = MIMEText(html_content, 'html')
                    msg_local.attach(html_part_local)
                # Attachments
                if attachments:
                    for attachment in attachments:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment['content'])
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f"attachment; filename= {attachment['filename']}")
                        msg_local.attach(part)
                return msg_local

            msg = build_message()

            # Blocking SMTP IO wrapped in a thread with timeout
            def send_sync():
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.smtp_timeout) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)

            await asyncio.to_thread(send_sync)

            logger.info(f"Successfully sent email to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}", exc_info=True)
            return False
    
    async def send_reflection_summary(
        self, 
        recipient_email: str, 
        reflection_summary: Dict[str, Any],
        participant_name: str = "MI Practitioner"
    ) -> bool:
        """
        Send reflection summary via email
        
        Args:
            recipient_email: Email address to send to
            reflection_summary: The reflection summary data
            participant_name: Name of the participant
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not enabled - cannot send reflection summary")
            return False
        
        try:
            subject = f"1 to 1 Practice Reflection Summary - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Generate text content
            text_content = self._format_reflection_text(reflection_summary, participant_name)
            
            # Generate HTML content (optional enhancement)
            html_content = self._format_reflection_html(reflection_summary, participant_name)
            
            return await self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                text_content=text_content,
                html_content=html_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send reflection summary: {e}", exc_info=True)
            return False
    
    def _format_reflection_text(self, reflection_summary: Dict[str, Any], participant_name: str) -> str:
        """Format reflection summary as plain text"""
        text = f"""
Hello {participant_name},

Thank you for completing your practice reflection on the 1 to 1 Platform.

REFLECTION SUMMARY
==================

{reflection_summary.get('summary', 'No summary available')}

SESSION DETAILS
===============
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

Keep practicing! Come back anytime to continue improving your skills.

- The 1-1 Practice Platform Team
Virtual Health Labs
        """
        return text.strip()
    
    def _format_reflection_html(self, reflection_summary: Dict[str, Any], participant_name: str) -> str:
        """Format reflection summary as HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #008080 0%, #66b2b2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }}
        .section {{ background: white; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #008080; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Practice Reflection Summary</h1>
            <p>1 to 1 Practice Platform</p>
        </div>
        <div class="content">
            <p>Hello {participant_name},</p>
            <p>Thank you for completing your practice reflection.</p>
            
            <div class="section">
                <h2>Your Reflection</h2>
                <p>{reflection_summary.get('summary', 'No summary available')}</p>
            </div>
            
            <div class="footer">
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</p>
                <p>Keep practicing! Come back anytime to continue improving your skills.</p>
                <p><strong>Virtual Health Labs</strong></p>
            </div>
        </div>
    </div>
</body>
</html>
        """
        return html.strip()
    
    async def send_analysis_report(
        self,
        recipient_email: str,
        analysis_result: Dict[str, Any],
        participant_name: str = "MI Practitioner"
    ) -> bool:
        """
        Send analysis report via email
        
        Args:
            recipient_email: Email address to send to
            analysis_result: The analysis result data
            participant_name: Name of the participant
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Email service not enabled - cannot send analysis report")
            return False
        
        try:
            subject = f"Practice Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Generate text content
            text_content = self._format_analysis_text(analysis_result, participant_name)
            
            return await self._send_email(
                recipient_email=recipient_email,
                subject=subject,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Failed to send analysis report: {e}", exc_info=True)
            return False
    
    def _format_analysis_text(self, analysis_result: Dict[str, Any], participant_name: str) -> str:
        """Format analysis result as plain text"""
        text = f"""
Hello {participant_name},

Your practice session analysis is ready.

ANALYSIS SUMMARY
================

{json.dumps(analysis_result, indent=2)}

SESSION DETAILS
===============
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

- The 1-1 Practice Platform Team
Virtual Health Labs
        """
        return text.strip()


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get or create the email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

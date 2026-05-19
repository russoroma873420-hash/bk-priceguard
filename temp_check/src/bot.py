"""Telegram bot module for sending price alerts"""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org"


def send_telegram(token: str, chat_id: str, message: str,
                  parse_mode: str = "HTML", use_mock: bool = False) -> bool:
    """Send message to Telegram chat

    Args:
        token: Bot token from @BotFather
        chat_id: Chat ID (can be string or int)
        message: Message text (supports HTML formatting)
        parse_mode: Message parsing mode ('HTML', 'Markdown', or 'MarkdownV2')
        use_mock: Use mock response (for testing)

    Returns:
        True if message sent successfully, False otherwise
    """
    if not token or not chat_id or not message:
        logger.error("Missing required parameters: token, chat_id, or message")
        return False

    # For testing/development
    if token == "YOUR_BOT_TOKEN_HERE" or token.startswith("MOCK_"):
        if use_mock:
            logger.info(f"[MOCK] Would send to {chat_id}: {message[:50]}...")
            return True
        else:
            logger.warning("Telegram token not configured properly")
            return False

    try:
        # Telegram Bot API endpoint
        url = f"{TELEGRAM_API_URL}/bot{token}/sendMessage"

        payload = {
            'chat_id': str(chat_id),
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }

        logger.debug(f"Sending message to {chat_id}")
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()
        if result.get('ok'):
            logger.info(f"Message sent to {chat_id} (message_id={result.get('result', {}).get('message_id')})")
            return True
        else:
            logger.error(f"Telegram API error: {result.get('description')}")
            return False

    except requests.exceptions.Timeout:
        logger.error("Timeout sending message to Telegram")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("Connection error sending message to Telegram")
        return False
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error sending message: {e}")
        return False
    except ValueError as e:
        logger.error(f"Invalid JSON response from Telegram: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        return False


def send_opportunity_alert(token: str, chat_id: str, opportunity) -> bool:
    """Send price opportunity alert to Telegram

    Args:
        token: Bot token
        chat_id: Chat ID
        opportunity: PriceOpportunity object

    Returns:
        True if sent successfully
    """
    try:
        message = opportunity.format_message()
        return send_telegram(token, chat_id, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send opportunity alert: {e}")
        return False


def send_status_report(token: str, chat_id: str, status_data: dict) -> bool:
    """Send monitoring status report to Telegram

    Args:
        token: Bot token
        chat_id: Chat ID
        status_data: Dictionary with status info:
            {
                'total_checks': int,
                'opportunities_found': int,
                'dumping_alerts': int,
                'advantage_alerts': int,
                'errors': int,
                'timestamp': datetime
            }

    Returns:
        True if sent successfully
    """
    try:
        message = format_status_report(status_data)
        return send_telegram(token, chat_id, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send status report: {e}")
        return False


def format_status_report(status_data: dict) -> str:
    """Format status report as HTML message

    Args:
        status_data: Status dictionary

    Returns:
        Formatted HTML message
    """
    timestamp = status_data.get('timestamp', '')
    total_checks = status_data.get('total_checks', 0)
    opportunities = status_data.get('opportunities_found', 0)
    dumping = status_data.get('dumping_alerts', 0)
    advantage = status_data.get('advantage_alerts', 0)
    errors = status_data.get('errors', 0)

    message = (
        "<b>📊 BK-PriceGuard Status Report</b>\n\n"
        f"<b>Timestamp:</b> {timestamp}\n"
        f"<b>Checks performed:</b> {total_checks}\n"
        f"<b>Opportunities found:</b> {opportunities}\n"
        f"  • <b>Dumping alerts:</b> {dumping}\n"
        f"  • <b>Our advantages:</b> {advantage}\n"
        f"<b>Errors:</b> {errors}\n"
    )
    return message


def send_error_notification(token: str, chat_id: str, error_message: str,
                           error_type: str = "ERROR") -> bool:
    """Send error notification to Telegram

    Args:
        token: Bot token
        chat_id: Chat ID
        error_message: Error description
        error_type: Type of error

    Returns:
        True if sent successfully
    """
    try:
        message = (
            f"<b>⚠️ {error_type}</b>\n\n"
            f"<code>{error_message}</code>"
        )
        return send_telegram(token, chat_id, message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")
        return False


class TelegramNotifier:
    """Helper class for managing Telegram notifications"""

    def __init__(self, token: str, chat_id: str):
        """Initialize notifier

        Args:
            token: Bot token
            chat_id: Chat ID
        """
        self.token = token
        self.chat_id = chat_id
        self.message_count = 0

    def notify_opportunity(self, opportunity) -> bool:
        """Send opportunity alert"""
        success = send_opportunity_alert(self.token, self.chat_id, opportunity)
        if success:
            self.message_count += 1
        return success

    def notify_status(self, status_data: dict) -> bool:
        """Send status report"""
        success = send_status_report(self.token, self.chat_id, status_data)
        if success:
            self.message_count += 1
        return success

    def notify_error(self, error_message: str, error_type: str = "ERROR") -> bool:
        """Send error notification"""
        success = send_error_notification(self.token, self.chat_id, error_message, error_type)
        if success:
            self.message_count += 1
        return success

    def get_stats(self) -> dict:
        """Get notifier statistics"""
        return {
            'total_messages_sent': self.message_count
        }

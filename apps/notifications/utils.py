# ── utils.py ──────────────────────────────────────────────────────────────────
from .models import Notification


def create_notification(user, notification_type, title, message,
                        related_book=None, related_borrowing=None):
    """Helper to create an in-app notification."""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_book=related_book,
        related_borrowing=related_borrowing,
    )
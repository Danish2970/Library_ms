from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta


@shared_task
def send_due_date_reminders():
    """
    Runs daily at 9 AM.
    Sends email + in-app notification to students whose books are due tomorrow.
    """
    from apps.borrowings.models import Borrowing
    from .utils import create_notification

    tomorrow = (timezone.now() + timedelta(days=1)).date()
    due_tomorrow = Borrowing.objects.filter(
        status='ISSUED', due_date=tomorrow
    ).select_related('user', 'book')

    for borrowing in due_tomorrow:
        user = borrowing.user
        book = borrowing.book

        # In-app notification
        create_notification(
            user=user,
            notification_type='DUE_REMINDER',
            title=f"Due Tomorrow: {book.title}",
            message=f"Please return '{book.title}' by tomorrow ({borrowing.due_date.strftime('%d %b %Y')}) to avoid a fine.",
            related_book=book,
            related_borrowing=borrowing,
        )

        # Email
        if user.email:
            send_mail(
                subject=f"[Library] Due Tomorrow: {book.title}",
                message=(
                    f"Dear {user.get_full_name() or user.username},\n\n"
                    f"This is a reminder that '{book.title}' is due for return tomorrow "
                    f"({borrowing.due_date.strftime('%d %b %Y')}).\n\n"
                    f"Please return it on time to avoid a fine of ₹{settings.FINE_PER_DAY}/day.\n\n"
                    f"Library Management System"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )

    return f"Sent reminders for {due_tomorrow.count()} borrowings."


@shared_task
def flag_overdue_books():
    """
    Runs daily at 8 AM.
    Flags overdue borrowings, calculates fines, notifies student and librarian.
    """
    from apps.borrowings.models import Borrowing
    from apps.users.models import CustomUser
    from .utils import create_notification

    today = timezone.now().date()
    overdue = Borrowing.objects.filter(
        status='ISSUED', due_date__lt=today
    ).select_related('user', 'book')

    librarians = CustomUser.objects.filter(role='LIBRARIAN', is_active=True)

    for borrowing in overdue:
        fine = borrowing.calculate_fine()
        borrowing.status = 'OVERDUE'
        borrowing.fine_amount = fine
        borrowing.save(update_fields=['status', 'fine_amount'])

        create_notification(
            user=borrowing.user,
            notification_type='OVERDUE',
            title=f"Overdue: {borrowing.book.title}",
            message=f"'{borrowing.book.title}' is overdue by {(today - borrowing.due_date).days} day(s). Current fine: ₹{fine}.",
            related_book=borrowing.book,
            related_borrowing=borrowing,
        )

    # Notify librarians with a summary
    if overdue.count() > 0:
        for librarian in librarians:
            create_notification(
                user=librarian,
                notification_type='OVERDUE',
                title=f"{overdue.count()} Overdue Books Today",
                message=f"There are {overdue.count()} overdue borrowings as of {today.strftime('%d %b %Y')}. Check the borrowings dashboard.",
            )

    return f"Flagged {overdue.count()} overdue borrowings."


@shared_task
def notify_new_arrival(book_id):
    """
    Triggered when a librarian adds a new book.
    Notifies users who have previously borrowed books of the same genre.
    """
    from apps.books.models import Book
    from apps.borrowings.models import BorrowingHistory
    from apps.users.models import CustomUser
    from .utils import create_notification

    try:
        book = Book.objects.get(pk=book_id)
    except Book.DoesNotExist:
        return

    # Find users who read this genre before
    interested_user_ids = BorrowingHistory.objects.filter(
        genre=book.genre
    ).values_list('user_id', flat=True).distinct()

    users = CustomUser.objects.filter(id__in=interested_user_ids, is_active=True)

    for user in users:
        create_notification(
            user=user,
            notification_type='NEW_ARRIVAL',
            title=f"New {book.get_genre_display()} book: {book.title}",
            message=f"A new book you might enjoy has arrived: '{book.title}' by {book.author}.",
            related_book=book,
        )

    return f"Notified {users.count()} users about '{book.title}'."
from django.db import models


class Notification(models.Model):
    TYPE_CHOICES = [
        ('DUE_REMINDER', 'Due Date Reminder'),
        ('OVERDUE', 'Overdue Alert'),
        ('NEW_ARRIVAL', 'New Book Arrival'),
        ('FINE', 'Fine Notice'),
        ('GENERAL', 'General'),
    ]

    user = models.ForeignKey(
        'users.CustomUser', on_delete=models.CASCADE, related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='GENERAL')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_book = models.ForeignKey(
        'books.Book', on_delete=models.SET_NULL, null=True, blank=True
    )
    related_borrowing = models.ForeignKey(
        'borrowings.Borrowing', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title} → {self.user.username}"
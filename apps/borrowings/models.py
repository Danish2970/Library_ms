from django.db import models
from django.utils import timezone
from datetime import timedelta

FINE_PER_DAY = 2  # Rs. 2 per day overdue
DEFAULT_BORROW_DAYS = 14


class Borrowing(models.Model):
    STATUS_CHOICES = [
        ('ISSUED', 'Issued'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
        ('LOST', 'Lost'),
    ]

    user = models.ForeignKey(
        'users.CustomUser', on_delete=models.CASCADE, related_name='borrowings'
    )
    book = models.ForeignKey(
        'books.Book', on_delete=models.CASCADE, related_name='borrowings'
    )
    issued_by = models.ForeignKey(
        'users.CustomUser', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='issued_borrowings'
    )
    issued_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ISSUED')
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fine_paid = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-set due_date if not provided
        if not self.due_date:
            self.due_date = (timezone.now() + timedelta(days=DEFAULT_BORROW_DAYS)).date()
        super().save(*args, **kwargs)

    def calculate_fine(self):
        """Calculate fine based on overdue days."""
        today = timezone.now().date()
        check_date = self.returned_date if self.returned_date else today
        if check_date > self.due_date:
            overdue_days = (check_date - self.due_date).days
            return overdue_days * FINE_PER_DAY
        return 0

    def is_overdue(self):
        today = timezone.now().date()
        return self.status == 'ISSUED' and today > self.due_date

    def days_remaining(self):
        today = timezone.now().date()
        delta = (self.due_date - today).days
        return delta  # negative means overdue

    def overdue_days(self):
        today = timezone.now().date()
        delta = (today - self.due_date).days
        return delta if delta > 0 else 0

    def __str__(self):
        return f"{self.user.username} — {self.book.title} ({self.status})"

    class Meta:
        ordering = ['-created_at']


class BorrowingHistory(models.Model):
    """
    Denormalized table for the ML recommendation pipeline.
    Gets populated automatically when a book is returned.
    """
    user = models.ForeignKey(
        'users.CustomUser', on_delete=models.CASCADE, related_name='borrow_history'
    )
    book = models.ForeignKey(
        'books.Book', on_delete=models.CASCADE, related_name='borrow_history'
    )
    genre = models.CharField(max_length=20)
    category = models.CharField(max_length=100, blank=True)
    borrowed_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # filled if user rated

    class Meta:
        ordering = ['-borrowed_at']

    def __str__(self):
        return f"{self.user.username} read {self.book.title}"


class FinePayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('ONLINE', 'Online'),
        ('WAIVED', 'Waived'),
    ]

    borrowing = models.OneToOneField(
        Borrowing, on_delete=models.CASCADE, related_name='payment'
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    collected_by = models.ForeignKey(
        'users.CustomUser', on_delete=models.SET_NULL, null=True, related_name='collected_fines'
    )

    def __str__(self):
        return f"Fine ₹{self.amount} for {self.borrowing}"
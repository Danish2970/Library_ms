from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('LIBRARIAN', 'Librarian'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_librarian(self):
        return self.role == 'LIBRARIAN'

    def is_student(self):
        return self.role == 'STUDENT'

    def get_active_borrows(self):
        return self.borrowings.filter(status='ISSUED')

    def get_borrow_count(self):
        return self.borrowings.count()

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


from django.contrib import admin
from .models import Borrowing, BorrowingHistory, FinePayment

@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'issued_date', 'due_date', 'status', 'fine_amount')
    list_filter = ('status', 'fine_paid')
    search_fields = ('user__username', 'book__title')
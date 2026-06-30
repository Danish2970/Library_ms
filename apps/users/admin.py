"""
Register all models across apps with the Django admin.
Run: python manage.py createsuperuser  to create librarian admin.
"""

# ── apps/users/admin.py ────────────────────────────────────────────────────────
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import CustomUser
#
# @admin.register(CustomUser)
# class CustomUserAdmin(UserAdmin):
#     list_display = ('username', 'email', 'role', 'department', 'is_active')
#     list_filter = ('role', 'department', 'is_active')
#     search_fields = ('username', 'email', 'student_id')
#     fieldsets = UserAdmin.fieldsets + (
#         ('Library Info', {'fields': ('role', 'student_id', 'department', 'phone', 'avatar')}),
#     )

# ── apps/books/admin.py ────────────────────────────────────────────────────────
# from django.contrib import admin
# from .models import Book, Category, BookRating
#
# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('name', 'slug', 'get_book_count')
#     prepopulated_fields = {'slug': ('name',)}
#
# @admin.register(Book)
# class BookAdmin(admin.ModelAdmin):
#     list_display = ('title', 'author', 'isbn', 'genre', 'available_quantity', 'total_quantity')
#     list_filter = ('genre', 'category', 'is_active')
#     search_fields = ('title', 'author', 'isbn')
#     list_editable = ('available_quantity',)

# ── apps/borrowings/admin.py ───────────────────────────────────────────────────
# from django.contrib import admin
# from .models import Borrowing, BorrowingHistory, FinePayment
#
# @admin.register(Borrowing)
# class BorrowingAdmin(admin.ModelAdmin):
#     list_display = ('user', 'book', 'issued_date', 'due_date', 'status', 'fine_amount')
#     list_filter = ('status', 'fine_paid')
#     search_fields = ('user__username', 'book__title')
#     readonly_fields = ('created_at', 'updated_at')

# Copy the relevant section into each app's admin.py file.
# This file is a reference — not meant to be imported directly.



from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active')
    search_fields = ('username', 'email', 'student_id')
    fieldsets = UserAdmin.fieldsets + (
        ('Library Info', {'fields': ('role', 'student_id', 'department', 'phone', 'avatar')}),
    )
from django.contrib import admin
from .models import Book, Category, BookRating

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'genre', 'available_quantity', 'total_quantity')
    list_filter = ('genre', 'category', 'is_active')
    search_fields = ('title', 'author', 'isbn')
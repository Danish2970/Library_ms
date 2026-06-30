from django import forms
from .models import Book, BookRating


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'isbn', 'title', 'author', 'publisher', 'publication_year',
            'genre', 'category', 'description', 'cover_image',
            'total_quantity', 'available_quantity', 'location', 'language', 'pages',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get('total_quantity', 0)
        available = cleaned.get('available_quantity', 0)
        if available > total:
            raise forms.ValidationError("Available quantity cannot exceed total quantity.")
        return cleaned


class BookRatingForm(forms.ModelForm):
    class Meta:
        model = BookRating
        fields = ['rating', 'review']
        widgets = {
            'review': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a short review...'}),
        }
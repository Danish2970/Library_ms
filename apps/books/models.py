from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_book_count(self):
        return self.books.count()

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']


class Book(models.Model):
    GENRE_CHOICES = [
        ('FICTION', 'Fiction'),
        ('NON_FICTION', 'Non-Fiction'),
        ('SCIENCE', 'Science'),
        ('TECHNOLOGY', 'Technology'),
        ('HISTORY', 'History'),
        ('BIOGRAPHY', 'Biography'),
        ('MATHEMATICS', 'Mathematics'),
        ('PHILOSOPHY', 'Philosophy'),
        ('ARTS', 'Arts'),
        ('REFERENCE', 'Reference'),
        ('OTHER', 'Other'),
    ]

    isbn = models.CharField(max_length=13, unique=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.PositiveIntegerField(null=True, blank=True)
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES, default='OTHER')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='books'
    )
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    total_quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=50, blank=True, help_text='Shelf/Rack location')
    language = models.CharField(max_length=50, default='English')
    pages = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(
        'users.CustomUser', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='added_books'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_available(self):
        return self.available_quantity > 0

    def get_average_rating(self):
        ratings = self.ratings.all()
        if not ratings:
            return 0
        return round(sum(r.rating for r in ratings) / ratings.count(), 1)

    def get_borrow_count(self):
        return self.borrowings.count()

    def __str__(self):
        return f"{self.title} by {self.author}"

    class Meta:
        ordering = ['title']


class BookRating(models.Model):
    user = models.ForeignKey(
        'users.CustomUser', on_delete=models.CASCADE, related_name='ratings'
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name='ratings'
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)]
    )
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} rated {self.book.title}: {self.rating}/5"
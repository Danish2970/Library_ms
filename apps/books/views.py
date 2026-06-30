from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Book, Category, BookRating
from .forms import BookForm, BookRatingForm
from apps.users.decorators import librarian_required


@login_required
def book_list(request):
    query = request.GET.get('q', '')
    genre = request.GET.get('genre', '')
    category_id = request.GET.get('category', '')
    available_only = request.GET.get('available', '')

    books = Book.objects.filter(is_active=True).select_related('category')

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query) |
            Q(description__icontains=query)
        )
    if genre:
        books = books.filter(genre=genre)
    if category_id:
        books = books.filter(category_id=category_id)
    if available_only:
        books = books.filter(available_quantity__gt=0)

    paginator = Paginator(books, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'genre_choices': Book.GENRE_CHOICES,
        'query': query,
        'selected_genre': genre,
        'selected_category': category_id,
    }
    return render(request, 'books/list.html', context)


@login_required
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk, is_active=True)
    user_rating = None
    if request.user.is_student():
        user_rating = BookRating.objects.filter(user=request.user, book=book).first()

    if request.method == 'POST' and request.user.is_student():
        form = BookRatingForm(request.POST, instance=user_rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.book = book
            rating.save()
            messages.success(request, "Rating submitted!")
            return redirect('books:detail', pk=pk)
    else:
        form = BookRatingForm(instance=user_rating)

    context = {
        'book': book,
        'ratings': book.ratings.select_related('user').all()[:10],
        'avg_rating': book.get_average_rating(),
        'borrow_count': book.get_borrow_count(),
        'form': form,
        'user_rating': user_rating,
    }
    return render(request, 'books/detail.html', context)


@librarian_required
def book_add(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.added_by = request.user
            book.save()

            # Notify users who borrow this genre — trigger Celery task
            from apps.notifications.tasks import notify_new_arrival
            notify_new_arrival.delay(book.id)

            messages.success(request, f"Book '{book.title}' added successfully.")
            return redirect('books:detail', pk=book.pk)
    else:
        form = BookForm()
    return render(request, 'books/form.html', {'form': form, 'action': 'Add'})


@librarian_required
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, "Book updated.")
            return redirect('books:detail', pk=pk)
    else:
        form = BookForm(instance=book)
    return render(request, 'books/form.html', {'form': form, 'action': 'Edit', 'book': book})


@librarian_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.is_active = False  # soft delete
        book.save()
        messages.success(request, f"'{book.title}' removed from catalog.")
        return redirect('books:list')
    return render(request, 'books/confirm_delete.html', {'book': book})
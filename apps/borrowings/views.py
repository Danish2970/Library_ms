from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from .models import Borrowing, BorrowingHistory, FinePayment
from apps.books.models import Book
from apps.users.models import CustomUser
from apps.users.decorators import librarian_required
from apps.notifications.utils import create_notification


MAX_BORROWS = getattr(settings, 'MAX_BOOKS_PER_STUDENT', 3)


@librarian_required
def issue_book(request):
    """Librarian issues a book to a student."""
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        book_id = request.POST.get('book_id')

        try:
            student = CustomUser.objects.get(student_id=student_id, role='STUDENT')
        except CustomUser.DoesNotExist:
            messages.error(request, "Student not found with that ID.")
            return redirect('borrowings:issue')

        book = get_object_or_404(Book, pk=book_id, is_active=True)

        # Validations
        if not book.is_available():
            messages.error(request, f"'{book.title}' is not available (0 copies left).")
            return redirect('borrowings:issue')

        active_count = student.get_active_borrows().count()
        if active_count >= MAX_BORROWS:
            messages.error(request, f"{student.get_full_name()} already has {active_count} books issued (max {MAX_BORROWS}).")
            return redirect('borrowings:issue')

        already_has = Borrowing.objects.filter(user=student, book=book, status='ISSUED').exists()
        if already_has:
            messages.error(request, f"Student already has '{book.title}' issued.")
            return redirect('borrowings:issue')

        # Create borrowing
        borrowing = Borrowing.objects.create(
            user=student,
            book=book,
            issued_by=request.user,
        )
        book.available_quantity -= 1
        book.save(update_fields=['available_quantity'])

        # Notify student
        create_notification(
            user=student,
            notification_type='GENERAL',
            title=f"Book Issued: {book.title}",
            message=f"'{book.title}' has been issued to you. Due date: {borrowing.due_date.strftime('%d %b %Y')}.",
            related_book=book,
            related_borrowing=borrowing,
        )

        messages.success(request, f"'{book.title}' issued to {student.get_full_name()}. Due: {borrowing.due_date.strftime('%d %b %Y')}.")
        return redirect('borrowings:issue')

    books = Book.objects.filter(is_active=True, available_quantity__gt=0).order_by('title')
    return render(request, 'borrowings/issue.html', {'books': books})


@login_required
def borrow_book_student(request, book_id):
    """Student borrows a book directly."""
    if request.user.is_librarian():
        return redirect('borrowings:issue')
        
    if request.method == 'POST':
        book = get_object_or_404(Book, pk=book_id, is_active=True)
        
        if not book.is_available():
            messages.error(request, f"'{book.title}' is not available (0 copies left).")
            return redirect('books:detail', pk=book_id)

        active_count = request.user.get_active_borrows().count()
        if active_count >= MAX_BORROWS:
            messages.error(request, f"You already have {active_count} books issued (max {MAX_BORROWS}).")
            return redirect('books:detail', pk=book_id)

        already_has = Borrowing.objects.filter(user=request.user, book=book, status='ISSUED').exists()
        if already_has:
            messages.error(request, f"You already have '{book.title}' issued.")
            return redirect('books:detail', pk=book_id)

        borrowing = Borrowing.objects.create(
            user=request.user,
            book=book,
        )
        book.available_quantity -= 1
        book.save(update_fields=['available_quantity'])

        create_notification(
            user=request.user,
            notification_type='GENERAL',
            title=f"Book Borrowed: {book.title}",
            message=f"'{book.title}' has been issued to you. Due date: {borrowing.due_date.strftime('%d %b %Y')}.",
            related_book=book,
            related_borrowing=borrowing,
        )

        messages.success(request, f"You successfully borrowed '{book.title}'. Due: {borrowing.due_date.strftime('%d %b %Y')}.")
        return redirect('borrowings:my_borrows')
        
    return redirect('books:detail', pk=book_id)


@login_required
def student_return_book(request, borrowing_id):
    """Student returning their own book."""
    borrowing = get_object_or_404(Borrowing, pk=borrowing_id, user=request.user, status__in=['ISSUED', 'OVERDUE'])
    
    if request.method == 'POST':
        today = timezone.now().date()
        borrowing.returned_date = today
        borrowing.status = 'RETURNED'
        fine = borrowing.calculate_fine()
        borrowing.fine_amount = fine
        borrowing.save()

        # Increment book quantity
        book = borrowing.book
        book.available_quantity += 1
        book.save(update_fields=['available_quantity'])

        # Record in ML history table
        BorrowingHistory.objects.create(
            user=borrowing.user,
            book=book,
            genre=book.genre,
            category=book.category.name if book.category else '',
            borrowed_at=borrowing.created_at,
            returned_at=timezone.now(),
        )
        
        # Trigger ML refresh for the user in background/synchronously
        try:
            from apps.recommendations.engine import refresh_recommendations_for_user
            refresh_recommendations_for_user(request.user.id)
        except Exception:
            pass

        if fine > 0:
            messages.warning(request, f"You returned '{book.title}', but you have an outstanding fine of ₹{fine}.")
        else:
            messages.success(request, f"You successfully returned '{book.title}'.")
            
        return redirect('borrowings:my_borrows')
        
    return redirect('borrowings:my_borrows')


@librarian_required
def return_book(request, borrowing_id):
    """Librarian processes a book return."""
    borrowing = get_object_or_404(Borrowing, pk=borrowing_id, status='ISSUED')

    if request.method == 'POST':
        today = timezone.now().date()
        borrowing.returned_date = today
        borrowing.status = 'RETURNED'
        fine = borrowing.calculate_fine()
        borrowing.fine_amount = fine
        borrowing.save()

        # Increment book quantity
        book = borrowing.book
        book.available_quantity += 1
        book.save(update_fields=['available_quantity'])

        # Record in ML history table
        BorrowingHistory.objects.create(
            user=borrowing.user,
            book=book,
            genre=book.genre,
            category=book.category.name if book.category else '',
            borrowed_at=borrowing.created_at,
            returned_at=timezone.now(),
        )

        if fine > 0:
            msg = f"Book returned. Fine of ₹{fine} is due."
            messages.warning(request, msg)
            create_notification(
                user=borrowing.user,
                notification_type='FINE',
                title=f"Fine Due: ₹{fine}",
                message=f"Your fine for late return of '{book.title}' is ₹{fine}.",
                related_borrowing=borrowing,
            )
        else:
            messages.success(request, f"'{book.title}' returned successfully. No fine.")

        return redirect('borrowings:all_borrows')

    context = {
        'borrowing': borrowing,
        'fine_preview': borrowing.calculate_fine(),
        'days_remaining': borrowing.days_remaining(),
    }
    return render(request, 'borrowings/return_confirm.html', context)


@login_required
def my_borrows(request):
    """Student's own borrow list. Librarians see all."""
    if request.user.is_librarian():
        return redirect('borrowings:all_borrows')

    borrows = Borrowing.objects.filter(
        user=request.user
    ).select_related('book', 'book__category').order_by('-created_at')

    # Auto-flag overdue in DB
    for b in borrows.filter(status='ISSUED'):
        if b.is_overdue():
            b.status = 'OVERDUE'
            b.fine_amount = b.calculate_fine()
            b.save(update_fields=['status', 'fine_amount'])

    context = {
        'active_borrows': borrows.filter(status__in=['ISSUED', 'OVERDUE']),
        'history': borrows.filter(status='RETURNED'),
    }
    return render(request, 'borrowings/my_borrows.html', context)


@librarian_required
def all_borrows(request):
    """Librarian view: all current borrowings with filters."""
    status_filter = request.GET.get('status', 'ISSUED')
    borrows = Borrowing.objects.filter(
        status=status_filter
    ).select_related('user', 'book').order_by('-created_at')

    context = {
        'borrows': borrows,
        'status_filter': status_filter,
        'overdue_count': Borrowing.objects.filter(status='OVERDUE').count(),
    }
    return render(request, 'borrowings/all_borrows.html', context)
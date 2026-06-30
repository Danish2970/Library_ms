from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from apps.borrowings.models import Borrowing
from apps.books.models import Book, Category
from apps.users.models import CustomUser
from apps.users.decorators import librarian_required


@login_required
def dashboard(request):
    if request.user.is_librarian():
        return librarian_dashboard(request)
    return student_dashboard(request)


def librarian_dashboard(request):
    today = timezone.now().date()
    context = {
        'total_books': Book.objects.filter(is_active=True).count(),
        'total_users': CustomUser.objects.filter(role='STUDENT', is_active=True).count(),
        'active_borrows': Borrowing.objects.filter(status='ISSUED').count(),
        'overdue_count': Borrowing.objects.filter(status='OVERDUE').count(),
        'total_fine': Borrowing.objects.aggregate(total=Sum('fine_amount'))['total'] or 0,
        'recent_borrows': Borrowing.objects.select_related('user', 'book').order_by('-created_at')[:8],
        'low_stock_books': Book.objects.filter(is_active=True, available_quantity=0).order_by('title')[:5],
    }
    return render(request, 'analytics/librarian_dashboard.html', context)


def student_dashboard(request):
    user = request.user
    active = user.get_active_borrows().select_related('book')

    # Flag overdue
    for b in active.filter(status='ISSUED'):
        if b.is_overdue():
            b.status = 'OVERDUE'
            b.fine_amount = b.calculate_fine()
            b.save(update_fields=['status', 'fine_amount'])

    context = {
        'active_borrows': active,
        'history_count': user.borrowings.filter(status='RETURNED').count(),
        'recommendations': user.recommendations.select_related('book').all()[:6],
        'total_fine': user.borrowings.aggregate(total=Sum('fine_amount'))['total'] or 0,
    }
    return render(request, 'analytics/student_dashboard.html', context)


# ── JSON endpoints for Chart.js ────────────────────────────────────────────────

@librarian_required
def chart_borrows_per_day(request):
    """Line chart: books issued per day over last 30 days."""
    days = 30
    today = timezone.now().date()
    data = []
    labels = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        count = Borrowing.objects.filter(issued_date=day).count()
        labels.append(day.strftime('%d %b'))
        data.append(count)
    return JsonResponse({'labels': labels, 'data': data})


@librarian_required
def chart_top_books(request):
    """Bar chart: top 10 most borrowed books."""
    top = (
        Book.objects.filter(is_active=True)
        .annotate(borrow_count=Count('borrowings'))
        .order_by('-borrow_count')[:10]
    )
    return JsonResponse({
        'labels': [b.title[:30] for b in top],
        'data': [b.borrow_count for b in top],
    })


@librarian_required
def chart_genre_distribution(request):
    """Pie chart: borrowings per genre."""
    data = (
        Borrowing.objects.values('book__genre')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    return JsonResponse({
        'labels': [d['book__genre'] for d in data],
        'data': [d['count'] for d in data],
    })


@librarian_required
def reports(request):
    overdue = Borrowing.objects.filter(
        status='OVERDUE'
    ).select_related('user', 'book').order_by('-due_date')

    context = {
        'overdue_borrows': overdue,
        'categories': Category.objects.annotate(book_count=Count('books')).order_by('-book_count'),
    }
    return render(request, 'analytics/reports.html', context)
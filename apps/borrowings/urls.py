from django.urls import path
from . import views

app_name = 'borrowings'

urlpatterns = [
    path('issue/', views.issue_book, name='issue'),
    path('borrow/<int:book_id>/', views.borrow_book_student, name='borrow_student'),
    path('return/<int:borrowing_id>/', views.return_book, name='return'),
    path('my/return/<int:borrowing_id>/', views.student_return_book, name='student_return'),
    path('my/', views.my_borrows, name='my_borrows'),
    path('all/', views.all_borrows, name='all_borrows'),
]